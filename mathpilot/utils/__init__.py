"""Utility functions for logging, config, and file handling."""

import logging
import sys
from pathlib import Path
from typing import Optional


def get_logger(name: str) -> logging.Logger:
    """
    Create a logger instance.

    Args:
        name: Module name (__name__)

    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def ensure_dir(path: Path, description: str = "") -> Path:
    """
    Create directory if it doesn't exist.

    Args:
        path: Directory path
        description: Optional description for logging

    Returns:
        Path object
    """
    path = Path(path).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_file(path: str) -> str:
    """Read file contents."""
    return Path(path).expanduser().read_text()


def write_file(path: str, content: str, overwrite: bool = False) -> None:
    """Write content to file."""
    p = Path(path).expanduser()
    if p.exists() and not overwrite:
        raise FileExistsError(f"{path} already exists")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
