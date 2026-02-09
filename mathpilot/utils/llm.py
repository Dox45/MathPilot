"""LLM integration utilities for Gemini API calls."""

import json
import logging
from typing import Any, Optional, TypeVar, Type

import google.generativeai as genai
from pydantic import BaseModel, ValidationError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from mathpilot.utils.config import Config

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)

# Initialize Gemini
config = Config()
api_key = config.get("llm.api_key")
if api_key:
    genai.configure(api_key=api_key)
else:
    logger.warning("GEMINI_API_KEY not configured. LLM calls will fail.")


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    before_sleep=lambda retry_state: logger.debug(
        f"LLM call failed, retrying... (attempt {retry_state.attempt_number})"
    ),
)
def call_gemini(
    prompt: str,
    model: str = "gemini-2.0-flash",
    temperature: float = 0.1,
    schema: Optional[Type[T]] = None,
) -> str | T:
    """
    Call Gemini API with a prompt.

    Args:
        prompt: The prompt to send to the model
        model: Model name (default: gemini-2.0-flash)
        temperature: Creativity level (0.0 to 1.0)
        schema: Optional Pydantic model for structured output

    Returns:
        Parsed response as string or Pydantic model if schema provided

    Raises:
        ValueError: If API call fails or response cannot be parsed
    """
    logger.debug(f"Calling Gemini with prompt length: {len(prompt)}")

    try:
        client = genai.GenerativeModel(model)
        response = client.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                top_p=0.95,
                top_k=40,
            ),
        )

        if not response.text:
            raise ValueError("Empty response from Gemini")

        logger.debug(f"Received response length: {len(response.text)}")

        # If schema provided, try to parse as JSON and validate
        if schema:
            return _parse_structured_response(response.text, schema)

        return response.text

    except Exception as e:
        logger.error(f"Gemini API call failed: {e}")
        raise ValueError(f"LLM call failed: {e}") from e


def _parse_structured_response(text: str, schema: Type[T]) -> T:
    """
    Parse LLM response as JSON and validate against Pydantic schema.

    Attempts to extract JSON from markdown code blocks if needed.

    Args:
        text: LLM response text
        schema: Pydantic model class to validate against

    Returns:
        Validated model instance

    Raises:
        ValueError: If JSON parsing or validation fails
    """
    # Try to extract JSON from markdown code blocks
    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        if end > start:
            text = text[start:end].strip()
    elif "```" in text:
        start = text.find("```") + 3
        end = text.find("```", start)
        if end > start:
            text = text[start:end].strip()

    try:
        data = json.loads(text)
        logger.debug(f"Parsed JSON structure: {list(data.keys())}")
        return schema.model_validate(data)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        raise ValueError(f"Invalid JSON from LLM: {e}") from e
    except ValidationError as e:
        logger.error(f"Schema validation failed: {e}")
        raise ValueError(f"Response doesn't match schema: {e}") from e


def batch_call_gemini(
    prompts: list[str],
    model: str = "gemini-2.0-flash",
    temperature: float = 0.1,
) -> list[str]:
    """
    Call Gemini multiple times in sequence (not parallelized due to API limits).

    Args:
        prompts: List of prompts to send
        model: Model name
        temperature: Creativity level

    Returns:
        List of responses in same order as prompts

    Raises:
        ValueError: If any call fails after retries
    """
    logger.info(f"Batch calling Gemini with {len(prompts)} prompts")
    results = []

    for i, prompt in enumerate(prompts):
        logger.debug(f"Batch call {i+1}/{len(prompts)}")
        result = call_gemini(prompt, model=model, temperature=temperature)
        results.append(result)

    return results


def extract_json_from_response(text: str, key: Optional[str] = None) -> dict | list:
    """
    Extract JSON object or array from LLM response text.

    Useful when LLM response contains JSON but may have extra text.

    Args:
        text: Response text that may contain JSON
        key: Optional key to extract from response dict

    Returns:
        Parsed JSON as dict or list

    Raises:
        ValueError: If no valid JSON found
    """
    # Try to find JSON object or array
    for start_char in ["{", "["]:
        idx = text.find(start_char)
        if idx == -1:
            continue

        # Find matching closing bracket
        open_char = "{" if start_char == "{" else "["
        close_char = "}" if start_char == "{" else "]"
        depth = 0

        for i, char in enumerate(text[idx:], start=idx):
            if char == open_char:
                depth += 1
            elif char == close_char:
                depth -= 1
                if depth == 0:
                    try:
                        data = json.loads(text[idx : i + 1])
                        if key and isinstance(data, dict):
                            return data.get(key)
                        return data
                    except json.JSONDecodeError:
                        continue

    raise ValueError("No valid JSON found in response")
