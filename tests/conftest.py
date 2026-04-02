from __future__ import annotations

from collections.abc import Iterator
from io import BytesIO
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image

from app.core.config import Settings
from app.main import create_app


def make_image_bytes(
    image_format: str = "PNG",
    *,
    size: tuple[int, int] = (64, 64),
    color: tuple[int, int, int] = (120, 60, 220),
) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", size, color).save(buffer, format=image_format)
    return buffer.getvalue()


@pytest.fixture()
def settings(tmp_path: Path) -> Settings:
    return Settings(
        app_name="photo-upload-app-test",
        app_env="test",
        debug=True,
        upload_dir=str(tmp_path / "uploads"),
        max_upload_files=3,
        max_file_size_mb=1,
        allowed_extensions=(".jpg", ".jpeg", ".png", ".webp"),
        allowed_content_types=("image/jpeg", "image/png", "image/webp"),
        enable_image_preview=True,
        log_level="INFO",
    )


@pytest.fixture()
def app(settings: Settings) -> FastAPI:
    return create_app(settings)


@pytest.fixture()
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def png_image_bytes() -> bytes:
    return make_image_bytes("PNG")


@pytest.fixture()
def jpeg_image_bytes() -> bytes:
    return make_image_bytes("JPEG")
