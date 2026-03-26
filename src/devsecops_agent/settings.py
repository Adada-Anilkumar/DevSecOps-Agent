"""Centralized configuration with Pydantic validation."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM Provider Selection
    llm_provider: Literal["openai", "gemini"] = Field(
        default="gemini",
        description="LLM provider to use (openai or gemini)",
    )

    # OpenAI Configuration (optional if using Gemini)
    openai_api_key: str | None = Field(
        default=None,
        description="OpenAI API key (required if llm_provider=openai)",
    )
    openai_model: str = Field(
        default="gpt-4o-mini",
        description="Chat model for generating reviews",
    )
    openai_embedding_model: str = Field(
        default="text-embedding-3-small",
        description="Embedding model for RAG",
    )
    openai_base_url: str | None = Field(
        default=None,
        description="Custom API base URL (Azure, proxies)",
    )
    openai_timeout: int = Field(
        default=120,
        ge=10,
        le=600,
        description="API timeout in seconds",
    )
    openai_max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Max retry attempts for API calls",
    )

    # Gemini Configuration (FREE!)
    gemini_api_key: str | None = Field(
        default=None,
        description="Google Gemini API key (required if llm_provider=gemini)",
    )
    gemini_model: str = Field(
        default="gemini-2.5-flash",
        description="Gemini model (gemini-2.5-flash, gemini-2.5-pro, or gemini-flash-latest)",
    )
    gemini_temperature: float = Field(
        default=0.2,
        ge=0.0,
        le=2.0,
        description="Temperature for Gemini responses",
    )
    gemini_timeout: int = Field(
        default=120,
        ge=30,
        le=600,
        description="Gemini API timeout in seconds (default: 120)",
    )

    # RAG Configuration
    devsecops_chroma_path: Path = Field(
        default=Path(".devsecops/chroma"),
        description="Vector store persistence path",
    )
    devsecops_chroma_collection: str = Field(
        default="devsecops_policies",
        description="Chroma collection name",
    )
    rag_chunk_size: int = Field(
        default=1200,
        ge=100,
        le=4000,
        description="Text chunk size for indexing",
    )
    rag_chunk_overlap: int = Field(
        default=200,
        ge=0,
        le=1000,
        description="Overlap between chunks",
    )

    # GitHub Webhook Configuration
    github_token: str | None = Field(
        default=None,
        description="GitHub PAT for API access",
    )
    github_webhook_secret: str | None = Field(
        default=None,
        description="Webhook signature verification secret",
    )
    github_api_url: str = Field(
        default="https://api.github.com",
        description="GitHub API base URL",
    )

    # Webhook Server Configuration
    webhook_host: str = Field(default="0.0.0.0", description="Server bind address")
    port: int = Field(default=8080, ge=1, le=65535, description="Server port")
    webhook_allow_unsigned: bool = Field(
        default=False,
        description="Allow unsigned webhooks (dev only)",
    )
    webhook_pr_actions: str = Field(
        default="opened,synchronize,reopened",
        description="PR actions to process",
    )
    webhook_use_rag: bool = Field(
        default=False,
        description="Enable RAG for webhook reviews",
    )
    webhook_rag_k: int = Field(
        default=6,
        ge=1,
        le=20,
        description="Top-K chunks to retrieve",
    )
    webhook_default_language: str | None = Field(
        default=None,
        description="Default language hint",
    )
    webhook_review_context: str | None = Field(
        default=None,
        description="Additional context for reviews",
    )
    webhook_review_mode: Literal["comprehensive", "security", "architecture", "infrastructure"] = Field(
        default="comprehensive",
        description="Review mode: comprehensive (all aspects), security (vulnerabilities only), architecture (code quality), infrastructure (DevOps/cloud)",
    )
    webhook_prompt_style: Literal["detailed", "compact", "ultra"] = Field(
        default="ultra",
        description="Prompt style: detailed (thorough, most tokens), compact (50% fewer tokens), ultra (86% fewer tokens, recommended)",
    )
    webhook_max_diff_chars: int = Field(
        default=500000,
        ge=1000,
        le=10000000,
        description="Max diff size in characters",
    )
    webhook_post_on_failure: bool = Field(
        default=False,
        description="Post comment on review failure",
    )

    # Rate Limiting
    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable rate limiting",
    )
    rate_limit_per_minute: int = Field(
        default=10,
        ge=1,
        le=1000,
        description="Max requests per minute per IP",
    )

    # Monitoring & Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )
    enable_metrics: bool = Field(
        default=True,
        description="Enable Prometheus metrics",
    )
    sentry_dsn: str | None = Field(
        default=None,
        description="Sentry DSN for error tracking",
    )

    # Redis/Queue Configuration
    redis_url: str | None = Field(
        default=None,
        description="Redis URL for job queue (optional)",
    )
    use_background_queue: bool = Field(
        default=False,
        description="Use Redis queue instead of FastAPI BackgroundTasks",
    )

    # Cost Management
    max_tokens_per_request: int = Field(
        default=16000,
        ge=1000,
        le=128000,
        description="Max tokens per review request",
    )
    enable_cost_tracking: bool = Field(
        default=True,
        description="Track API costs",
    )

    @field_validator("devsecops_chroma_path", mode="before")
    @classmethod
    def resolve_path(cls, v: str | Path) -> Path:
        """Resolve path to absolute."""
        return Path(v).resolve()

    @field_validator("webhook_pr_actions")
    @classmethod
    def validate_actions(cls, v: str) -> str:
        """Validate PR actions."""
        valid = {"opened", "synchronize", "reopened", "edited", "closed"}
        actions = {a.strip() for a in v.split(",") if a.strip()}
        invalid = actions - valid
        if invalid:
            raise ValueError(f"Invalid PR actions: {invalid}")
        return v

    def get_pr_actions(self) -> set[str]:
        """Parse PR actions into set."""
        return {a.strip() for a in self.webhook_pr_actions.split(",") if a.strip()}

    def get_api_key(self) -> str:
        """Get the appropriate API key based on provider."""
        if self.llm_provider == "gemini":
            if not self.gemini_api_key:
                raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini")
            return self.gemini_api_key
        else:
            if not self.openai_api_key:
                raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
            return self.openai_api_key

    def get_model_name(self) -> str:
        """Get the model name based on provider."""
        if self.llm_provider == "gemini":
            return self.gemini_model
        else:
            return self.openai_model


# Global settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get or create settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Reset settings (for testing)."""
    global _settings
    _settings = None
