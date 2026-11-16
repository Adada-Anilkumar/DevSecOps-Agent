"""LLM provider abstraction - supports OpenAI and Gemini with structured outputs and fallback."""

from __future__ import annotations

import json
import re
import time
from typing import Any, Protocol, Type, TypeVar

from pydantic import BaseModel

from devsecops_agent.settings import get_settings
from devsecops_agent.utils.cost_tracker import get_cost_tracker
from devsecops_agent.utils.logging_config import get_logger
from devsecops_agent.utils.metrics import (
    api_calls_total,
    api_duration_seconds,
    review_duration_seconds,
    review_errors_total,
    review_requests_total,
)
from devsecops_agent.utils.retry import retry_with_backoff

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


def _extract_json_block(text: str) -> str:
    """Extract valid JSON from response string, removing potential markdown wraps."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        return match.group(1).strip()
    return text


class LLMProvider(Protocol):
    """Protocol for LLM providers."""

    def generate(self, system_prompt: str, user_message: str) -> str:
        """Generate a text response from the LLM."""
        ...

    def generate_structured(
        self,
        system_prompt: str,
        user_message: str,
        schema: Type[T],
    ) -> T:
        """Generate structured Pydantic object from the LLM."""
        ...


class GeminiProvider:
    """Google Gemini provider."""

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.gemini_api_key
        self.model = settings.gemini_model
        self.temperature = settings.gemini_temperature
        self.timeout = settings.gemini_timeout

        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(self.model)
        except ImportError:
            raise ImportError(
                "google-generativeai not installed. "
                "Install with: pip install google-generativeai"
            )

    @retry_with_backoff(
        max_attempts=3,
        initial_delay=2.0,
        max_delay=30.0,
        exceptions=(Exception,),
    )
    def generate(self, system_prompt: str, user_message: str) -> str:
        """Generate response using Gemini."""
        start_time = time.time()

        try:
            input_chars = len(system_prompt) + len(user_message)
            logger.info(
                "Starting Gemini review",
                model=self.model,
                input_size_chars=input_chars,
            )

            full_prompt = f"{system_prompt}\n\n{user_message}"
            api_start = time.time()

            response = self.client.generate_content(
                full_prompt,
                generation_config={
                    "temperature": self.temperature,
                    "max_output_tokens": 8192,
                },
                request_options={"timeout": self.timeout},
            )
            api_duration = time.time() - api_start

            api_calls_total.labels(service="gemini", status="success").inc()
            api_duration_seconds.labels(service="gemini").observe(api_duration)

            if not response.text:
                logger.warning("Empty response from Gemini")
                review_requests_total.labels(status="empty", use_rag="false").inc()
                return ""

            if hasattr(response, "usage_metadata"):
                prompt_tokens = getattr(response.usage_metadata, "prompt_token_count", 0)
                completion_tokens = getattr(
                    response.usage_metadata, "candidates_token_count", 0
                )
                if prompt_tokens or completion_tokens:
                    cost_tracker = get_cost_tracker()
                    cost_tracker.track_usage(
                        f"gemini-{self.model}",
                        prompt_tokens,
                        completion_tokens,
                    )

            duration = time.time() - start_time
            review_duration_seconds.labels(use_rag="false").observe(duration)
            review_requests_total.labels(status="success", use_rag="false").inc()

            return response.text.strip()

        except Exception as e:
            logger.error("Gemini review failed", error=str(e), exc_info=True)
            review_errors_total.labels(error_type=type(e).__name__).inc()
            review_requests_total.labels(status="error", use_rag="false").inc()
            api_calls_total.labels(service="gemini", status="error").inc()
            raise

    def generate_structured(
        self,
        system_prompt: str,
        user_message: str,
        schema: Type[T],
    ) -> T:
        """Generate structured response validated against Pydantic schema."""
        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        structured_system = (
            f"{system_prompt}\n\n"
            "CRITICAL INSTRUCTION: You must respond ONLY with a valid JSON object matching the JSON schema below.\n"
            "Do NOT include markdown formatting or extra text outside the JSON object.\n\n"
            f"SCHEMA:\n{schema_json}"
        )

        raw_output = self.generate(structured_system, user_message)
        json_str = _extract_json_block(raw_output)

        try:
            return schema.model_validate_json(json_str)
        except Exception as e:
            logger.warning(
                "Direct JSON parsing failed, attempting fallback repair",
                error=str(e),
                raw_preview=raw_output[:200],
            )
            # Basic fallback attempt
            parsed = json.loads(json_str)
            return schema.model_validate(parsed)


class OpenAIProvider:
    """OpenAI provider."""

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.openai_api_key
        self.model = settings.openai_model
        self.base_url = settings.openai_base_url
        self.timeout = settings.openai_timeout

        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_openai import ChatOpenAI

        self.ChatOpenAI = ChatOpenAI
        self.SystemMessage = SystemMessage
        self.HumanMessage = HumanMessage

    @retry_with_backoff(
        max_attempts=3,
        initial_delay=2.0,
        max_delay=30.0,
        exceptions=(Exception,),
    )
    def generate(self, system_prompt: str, user_message: str) -> str:
        """Generate response using OpenAI."""
        start_time = time.time()

        try:
            logger.info("Starting OpenAI review", model=self.model)

            llm = self.ChatOpenAI(
                model=self.model,
                temperature=0.2,
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout,
                max_retries=0,
            )

            api_start = time.time()
            resp = llm.invoke(
                [
                    self.SystemMessage(content=system_prompt),
                    self.HumanMessage(content=user_message),
                ]
            )
            api_duration = time.time() - api_start

            api_calls_total.labels(service="openai_chat", status="success").inc()
            api_duration_seconds.labels(service="openai_chat").observe(api_duration)

            if hasattr(resp, "response_metadata"):
                usage = resp.response_metadata.get("token_usage", {})
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                if prompt_tokens or completion_tokens:
                    cost_tracker = get_cost_tracker()
                    cost = cost_tracker.track_usage(
                        self.model,
                        prompt_tokens,
                        completion_tokens,
                    )

            content = resp.content
            if not content:
                logger.warning("Empty response from OpenAI")
                review_requests_total.labels(status="empty", use_rag="false").inc()
                return ""

            duration = time.time() - start_time
            review_duration_seconds.labels(use_rag="false").observe(duration)
            review_requests_total.labels(status="success", use_rag="false").inc()

            return str(content).strip()

        except Exception as e:
            logger.error("OpenAI review failed", error=str(e), exc_info=True)
            review_errors_total.labels(error_type=type(e).__name__).inc()
            review_requests_total.labels(status="error", use_rag="false").inc()
            api_calls_total.labels(service="openai_chat", status="error").inc()
            raise

    def generate_structured(
        self,
        system_prompt: str,
        user_message: str,
        schema: Type[T],
    ) -> T:
        """Generate structured response using OpenAI structured output parser."""
        try:
            llm = self.ChatOpenAI(
                model=self.model,
                temperature=0.2,
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout,
                max_retries=0,
            )
            structured_llm = llm.with_structured_output(schema)
            return structured_llm.invoke(
                [
                    self.SystemMessage(content=system_prompt),
                    self.HumanMessage(content=user_message),
                ]
            )
        except Exception as e:
            logger.warning(
                "Structured output with with_structured_output failed; falling back to prompt extraction",
                error=str(e),
            )
            schema_json = json.dumps(schema.model_json_schema(), indent=2)
            structured_system = (
                f"{system_prompt}\n\n"
                "Respond ONLY with a JSON object adhering to this schema:\n"
                f"{schema_json}"
            )
            raw = self.generate(structured_system, user_message)
            json_str = _extract_json_block(raw)
            return schema.model_validate_json(json_str)


class ResilientProvider:
    """Combines primary and secondary providers with automatic fallback."""

    def __init__(self, primary: LLMProvider, secondary: LLMProvider | None = None):
        self.primary = primary
        self.secondary = secondary

    def generate(self, system_prompt: str, user_message: str) -> str:
        try:
            return self.primary.generate(system_prompt, user_message)
        except Exception as primary_err:
            if self.secondary:
                logger.warning(
                    "Primary provider failed, failing over to secondary",
                    primary_error=str(primary_err),
                )
                return self.secondary.generate(system_prompt, user_message)
            raise

    def generate_structured(
        self,
        system_prompt: str,
        user_message: str,
        schema: Type[T],
    ) -> T:
        try:
            return self.primary.generate_structured(system_prompt, user_message, schema)
        except Exception as primary_err:
            if self.secondary:
                logger.warning(
                    "Primary provider structured generation failed, failing over to secondary",
                    primary_error=str(primary_err),
                )
                return self.secondary.generate_structured(system_prompt, user_message, schema)
            raise


def get_llm_provider() -> LLMProvider:
    """Get the configured LLM provider with fallback support if both keys are present."""
    settings = get_settings()

    primary: LLMProvider
    secondary: LLMProvider | None = None

    if settings.llm_provider == "gemini":
        primary = GeminiProvider()
        if settings.openai_api_key:
            try:
                secondary = OpenAIProvider()
            except Exception:
                pass
    elif settings.llm_provider == "openai":
        primary = OpenAIProvider()
        if settings.gemini_api_key:
            try:
                secondary = GeminiProvider()
            except Exception:
                pass
    else:
        raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")

    return ResilientProvider(primary, secondary) if secondary else primary
