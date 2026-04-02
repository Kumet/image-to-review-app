"""テンプレート向け表示データ整形サービス。"""

from __future__ import annotations

from datetime import UTC

from app.schemas.result import (
    DummyAnalysisResult,
    GeneratedArticleView,
    UnifiedResultView,
    UploadImageView,
    UploadProcessOutcome,
    UploadResultFieldView,
    UploadResultView,
)
from app.schemas.upload import UploadJob
from app.services.article_render_service import ArticleRenderService


class ResultService:
    """テンプレートで扱いやすい結果データを構築する。"""

    def __init__(self, *, article_render_service: ArticleRenderService) -> None:
        self.article_render_service = article_render_service

    def build_view(self, *, job: UploadJob, analysis: DummyAnalysisResult) -> UploadResultView:
        source_images = []

        for uploaded in job.files:
            dimensions = (
                f"{uploaded.width} x {uploaded.height}"
                if uploaded.width is not None and uploaded.height is not None
                else "取得不可"
            )
            source_images.append(
                UploadImageView(
                    original_filename=uploaded.original_filename,
                    stored_filename=uploaded.stored_filename,
                    preview_url=f"/static/{uploaded.relative_path}",
                    content_type=uploaded.content_type,
                    size_kb=f"{uploaded.size_bytes / 1024:.1f} KB",
                    dimensions=dimensions,
                )
            )

        uploaded_at_text = job.uploaded_at.astimezone(UTC).strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )
        unified_generated_articles = self.article_render_service.render_articles(
            analysis.extracted_fields
        )

        return UploadResultView(
            job_id=job.job_id,
            uploaded_at=uploaded_at_text,
            file_count=job.file_count,
            summary=analysis.summary,
            source_images=source_images,
            unified_result=UnifiedResultView(
                source_image_count=analysis.source_image_count,
                extracted_fields=[
                    UploadResultFieldView(
                        key=field.key,
                        label=field.label,
                        value=field.value,
                    )
                    for field in analysis.extracted_fields
                ],
                generated_articles=[
                    GeneratedArticleView(
                        template_id=article.template_id,
                        template_name=article.template_name,
                        title=article.title,
                        body=article.body,
                    )
                    for article in unified_generated_articles
                ],
            ),
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
