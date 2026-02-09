"""Tests for LLM utilities."""

import json
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

from mathpilot.utils.llm import (
    call_gemini,
    batch_call_gemini,
    _parse_structured_response,
    extract_json_from_response,
)


class SampleModel(BaseModel):
    """Sample model for testing structured responses."""

    name: str
    value: int


def test_call_gemini_success():
    """Test successful Gemini API call."""
    with patch("mathpilot.utils.llm.genai.GenerativeModel") as mock_model:
        mock_response = MagicMock()
        mock_response.text = "This is a test response"

        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance

        result = call_gemini("What is 2+2?")
        assert result == "This is a test response"
        mock_instance.generate_content.assert_called_once()


def test_call_gemini_empty_response():
    """Test handling of empty response from Gemini."""
    with patch("mathpilot.utils.llm.genai.GenerativeModel") as mock_model:
        mock_response = MagicMock()
        mock_response.text = ""

        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance

        with pytest.raises(Exception):  # Retries will wrap the ValueError
            call_gemini("What is 2+2?")


def test_call_gemini_with_schema():
    """Test Gemini call with Pydantic schema for structured output."""
    with patch("mathpilot.utils.llm.genai.GenerativeModel") as mock_model:
        mock_response = MagicMock()
        mock_response.text = '{"name": "test", "value": 42}'

        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance

        result = call_gemini("Generate JSON", schema=SampleModel)
        assert isinstance(result, SampleModel)
        assert result.name == "test"
        assert result.value == 42


def test_call_gemini_with_schema_in_markdown():
    """Test parsing JSON from markdown code blocks."""
    with patch("mathpilot.utils.llm.genai.GenerativeModel") as mock_model:
        mock_response = MagicMock()
        mock_response.text = """
        Here's the JSON:
        ```json
        {"name": "test", "value": 42}
        ```
        """

        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance

        result = call_gemini("Generate JSON", schema=SampleModel)
        assert isinstance(result, SampleModel)
        assert result.name == "test"
        assert result.value == 42


def test_parse_structured_response_valid_json():
    """Test parsing valid JSON response."""
    json_str = '{"name": "test", "value": 42}'
    result = _parse_structured_response(json_str, SampleModel)
    assert result.name == "test"
    assert result.value == 42


def test_parse_structured_response_with_extra_text():
    """Test parsing JSON with surrounding text."""
    json_str = 'Some text before {"name": "test", "value": 42} and after'
    # This should still work if we handle extraction properly
    with pytest.raises(ValueError):
        _parse_structured_response(json_str, SampleModel)


def test_parse_structured_response_invalid_json():
    """Test handling of invalid JSON."""
    json_str = '{"name": "test", "value": "not_an_int"}'
    with pytest.raises(ValueError, match="doesn't match schema"):
        _parse_structured_response(json_str, SampleModel)


def test_batch_call_gemini():
    """Test batch calling multiple prompts."""
    with patch("mathpilot.utils.llm.call_gemini") as mock_call:
        mock_call.side_effect = ["Response 1", "Response 2", "Response 3"]

        prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]
        results = batch_call_gemini(prompts)

        assert results == ["Response 1", "Response 2", "Response 3"]
        assert mock_call.call_count == 3


def test_extract_json_from_response_object():
    """Test extracting JSON object from response."""
    text = 'Here is the data: {"key": "value", "number": 123} after text'
    result = extract_json_from_response(text)
    assert result == {"key": "value", "number": 123}


def test_extract_json_from_response_array():
    """Test extracting JSON array from response."""
    text = 'Items: [1, 2, 3, 4] done'
    result = extract_json_from_response(text)
    assert result == [1, 2, 3, 4]


def test_extract_json_from_response_with_key():
    """Test extracting specific key from JSON object."""
    text = '{"data": {"nested": "value"}, "other": 123}'
    result = extract_json_from_response(text, key="data")
    assert result == {"nested": "value"}


def test_extract_json_from_response_not_found():
    """Test handling when no JSON found."""
    text = "This is just plain text with no JSON"
    with pytest.raises(ValueError, match="No valid JSON"):
        extract_json_from_response(text)


def test_extract_json_from_response_malformed():
    """Test handling of malformed JSON."""
    text = "Data: {unclosed json"
    with pytest.raises(ValueError, match="No valid JSON"):
        extract_json_from_response(text)
