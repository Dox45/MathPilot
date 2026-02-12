import logging
import feedparser
import urllib.parse
from datetime import datetime
from typing import List, Optional
from mathpilot.search.models import Paper
from mathpilot.utils import get_logger

import httpx
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_exponential

logger = get_logger("search")

class ArxivClient:
    """Client for querying arXiv API with intelligent search strategies.
    
    Search Tips:
    - Best: Use arXiv ID (e.g., "1706.03762") for exact paper lookup
    - Good: Use explicit prefix (e.g., "ti:Your Title" or "au:Author Name")
    - Fair: Use natural language (e.g., "your research topic")
      Note: Natural language searches may not rank papers by exact title match
      due to arXiv API relevance ranking. If a specific paper isn't in the
      top results, try using its arXiv ID or explicit title prefix.
    
    Examples:
        client = ArxivClient(max_results=5)
        papers = client.search("1706.03762")  # Exact paper
        papers = client.search("au:Vaswani")  # Papers by author
        papers = client.search("machine learning optimization")  # Topic search
    """
    
    BASE_URL = "http://export.arxiv.org/api/query"

    def __init__(self, max_results: int = 10, cache_dir: Optional[str] = None):
        self.max_results = max_results
        self.cache_dir = cache_dir

    def download_pdf(self, pdf_url: str, output_path: str) -> str:
        """Download PDF from URL to output path."""
        logger.info(f"Downloading PDF from {pdf_url} to {output_path}")
        
        # Ensure directory exists
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with httpx.Client(follow_redirects=True, timeout=30.0) as client:
                response = client.get(pdf_url)
                response.raise_for_status()
                path.write_bytes(response.content)
            logger.info("Download complete.")
            return str(path)
        except Exception as e:
            logger.error(f"Failed to download PDF: {e}")
            raise
            
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def _fetch_feed(self, url: str):
        """Fetch feed with retry logic for 429/5xx errors."""
        import feedparser
        
        headers = {
            "User-Agent": "MathPilot/1.0 (mailto:admin@mathpilot.org)"
        }
        
        with httpx.Client(follow_redirects=True, timeout=30.0, headers=headers) as client:
            response = client.get(url)
            if response.status_code == 429:
                logger.warning("Rate limit hit (429), retrying...")
                response.raise_for_status()
            elif response.status_code >= 500:
                logger.warning(f"Server error ({response.status_code}), retrying...")
                response.raise_for_status()
                
            response.raise_for_status()
            return feedparser.parse(response.content)

    def search(self, query: str) -> List[Paper]:
        """
        Search arXiv for papers matching the query.
        Strategies (in order):
        1. If looks like arxiv ID (YYMM.NNNNN), search by ID
        2. If has explicit prefix (ti:, au:, etc.), use it as-is
        3. Otherwise search title and abstract
        4. If no results, try broader search across all fields
        
        Tip: For better results, provide:
        - ArXiv ID: "1706.03762"
        - Explicit prefix: "ti:Attention Is All You Need" or "au:Vaswani"
        """
        logger.info(f"Querying arXiv for: {query}")
        
        query = query.strip()
        
        # Clean up common noise
        # "et al" is often included in author searches but confuses the API
        import re
        query = re.sub(r'\b(et\.?\s*al\.?)\b', '', query, flags=re.IGNORECASE).strip()
        
        # Check if it's an arxiv ID (format: YYMM.NNNNN or YYMM.NNNNNV)
        import re
        arxiv_id_pattern = r'^(\d{4}\.\d{4,5})(v\d+)?$'
        is_arxiv_id = bool(re.match(arxiv_id_pattern, query))
        
        # Check if query already has a prefix
        prefixes = ["all:", "ti:", "au:", "abs:", "co:", "jr:", "cat:", "rn:", "id:"]
        has_prefix = any(query.startswith(p) for p in prefixes)
        
        # Strategy: Try primary search, then fallback if needed
        if has_prefix:
            # User provided explicit prefix
            search_query = query
        elif is_arxiv_id:
            # Looks like an arxiv ID
            search_query = f"id:{query}"
        else:
            # Default: search title and abstract
            search_query = f"ti:{query} OR abs:{query}"
        
        # Execute primary search
        papers = self._execute_search(search_query)
        
        # If no results and no explicit prefix, try broader search
        if not papers and not has_prefix and not is_arxiv_id:
            logger.info("No results found, trying broader search...")
            papers = self._execute_search(f"all:{query}")
        
        return papers
    
    def _execute_search(self, search_query: str) -> List[Paper]:
        """Execute the actual arXiv search query and return parsed papers."""
        params = {
            "search_query": search_query,
            "start": 0,
            "max_results": self.max_results,
            "sortBy": "relevance",
            "sortOrder": "descending"
        }
        
        encoded_query = urllib.parse.urlencode(params)
        url = f"{self.BASE_URL}?{encoded_query}"
        logger.info(f"ArXiv API URL: {url}")
        
        try:
            feed = self._fetch_feed(url)
        except Exception as e:
            logger.error(f"Failed to fetch ArXiv feed after retries: {e}")
            return []

        if feed.bozo:
             logger.error(f"Error parsing arXiv feed: {feed.bozo_exception}")
             return []

        papers = []
        for entry in feed.entries:
            try:
                # Extract PDF link
                pdf_link = None
                for link in entry.links:
                    if link.type == 'application/pdf':
                        pdf_link = link.href
                        break
                
                # Parse date
                published_dt = datetime(*entry.published_parsed[:6])
                updated_dt = datetime(*entry.updated_parsed[:6])

                paper = Paper(
                    id=entry.id.split('/abs/')[-1],
                    title=entry.title.replace('\n', ' ').strip(),
                    authors=[author.name for author in entry.authors],
                    summary=entry.summary.replace('\n', ' ').strip(),
                    published=published_dt,
                    updated=updated_dt,
                    pdf_url=pdf_link,
                    category=entry.arxiv_primary_category['term'] if 'arxiv_primary_category' in entry else 'unknown'
                )
                papers.append(paper)
            except Exception as e:
                logger.warning(f"Failed to parse paper entry: {e}")
                continue
        
        logger.info(f"Found {len(papers)} papers.")
        return papers
