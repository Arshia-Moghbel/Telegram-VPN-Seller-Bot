"""Centralised, bounded logging suitable for a long-running bot."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def configure_logging(level_name: str, log_file: str = "") -> None:
    level = getattr(logging, level_name.upper(), logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if log_file:
        path = Path(log_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(RotatingFileHandler(path, maxBytes=5_000_000, backupCount=5, encoding="utf-8"))
    for handler in handlers:
        handler.setFormatter(formatter)
    logging.basicConfig(level=level, handlers=handlers, force=True)
