"""抽出候補を画像横断で統合する。"""

from __future__ import annotations

from collections import defaultdict

from app.schemas.admin import ExtractionFieldConfig
from app.schemas.result import (
    ExtractedFieldCandidate,
    ExtractedFieldResult,
    UnifiedInferenceResult,
)


class FusionService:
    """候補群から項目ごとの最終値を選ぶ。"""

    def unify(
        self,
        *,
        candidates: list[ExtractedFieldCandidate],
        configured_fields: list[ExtractionFieldConfig],
        source_image_count: int,
    ) -> UnifiedInferenceResult:
        grouped: dict[str, list[ExtractedFieldCandidate]] = defaultdict(list)
        for candidate in candidates:
            grouped[candidate.key].append(candidate)

        warnings: list[str] = []
        extracted_fields: list[ExtractedFieldResult] = []

        for field in configured_fields:
            selected = self._select_best_candidate(field.key, grouped.get(field.key, []))
            if selected is None:
                warnings.append(f"{field.label} を抽出できませんでした")
                extracted_fields.append(
                    ExtractedFieldResult(
                        key=field.key,
                        label=field.label,
                        value="未設定",
                        source="ocr",
                        confidence=0.0,
                    )
                )
                continue

            extracted_fields.append(
                ExtractedFieldResult(
                    key=field.key,
                    label=field.label,
                    value=selected.value,
                    source="ocr",
                    confidence=selected.confidence,
                )
            )

        return UnifiedInferenceResult(
            source_image_count=source_image_count,
            extracted_fields=extracted_fields,
            warnings=warnings,
        )

    def _select_best_candidate(
        self,
        key: str,
        candidates: list[ExtractedFieldCandidate],
    ) -> ExtractedFieldCandidate | None:
        if not candidates:
            return None
        frequency_map = self._build_frequency_map(candidates)
        return max(
            candidates,
            key=lambda candidate: (
                candidate.confidence,
                frequency_map.get(self._normalize_value(key, candidate.value), 0),
                self._format_score(key, candidate.value),
            ),
        )

    def _format_score(self, key: str, value: str) -> int:
        if key == "ingredients":
            return value.count("、") + min(len(value), 40)
        if key == "calories":
            return 1 if "kcal" in value.lower() else 0
        if key == "price":
            return 1 if ("円" in value or "¥" in value) else 0
        if key == "product_name":
            return int(20 - abs(len(value) - 12))
        return len(value)

    def _build_frequency_map(
        self,
        candidates: list[ExtractedFieldCandidate],
    ) -> dict[str, int]:
        frequency_map: dict[str, int] = defaultdict(int)
        for candidate in candidates:
            frequency_map[self._normalize_value(candidate.key, candidate.value)] += 1
        return frequency_map

    def _normalize_value(self, key: str, value: str) -> str:
        normalized = value.strip().lower()
        if key in {"price", "calories"}:
            normalized = normalized.replace(" ", "")
        return normalized
