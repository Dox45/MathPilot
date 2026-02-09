"""PDF parsing and text extraction utilities."""

import logging
from pathlib import Path
from typing import Optional

import pdfplumber

logger = logging.getLogger(__name__)


def extract_pdf_text(pdf_path: str, max_pages: Optional[int] = None) -> str:
    """
    Extract all text from PDF file.

    Args:
        pdf_path: Path to PDF file
        max_pages: Optional limit on number of pages to extract

    Returns:
        Complete text from PDF

    Raises:
        FileNotFoundError: If PDF doesn't exist
        ValueError: If PDF cannot be parsed
    """
    path = Path(pdf_path).expanduser()

    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    logger.debug(f"Extracting text from: {path}")

    try:
        with pdfplumber.open(path) as pdf:
            pages = pdf.pages
            if max_pages:
                pages = pages[:max_pages]

            text_parts = []
            for i, page in enumerate(pages):
                try:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {i + 1}: {e}")
                    continue

            full_text = "\n\n".join(text_parts)
            logger.debug(f"Extracted {len(full_text)} characters from {len(pages)} pages")
            return full_text

    except Exception as e:
        raise ValueError(f"Failed to parse PDF: {e}") from e


def extract_pdf_sections(
    pdf_path: str,
    sections: list[str] | None = None,
    max_pages: Optional[int] = None,
) -> dict[str, str]:
    """
    Extract specific sections from PDF based on section headers.

    Common sections: 'abstract', 'introduction', 'methods', 'results', 'conclusion'

    Args:
        pdf_path: Path to PDF file
        sections: List of section names to extract (case-insensitive)
        max_pages: Optional limit on number of pages to extract

    Returns:
        Dict mapping section names to extracted text
        (sections not found will have empty strings)

    Raises:
        FileNotFoundError: If PDF doesn't exist
        ValueError: If PDF cannot be parsed
    """
    if sections is None:
        sections = ["abstract", "introduction", "methods"]

    # Normalize section names for matching
    target_sections = {s.lower(): s for s in sections}

    logger.debug(f"Extracting sections {list(target_sections.keys())} from: {pdf_path}")

    # Extract full text
    full_text = extract_pdf_text(pdf_path, max_pages=max_pages)

    # Simple section extraction by header matching
    result = {section: "" for section in sections}

    # Split by common section headers (case-insensitive)
    lines = full_text.split("\n")
    current_section = None
    current_content = []

    for line in lines:
        line_lower = line.lower().strip()

        # Check if this line starts a new section
        found_section = False
        for target_key, original_name in target_sections.items():
            # Match headers like "Abstract", "1. Introduction", "Methods and Materials", etc.
            # Check for exact match at start or with common prefixes
            if (
                line_lower.startswith(target_key)
                or line_lower.startswith(f"{target_key}:")
                or line_lower.startswith(f"{target_key}.")
                or line_lower == target_key
            ):
                # Save previous section
                if current_section:
                    result[current_section] = "\n".join(current_content).strip()

                current_section = original_name
                current_content = []
                found_section = True
                break

        if not found_section and current_section:
            current_content.append(line)

    # Save last section
    if current_section:
        result[current_section] = "\n".join(current_content).strip()

    # Log extraction results
    for section, text in result.items():
        logger.debug(f"Section '{section}': {len(text)} characters")

    return result


def get_pdf_metadata(pdf_path: str) -> dict:
    """
    Extract metadata from PDF file.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Dict with keys like: title, author, subject, creator, producer, etc.

    Raises:
        FileNotFoundError: If PDF doesn't exist
        ValueError: If PDF cannot be parsed
    """
    path = Path(pdf_path).expanduser()

    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    logger.debug(f"Extracting metadata from: {path}")

    try:
        with pdfplumber.open(path) as pdf:
            metadata = pdf.metadata or {}
            logger.debug(f"Found metadata keys: {list(metadata.keys())}")
            return metadata

    except Exception as e:
        raise ValueError(f"Failed to extract PDF metadata: {e}") from e


def pdf_to_text_with_fallback(pdf_path: str, max_pages: Optional[int] = None) -> str:
    """
    Extract PDF text with graceful fallback if full extraction fails.

    Attempts:
    1. Full text extraction
    2. If that fails, returns empty string with warning

    Args:
        pdf_path: Path to PDF file
        max_pages: Optional page limit

    Returns:
        Extracted text (may be empty string if extraction fails)
    """
    try:
        return extract_pdf_text(pdf_path, max_pages=max_pages)
    except Exception as e:
        logger.warning(f"PDF extraction failed with fallback: {e}")
        logger.info(f"Attempting to extract metadata instead...")
        try:
            metadata = get_pdf_metadata(pdf_path)
            # Return metadata as text
            return "\n".join(f"{k}: {v}" for k, v in metadata.items())
        except Exception as e2:
            logger.error(f"All PDF extraction methods failed: {e2}")
            return ""
