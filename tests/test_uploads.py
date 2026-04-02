from __future__ import annotations

from fastapi.testclient import TestClient


def test_uploads_returns_partial_for_valid_images(
    client: TestClient,
    png_image_bytes: bytes,
    jpeg_image_bytes: bytes,
) -> None:
    response = client.post(
        "/uploads",
        headers={"HX-Request": "true"},
        files=[
            ("images", ("sample-1.png", png_image_bytes, "image/png")),
            ("images", ("sample-2.jpg", jpeg_image_bytes, "image/jpeg")),
        ],
    )

    assert response.status_code == 200
    assert "解析結果" in response.text
    assert "sample-1.png" in response.text
    assert "sample-2.jpg" in response.text
    assert "/static/uploads/" in response.text


def test_uploads_returns_error_when_no_files_selected(client: TestClient) -> None:
    response = client.post("/uploads", headers={"HX-Request": "true"})

    assert response.status_code == 400
    assert response.headers["HX-Retarget"] == "#error-area"
    assert "画像が選択されていません" in response.text


def test_uploads_returns_error_for_unsupported_extension(
    client: TestClient,
    png_image_bytes: bytes,
) -> None:
    response = client.post(
        "/uploads",
        headers={"HX-Request": "true"},
        files=[("images", ("invalid.txt", png_image_bytes, "image/png"))],
    )

    assert response.status_code == 400
    assert "対応していない画像形式です" in response.text


def test_uploads_returns_error_for_too_many_files(
    client: TestClient,
    png_image_bytes: bytes,
) -> None:
    response = client.post(
        "/uploads",
        headers={"HX-Request": "true"},
        files=[
            ("images", ("a.png", png_image_bytes, "image/png")),
            ("images", ("b.png", png_image_bytes, "image/png")),
            ("images", ("c.png", png_image_bytes, "image/png")),
            ("images", ("d.png", png_image_bytes, "image/png")),
        ],
    )

    assert response.status_code == 400
    assert "アップロード上限を超えています" in response.text


def test_uploads_returns_error_for_corrupted_image(client: TestClient) -> None:
    response = client.post(
        "/uploads",
        headers={"HX-Request": "true"},
        files=[("images", ("broken.png", b"not-an-image", "image/png"))],
    )

    assert response.status_code == 400
    assert "画像の処理に失敗しました" in response.text
