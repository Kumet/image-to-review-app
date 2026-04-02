"""設定値に応じて analyzer を構築する。"""

from __future__ import annotations

from app.core.config import Settings
from app.services.analyzer import Analyzer
from app.services.dummy_analyzer import DummyAnalyzer
from app.services.extraction_field_service import ExtractionFieldService
from app.services.product_analyzer import ProductAnalyzer


class AnalyzerFactory:
    """analyzer mode から実装を選ぶ。"""

    def create(
        self,
        *,
        settings: Settings,
        field_service: ExtractionFieldService,
        analyzer_mode: str | None = None,
    ) -> Analyzer:
        resolved_mode = analyzer_mode or settings.analyzer_mode
        if resolved_mode == "dummy":
            return DummyAnalyzer(field_service)
        if resolved_mode == "ocr":
            return ProductAnalyzer(
                field_service,
                upload_root=settings.upload_dir_path,
            )
        if resolved_mode in {"ai", "hybrid"}:
            raise NotImplementedError(
                f"analyzer_mode={resolved_mode} は未実装です"
            )
        raise ValueError(f"Unknown analyzer_mode: {resolved_mode}")
