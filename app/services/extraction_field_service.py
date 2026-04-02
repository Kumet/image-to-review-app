"""抽出項目設定の保存と参照を扱うサービス。"""

from __future__ import annotations

import json
from pathlib import Path

from app.core.constants import DEFAULT_EXTRACTION_FIELDS
from app.core.exceptions import ConfigPersistenceError, ValidationError
from app.schemas.admin import (
    ExtractionFieldConfig,
    ExtractionFieldCreate,
    ExtractionFieldUpdate,
)
from app.utils.ids import generate_field_id
from app.utils.time import utc_now


class ExtractionFieldService:
    """JSON ファイルに保存される抽出項目設定を管理する。"""

    def __init__(self, config_path: Path) -> None:
        self.config_path = config_path

    def ensure_config_file(self) -> None:
        """設定ファイルがなければ既定値で作成する。"""

        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        if self.config_path.exists():
            return
        now = utc_now()
        default_fields = [
            ExtractionFieldConfig.model_validate(
                {
                    **field,
                    "created_at": now,
                    "updated_at": now,
                }
            )
            for field in DEFAULT_EXTRACTION_FIELDS
        ]
        self._write_fields(default_fields)

    def list_fields(self) -> list[ExtractionFieldConfig]:
        """保存済みの抽出項目一覧を返す。"""

        self.ensure_config_file()
        try:
            raw_data = json.loads(self.config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ConfigPersistenceError("設定の読み込みに失敗しました") from exc
        fields = [ExtractionFieldConfig.model_validate(item) for item in raw_data]
        return sorted(fields, key=lambda field: (field.sort_order, field.created_at))

    def list_enabled_fields(self) -> list[ExtractionFieldConfig]:
        """有効な抽出項目のみ返す。"""

        return [field for field in self.list_fields() if field.enabled]

    def get_field(self, field_id: str) -> ExtractionFieldConfig:
        """指定 ID の抽出項目を返す。"""

        for field in self.list_fields():
            if field.field_id == field_id:
                return field
        raise ValidationError("指定された抽出項目が見つかりません")

    def create_field(self, payload: ExtractionFieldCreate) -> ExtractionFieldConfig:
        """抽出項目を新規作成する。"""

        fields = self.list_fields()
        if any(field.key == payload.key for field in fields):
            raise ValidationError("同じ key の項目が既に存在します")

        now = utc_now()
        created = ExtractionFieldConfig(
            field_id=generate_field_id(),
            key=payload.key,
            label=payload.label,
            field_type=payload.field_type,
            enabled=payload.enabled,
            required=payload.required,
            sort_order=len(fields) + 1,
            placeholder=payload.placeholder,
            description=payload.description,
            created_at=now,
            updated_at=now,
        )
        fields.append(created)
        self._write_fields(fields)
        return created

    def update_field(self, field_id: str, payload: ExtractionFieldUpdate) -> ExtractionFieldConfig:
        """既存抽出項目を更新する。"""

        fields = self.list_fields()
        updated_field: ExtractionFieldConfig | None = None
        now = utc_now()
        new_fields: list[ExtractionFieldConfig] = []

        for field in fields:
            if field.field_id != field_id:
                new_fields.append(field)
                continue
            updated_field = field.model_copy(
                update={
                    "label": payload.label,
                    "field_type": payload.field_type,
                    "enabled": payload.enabled,
                    "required": payload.required,
                    "placeholder": payload.placeholder,
                    "description": payload.description,
                    "updated_at": now,
                }
            )
            new_fields.append(updated_field)

        if updated_field is None:
            raise ValidationError("指定された抽出項目が見つかりません")

        self._write_fields(new_fields)
        return updated_field

    def toggle_field(self, field_id: str) -> ExtractionFieldConfig:
        """enabled を反転させる。"""

        field = self.get_field(field_id)
        return self.update_field(
            field_id,
            ExtractionFieldUpdate(
                label=field.label,
                field_type=field.field_type,
                enabled=not field.enabled,
                required=field.required,
                placeholder=field.placeholder,
                description=field.description,
            ),
        )

    def reorder_fields(self, field_ids: list[str]) -> list[ExtractionFieldConfig]:
        """指定順に sort_order を振り直す。"""

        fields = self.list_fields()
        field_map = {field.field_id: field for field in fields}
        if set(field_ids) != set(field_map):
            raise ValidationError("並び替え対象が不正です")

        now = utc_now()
        reordered = [
            field_map[field_id].model_copy(update={"sort_order": index, "updated_at": now})
            for index, field_id in enumerate(field_ids, start=1)
        ]
        self._write_fields(reordered)
        return reordered

    def _write_fields(self, fields: list[ExtractionFieldConfig]) -> None:
        try:
            serialized = [field.model_dump(mode="json") for field in fields]
            self.config_path.write_text(
                json.dumps(serialized, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            raise ConfigPersistenceError("設定の保存に失敗しました") from exc
