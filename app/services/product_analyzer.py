"""ローカル OCR ベースの実推論サービス。"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Protocol

from PIL import Image

from app.core.exceptions import AnalyzeError
from app.schemas.result import (
    DummyAnalysisResult,
    ExtractedFieldCandidate,
    ExtractedFieldResult,
    OCRImageResult,
)
from app.schemas.upload import UploadJob
from app.services.extraction_field_service import ExtractionFieldService
from app.services.field_extractor import FieldExtractor
from app.services.fusion_service import FusionService
from app.services.image_preprocessor import ImagePreprocessor
from app.services.ocr_service import OCRService

logger = logging.getLogger(__name__)


class Preprocessor(Protocol):
    def preprocess(self, image_path: Path) -> Image.Image: ...


class OCRRunner(Protocol):
    def extract_text(self, image: Image.Image, *, image_path: Path) -> OCRImageResult: ...


class CandidateExtractor(Protocol):
    def extract(self, ocr_result: OCRImageResult) -> list[ExtractedFieldCandidate]: ...


class ProductAnalyzer:
    """複数画像をまとめて OCR 解析し、統合結果を返す。"""

    def __init__(
        self,
        field_service: ExtractionFieldService,
        *,
        upload_root: Path,
        preprocessor: Preprocessor | None = None,
        ocr_service: OCRRunner | None = None,
        field_extractor: CandidateExtractor | None = None,
        fusion_service: FusionService | None = None,
    ) -> None:
        self.field_service = field_service
        self.upload_root = upload_root
        self.preprocessor = preprocessor or ImagePreprocessor()
        self.ocr_service = ocr_service or OCRService()
        self.field_extractor = field_extractor or FieldExtractor()
        self.fusion_service = fusion_service or FusionService()

    def analyze(self, job: UploadJob) -> DummyAnalysisResult:
        if not job.files:
            raise AnalyzeError("解析対象の画像がありません")

        logger.info("ocr analyze started: job_id=%s count=%s", job.job_id, job.file_count)
        all_candidates: list[ExtractedFieldCandidate] = []
        warnings: list[str] = []

        for uploaded in job.files:
            image_path = self.upload_root / job.job_id / uploaded.stored_filename
            try:
                ocr_results = self._build_ocr_results(image_path)
                if not any(result.lines for result in ocr_results):
                    warnings.append(
                        f"{uploaded.original_filename} から OCR テキストを取得できませんでした"
                    )
                    continue
                image_candidates = []
                for ocr_result in ocr_results:
                    candidates = self.field_extractor.extract(ocr_result)
                    image_candidates.extend(candidates)
                all_candidates.extend(image_candidates)
                logger.info(
                    "ocr analyze image completed: job_id=%s file=%s candidates=%s",
                    job.job_id,
                    uploaded.original_filename,
                    len(image_candidates),
                )
            except Exception as exc:
                logger.warning(
                    "ocr analyze image failed: job_id=%s file=%s error=%s",
                    job.job_id,
                    uploaded.original_filename,
                    exc,
                )
                warnings.append(f"{uploaded.original_filename} の解析に失敗しました")

        configured_fields = self.field_service.list_enabled_fields()
        unified = self.fusion_service.unify(
            candidates=all_candidates,
            configured_fields=configured_fields,
            source_image_count=job.file_count,
        )
        extracted_fields = self._build_summary_field(unified.extracted_fields)
        summary_text = self._build_job_summary(job.file_count, warnings + unified.warnings)
        logger.info(
            "ocr analyze completed: job_id=%s extracted_fields=%s warnings=%s",
            job.job_id,
            len(extracted_fields),
            len(warnings) + len(unified.warnings),
        )
        return DummyAnalysisResult(
            job_id=job.job_id,
            summary=summary_text,
            source_image_count=unified.source_image_count,
            extracted_fields=extracted_fields,
        )

    def _build_summary_field(
        self, extracted_fields: list[ExtractedFieldResult]
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
        summary_field.confidence = 0.4
        summary_field.source = "generated"
        return extracted_fields

    def _build_job_summary(self, file_count: int, warnings: list[str]) -> str:
        base = (
            f"{file_count} 枚の画像を統合して 1 件の推論結果を作成しました。"
            "ローカル OCR による統合推論結果です。"
        )
        if not warnings:
            return base
        return f"{base} 一部の項目は抽出できず未設定になっています。"

    def _field_value_or_default(
        self,
        field_map: dict[str, ExtractedFieldResult],
        key: str,
    ) -> str:
        field = field_map.get(key)
        return field.value if field is not None else "未設定"

    def _build_ocr_results(self, image_path: Path) -> list[OCRImageResult]:
        try:
            with Image.open(image_path) as original_image:
                region_images = self._build_region_images(original_image)
        except Exception:
            processed_image = self.preprocessor.preprocess(image_path)
            return [self.ocr_service.extract_text(processed_image, image_path=image_path)]

        ocr_results: list[OCRImageResult] = []
        for region_name, region_image in region_images:
            if region_name == "full":
                processed_image = self.preprocessor.preprocess(image_path)
                result_image_path = image_path
            elif hasattr(self.preprocessor, "preprocess_image"):
                processed_image = self.preprocessor.preprocess_image(region_image)
                result_image_path = Path(f"{image_path}#{region_name}")
            else:
                continue
            ocr_results.append(
                self.ocr_service.extract_text(
                    processed_image,
                    image_path=result_image_path,
                )
            )
        return ocr_results

    def _build_region_images(self, image: Image.Image) -> list[tuple[str, Image.Image]]:
        width, height = image.size
        top_crop = image.crop((0, 0, width, max(1, int(height * 0.35))))
        center_crop = image.crop(
            (0, int(height * 0.2), width, max(int(height * 0.8), int(height * 0.2) + 1))
        )
        bottom_crop = image.crop((0, int(height * 0.55), width, height))
        return [
            ("full", image.copy()),
            ("top", top_crop),
            ("center", center_crop),
            ("bottom", bottom_crop),
        ]
