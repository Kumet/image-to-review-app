"""OCR デバッグ表示向けサービス。"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from app.schemas.result import (
    ExtractedFieldResult,
    OCRDebugImageView,
    OCRDebugOptions,
    OCRDebugResultView,
    OCRImageResult,
    UnifiedInferenceResult,
)
from app.schemas.upload import UploadJob
from app.services.article_render_service import ArticleRenderService
from app.services.extraction_field_service import ExtractionFieldService
from app.services.field_extractor import FieldExtractor
from app.services.fusion_service import FusionService
from app.services.image_preprocessor import ImagePreprocessor
from app.services.ocr_service import OCRService


class OCRDebugService:
    """OCR の中間結果を可視化する。"""

    def __init__(
        self,
        *,
        upload_root: Path,
        field_service: ExtractionFieldService,
        article_render_service: ArticleRenderService,
        preprocessor: ImagePreprocessor | None = None,
        field_extractor: FieldExtractor | None = None,
        fusion_service: FusionService | None = None,
    ) -> None:
        self.upload_root = upload_root
        self.field_service = field_service
        self.article_render_service = article_render_service
        self.preprocessor = preprocessor or ImagePreprocessor()
        self.field_extractor = field_extractor or FieldExtractor()
        self.fusion_service = fusion_service or FusionService()

    def run(self, *, job: UploadJob, options: OCRDebugOptions) -> OCRDebugResultView:
        ocr_service = OCRService(
            lang=options.lang,
            config=f"--psm {options.psm}",
        )
        all_candidates = []
        image_views: list[OCRDebugImageView] = []
        warnings: list[str] = []

        for uploaded in job.files:
            image_path = self.upload_root / job.job_id / uploaded.stored_filename
            processed = self.preprocessor.preprocess(
                image_path,
                contrast=options.contrast,
                threshold=options.threshold,
                resize_scale=options.resize_scale,
            )
            processed_name = f"preprocessed-{Path(uploaded.stored_filename).stem}.png"
            processed_path = self.upload_root / job.job_id / processed_name
            processed.save(processed_path, format="PNG")

            full_result = ocr_service.extract_text(processed, image_path=Path(f"{image_path}#full"))
            ocr_results = [full_result, *self._build_roi_results(image_path, ocr_service, options)]
            candidates = []
            for ocr_result in ocr_results:
                candidates.extend(self.field_extractor.extract(ocr_result))
            all_candidates.extend(candidates)
            if not any(result.lines for result in ocr_results):
                warnings.append(
                    f"{uploaded.original_filename} から OCR テキストを取得できませんでした"
                )

            image_views.append(
                OCRDebugImageView(
                    original_filename=uploaded.original_filename,
                    original_preview_url=f"/static/{uploaded.relative_path}",
                    preprocessed_preview_url=f"/static/uploads/{job.job_id}/{processed_name}",
                    raw_text=full_result.raw_text or "",
                    lines=full_result.lines,
                    candidates=candidates,
                )
            )

        configured_fields = self.field_service.list_enabled_fields()
        unified_result = self.fusion_service.unify(
            candidates=all_candidates,
            configured_fields=configured_fields,
            source_image_count=job.file_count,
        )
        extracted_fields = self._fill_summary(unified_result.extracted_fields)
        unified_result = UnifiedInferenceResult(
            source_image_count=unified_result.source_image_count,
            extracted_fields=extracted_fields,
            warnings=[*warnings, *unified_result.warnings],
        )

        generated_articles = self.article_render_service.render_articles(
            unified_result.extracted_fields
        )
        return OCRDebugResultView(
            job_id=job.job_id,
            options=options,
            images=image_views,
            unified_result=unified_result,
            generated_articles=generated_articles,
            summary=self._build_summary(job.file_count, unified_result.warnings),
        )

    def _fill_summary(
        self,
        extracted_fields: list[ExtractedFieldResult],
    ) -> list[ExtractedFieldResult]:
        field_map = {field.key: field for field in extracted_fields}
        summary_field = field_map.get("summary")
        if summary_field is None or summary_field.value != "未設定":
            return extracted_fields

        product_name = self._field_value_or_default(field_map, "product_name")
        ingredients = self._field_value_or_default(field_map, "ingredients")
        calories = self._field_value_or_default(field_map, "calories")
        price = self._field_value_or_default(field_map, "price")
        summary_field.value = (
            f"{product_name} は {ingredients} を含む商品で、"
            f"{calories}、価格は {price} です。"
        )
        summary_field.source = "generated"
        summary_field.confidence = 0.4
        return extracted_fields

    def _field_value_or_default(
        self,
        field_map: dict[str, ExtractedFieldResult],
        key: str,
    ) -> str:
        field = field_map.get(key)
        return field.value if field is not None else "未設定"

    def _build_summary(self, file_count: int, warnings: list[str]) -> str:
        base = (
            f"{file_count} 枚の画像を対象に OCR テストを実行しました。"
            "前処理、OCR、生テキスト、抽出候補、統合結果を確認できます。"
        )
        if not warnings:
            return base
        return f"{base} 一部の画像または項目は抽出できず未設定になっています。"

    def _build_roi_results(
        self,
        image_path: Path,
        ocr_service: OCRService,
        options: OCRDebugOptions,
    ) -> list[OCRImageResult]:
        with Image.open(image_path) as original_image:
            width, height = original_image.size
            region_images = [
                ("top", original_image.crop((0, 0, width, max(1, int(height * 0.35))))),
                (
                    "center",
                    original_image.crop(
                        (0, int(height * 0.2), width, max(int(height * 0.8), int(height * 0.2) + 1))
                    ),
                ),
                ("bottom", original_image.crop((0, int(height * 0.55), width, height))),
            ]

        return [
            ocr_service.extract_text(
                self.preprocessor.preprocess_image(
                    region_image,
                    contrast=options.contrast,
                    threshold=options.threshold,
                    resize_scale=options.resize_scale,
                ),
                image_path=Path(f"{image_path}#{region_name}"),
            )
            for region_name, region_image in region_images
        ]
