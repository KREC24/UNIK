"""
Сервис управления настройками приложения.

Хранит настройки в JSON-файле settings.json в корне backend/.
Поддерживает чтение, запись и сброс к заводским настройкам.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.schemas.settings import (
    AppSettings,
    AiProvidersSettings,
    AiProviderConfig,
    AiProviderModel,
    AdminSettings,
    SettingsUpdateRequest,
)

logger = logging.getLogger(__name__)

SETTINGS_FILE = Path(__file__).resolve().parent.parent.parent / "settings.json"


def _default_settings() -> AppSettings:
    """Заводские настройки."""
    return AppSettings(
        ai_providers=AiProvidersSettings(
            deepseek=AiProviderConfig(
                enabled=False,
                api_key="",
                api_base="https://api.deepseek.com/v1",
                model="deepseek-chat",
                temperature=0.3,
                max_tokens=16384,
                available_models=[
                    AiProviderModel(model_id="deepseek-chat", display_name="DeepSeek Chat (V3)", max_tokens=65536),
                    AiProviderModel(model_id="deepseek-reasoner", display_name="DeepSeek Reasoner (R1)", max_tokens=65536),
                ],
            ),
            claude=AiProviderConfig(
                enabled=False,
                api_key="",
                api_base="https://api.anthropic.com/v1",
                model="claude-sonnet-4-20250514",
                temperature=0.3,
                max_tokens=16384,
                available_models=[
                    AiProviderModel(model_id="claude-sonnet-4-20250514", display_name="Claude Sonnet 4", max_tokens=200000),
                    AiProviderModel(model_id="claude-3-5-sonnet-20241022", display_name="Claude 3.5 Sonnet", max_tokens=200000),
                    AiProviderModel(model_id="claude-3-opus-20240229", display_name="Claude 3 Opus", max_tokens=200000),
                    AiProviderModel(model_id="claude-3-haiku-20240307", display_name="Claude 3 Haiku", max_tokens=200000),
                ],
            ),
        ),
        admin=AdminSettings(
            app_name="UNIK ERP",
            company_name="",
            max_upload_size_mb=50,
            default_currency="RUB",
            default_environment="сухая",
            auto_backup_enabled=False,
            backup_interval_hours=24,
            debug_mode=False,
            log_level="INFO",
            language="ru",
        ),
    )


def load_settings() -> AppSettings:
    """Загружает настройки из файла или возвращает заводские."""
    if SETTINGS_FILE.exists():
        try:
            raw = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            return AppSettings.model_validate(raw)
        except Exception as e:
            logger.warning("Failed to load settings.json, using defaults: %s", e)
    return _default_settings()


def save_settings(settings: AppSettings) -> None:
    """Сохраняет настройки в файл."""
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = settings.model_dump()
    SETTINGS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Settings saved to %s", SETTINGS_FILE)


def get_settings() -> dict:
    """Получить текущие настройки (с метаданными)."""
    settings = load_settings()
    mtime = None
    if SETTINGS_FILE.exists():
        mtime = datetime.fromtimestamp(SETTINGS_FILE.stat().st_mtime, tz=timezone.utc).isoformat()
    return {
        "settings": settings.model_dump(exclude={"ai_providers": {"deepseek": {"api_key"}, "claude": {"api_key"}}}),
        "last_modified": mtime,
        "version": 1,
    }


def update_settings(data: SettingsUpdateRequest) -> dict:
    """Частичное обновление настроек."""
    settings = load_settings()

    if data.ai_providers is not None:
        settings.ai_providers = data.ai_providers
    if data.admin is not None:
        settings.admin = data.admin

    save_settings(settings)
    return get_settings()


def reset_settings() -> dict:
    """Сброс настроек к заводским."""
    settings = _default_settings()
    save_settings(settings)
    return get_settings()


def get_provider_config(provider: str) -> Optional[AiProviderConfig]:
    """Получить настройки конкретного AI-провайдера."""
    settings = load_settings()
    if provider == "deepseek":
        return settings.ai_providers.deepseek
    elif provider == "claude":
        return settings.ai_providers.claude
    return None


def get_admin_settings() -> AdminSettings:
    """Получить админские настройки."""
    return load_settings().admin
