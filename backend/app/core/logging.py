"""Structured logging setup for Enterprise AI Knowledge Assistant."""

import logging
import sys
import json
from datetime import datetime, timezone
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured cloud and local logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }

        # Add optional tracing context if present
        for attr in ("request_id", "user_id", "organization_id", "workspace_id"):
            if hasattr(record, attr):
                log_entry[attr] = getattr(record, attr)

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_logging(log_level: str = "INFO", json_logs: bool = False) -> None:
    """Configures application-wide logging."""
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Clear existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    if json_logs:
        handler.setFormatter(JSONFormatter())
    else:
        standard_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        handler.setFormatter(logging.Formatter(standard_format))

    logger.addHandler(handler)


logger = logging.getLogger("enterprise_rag")
