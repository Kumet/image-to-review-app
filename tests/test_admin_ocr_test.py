from __future__ import annotations

from typing import Any, cast

from fastapi.testclient import TestClient

from app.schemas.result import (
    ExtractedFieldCandidate,
    ExtractedFieldResult,
    GeneratedArticleView,
    OCRDebugImageView,
    OCRDebugOptions,
    OCRDebugResultView,
    UnifiedInferenceResult,
)
from app.schemas.upload import UploadedImageInfo, UploadJob
from app.utils.time import utc_now


class StubUploadService:
    async def save_uploads(self, files: list[object] | None) -> UploadJob:
        return UploadJob(
            job_id="job-ocr-test",
            uploaded_at=utc_now(),
            file_count=1,
            files=[
                UploadedImageInfo(
                    original_filename="sample.png",
                    stored_filename="stored.png",
                    relative_path="uploads/job-ocr-test/stored.png",
                    content_type="image/png",
                    size_bytes=1024,
                    width=100,
                    height=80,
                )
            ],
        )


class StubOCRDebugService:
    def run(self, *, job: UploadJob, options: OCRDebugOptions) -> OCRDebugResultView:
        return OCRDebugResultView(
            job_id=job.job_id,
            options=options,
            images=[
                OCRDebugImageView(
                    original_filename="sample.png",
                    original_preview_url="/static/uploads/job-ocr-test/stored.png",
                    preprocessed_preview_url="/static/uploads/job-ocr-test/preprocessed-stored.png",
                    raw_text="濃厚チーズせんべい\n税込 198円",
                    lines=["濃厚チーズせんべい", "税込 198円"],
                    candidates=[
                        ExtractedFieldCandidate(
                            key="product_name",
                            value="濃厚チーズせんべい",
                            confidence=0.8,
                            image_id="stored.png",
                            source_text="濃厚チーズせんべい",
                        )
                    ],
                )
            ],
            unified_result=UnifiedInferenceResult(
                source_image_count=1,
                extracted_fields=[
                    ExtractedFieldResult(
                        key="product_name",
                        label="商品名",
                        value="濃厚チーズせんべい",
                    )
                ],
                warnings=[],
            ),
            generated_articles=[
                GeneratedArticleView(
                    template_id="template_blog_intro",
                    template_name="商品紹介ブログ",
                    title="濃厚チーズせんべい を紹介",
                    body="本文",
                )
            ],
            summary="1 枚の画像を対象に OCR テストを実行しました。",
        )


def test_admin_ocr_test_page_returns_200(client: TestClient) -> None:
    response = client.get("/admin/ocr-test")

    assert response.status_code == 200
    assert "OCRテスト" in response.text
    assert 'hx-post="/admin/ocr-test"' in response.text
    assert "二値化閾値" in response.text


def test_admin_ocr_test_run_returns_partial(
    client: TestClient,
    png_image_bytes: bytes,
) -> None:
    cast(Any, client.app).state.upload_service = StubUploadService()
    cast(Any, client.app).state.ocr_debug_service = StubOCRDebugService()

    response = client.post(
        "/admin/ocr-test",
        headers={"HX-Request": "true"},
        data={
            "lang": "jpn+eng",
            "psm": "6",
            "threshold": "160",
            "contrast": "1.8",
            "resize_scale": "2.0",
        },
        files=[("images", ("sample.png", png_image_bytes, "image/png"))],
    )

    assert response.status_code == 200
    assert "OCRテスト結果" in response.text
    assert "濃厚チーズせんべい" in response.text
    assert "税込 198円" in response.text
    assert "商品紹介ブログ" in response.text
