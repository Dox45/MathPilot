"""Configuration management."""

import os
from pathlib import Path
from typing import Optional

import yaml


class Config:
    """Application configuration."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Load configuration from file or defaults.

        Searches in order:
        1. Provided config_path
        2. ./.mathpilot.yaml
        3. ~/.mathpilot.yaml
        4. Built-in defaults
        """
        self.config = self._load_config(config_path)

    def _load_config(self, path: Optional[str]) -> dict:
        """Load YAML config from file and environment variables."""
        from dotenv import load_dotenv
        load_dotenv()

        # Default configuration
        config = {
            "llm": {
                "provider": "gemini",
                "model": "gemini-2.5-pro",
                "api_key": os.getenv("GEMINI_API_KEY"),
            },
            "arxiv": {
                "cache_dir": os.path.expanduser("~/.mathpilot/cache"),
                "max_results": 10,
            },
            "executor": {
                "sandbox": True,
                "timeout_seconds": 300,
            },
        }

        # TODO: Merge with file-based config if provided
        if path and os.path.exists(path):
            with open(path, "r") as f:
                file_config = yaml.safe_load(f)
                # Simple merge (deep merge would be better in production)
                config.update(file_config)

        return config

    def get(self, key: str, default=None):
        """Get configuration value."""
        parts = key.split(".")
        value = self.config
        for part in parts:
            value = value.get(part, {})
        return value or default

    def set(self, key: str, value) -> None:
        """Set configuration value."""
        # TODO: Implement
        pass
