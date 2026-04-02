"""抽出結果を記事テンプレートへ安全に埋め込むサービス。"""

from __future__ import annotations

import re

from app.core.exceptions import ValidationError
from app.schemas.result import ExtractedFieldResult, GeneratedArticleView
from app.services.article_template_service import ArticleTemplateService

PLACEHOLDER_PATTERN = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


class ArticleRenderService:
    """記事テンプレートの検証とレンダリングを行う。"""

    def __init__(self, template_service: ArticleTemplateService) -> None:
        self.template_service = template_service

    def validate_template_strings(
        self,
        *,
        title_template: str,
        body_template: str,
        allowed_keys: set[str],
    ) -> None:
        unknown = (
            self._extract_unknown_keys(title_template, allowed_keys)
            | self._extract_unknown_keys(body_template, allowed_keys)
        )
        if unknown:
            joined = ", ".join(sorted(unknown))
            raise ValidationError(f"使用できない変数があります: {joined}")

    def render_articles(
        self,
        extracted_fields: list[ExtractedFieldResult],
    ) -> list[GeneratedArticleView]:
        context = {field.key: field.value for field in extracted_fields}
        return [
            GeneratedArticleView(
                template_id=template.template_id,
                template_name=template.name,
                title=self._replace_placeholders(template.title_template, context),
                body=self._replace_placeholders(template.body_template, context),
            )
            for template in self.template_service.list_enabled_templates()
        ]

    def available_variables(self, allowed_keys: list[str]) -> list[str]:
        return [f"{{{key}}}" for key in allowed_keys]

    def _extract_unknown_keys(self, template: str, allowed_keys: set[str]) -> set[str]:
        keys = {match.group(1) for match in PLACEHOLDER_PATTERN.finditer(template)}
        return keys - allowed_keys

    def _replace_placeholders(self, template: str, context: dict[str, str]) -> str:
        def replacer(match: re.Match[str]) -> str:
            key = match.group(1)
            value = context.get(key, "未設定")
            return value if value else "未設定"

        return PLACEHOLDER_PATTERN.sub(replacer, template)
