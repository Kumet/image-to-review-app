from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.services.extraction_field_service import ExtractionFieldService


def test_admin_can_create_and_toggle_field(
    client: TestClient,
    settings: Settings,
) -> None:
    response = client.post(
        "/admin/extraction-fields",
        data={
            "key": "brand_name",
            "label": "ブランド名",
            "field_type": "text",
            "enabled": "on",
            "placeholder": "ブランド名",
            "description": "ブランド名の抽出項目",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "ブランド名" in response.text

    service = ExtractionFieldService(Path(settings.extraction_config_path))
    created = next(field for field in service.list_fields() if field.key == "brand_name")

    toggle_response = client.post(
        f"/admin/extraction-fields/{created.field_id}/toggle",
        follow_redirects=True,
    )

    assert toggle_response.status_code == 200
    assert "無効" in toggle_response.text


def test_admin_can_edit_and_reorder_fields(
    client: TestClient,
    settings: Settings,
) -> None:
    service = ExtractionFieldService(Path(settings.extraction_config_path))
    fields = service.list_fields()
    first_field = fields[0]
    last_field = fields[-1]

    edit_response = client.post(
        f"/admin/extraction-fields/{first_field.field_id}",
        data={
            "label": "商品名称",
            "field_type": first_field.field_type,
            "enabled": "on",
            "required": "on",
            "placeholder": "変更後",
            "description": "更新済み",
        },
        follow_redirects=True,
    )

    assert edit_response.status_code == 200
    assert "商品名称" in edit_response.text

    reorder_response = client.post(
        "/admin/extraction-field-actions/reorder",
        data={"field_ids": [last_field.field_id, *[field.field_id for field in fields[:-1]]]},
        follow_redirects=True,
    )

    assert reorder_response.status_code == 200
    reordered_fields = service.list_fields()
    assert reordered_fields[0].field_id == last_field.field_id
