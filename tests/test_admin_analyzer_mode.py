from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.services.analyzer_mode_service import AnalyzerModeService


def test_admin_analyzer_mode_page_returns_200(client: TestClient) -> None:
    response = client.get("/admin/analyzer-mode")

    assert response.status_code == 200
    assert "解析モード設定" in response.text
    assert 'name="analyzer_mode"' in response.text


def test_admin_can_switch_analyzer_mode(
    client: TestClient,
    settings: Settings,
) -> None:
    response = client.post(
        "/admin/analyzer-mode",
        data={"analyzer_mode": "dummy"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "現在: dummy" in response.text

    service = AnalyzerModeService(
        Path(settings.analyzer_config_path),
        default_mode=settings.analyzer_mode,
    )
    assert service.get_mode() == "dummy"
