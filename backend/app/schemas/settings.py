from pydantic import BaseModel, Field
from typing import Optional


class AiProviderModel(BaseModel):
    """Описание доступной модели AI-провайдера."""
    model_id: str
    display_name: str
    max_tokens: int = 16384


class AiProviderConfig(BaseModel):
    """Конфигурация AI-провайдера (DeepSeek / Claude)."""
    enabled: bool = False
    api_key: str = ""
    api_base: str = ""
    model: str = ""
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    max_tokens: int = Field(default=16384, ge=1, le=200000)
    available_models: list[AiProviderModel] = Field(default_factory=list)


class AiProvidersSettings(BaseModel):
    """Настройки всех AI-провайдеров."""
    deepseek: AiProviderConfig = Field(default_factory=AiProviderConfig)
    claude: AiProviderConfig = Field(default_factory=AiProviderConfig)


class AdminSettings(BaseModel):
    """Администраторские настройки приложения."""
    app_name: str = "UNIK ERP"
    company_name: str = ""
    max_upload_size_mb: int = Field(default=50, ge=1, le=500)
    default_currency: str = "RUB"
    default_environment: str = "сухая"
    auto_backup_enabled: bool = False
    backup_interval_hours: int = Field(default=24, ge=1, le=168)
    debug_mode: bool = False
    log_level: str = "INFO"
    language: str = "ru"


class AppSettings(BaseModel):
    """Корневые настройки приложения."""
    ai_providers: AiProvidersSettings = Field(default_factory=AiProvidersSettings)
    admin: AdminSettings = Field(default_factory=AdminSettings)


class SettingsResponse(BaseModel):
    """Ответ API: все настройки."""
    settings: AppSettings
    last_modified: Optional[str] = None
    version: int = 1


class SettingsUpdateRequest(BaseModel):
    """Запрос на частичное обновление настроек."""
    ai_providers: Optional[AiProvidersSettings] = None
    admin: Optional[AdminSettings] = None
