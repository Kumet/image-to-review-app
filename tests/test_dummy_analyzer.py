from __future__ import annotations

from pathlib import Path

from app.schemas.admin import ExtractionFieldCreate
from app.schemas.upload import UploadedImageInfo, UploadJob
from app.services.dummy_analyzer import DummyAnalyzer
from app.services.extraction_field_service import ExtractionFieldService
from app.utils.time import utc_now


def test_dummy_analyzer_returns_structured_and_stable_result(tmp_path: Path) -> None:
    uploaded = UploadedImageInfo(
        original_filename="sample.png",
        stored_filename="stored.png",
        relative_path="uploads/job-1/stored.png",
        content_type="image/png",
        size_bytes=1024,
        width=100,
        height=80,
    )
    job = UploadJob(job_id="job-1", uploaded_at=utc_now(), file_count=1, files=[uploaded])
    field_service = ExtractionFieldService(tmp_path / "config" / "extraction_fields.json")
    field_service.ensure_config_file()
    analyzer = DummyAnalyzer(field_service)

    first = analyzer.analyze(job)
    second = analyzer.analyze(job)

    assert first.model_dump() == second.model_dump()
    assert first.job_id == "job-1"
    assert len(first.item_results) == 1
    assert first.item_results[0].filename == "stored.png"
    assert 60.0 <= first.item_results[0].score <= 100.0
    assert first.item_results[0].comment
    assert [field.key for field in first.item_results[0].extracted_fields] == [
        "product_name",
        "ingredients",
        "calories",
        "price",
        "summary",
    ]


def test_dummy_analyzer_respects_enabled_fields(tmp_path: Path) -> None:
    uploaded = UploadedImageInfo(
        original_filename="sample.png",
        stored_filename="stored.png",
        relative_path="uploads/job-1/stored.png",
        content_type="image/png",
        size_bytes=1024,
        width=100,
        height=80,
    )
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
    analyzer = DummyAnalyzer(field_service)
    job = UploadJob(job_id="job-1", uploaded_at=utc_now(), file_count=1, files=[uploaded])

    result = analyzer.analyze(job)

    returned_keys = [field.key for field in result.item_results[0].extracted_fields]
    assert "brand_name" not in returned_keys
