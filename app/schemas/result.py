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


class OCRImageResult(AppSchema):
    image_path: str
    raw_text: str
    lines: list[str]


class ExtractedFieldCandidate(AppSchema):
    key: str
    value: str
    confidence: float
    image_id: str
    source_text: str


class UnifiedInferenceResult(AppSchema):
    source_image_count: int
    extracted_fields: list[ExtractedFieldResult]
    warnings: list[str]


class OCRDebugOptions(AppSchema):
    lang: str = "jpn+eng"
    psm: int = 6
    threshold: int = 160
    contrast: float = 1.8
    resize_scale: float = 2.0


class OCRDebugImageView(AppSchema):
    original_filename: str
    original_preview_url: str
    preprocessed_preview_url: str
    raw_text: str
    lines: list[str]
    candidates: list[ExtractedFieldCandidate]


class OCRDebugResultView(AppSchema):
    job_id: str
    options: OCRDebugOptions
    images: list[OCRDebugImageView]
    unified_result: UnifiedInferenceResult
    generated_articles: list[GeneratedArticleView]
    summary: str


class UploadResultFieldView(AppSchema):
    key: str
    label: str
    value: str


class GeneratedArticleView(AppSchema):
    template_id: str
    template_name: str
    title: str
    body: str


class DummyAnalysisResult(AppSchema):
    job_id: str
    summary: str
    source_image_count: int
    extracted_fields: list[ExtractedFieldResult]


class UploadImageView(AppSchema):
    original_filename: str
    stored_filename: str
    preview_url: str
    content_type: str
    size_kb: str
    dimensions: str


class UnifiedResultView(AppSchema):
    source_image_count: int
    extracted_fields: list[UploadResultFieldView]
    generated_articles: list[GeneratedArticleView]


class UploadResultView(AppSchema):
    job_id: str
    uploaded_at: str
    file_count: int
    summary: str
    source_images: list[UploadImageView]
    unified_result: UnifiedResultView


class UploadProcessOutcome(AppSchema):
    job: UploadJob
    analysis: DummyAnalysisResult
    view: UploadResultView
