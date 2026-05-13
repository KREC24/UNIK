from fastapi import APIRouter, HTTPException

from app.schemas.settings import (
    SettingsUpdateRequest,
    AiProvidersSettings,
    AdminSettings,
)
from app.services.settings_service import (
    get_settings,
    update_settings,
    reset_settings,
    get_provider_config,
)

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("")
async def get_app_settings():
    """Получить все настройки приложения."""
    return get_settings()


@router.put("")
async def update_app_settings(data: SettingsUpdateRequest):
    """Обновить настройки приложения (частичное обновление)."""
    return update_settings(data)


@router.post("/reset")
async def reset_app_settings():
    """Сбросить настройки к заводским значениям."""
    return reset_settings()


# ---------- Admin routes (must be before /ai/{provider} to avoid route collision) ----------

@router.get("/admin")
async def get_admin_settings():
    """Получить администраторские настройки."""
    from app.services.settings_service import get_admin_settings
    return get_admin_settings().model_dump()


@router.put("/admin")
async def update_admin_settings(data: AdminSettings):
    """Обновить администраторские настройки."""
    from app.services.settings_service import load_settings, save_settings

    settings = load_settings()
    settings.admin = data
    save_settings(settings)

    return settings.admin.model_dump()


# ---------- AI provider routes ----------

@router.get("/ai")
async def get_ai_providers():
    """Получить настройки AI-провайдеров."""
    settings = get_settings()
    return settings["settings"]["ai_providers"]


@router.get("/ai/{provider}")
async def get_ai_provider(provider: str):
    """Получить настройки конкретного AI-провайдера (deepseek / claude)."""
    if provider not in ("deepseek", "claude"):
        raise HTTPException(400, "Поддерживаются: deepseek, claude")

    config = get_provider_config(provider)
    if not config:
        raise HTTPException(404, f"Провайдер {provider} не найден")

    return config.model_dump(exclude={"api_key"})


@router.put("/ai/{provider}")
async def update_ai_provider(provider: str, config: dict):
    """Обновить настройки AI-провайдера."""
    if provider not in ("deepseek", "claude"):
        raise HTTPException(400, "Поддерживаются: deepseek, claude")

    from app.services.settings_service import load_settings, save_settings
    from app.schemas.settings import AiProviderConfig

    settings = load_settings()
    provider_config = AiProviderConfig.model_validate(config)

    if provider == "deepseek":
        settings.ai_providers.deepseek = provider_config
    else:
        settings.ai_providers.claude = provider_config

    save_settings(settings)

    return provider_config.model_dump(exclude={"api_key"})
