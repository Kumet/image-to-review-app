"""記事テンプレート設定の保存と参照を扱うサービス。"""

from __future__ import annotations

import json
from pathlib import Path

from app.core.constants import DEFAULT_ARTICLE_TEMPLATES
from app.core.exceptions import ConfigPersistenceError, ValidationError
from app.schemas.admin import (
    ArticleTemplateConfig,
    ArticleTemplateCreate,
    ArticleTemplateUpdate,
)
from app.utils.ids import generate_template_id
from app.utils.time import utc_now


class ArticleTemplateService:
    """JSON ファイルに保存される記事テンプレート設定を管理する。"""

    def __init__(self, config_path: Path) -> None:
        self.config_path = config_path

    def ensure_config_file(self) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        if self.config_path.exists():
            return

        now = utc_now()
        templates = [
            ArticleTemplateConfig.model_validate(
                {**template, "created_at": now, "updated_at": now}
            )
            for template in DEFAULT_ARTICLE_TEMPLATES
        ]
        self._write_templates(templates)

    def list_templates(self) -> list[ArticleTemplateConfig]:
        self.ensure_config_file()
        try:
            raw_data = json.loads(self.config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ConfigPersistenceError("テンプレート設定の読み込みに失敗しました") from exc

        templates = [ArticleTemplateConfig.model_validate(item) for item in raw_data]
        return sorted(templates, key=lambda item: (item.sort_order, item.created_at))

    def list_enabled_templates(self) -> list[ArticleTemplateConfig]:
        return [template for template in self.list_templates() if template.enabled]

    def get_template(self, template_id: str) -> ArticleTemplateConfig:
        for template in self.list_templates():
            if template.template_id == template_id:
                return template
        raise ValidationError("指定された記事テンプレートが見つかりません")

    def create_template(self, payload: ArticleTemplateCreate) -> ArticleTemplateConfig:
        templates = self.list_templates()
        if any(template.name == payload.name for template in templates):
            raise ValidationError("同じ名前の記事テンプレートが既に存在します")

        now = utc_now()
        created = ArticleTemplateConfig(
            template_id=generate_template_id(),
            name=payload.name,
            description=payload.description,
            title_template=payload.title_template,
            body_template=payload.body_template,
            enabled=payload.enabled,
            sort_order=len(templates) + 1,
            created_at=now,
            updated_at=now,
        )
        templates.append(created)
        self._write_templates(templates)
        return created

    def update_template(
        self,
        template_id: str,
        payload: ArticleTemplateUpdate,
    ) -> ArticleTemplateConfig:
        templates = self.list_templates()
        updated_template: ArticleTemplateConfig | None = None
        now = utc_now()
        new_templates: list[ArticleTemplateConfig] = []

        for template in templates:
            if template.template_id != template_id:
                new_templates.append(template)
                continue

            updated_template = template.model_copy(
                update={
                    "name": payload.name,
                    "description": payload.description,
                    "title_template": payload.title_template,
                    "body_template": payload.body_template,
                    "enabled": payload.enabled,
                    "updated_at": now,
                }
            )
            new_templates.append(updated_template)

        if updated_template is None:
            raise ValidationError("指定された記事テンプレートが見つかりません")

        self._write_templates(new_templates)
        return updated_template

    def toggle_template(self, template_id: str) -> ArticleTemplateConfig:
        template = self.get_template(template_id)
        return self.update_template(
            template_id,
            ArticleTemplateUpdate(
                name=template.name,
                description=template.description,
                title_template=template.title_template,
                body_template=template.body_template,
                enabled=not template.enabled,
            ),
        )

    def reorder_templates(self, template_ids: list[str]) -> list[ArticleTemplateConfig]:
        templates = self.list_templates()
        template_map = {template.template_id: template for template in templates}
        if set(template_ids) != set(template_map):
            raise ValidationError("並び替え対象が不正です")

        now = utc_now()
        reordered = [
            template_map[template_id].model_copy(update={"sort_order": index, "updated_at": now})
            for index, template_id in enumerate(template_ids, start=1)
        ]
        self._write_templates(reordered)
        return reordered

    def _write_templates(self, templates: list[ArticleTemplateConfig]) -> None:
        try:
            serialized = [template.model_dump(mode="json") for template in templates]
            self.config_path.write_text(
                json.dumps(serialized, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        except OSError as exc:
            raise ConfigPersistenceError("テンプレート設定の保存に失敗しました") from exc
