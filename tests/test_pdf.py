"""Tests for PDF utilities."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mathpilot.utils.pdf import (
    extract_pdf_text,
    extract_pdf_sections,
    get_pdf_metadata,
    pdf_to_text_with_fallback,
)


@pytest.fixture
def sample_pdf_path():
    """Create a temporary PDF for testing."""
    # We'll mock this since creating real PDFs is complex
    return "/tmp/sample.pdf"


def test_extract_pdf_text_success(sample_pdf_path):
    """Test successful PDF text extraction."""
    with patch("mathpilot.utils.pdf.pdfplumber.open") as mock_open:
        mock_pdf = MagicMock()
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Page 1 content"
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "Page 2 content"

        mock_pdf.pages = [mock_page1, mock_page2]
        mock_open.return_value.__enter__.return_value = mock_pdf

        with patch("pathlib.Path.exists", return_value=True):
            result = extract_pdf_text(sample_pdf_path)

        assert "Page 1 content" in result
        assert "Page 2 content" in result


def test_extract_pdf_text_not_found():
    """Test handling of missing PDF."""
    with patch("pathlib.Path.exists", return_value=False):
        with pytest.raises(FileNotFoundError, match="PDF not found"):
            extract_pdf_text("/nonexistent/file.pdf")


def test_extract_pdf_text_with_max_pages(sample_pdf_path):
    """Test PDF extraction with page limit."""
    with patch("mathpilot.utils.pdf.pdfplumber.open") as mock_open:
        mock_pdf = MagicMock()
        pages = []
        for i in range(5):
            mock_page = MagicMock()
            mock_page.extract_text.return_value = f"Page {i+1}"
            pages.append(mock_page)

        mock_pdf.pages = pages
        mock_open.return_value.__enter__.return_value = mock_pdf

        with patch("pathlib.Path.exists", return_value=True):
            result = extract_pdf_text(sample_pdf_path, max_pages=2)

        # Should only extract first 2 pages
        assert "Page 1" in result
        assert "Page 2" in result
        assert "Page 3" not in result


def test_extract_pdf_text_parse_error(sample_pdf_path):
    """Test handling of PDF parse errors."""
    with patch("mathpilot.utils.pdf.pdfplumber.open") as mock_open:
        mock_open.side_effect = Exception("Corrupted PDF")

        with patch("pathlib.Path.exists", return_value=True):
            with pytest.raises(ValueError, match="Failed to parse PDF"):
                extract_pdf_text(sample_pdf_path)


def test_extract_pdf_sections_success(sample_pdf_path):
    """Test section extraction from PDF."""
    with patch("mathpilot.utils.pdf.extract_pdf_text") as mock_extract:
        mock_extract.return_value = """
        Abstract
        This is the abstract content.
        
        Introduction
        This is the introduction.
        
        Methods
        This is the methods section.
        """

        result = extract_pdf_sections(
            sample_pdf_path, sections=["abstract", "introduction", "methods"]
        )

        assert "abstract content" in result["abstract"].lower()
        assert "introduction" in result["introduction"].lower()
        assert "methods section" in result["methods"].lower()


def test_extract_pdf_sections_case_insensitive(sample_pdf_path):
    """Test that section extraction is case-insensitive."""
    with patch("mathpilot.utils.pdf.extract_pdf_text") as mock_extract:
        mock_extract.return_value = """
        ABSTRACT
        This is the abstract.
        
        INTRODUCTION
        This is the introduction.
        """

        result = extract_pdf_sections(sample_pdf_path, sections=["abstract", "introduction"])

        assert "abstract" in result["abstract"].lower()
        assert "introduction" in result["introduction"].lower()


def test_extract_pdf_sections_not_found(sample_pdf_path):
    """Test handling of missing sections."""
    with patch("mathpilot.utils.pdf.extract_pdf_text") as mock_extract:
        mock_extract.return_value = "Some random content without sections"

        result = extract_pdf_sections(sample_pdf_path, sections=["abstract", "methods"])

        # Should return empty strings for not found sections
        assert result["abstract"] == ""
        assert result["methods"] == ""


def test_get_pdf_metadata_success(sample_pdf_path):
    """Test PDF metadata extraction."""
    with patch("mathpilot.utils.pdf.pdfplumber.open") as mock_open:
        mock_pdf = MagicMock()
        mock_pdf.metadata = {"Title": "Test Paper", "Author": "Test Author"}

        mock_open.return_value.__enter__.return_value = mock_pdf

        with patch("pathlib.Path.exists", return_value=True):
            result = get_pdf_metadata(sample_pdf_path)

        assert result["Title"] == "Test Paper"
        assert result["Author"] == "Test Author"


def test_get_pdf_metadata_not_found():
    """Test handling of missing PDF for metadata."""
    with patch("pathlib.Path.exists", return_value=False):
        with pytest.raises(FileNotFoundError):
            get_pdf_metadata("/nonexistent/file.pdf")


def test_pdf_to_text_with_fallback_success(sample_pdf_path):
    """Test fallback extraction succeeds."""
    with patch("mathpilot.utils.pdf.extract_pdf_text") as mock_extract:
        mock_extract.return_value = "Extracted text"

        result = pdf_to_text_with_fallback(sample_pdf_path)
        assert result == "Extracted text"


def test_pdf_to_text_with_fallback_uses_metadata(sample_pdf_path):
    """Test fallback to metadata when text extraction fails."""
    with patch("mathpilot.utils.pdf.extract_pdf_text") as mock_extract:
        mock_extract.side_effect = Exception("Text extraction failed")

        with patch("mathpilot.utils.pdf.get_pdf_metadata") as mock_metadata:
            mock_metadata.return_value = {"Title": "Test", "Author": "Author"}

            result = pdf_to_text_with_fallback(sample_pdf_path)
            assert "Title: Test" in result
            assert "Author: Author" in result


def test_pdf_to_text_with_fallback_all_fail(sample_pdf_path):
    """Test fallback returns empty string when all methods fail."""
    with patch("mathpilot.utils.pdf.extract_pdf_text") as mock_extract:
        mock_extract.side_effect = Exception("Text extraction failed")

        with patch("mathpilot.utils.pdf.get_pdf_metadata") as mock_metadata:
            mock_metadata.side_effect = Exception("Metadata extraction failed")

            result = pdf_to_text_with_fallback(sample_pdf_path)
            assert result == ""
