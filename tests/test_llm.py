"""Tests for LLM utilities."""

import json
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

from mathpilot.utils.llm import (
    call_llm,
    call_gemini,
    _parse_structured_response,
)


class SampleModel(BaseModel):
    """Sample model for testing structured responses."""

    name: str
    value: int


def test_call_gemini_success():
    """Test successful Gemini API call."""
    with patch("mathpilot.utils.llm._call_groq_api") as mock_groq:
        mock_groq.return_value = "This is a test response"

        result = call_gemini("What is 2+2?")
        assert result == "This is a test response"


def test_call_gemini_empty_response():
    """Test handling of empty response from Gemini."""
    from tenacity import RetryError
    with patch("mathpilot.utils.llm._call_groq_api") as mock_groq:
        mock_groq.side_effect = ValueError("Empty response")

        with pytest.raises(RetryError):
            call_gemini("What is 2+2?")


def test_call_gemini_with_schema():
    """Test Gemini call with Pydantic schema for structured output."""
    with patch("mathpilot.utils.llm._call_groq_api") as mock_groq:
        mock_groq.return_value = '{"name": "test", "value": 42}'

        result = call_gemini("Generate JSON", schema=SampleModel)
        assert isinstance(result, SampleModel)
        assert result.name == "test"
        assert result.value == 42


def test_call_gemini_with_schema_in_markdown():
    """Test parsing JSON from markdown code blocks."""
    with patch("mathpilot.utils.llm._call_groq_api") as mock_groq:
        mock_groq.return_value = """
        Here's the JSON:
        ```json
        {"name": "test", "value": 42}
        ```
        """

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
    json_str = '{"name": "test", "value": 42}'
    result = _parse_structured_response(json_str, SampleModel)
    assert result.name == "test"
    assert result.value == 42


def test_parse_structured_response_invalid_json():
    """Test handling of invalid JSON."""
    json_str = '{"name": "test", "value": "not_an_int"}'
    with pytest.raises(ValueError):
        _parse_structured_response(json_str, SampleModel)


def test_batch_call_gemini():
    """Test batch calling multiple prompts."""
    with patch("mathpilot.utils.llm._call_groq_api") as mock_groq:
        mock_groq.side_effect = ["Response 1", "Response 2", "Response 3"]

        prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]
        results = [call_gemini(p) for p in prompts]

        assert results == ["Response 1", "Response 2", "Response 3"]
        assert mock_groq.call_count == 3


def test_extract_json_from_response_object():
    """Test extracting JSON object from response."""
    text = '{"key": "value", "number": 123}'
    
    class TestModel(BaseModel):
        key: str
        number: int
    
    result = _parse_structured_response(text, TestModel)
    assert result.key == "value"
    assert result.number == 123


def test_extract_json_from_response_array():
    """Test extracting JSON array from response."""
    text = '```json\n{"items": [1, 2, 3, 4]}\n```'
    
    class TestModel(BaseModel):
        items: list
    
    result = _parse_structured_response(text, TestModel)
    assert result.items == [1, 2, 3, 4]


def test_extract_json_from_response_with_key():
    """Test extracting nested JSON from response."""
    text = '```json\n{"data": {"nested": "value"}, "other": 123}\n```'
    
    class TestModel(BaseModel):
        data: dict
        other: int
    
    result = _parse_structured_response(text, TestModel)
    assert result.data == {"nested": "value"}
    assert result.other == 123


def test_extract_json_from_response_not_found():
    """Test handling when no JSON found."""
    text = "This is just plain text with no JSON"
    
    class TestModel(BaseModel):
        key: str
    
    with pytest.raises(ValueError):
        _parse_structured_response(text, TestModel)


def test_extract_json_from_response_malformed():
    """Test handling of malformed JSON."""
    text = "Data: {unclosed json"
    
    class TestModel(BaseModel):
        key: str
    
    with pytest.raises(ValueError):
        _parse_structured_response(text, TestModel)
