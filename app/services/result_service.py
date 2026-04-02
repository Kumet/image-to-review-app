"""テンプレート向け表示データ整形サービス。"""

from __future__ import annotations

from datetime import UTC

from app.schemas.result import (
    DummyAnalysisResult,
    UploadProcessOutcome,
    UploadResultFieldView,
    UploadResultItemView,
    UploadResultView,
)
from app.schemas.upload import UploadJob


class ResultService:
    """テンプレートで扱いやすい結果データを構築する。"""

    def build_view(self, *, job: UploadJob, analysis: DummyAnalysisResult) -> UploadResultView:
        result_map = {item.filename: item for item in analysis.item_results}
        items = []

        for uploaded in job.files:
            item_result = result_map[uploaded.stored_filename]
            dimensions = (
                f"{uploaded.width} x {uploaded.height}"
                if uploaded.width is not None and uploaded.height is not None
                else "取得不可"
            )
            items.append(
                UploadResultItemView(
                    original_filename=uploaded.original_filename,
                    stored_filename=uploaded.stored_filename,
                    preview_url=f"/static/{uploaded.relative_path}",
                    content_type=uploaded.content_type,
                    size_kb=f"{uploaded.size_bytes / 1024:.1f} KB",
                    dimensions=dimensions,
                    dummy_label=item_result.dummy_label,
                    score=item_result.score,
                    comment=item_result.comment,
                    extracted_fields=[
                        UploadResultFieldView(
                            key=field.key,
                            label=field.label,
                            value=field.value,
                        )
                        for field in item_result.extracted_fields
                    ],
                )
            )

        average_score = round(sum(item.score for item in items) / len(items), 1)
        uploaded_at_text = job.uploaded_at.astimezone(UTC).strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )

        return UploadResultView(
            job_id=job.job_id,
            uploaded_at=uploaded_at_text,
            file_count=job.file_count,
            summary=analysis.summary,
            average_score=average_score,
            items=items,
        )

    def build_outcome(
        self,
        *,
        job: UploadJob,
        analysis: DummyAnalysisResult,
    ) -> UploadProcessOutcome:
        """ジョブ、解析、表示データをまとめる。"""

        return UploadProcessOutcome(
            job=job,
            analysis=analysis,
            view=self.build_view(job=job, analysis=analysis),
        )
