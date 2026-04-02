from __future__ import annotations

from app.schemas.result import OCRImageResult
from app.services.field_extractor import FieldExtractor


def test_field_extractor_extracts_expected_candidates() -> None:
    extractor = FieldExtractor()
    ocr_result = OCRImageResult(
        image_path="uploads/job-1/sample.png",
        raw_text=(
            "濃厚チーズせんべい\n"
            "原材料名: チーズ、でん粉、食塩\n"
            "熱量 245kcal\n"
            "税込 198円\n"
            "チーズのコクと食感が特徴です\n"
        ),
        lines=[
            "濃厚チーズせんべい",
            "原材料名: チーズ、でん粉、食塩",
            "熱量 245kcal",
            "税込 198円",
            "チーズのコクと食感が特徴です",
        ],
    )

    candidates = extractor.extract(ocr_result)
    best_candidates = {
        key: max(
            [candidate for candidate in candidates if candidate.key == key],
            key=lambda candidate: candidate.confidence,
        )
        for key in {"product_name", "ingredients", "calories", "price", "summary"}
    }

    assert best_candidates["product_name"].value == "濃厚チーズせんべい"
    assert best_candidates["ingredients"].value == "チーズ、でん粉、食塩"
    assert best_candidates["calories"].value == "245 kcal"
    assert best_candidates["price"].value == "税込 198円"
    assert best_candidates["summary"].value == "チーズのコクと食感が特徴です"
