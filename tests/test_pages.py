from __future__ import annotations

from fastapi.testclient import TestClient


def test_index_returns_200(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "複数画像アップロード" in response.text
    assert 'hx-post="/uploads"' in response.text
    assert "/admin/extraction-fields" in response.text


def test_admin_extraction_fields_returns_200(client: TestClient) -> None:
    response = client.get("/admin/extraction-fields")

    assert response.status_code == 200
    assert "抽出項目管理" in response.text
    assert "商品名" in response.text
    assert "原材料" in response.text


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
