import logging
import sys

import structlog


def setup_logging(service_name: str, log_level: str = "INFO") -> None:
    """Configure structured JSON logging for a service.

    Call this once at service startup. After this, all loggers
    (both structlog and stdlib) output JSON with consistent fields.
    """
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # also capture stdlib logging (uvicorn, httpx, etc.) into structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )


def get_logger(service_name: str) -> structlog.stdlib.BoundLogger:
    """Get a logger bound with the service name."""
    logger: structlog.stdlib.BoundLogger = structlog.get_logger(service=service_name)
    return logger
