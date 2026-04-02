from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_app_uses_dummy_analyzer_when_configured(
    tmp_path: Path,
    png_image_bytes: bytes,
) -> None:
    settings = Settings(
        app_name="photo-upload-app-test",
        app_env="test",
        debug=True,
        upload_dir=str(tmp_path / "uploads"),
        extraction_config_path=str(tmp_path / "config" / "extraction_fields.json"),
        article_template_config_path=str(tmp_path / "config" / "article_templates.json"),
        max_upload_files=3,
        max_file_size_mb=1,
        allowed_extensions=(".jpg", ".jpeg", ".png", ".webp"),
        allowed_content_types=("image/jpeg", "image/png", "image/webp"),
        enable_image_preview=True,
        analyzer_config_path=str(tmp_path / "config" / "analyzer_settings.json"),
        analyzer_mode="dummy",
        log_level="INFO",
    )
    app = create_app(settings)

    with TestClient(app) as client:
        response = client.post(
            "/uploads",
            headers={"HX-Request": "true"},
            files=[("images", ("sample-1.png", png_image_bytes, "image/png"))],
        )

    assert response.status_code == 200
    assert "複数角度・ズーム画像を前提にしたダミー統合推論です。" in response.text
    assert "統合推定商品 sample-1" in response.text
