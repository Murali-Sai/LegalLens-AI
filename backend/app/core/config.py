from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Explicitly load .env before settings init
_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_env_path, override=True)


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    chroma_persist_dir: str = "./data/chroma_db"
    mlflow_tracking_uri: str = "./mlruns"
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    max_file_size_mb: int = 20
    mock_mode: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def effective_mock_mode(self) -> bool:
        """Auto-enable mock mode when no API key is configured."""
        return self.mock_mode or not self.openai_api_key.strip()


settings = Settings()
