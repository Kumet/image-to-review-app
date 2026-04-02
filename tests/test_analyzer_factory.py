from __future__ import annotations

from pathlib import Path

from app.core.config import Settings
from app.services.analyzer_factory import AnalyzerFactory
from app.services.dummy_analyzer import DummyAnalyzer
from app.services.extraction_field_service import ExtractionFieldService
from app.services.product_analyzer import ProductAnalyzer


def build_settings(tmp_path: Path, analyzer_mode: str) -> Settings:
    return Settings(
        app_name="photo-upload-app-test",
        app_env="test",
        debug=True,
        upload_dir=str(tmp_path / "uploads"),
        extraction_config_path=str(tmp_path / "config" / "extraction_fields.json"),
        article_template_config_path=str(tmp_path / "config" / "article_templates.json"),
        analyzer_mode=analyzer_mode,
    )


def test_analyzer_factory_creates_dummy_analyzer(tmp_path: Path) -> None:
    settings = build_settings(tmp_path, "dummy")
    field_service = ExtractionFieldService(tmp_path / "config" / "extraction_fields.json")
    factory = AnalyzerFactory()

    analyzer = factory.create(settings=settings, field_service=field_service)

    assert isinstance(analyzer, DummyAnalyzer)


def test_analyzer_factory_creates_ocr_analyzer(tmp_path: Path) -> None:
    settings = build_settings(tmp_path, "ocr")
    field_service = ExtractionFieldService(tmp_path / "config" / "extraction_fields.json")
    factory = AnalyzerFactory()

    analyzer = factory.create(settings=settings, field_service=field_service)

    assert isinstance(analyzer, ProductAnalyzer)
