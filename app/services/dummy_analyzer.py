"""ダミー解析サービス。"""

from __future__ import annotations

import hashlib

from app.core.constants import DUMMY_COMMENTS, DUMMY_LABELS
from app.core.exceptions import AnalyzeError
from app.schemas.admin import ExtractionFieldConfig
from app.schemas.result import (
    DummyAnalysisResult,
    DummyItemResult,
    ExtractedFieldResult,
)
from app.schemas.upload import UploadedImageInfo, UploadJob
from app.services.extraction_field_service import ExtractionFieldService


class DummyAnalyzer:
    """将来の AI 解析差し替えを見据えたダミー実装。"""

    def __init__(self, field_service: ExtractionFieldService) -> None:
        self.field_service = field_service

    def analyze(self, job: UploadJob) -> DummyAnalysisResult:
        """保存済み画像一覧から疑似解析結果を返す。"""

        if not job.files:
            raise AnalyzeError("解析対象の画像がありません")

        configured_fields = self.field_service.list_enabled_fields()
        item_results = [
            self._build_item_result(uploaded, configured_fields) for uploaded in job.files
        ]
        average_score = round(sum(item.score for item in item_results) / len(item_results), 1)
        summary = f"{job.file_count} 件の画像を受理しました。平均スコアは {average_score} 点です。"
        return DummyAnalysisResult(job_id=job.job_id, summary=summary, item_results=item_results)

    def _build_item_result(
        self,
        uploaded: UploadedImageInfo,
        configured_fields: list[ExtractionFieldConfig],
    ) -> DummyItemResult:
        seed = self._score_seed(uploaded)
        score = round(60 + (seed % 401) / 10, 1)
        label = DUMMY_LABELS[seed % len(DUMMY_LABELS)]
        comment = DUMMY_COMMENTS[(seed // 3) % len(DUMMY_COMMENTS)]
        comment = f"{comment} 仮判定ラベルは「{label}」です。"

        return DummyItemResult(
            filename=uploaded.stored_filename,
            dummy_label=label,
            score=score,
            comment=comment,
            extracted_fields=[
                ExtractedFieldResult(
                    key=field.key,
                    label=field.label,
                    value=self._build_field_value(field, uploaded, seed),
                )
                for field in configured_fields
            ],
        )

    def _build_field_value(
        self,
        field: ExtractionFieldConfig,
        uploaded: UploadedImageInfo,
        seed: int,
    ) -> str:
        values = {
            "product_name": f"サンプル商品 {uploaded.original_filename.rsplit('.', 1)[0]}",
            "ingredients": "砂糖、小麦粉、植物油脂、食塩、香料",
            "calories": f"{180 + seed % 120} kcal",
            "price": f"{98 + seed % 500}円",
            "summary": (
                "商品画像から抽出した想定のダミー概要です。"
                "複数画像比較にも対応しやすい構造です。"
            ),
        }
        return values.get(field.key, f"{field.label} のダミー値")

    def _score_seed(self, uploaded: UploadedImageInfo) -> int:
        raw = (
            f"{uploaded.stored_filename}:{uploaded.size_bytes}:"
            f"{uploaded.width}x{uploaded.height}:{uploaded.content_type}"
        )
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return int(digest[:8], 16)
