"""OCR テキストから項目候補を抽出する。"""

from __future__ import annotations

import re

from app.schemas.result import ExtractedFieldCandidate, OCRImageResult

PRICE_PATTERNS = (
    re.compile(r"(税込\s*)?([0-9]{2,5})\s*円"),
    re.compile(r"¥\s*([0-9]{2,5})"),
)
CALORIE_PATTERN = re.compile(r"([0-9]{1,4})\s*kcal", re.IGNORECASE)
LABEL_KEYWORDS = ("原材料名", "栄養成分表示", "内容量", "保存方法", "価格", "熱量")
SUMMARY_KEYWORDS = ("こだわり", "おすすめ", "風味", "食感", "特徴", "仕上げ")
INGREDIENT_LABEL_PATTERN = re.compile(r"原材料[名各]?[：:]?")
STOP_LABEL_PATTERNS = (
    re.compile(r"栄養成分表示"),
    re.compile(r"内容量"),
    re.compile(r"保存方法"),
    re.compile(r"価格"),
    re.compile(r"熱量"),
)
NUMERIC_TEXT_NORMALIZATION = str.maketrans(
    {
        "O": "0",
        "o": "0",
        "I": "1",
        "l": "1",
        "ｌ": "1",
        "¥": "¥",
        "，": ",",
        "．": ".",
    }
)


class FieldExtractor:
    """OCR の行データから抽出候補を構築する。"""

    def extract(self, ocr_result: OCRImageResult) -> list[ExtractedFieldCandidate]:
        candidates = []
        candidates.extend(self._extract_price_candidates(ocr_result))
        candidates.extend(self._extract_calorie_candidates(ocr_result))
        candidates.extend(self._extract_ingredients_candidate(ocr_result))
        candidates.extend(self._extract_product_name_candidate(ocr_result))

        summary_candidate = self._extract_summary_candidate(ocr_result)
        if summary_candidate is not None:
            candidates.append(summary_candidate)

        return candidates

    def _extract_price_candidates(
        self, ocr_result: OCRImageResult
    ) -> list[ExtractedFieldCandidate]:
        candidates: list[ExtractedFieldCandidate] = []
        for line in ocr_result.lines:
            normalized_line = self._normalize_numeric_text(line)
            for pattern in PRICE_PATTERNS:
                match = pattern.search(normalized_line)
                if not match:
                    continue
                price_text = match.group(0).replace("  ", " ").strip()
                if "円" not in price_text:
                    price_text = f"¥{match.group(1)}"
                candidates.append(
                    ExtractedFieldCandidate(
                        key="price",
                        value=price_text,
                        confidence=0.95 if "円" in price_text else 0.9,
                        image_id=ocr_result.image_path,
                        source_text=line,
                    )
                )
        return candidates

    def _extract_calorie_candidates(
        self, ocr_result: OCRImageResult
    ) -> list[ExtractedFieldCandidate]:
        candidates: list[ExtractedFieldCandidate] = []
        for line in ocr_result.lines:
            normalized_line = self._normalize_calorie_text(line)
            match = CALORIE_PATTERN.search(normalized_line)
            if not match:
                continue
            candidates.append(
                ExtractedFieldCandidate(
                    key="calories",
                    value=f"{match.group(1)} kcal",
                    confidence=0.95,
                    image_id=ocr_result.image_path,
                    source_text=line,
                )
            )
        return candidates

    def _extract_ingredients_candidate(
        self, ocr_result: OCRImageResult
    ) -> list[ExtractedFieldCandidate]:
        candidates: list[ExtractedFieldCandidate] = []
        for index, line in enumerate(ocr_result.lines):
            normalized_line = self._normalize_label_text(line)
            if not INGREDIENT_LABEL_PATTERN.search(normalized_line):
                continue
            merged_lines = [line]
            for next_line in ocr_result.lines[index + 1 : index + 4]:
                normalized_next = self._normalize_label_text(next_line)
                if any(pattern.search(normalized_next) for pattern in STOP_LABEL_PATTERNS):
                    break
                if self._looks_like_price_or_calorie(next_line):
                    break
                merged_lines.append(next_line)

            merged = " ".join(merged_lines)
            value = INGREDIENT_LABEL_PATTERN.sub("", merged, count=1).strip(" :：")
            if not value:
                continue
            candidates.append(
                ExtractedFieldCandidate(
                    key="ingredients",
                    value=value,
                    confidence=0.97 if len(merged_lines) > 1 else 0.94,
                    image_id=ocr_result.image_path,
                    source_text=merged,
                )
            )
        return self._dedupe_candidates(candidates)

    def _extract_product_name_candidate(
        self, ocr_result: OCRImageResult
    ) -> list[ExtractedFieldCandidate]:
        scored_candidates: list[tuple[float, str]] = []
        for index, line in enumerate(ocr_result.lines[:8]):
            normalized = line.strip()
            if self._is_product_name_line(normalized):
                score = self._product_name_score(normalized, index)
                scored_candidates.append((score, normalized))

        sorted_candidates = sorted(scored_candidates, key=lambda item: item[0], reverse=True)
        return [
            ExtractedFieldCandidate(
                key="product_name",
                value=value,
                confidence=score,
                image_id=ocr_result.image_path,
                source_text=value,
            )
            for score, value in sorted_candidates[:3]
        ]

    def _extract_summary_candidate(
        self, ocr_result: OCRImageResult
    ) -> ExtractedFieldCandidate | None:
        for line in ocr_result.lines:
            normalized = line.strip()
            if len(normalized) < 12:
                continue
            if any(keyword in normalized for keyword in SUMMARY_KEYWORDS):
                return ExtractedFieldCandidate(
                    key="summary",
                    value=normalized,
                    confidence=0.65,
                    image_id=ocr_result.image_path,
                    source_text=line,
                )
        return None

    def _is_product_name_line(self, line: str) -> bool:
        if len(line) < 3 or len(line) > 40:
            return False
        if any(keyword in line for keyword in LABEL_KEYWORDS):
            return False
        if self._looks_like_price_or_calorie(line):
            return False
        if re.fullmatch(r"[0-9\s¥円kcal,.%-]+", line, re.IGNORECASE):
            return False
        if sum(character.isalnum() for character in line) < 2:
            return False
        return True

    def _product_name_score(self, line: str, index: int) -> float:
        score = 0.5
        if 5 <= len(line) <= 24:
            score += 0.15
        if any(
            "\u3040" <= character <= "\u30ff" or "\u4e00" <= character <= "\u9fff"
            for character in line
        ):
            score += 0.15
        if index == 0:
            score += 0.2
        elif index <= 2:
            score += 0.12
        if re.search(r"[!！【】\[\]]", line) is None:
            score += 0.05
        if any(keyword in line for keyword in SUMMARY_KEYWORDS):
            score -= 0.2
        return min(score, 0.95)

    def _normalize_numeric_text(self, line: str) -> str:
        return line.translate(NUMERIC_TEXT_NORMALIZATION)

    def _normalize_label_text(self, line: str) -> str:
        normalized = line.replace(" ", "").replace("\u3000", "")
        return normalized.replace("材科", "材料").replace("原科", "原料")

    def _looks_like_price_or_calorie(self, line: str) -> bool:
        normalized = self._normalize_numeric_text(line)
        normalized = self._normalize_calorie_text(normalized)
        return bool(any(pattern.search(normalized) for pattern in PRICE_PATTERNS)) or bool(
            CALORIE_PATTERN.search(normalized)
        )

    def _normalize_calorie_text(self, line: str) -> str:
        normalized = self._normalize_numeric_text(line)
        return normalized.replace("kcaI", "kcal").replace("kca1", "kcal").replace("Kca1", "kcal")

    def _dedupe_candidates(
        self,
        candidates: list[ExtractedFieldCandidate],
    ) -> list[ExtractedFieldCandidate]:
        unique: dict[str, ExtractedFieldCandidate] = {}
        for candidate in candidates:
            existing = unique.get(candidate.value)
            if existing is None or candidate.confidence > existing.confidence:
                unique[candidate.value] = candidate
        return list(unique.values())
