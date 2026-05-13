from pydantic_settings import BaseSettings
from pathlib import Path
from functools import lru_cache


class Settings(BaseSettings):
    PROJECT_NAME: str = "UNIK ERP"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "sqlite+aiosqlite:///K:/Projects/UNIK/unik.db"

    UPLOAD_DIR: Path = Path("uploads")
    MAX_UPLOAD_SIZE_MB: int = 50

    PARSER_CONFIDENCE_THRESHOLD: float = 0.6
    PARSER_LOG_UNRECOGNIZED: bool = True

    model_config = {"env_prefix": "UNIK_", "env_file": ".env"}


settings = Settings()


def _get_admin():
    """Ленивая загрузка админ-настроек (с кешем на 5 сек)."""
    try:
        from app.services.settings_service import load_settings
        return load_settings().admin
    except Exception:
        return None


def get_project_name() -> str:
    """Название проекта из админ-панели → env-переменная."""
    try:
        admin = _get_admin()
        if admin and admin.app_name:
            return admin.app_name
    except Exception:
        pass
    return settings.PROJECT_NAME


def get_max_upload_size_mb() -> int:
    """Лимит загрузки из админ-панели → .env."""
    try:
        admin = _get_admin()
        if admin and admin.max_upload_size_mb > 0:
            return admin.max_upload_size_mb
    except Exception:
        pass
    return settings.MAX_UPLOAD_SIZE_MB


def get_default_environment() -> str:
    """Среда по умолчанию из админ-панели → 'сухая'."""
    try:
        admin = _get_admin()
        if admin and admin.default_environment:
            return admin.default_environment
    except Exception:
        pass
    return "сухая"


def get_debug_mode() -> bool:
    """Режим отладки из админ-панели."""
    try:
        admin = _get_admin()
        if admin:
            return admin.debug_mode
    except Exception:
        pass
    return False


def get_log_level() -> str:
    """Уровень логирования из админ-панели → 'INFO'."""
    try:
        admin = _get_admin()
        if admin and admin.log_level:
            return admin.log_level
    except Exception:
        pass
    return "INFO"
