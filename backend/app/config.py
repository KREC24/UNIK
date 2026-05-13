from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    PROJECT_NAME: str = "UNIK ERP"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/unik"

    UPLOAD_DIR: Path = Path("uploads")
    MAX_UPLOAD_SIZE_MB: int = 50

    PARSER_CONFIDENCE_THRESHOLD: float = 0.6
    PARSER_LOG_UNRECOGNIZED: bool = True

    model_config = {"env_prefix": "UNIK_", "env_file": ".env"}


settings = Settings()
