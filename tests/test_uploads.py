from __future__ import annotations

from typing import Any, cast

from fastapi.testclient import TestClient

from app.schemas.result import DummyAnalysisResult, ExtractedFieldResult


class StubAnalyzer:
    def analyze(self, job: object) -> DummyAnalysisResult:
        return DummyAnalysisResult(
            job_id="job-stub",
            summary=(
                "2 枚の画像を統合して 1 件の推論結果を作成しました。"
                "ローカル OCR による統合推論結果です。"
            ),
            source_image_count=2,
            extracted_fields=[
                ExtractedFieldResult(
                    key="product_name",
                    label="商品名",
                    value="濃厚チーズせんべい",
                ),
                ExtractedFieldResult(
                    key="ingredients",
                    label="原材料",
                    value="チーズ、でん粉、食塩",
                ),
                ExtractedFieldResult(key="calories", label="カロリー", value="245 kcal"),
                ExtractedFieldResult(key="price", label="値段", value="198円"),
                ExtractedFieldResult(
                    key="summary",
                    label="商品概要",
                    value=(
                        "濃厚チーズせんべい は チーズ、でん粉、食塩 を含む商品で、"
                        "245 kcal、価格は 198円 です。"
                    ),
                ),
            ],
        )


def test_uploads_returns_partial_for_valid_images(
    client: TestClient,
    png_image_bytes: bytes,
    jpeg_image_bytes: bytes,
) -> None:
    cast(Any, client.app).state.upload_service.analyzer = StubAnalyzer()
    response = client.post(
        "/uploads",
        headers={"HX-Request": "true"},
        files=[
            ("images", ("sample-1.png", png_image_bytes, "image/png")),
            ("images", ("sample-2.jpg", jpeg_image_bytes, "image/jpeg")),
        ],
    )

    assert response.status_code == 200
    assert "統合推論結果" in response.text
    assert "sample-1.png" in response.text
    assert "sample-2.jpg" in response.text
    assert "/static/uploads/" in response.text
    assert "2 枚の画像を統合" in response.text
    assert "商品名" in response.text
    assert "原材料" in response.text
    assert "カロリー" in response.text
    assert "値段" in response.text
    assert "商品概要" in response.text
    assert "生成記事" in response.text
    assert "商品紹介ブログ" in response.text
    assert "濃厚チーズせんべい を紹介" in response.text
    assert "平均" not in response.text
    assert "スコア" not in response.text


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
