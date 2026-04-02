"""環境変数ベースの設定管理。"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import field_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from app.core.constants import DEFAULT_ALLOWED_CONTENT_TYPES, DEFAULT_ALLOWED_EXTENSIONS

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _parse_env_list(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return tuple(part.strip() for part in value.split(",") if part.strip())
    if isinstance(value, (list, tuple, set)):
        return tuple(str(part).strip() for part in value if str(part).strip())
    raise TypeError("Expected a string or sequence for list-like setting.")


class Settings(BaseSettings):
    """アプリケーション設定。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        enable_decoding=False,
    )

    app_name: str = "photo-upload-app"
    app_env: str = "local"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    max_upload_files: int = 10
    max_file_size_mb: int = 10
    upload_dir: str = "app/static/uploads"
    allowed_extensions: tuple[str, ...] = DEFAULT_ALLOWED_EXTENSIONS
    allowed_content_types: tuple[str, ...] = DEFAULT_ALLOWED_CONTENT_TYPES
    enable_image_preview: bool = True
    log_level: str = "INFO"
    extraction_config_path: str = "config/extraction_fields.json"

    @field_validator("allowed_extensions", mode="before")
    @classmethod
    def parse_allowed_extensions(cls, value: Any) -> tuple[str, ...]:
        parsed = _parse_env_list(value) or DEFAULT_ALLOWED_EXTENSIONS
        return tuple(item if item.startswith(".") else f".{item}" for item in parsed)

    @field_validator("allowed_content_types", mode="before")
    @classmethod
    def parse_allowed_content_types(cls, value: Any) -> tuple[str, ...]:
        return _parse_env_list(value) or DEFAULT_ALLOWED_CONTENT_TYPES

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return init_settings, dotenv_settings, env_settings, file_secret_settings

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    @property
    def templates_dir(self) -> Path:
        return PROJECT_ROOT / "app" / "templates"

    @property
    def static_dir(self) -> Path:
        return PROJECT_ROOT / "app" / "static"

    @property
    def upload_dir_path(self) -> Path:
        upload_path = Path(self.upload_dir)
        if upload_path.is_absolute():
            return upload_path
        return (PROJECT_ROOT / upload_path).resolve()

    @property
    def extraction_config_file_path(self) -> Path:
        config_path = Path(self.extraction_config_path)
        if config_path.is_absolute():
            return config_path
        return (PROJECT_ROOT / config_path).resolve()


@lru_cache
def get_settings() -> Settings:
    """設定インスタンスをキャッシュして返す。"""

    return Settings()
