"""LLM integration utilities for Gemini, Anthropic Claude, and Groq."""

import json
import logging
import os
from typing import Any, Optional, TypeVar, Type

import google.generativeai as genai
import anthropic
import groq
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

# Initialize Config
config = Config()

def _get_provider(model: str) -> str:
    """Determine provider from model name."""
    if model.startswith("gemini"):
        return "gemini"
    elif model.startswith("claude"):
        return "anthropic"
    elif any(name in model for name in ["kimi", "llama", "mixtral", "gemma", "moonshotai"]):
        return "groq"
    else:
        # Fallback to configured default
        return config.get("llm.provider", "groq")

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    before_sleep=lambda retry_state: logger.debug(
        f"LLM call failed, retrying... (attempt {retry_state.attempt_number})"
    ),
)
def call_llm(
    prompt: str,
    model: Optional[str] = None,
    temperature: float = 0.1,
    schema: Optional[Type[T]] = None,
) -> str | T:
    """
    Call LLM API with a prompt, supporting multiple providers.

    Args:
        prompt: The prompt to send to the model
        model: Model name (default: from config)
        temperature: Creativity level (0.0 to 1.0)
        schema: Optional Pydantic model for structured output

    Returns:
        Parsed response as string or Pydantic model if schema provided
    """
    if model is None:
        model = config.get("llm.model", "moonshotai/kimi-k2-instruct-0905")
    
    provider = _get_provider(model)
    logger.debug(f"Calling LLM ({provider}/{model}) with prompt length: {len(prompt)}")

    # Append JSON instruction if schema provided
    # (Claude and Groq often benefit from explicit prompt instructions for JSON)
    if schema:
        json_instruction = _get_json_instruction(schema)
        prompt = f"{prompt}\n\n{json_instruction}"

    try:
        response_text = ""
        if provider == "gemini":
            response_text = _call_gemini_api(prompt, model, temperature)
        elif provider == "anthropic":
            response_text = _call_anthropic_api(prompt, model, temperature)
        elif provider == "groq":
            response_text = _call_groq_api(prompt, model, temperature)
        else:
            raise ValueError(f"Unknown LLM provider for model: {model}")

        logger.debug(f"Received response length: {len(response_text)}")

        # If schema provided, try to parse as JSON and validate
        if schema:
            return _parse_structured_response(response_text, schema)

        return response_text

    except Exception as e:
        logger.error(f"LLM call failed ({provider}/{model}): {e}")
        raise ValueError(f"LLM call failed: {e}") from e


def _call_gemini_api(prompt: str, model: str, temperature: float) -> str:
    """Call Google Gemini API."""
    api_key = config.get("llm.gemini_api_key")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not configured.")
    
    genai.configure(api_key=api_key)
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
    
    return response.text


def _call_anthropic_api(prompt: str, model: str, temperature: float) -> str:
    """Call Anthropic Claude API."""
    api_key = config.get("llm.anthropic_api_key")
    if not api_key:
        # Check explicit env var if config missing
        api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY (or CLAUDE_API_KEY) not configured.")
    
    client = anthropic.Anthropic(api_key=api_key)
    
    message = client.messages.create(
        model=model,
        max_tokens=4096,
        temperature=temperature,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    if not message.content:
        raise ValueError("Empty response from Claude")
        
    return message.content[0].text


def _call_groq_api(prompt: str, model: str, temperature: float) -> str:
    """Call Groq API."""
    api_key = config.get("llm.groq_api_key")
    if not api_key:
        # Check explicit env var
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
             raise ValueError("GROQ_API_KEY not configured.")

    client = groq.Groq(api_key=api_key)
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=model,
            temperature=temperature,
        )
    except AttributeError as e:
        # This catches weird client errors or library bugs
        logger.error(f"AttributeError during Groq API call. Client type: {type(client)}")
        raise ValueError(f"Groq client failed with AttributeError: {e}") from e
    except Exception as e:
        raise ValueError(f"Groq API call failed: {e}") from e

    if not hasattr(chat_completion, 'choices') or not chat_completion.choices:
         raise ValueError(f"Empty or invalid response from Groq. Type: {type(chat_completion)}")
    
    first_choice = chat_completion.choices[0]
    if not hasattr(first_choice, 'message'):
        raise ValueError(f"Invalid choice object from Groq: {type(first_choice)}")
        
    content = first_choice.message.content
    
    if content is None:
        logger.warning(f"Groq response content is None. Finish reason: {first_choice.finish_reason}")
        if first_choice.message.tool_calls:
             logger.warning(f"Tool calls received instead of content: {first_choice.message.tool_calls}")
        raise ValueError("Received empty content from Groq (possibly tool calls instead of text)")
         
    return content


def _get_json_instruction(schema: Type[T]) -> str:
    """Generate instruction for JSON output based on Pydantic schema."""
    schema_json = json.dumps(schema.model_json_schema(), indent=2)
    return (
        f"You must output valid JSON matching this schema:\n"
        f"```json\n{schema_json}\n```\n"
        f"Do not include any other text or markdown formatting outside the JSON block."
    )


def _parse_structured_response(text: str, schema: Type[T]) -> T:
    """
    Parse LLM response as JSON and validate against Pydantic schema.
    Attempts to extract JSON from markdown code blocks if needed.
    """
    # Clean up markdown code blocks
    cleaned_text = text.strip()
    if "```json" in cleaned_text:
        start = cleaned_text.find("```json") + 7
        end = cleaned_text.find("```", start)
        if end > start:
            cleaned_text = cleaned_text[start:end].strip()
    elif "```" in cleaned_text:
        start = cleaned_text.find("```") + 3
        end = cleaned_text.find("```", start)
        if end > start:
            cleaned_text = cleaned_text[start:end].strip()
            
    # Remove any leading/trailing non-JSON characters (aggressive heuristic)
    if not cleaned_text.startswith("{") and "{" in cleaned_text:
        cleaned_text = cleaned_text[cleaned_text.find("{"):]
    if not cleaned_text.endswith("}") and "}" in cleaned_text:
        cleaned_text = cleaned_text[:cleaned_text.rfind("}")+1]

    try:
        data = json.loads(cleaned_text)
        # logger.debug(f"Parsed JSON structure: {list(data.keys())}")
        return schema.model_validate(data)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        logger.debug(f"Raw text was: {text}")
        raise ValueError(f"Invalid JSON from LLM: {e}") from e
    except ValidationError as e:
        logger.error(f"Schema validation failed: {e}")
        raise ValueError(f"Response doesn't match schema: {e}") from e


# Alias for backward compatibility
call_gemini = call_llm 
