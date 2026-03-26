"""LLM provider abstraction - supports OpenAI and Gemini."""

from __future__ import annotations

import time
from typing import Protocol

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


class LLMProvider(Protocol):
    """Protocol for LLM providers."""

    def generate(self, system_prompt: str, user_message: str) -> str:
        """Generate a response from the LLM."""
        ...


class GeminiProvider:
    """Google Gemini provider (FREE!)."""

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.gemini_api_key
        self.model = settings.gemini_model
        self.temperature = settings.gemini_temperature
        self.timeout = settings.gemini_timeout

        # Import here to avoid dependency if not using Gemini
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
            # Calculate approximate input size
            input_chars = len(system_prompt) + len(user_message)
            logger.info(
                "Starting Gemini review",
                model=self.model,
                input_size_chars=input_chars,
                estimated_time_seconds="5-30s depending on size",
            )

            # Combine system and user prompts for Gemini
            full_prompt = f"{system_prompt}\n\n{user_message}"

            # Call Gemini API with timeout
            logger.info("Calling Gemini API", status="processing", timeout_seconds=self.timeout)
            api_start = time.time()
            
            # Set request options with timeout
            request_options = {
                "timeout": self.timeout,
            }
            
            response = self.client.generate_content(
                full_prompt,
                generation_config={
                    "temperature": self.temperature,
                    "max_output_tokens": 8192,
                },
                request_options=request_options,
            )
            api_duration = time.time() - api_start
            
            logger.info("Gemini API responded", duration_seconds=round(api_duration, 2))

            # Update metrics
            api_calls_total.labels(service="gemini", status="success").inc()
            api_duration_seconds.labels(service="gemini").observe(api_duration)

            # Extract text
            if not response.text:
                logger.warning("Empty response from Gemini")
                review_requests_total.labels(status="empty", use_rag="false").inc()
                return ""

            # Track usage (Gemini is free, but we track for monitoring)
            if hasattr(response, "usage_metadata"):
                prompt_tokens = getattr(response.usage_metadata, "prompt_token_count", 0)
                completion_tokens = getattr(
                    response.usage_metadata, "candidates_token_count", 0
                )

                if prompt_tokens or completion_tokens:
                    cost_tracker = get_cost_tracker()
                    # Gemini is free, so cost is $0
                    cost_tracker.track_usage(
                        f"gemini-{self.model}",
                        prompt_tokens,
                        completion_tokens,
                    )
                    logger.info(
                        "Review completed successfully",
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        cost_usd=0.0,  # FREE!
                        duration_seconds=round(time.time() - start_time, 2),
                    )

            # Success metrics
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


class OpenAIProvider:
    """OpenAI provider (requires paid API key)."""

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
                    logger.info(
                        "Review completed",
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        cost_usd=round(cost, 6),
                        duration_seconds=round(time.time() - start_time, 2),
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


def get_llm_provider() -> LLMProvider:
    """Get the configured LLM provider."""
    settings = get_settings()

    if settings.llm_provider == "gemini":
        return GeminiProvider()
    elif settings.llm_provider == "openai":
        return OpenAIProvider()
    else:
        raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")
