"""OpenAI API client functionality."""

import json
import logging
import re
import time
from typing import Any

from openai import OpenAI

from .constants import DEFAULT_MODEL, MAX_TOKENS, TEMPERATURE
from .exceptions import OpenAIServiceError

logger = logging.getLogger(__name__)

# Approximate cost per 1K tokens (USD) — updated as pricing changes
_COST_PER_1K: dict[str, dict[str, float]] = {
    "gpt-4o": {"input": 0.0025, "output": 0.01},
    "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
}


def _estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    rates = _COST_PER_1K.get(model, _COST_PER_1K["gpt-4o"])
    return (prompt_tokens * rates["input"] + completion_tokens * rates["output"]) / 1000


def _log_api_call(
    *,
    provider: str,
    endpoint: str,
    tokens_used: int,
    cost: float,
    response_time_ms: int,
    success: bool,
    error_message: str = "",
) -> None:
    """Best-effort write to APICallLog — never raises."""
    try:
        from apps.analytics.models import APICallLog

        APICallLog.objects.create(
            provider=provider,
            endpoint=endpoint,
            tokens_used=tokens_used,
            cost=cost,
            response_time_ms=response_time_ms,
            success=success,
            error_message=error_message,
        )
    except Exception:
        logger.debug("Failed to log API call", exc_info=True)


class OpenAIApiClient:
    """Handles direct communication with OpenAI API."""

    def __init__(self, client: OpenAI):
        self.client = client

    def make_request(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        response_format: dict[str, str] | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        """
        Make a request to OpenAI API with error handling.

        Args:
            messages: List of message dictionaries.
            model: Model to use (defaults to class default).
            response_format: Response format specification.
            max_tokens: Maximum tokens for response.
            temperature: Temperature for response generation.

        Returns:
            Response content from OpenAI.

        Raises:
            OpenAIServiceError: If the API request fails.
        """
        start_time = time.time()
        model_name = model or DEFAULT_MODEL
        total_tokens = sum(len(msg.get("content", "")) for msg in messages)

        logger.info(
            f"Starting OpenAI API request to {model_name}, input tokens: ~{total_tokens // 4}"
        )

        try:
            request_start = time.time()
            logger.info("Sending request to OpenAI API...")

            response = self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature or TEMPERATURE,
                max_tokens=max_tokens or MAX_TOKENS,
                response_format=response_format or {"type": "json_object"},
            )

            request_time = time.time() - request_start
            response_content = response.choices[0].message.content.strip()
            usage = response.usage

            logger.info(f"OpenAI API response received in {request_time:.2f} seconds")
            logger.info(f"Response tokens: {usage.total_tokens if usage else 'Unknown'}")
            logger.info(f"Response length: {len(response_content)} characters")

            total_time = time.time() - start_time
            logger.info(
                f"Total API request completed in {total_time:.2f} seconds (request: {request_time:.2f}s)"
            )

            _log_api_call(
                provider="openai",
                endpoint=model_name,
                tokens_used=usage.total_tokens if usage else 0,
                cost=_estimate_cost(
                    model_name,
                    usage.prompt_tokens if usage else 0,
                    usage.completion_tokens if usage else 0,
                ),
                response_time_ms=int(request_time * 1000),
                success=True,
            )

            return response_content

        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"OpenAI API request failed after {total_time:.2f} seconds: {e}")
            _log_api_call(
                provider="openai",
                endpoint=model_name,
                tokens_used=0,
                cost=0,
                response_time_ms=int(total_time * 1000),
                success=False,
                error_message=str(e),
            )
            raise OpenAIServiceError(f"Failed to process request: {e!s}")

    @staticmethod
    def clean_json_response(content: str) -> str:
        """
        Clean JSON response by removing markdown code blocks.

        Args:
            content: Raw response content.

        Returns:
            Cleaned JSON string.
        """
        # Remove markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        return content

    @staticmethod
    def parse_json_response(content: str) -> dict[str, Any]:
        """
        Parse JSON response with fallback extraction.

        Args:
            content: JSON content string.

        Returns:
            Parsed JSON data.

        Raises:
            OpenAIServiceError: If JSON parsing fails.
        """
        cleaned_content = OpenAIApiClient.clean_json_response(content)

        try:
            return json.loads(cleaned_content)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            json_match = re.search(r"\{.*\}", cleaned_content, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass

            logger.error(f"Failed to parse JSON response: {cleaned_content}")
            raise OpenAIServiceError("Failed to parse JSON response from OpenAI")
