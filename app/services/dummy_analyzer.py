"""ダミー解析サービス。"""

from __future__ import annotations

import hashlib

from app.core.exceptions import AnalyzeError
from app.schemas.admin import ExtractionFieldConfig
from app.schemas.result import DummyAnalysisResult, ExtractedFieldResult
from app.schemas.upload import UploadedImageInfo, UploadJob
from app.services.extraction_field_service import ExtractionFieldService


class DummyAnalyzer:
    """将来の AI 解析差し替えを見据えたダミー実装。"""

    def __init__(self, field_service: ExtractionFieldService) -> None:
        self.field_service = field_service

    def analyze(self, job: UploadJob) -> DummyAnalysisResult:
        """保存済み画像群をまとめて疑似解析する。"""

        if not job.files:
            raise AnalyzeError("解析対象の画像がありません")

        configured_fields = self.field_service.list_enabled_fields()
        extracted_fields = [
            ExtractedFieldResult(
                key=field.key,
                label=field.label,
                value=self._build_field_value(field, job.files),
            )
            for field in configured_fields
        ]
        summary = (
            f"{job.file_count} 枚の画像を統合して 1 件の推論結果を作成しました。"
            "複数角度・ズーム画像を前提にしたダミー統合推論です。"
        )
        return DummyAnalysisResult(
            job_id=job.job_id,
            summary=summary,
            source_image_count=job.file_count,
            extracted_fields=extracted_fields,
        )

    def _build_field_value(
        self,
        field: ExtractionFieldConfig,
        uploads: list[UploadedImageInfo],
    ) -> str:
        seed = self._job_seed(uploads)
        first_name = uploads[0].original_filename.rsplit(".", 1)[0]
        image_count = len(uploads)
        values = {
            "product_name": f"統合推定商品 {first_name}",
            "ingredients": "砂糖、小麦粉、植物油脂、食塩、香料",
            "calories": f"{180 + seed % 120} kcal",
            "price": f"{98 + seed % 500}円",
            "summary": (
                f"{image_count} 枚の画像を統合し、同一商品の複数角度写真から"
                "情報を補完した想定のダミー概要です。"
            ),
        }
        return values.get(field.key, f"{field.label} のダミー値")

    def _job_seed(self, uploads: list[UploadedImageInfo]) -> int:
        raw = "|".join(
            (
                f"{uploaded.stored_filename}:{uploaded.size_bytes}:"
                f"{uploaded.width}x{uploaded.height}:{uploaded.content_type}"
            )
            for uploaded in uploads
        )
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return int(digest[:8], 16)
