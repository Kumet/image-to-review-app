from __future__ import annotations

from pathlib import Path

from PIL import Image

from app.schemas.admin import ExtractionFieldCreate
from app.schemas.result import ExtractedFieldCandidate, OCRImageResult
from app.schemas.upload import UploadedImageInfo, UploadJob
from app.services.extraction_field_service import ExtractionFieldService
from app.services.product_analyzer import ProductAnalyzer
from app.utils.time import utc_now


class StubPreprocessor:
    def preprocess(self, image_path: Path) -> Image.Image:
        return Image.new("RGB", (32, 32), color=(255, 255, 255))


class StubOCRService:
    def __init__(self, results: dict[str, OCRImageResult]) -> None:
        self.results = results

    def extract_text(self, image: Image.Image, *, image_path: Path) -> OCRImageResult:
        return self.results[image_path.name]


class StubFieldExtractor:
    def __init__(self, candidates: dict[str, list[ExtractedFieldCandidate]]) -> None:
        self.candidates = candidates

    def extract(self, ocr_result: OCRImageResult) -> list[ExtractedFieldCandidate]:
        image_name = Path(ocr_result.image_path).name
        return self.candidates[image_name]


def test_product_analyzer_returns_structured_result_with_fused_values(tmp_path: Path) -> None:
    upload_root = tmp_path / "uploads"
    job_dir = upload_root / "job-1"
    job_dir.mkdir(parents=True)
    for filename in ("stored.png", "stored-detail.png"):
        (job_dir / filename).write_bytes(b"image")

    job = UploadJob(
        job_id="job-1",
        uploaded_at=utc_now(),
        file_count=2,
        files=[
            UploadedImageInfo(
                original_filename="sample.png",
                stored_filename="stored.png",
                relative_path="uploads/job-1/stored.png",
                content_type="image/png",
                size_bytes=1024,
                width=100,
                height=80,
            ),
            UploadedImageInfo(
                original_filename="sample-detail.png",
                stored_filename="stored-detail.png",
                relative_path="uploads/job-1/stored-detail.png",
                content_type="image/png",
                size_bytes=2048,
                width=320,
                height=240,
            ),
        ],
    )
    field_service = ExtractionFieldService(tmp_path / "config" / "extraction_fields.json")
    field_service.ensure_config_file()
    analyzer = ProductAnalyzer(
        field_service,
        upload_root=upload_root,
        preprocessor=StubPreprocessor(),
        ocr_service=StubOCRService(
            {
                "stored.png": OCRImageResult(
                    image_path=str(job_dir / "stored.png"),
                    raw_text="濃厚チーズせんべい",
                    lines=["濃厚チーズせんべい"],
                ),
                "stored-detail.png": OCRImageResult(
                    image_path=str(job_dir / "stored-detail.png"),
                    raw_text="詳細",
                    lines=["詳細"],
                ),
            }
        ),
        field_extractor=StubFieldExtractor(
            {
                "stored.png": [
                    ExtractedFieldCandidate(
                        key="product_name",
                        value="濃厚チーズせんべい",
                        confidence=0.8,
                        image_id="stored.png",
                        source_text="濃厚チーズせんべい",
                    ),
                    ExtractedFieldCandidate(
                        key="price",
                        value="198円",
                        confidence=0.95,
                        image_id="stored.png",
                        source_text="198円",
                    ),
                ],
                "stored-detail.png": [
                    ExtractedFieldCandidate(
                        key="ingredients",
                        value="チーズ、でん粉、食塩",
                        confidence=0.95,
                        image_id="stored-detail.png",
                        source_text="原材料名 チーズ、でん粉、食塩",
                    ),
                    ExtractedFieldCandidate(
                        key="calories",
                        value="245 kcal",
                        confidence=0.95,
                        image_id="stored-detail.png",
                        source_text="245 kcal",
                    ),
                ],
            }
        ),
    )

    result = analyzer.analyze(job)

    assert result.job_id == "job-1"
    assert result.source_image_count == 2
    assert "2 枚の画像を統合" in result.summary
    assert {field.key: field.value for field in result.extracted_fields} == {
        "product_name": "濃厚チーズせんべい",
        "ingredients": "チーズ、でん粉、食塩",
        "calories": "245 kcal",
        "price": "198円",
        "summary": (
            "濃厚チーズせんべい は チーズ、でん粉、食塩 を含む商品で、"
            "245 kcal、価格は 198円 です。"
        ),
    }


def test_product_analyzer_respects_enabled_fields(tmp_path: Path) -> None:
    upload_root = tmp_path / "uploads"
    job_dir = upload_root / "job-1"
    job_dir.mkdir(parents=True)
    (job_dir / "stored.png").write_bytes(b"image")

    field_service = ExtractionFieldService(tmp_path / "config" / "extraction_fields.json")
    field_service.ensure_config_file()
    field_service.create_field(
        ExtractionFieldCreate(
            key="brand_name",
            label="ブランド名",
            field_type="text",
            enabled=False,
            required=False,
        )
    )
    analyzer = ProductAnalyzer(
        field_service,
        upload_root=upload_root,
        preprocessor=StubPreprocessor(),
        ocr_service=StubOCRService(
            {
                "stored.png": OCRImageResult(
                    image_path=str(job_dir / "stored.png"),
                    raw_text="濃厚チーズせんべい",
                    lines=["濃厚チーズせんべい"],
                )
            }
        ),
        field_extractor=StubFieldExtractor(
            {
                "stored.png": [
                    ExtractedFieldCandidate(
                        key="product_name",
                        value="濃厚チーズせんべい",
                        confidence=0.8,
                        image_id="stored.png",
                        source_text="濃厚チーズせんべい",
                    )
                ]
            }
        ),
    )
    job = UploadJob(
        job_id="job-1",
        uploaded_at=utc_now(),
        file_count=1,
        files=[
            UploadedImageInfo(
                original_filename="sample.png",
                stored_filename="stored.png",
                relative_path="uploads/job-1/stored.png",
                content_type="image/png",
                size_bytes=1024,
                width=100,
                height=80,
            )
        ],
    )

    result = analyzer.analyze(job)

    returned_keys = [field.key for field in result.extracted_fields]
    assert "brand_name" not in returned_keys
