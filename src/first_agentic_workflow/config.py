"""Application configuration via environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    debug: bool = False
    default_model: str = "gemini-2.0-flash"
    budget_per_run_usd: float = 1.0
    n8n_base_url: str = "http://localhost:5678"
    apify_token: str = ""
    slack_alert_webhook: str = ""
    gemini_api_key: str = ""
    db_path: str = "data/leads.db"
    output_dir: str = "output"
    default_client: str = "example"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
