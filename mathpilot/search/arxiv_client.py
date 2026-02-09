import logging
import feedparser
import urllib.parse
from datetime import datetime
from typing import List, Optional
from mathpilot.search.models import Paper
from mathpilot.utils import get_logger

logger = get_logger("search")

class ArxivClient:
    """Client for querying arXiv API."""
    
    BASE_URL = "http://export.arxiv.org/api/query"

    def __init__(self, max_results: int = 10, cache_dir: Optional[str] = None):
        self.max_results = max_results
        self.cache_dir = cache_dir

    def search(self, query: str) -> List[Paper]:
        """
        Search arXiv for papers matching the query.
        """
        logger.info(f"Querying arXiv for: {query}")
        
        # Prepare query parameters
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": self.max_results,
            "sortBy": "relevance",
            "sortOrder": "descending"
        }
        
        encoded_query = urllib.parse.urlencode(params)
        url = f"{self.BASE_URL}?{encoded_query}"
        
        feed = feedparser.parse(url)

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
