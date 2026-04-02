"""解析結果関連スキーマ。"""

from __future__ import annotations

from app.schemas.common import AppSchema
from app.schemas.upload import UploadJob


class ExtractedFieldResult(AppSchema):
    key: str
    label: str
    value: str
    source: str = "dummy"
    confidence: float | None = None


class DummyItemResult(AppSchema):
    filename: str
    dummy_label: str
    score: float
    comment: str
    extracted_fields: list[ExtractedFieldResult]


class UploadResultFieldView(AppSchema):
    key: str
    label: str
    value: str


class DummyAnalysisResult(AppSchema):
    job_id: str
    summary: str
    item_results: list[DummyItemResult]


class UploadResultItemView(AppSchema):
    original_filename: str
    stored_filename: str
    preview_url: str
    content_type: str
    size_kb: str
    dimensions: str
    dummy_label: str
    score: float
    comment: str
    extracted_fields: list[UploadResultFieldView]


class UploadResultView(AppSchema):
    job_id: str
    uploaded_at: str
    file_count: int
    summary: str
    average_score: float
    items: list[UploadResultItemView]


class UploadProcessOutcome(AppSchema):
    job: UploadJob
    analysis: DummyAnalysisResult
    view: UploadResultView
