"""
Logging setup for HomeIQ.

Call setup_logging() once at the start of each CLI entry point.
All modules use: import logging; log = logging.getLogger(__name__)
"""
from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parents[1] / "logs"
LOG_FILE = LOG_DIR / "homeiq.log"

_FMT_CONSOLE = "%(asctime)s %(levelname)-8s %(name)-30s %(message)s"
_FMT_FILE    = "%(asctime)s %(levelname)-8s %(name)-30s %(message)s"
_DATE_FMT    = "%H:%M:%S"


def setup_logging(level: str = "INFO") -> None:
    """
    Configure root logger with console + rotating file handlers.
    Call once at CLI startup.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    if root.handlers:
        return  # already configured

    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(_FMT_CONSOLE, datefmt=_DATE_FMT))
    root.addHandler(ch)

    # Rotating file handler (5MB x 3 backups)
    fh = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(_FMT_FILE, datefmt=_DATE_FMT))
    root.addHandler(fh)

    # Silence noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
