"""CLI entry: `devsecops-webhook` — run uvicorn for the FastAPI app."""

from __future__ import annotations

import uvicorn

from devsecops_agent.settings import get_settings
from devsecops_agent.utils.logging_config import configure_logging


def main() -> None:
    settings = get_settings()
    
    # Configure logging
    configure_logging(settings.log_level)
    
    uvicorn.run(
        "devsecops_agent.webhook.app:app",
        host=settings.webhook_host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
