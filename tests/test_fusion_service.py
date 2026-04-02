from __future__ import annotations

from datetime import datetime

from app.schemas.admin import ExtractionFieldConfig
from app.schemas.result import ExtractedFieldCandidate
from app.services.fusion_service import FusionService


def test_fusion_service_selects_highest_confidence_candidate() -> None:
    service = FusionService()
    now = datetime.fromisoformat("2026-04-02T00:00:00+00:00")
    configured_fields = [
        ExtractionFieldConfig(
            field_id="field_product_name",
            key="product_name",
            label="商品名",
            field_type="text",
            enabled=True,
            required=True,
            sort_order=1,
            created_at=now,
            updated_at=now,
        ),
        ExtractionFieldConfig(
            field_id="field_price",
            key="price",
            label="値段",
            field_type="currency",
            enabled=True,
            required=False,
            sort_order=2,
            created_at=now,
            updated_at=now,
        ),
    ]

    result = service.unify(
        candidates=[
            ExtractedFieldCandidate(
                key="product_name",
                value="濃厚チーズせんべい",
                confidence=0.7,
                image_id="1",
                source_text="濃厚チーズせんべい",
            ),
            ExtractedFieldCandidate(
                key="price",
                value="198円",
                confidence=0.95,
                image_id="1",
                source_text="198円",
            ),
            ExtractedFieldCandidate(
                key="price",
                value="198",
                confidence=0.95,
                image_id="2",
                source_text="198",
            ),
        ],
        configured_fields=configured_fields,
        source_image_count=2,
    )

    values = {field.key: field.value for field in result.extracted_fields}
    assert result.source_image_count == 2
    assert values["product_name"] == "濃厚チーズせんべい"
    assert values["price"] == "198円"
    assert result.warnings == []
