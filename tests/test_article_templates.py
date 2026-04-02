from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.schemas.result import ExtractedFieldResult
from app.services.article_render_service import ArticleRenderService
from app.services.article_template_service import ArticleTemplateService


def test_admin_can_create_and_toggle_article_template(
    client: TestClient,
    settings: Settings,
) -> None:
    response = client.post(
        "/admin/article-templates",
        data={
            "name": "SNS向けテンプレート",
            "description": "短文向け",
            "title_template": "{product_name} の紹介",
            "body_template": "{product_name} は {summary}",
            "enabled": "on",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "SNS向けテンプレート" in response.text

    service = ArticleTemplateService(Path(settings.article_template_config_path))
    created = next(
        template
        for template in service.list_templates()
        if template.name == "SNS向けテンプレート"
    )

    toggle_response = client.post(
        f"/admin/article-templates/{created.template_id}/toggle",
        follow_redirects=True,
    )

    assert toggle_response.status_code == 200
    assert "無効" in toggle_response.text


def test_admin_can_edit_and_reorder_article_templates(
    client: TestClient,
    settings: Settings,
) -> None:
    service = ArticleTemplateService(Path(settings.article_template_config_path))
    templates = service.list_templates()
    first_template = templates[0]
    last_template = templates[-1]

    edit_response = client.post(
        f"/admin/article-templates/{first_template.template_id}",
        data={
            "name": "商品ブログテンプレート",
            "description": "更新済み",
            "title_template": "{product_name} を詳しく紹介",
            "body_template": "{summary}\n価格は {price}",
            "enabled": "on",
        },
        follow_redirects=True,
    )

    assert edit_response.status_code == 200
    assert "商品ブログテンプレート" in edit_response.text

    reorder_response = client.post(
        "/admin/article-template-actions/reorder",
        data={
            "template_ids": [
                last_template.template_id,
                *[template.template_id for template in templates[:-1]],
            ]
        },
        follow_redirects=True,
    )

    assert reorder_response.status_code == 200
    reordered_templates = service.list_templates()
    assert reordered_templates[0].template_id == last_template.template_id


def test_article_render_service_replaces_missing_values_with_placeholder(
    settings: Settings,
) -> None:
    template_service = ArticleTemplateService(Path(settings.article_template_config_path))
    template_service.ensure_config_file()
    render_service = ArticleRenderService(template_service)

    articles = render_service.render_articles(
        [
            ExtractedFieldResult(key="product_name", label="商品名", value="テスト商品"),
            ExtractedFieldResult(key="summary", label="商品概要", value="概要文"),
            ExtractedFieldResult(key="ingredients", label="原材料", value="砂糖"),
            ExtractedFieldResult(key="calories", label="カロリー", value="100 kcal"),
        ]
    )

    assert articles
    assert any("未設定" in article.body for article in articles)
