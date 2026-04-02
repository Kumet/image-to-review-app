"""管理画面向け設定スキーマ。"""

from __future__ import annotations

from datetime import datetime

from pydantic import field_validator

from app.core.constants import ALLOWED_FIELD_TYPES
from app.schemas.common import AppSchema


class ExtractionFieldConfig(AppSchema):
    field_id: str
    key: str
    label: str
    field_type: str
    enabled: bool = True
    required: bool = False
    sort_order: int
    placeholder: str | None = None
    description: str | None = None
    created_at: datetime
    updated_at: datetime

    @field_validator("field_type")
    @classmethod
    def validate_field_type(cls, value: str) -> str:
        if value not in ALLOWED_FIELD_TYPES:
            raise ValueError("Unsupported field type.")
        return value


class ExtractionFieldCreate(AppSchema):
    key: str
    label: str
    field_type: str
    enabled: bool = True
    required: bool = False
    placeholder: str | None = None
    description: str | None = None

    @field_validator("field_type")
    @classmethod
    def validate_field_type(cls, value: str) -> str:
        if value not in ALLOWED_FIELD_TYPES:
            raise ValueError("Unsupported field type.")
        return value


class ExtractionFieldUpdate(AppSchema):
    label: str
    field_type: str
    enabled: bool = True
    required: bool = False
    placeholder: str | None = None
    description: str | None = None

    @field_validator("field_type")
    @classmethod
    def validate_field_type(cls, value: str) -> str:
        if value not in ALLOWED_FIELD_TYPES:
            raise ValueError("Unsupported field type.")
        return value


class ArticleTemplateConfig(AppSchema):
    template_id: str
    name: str
    description: str | None = None
    title_template: str
    body_template: str
    enabled: bool = True
    sort_order: int
    created_at: datetime
    updated_at: datetime


class ArticleTemplateCreate(AppSchema):
    name: str
    description: str | None = None
    title_template: str
    body_template: str
    enabled: bool = True


class ArticleTemplateUpdate(AppSchema):
    name: str
    description: str | None = None
    title_template: str
    body_template: str
    enabled: bool = True
