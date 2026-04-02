"""解析モード設定の保存と参照を扱うサービス。"""

from __future__ import annotations

import json
from pathlib import Path

from app.core.config import ALLOWED_ANALYZER_MODES
from app.core.exceptions import ConfigPersistenceError, ValidationError
from app.schemas.analyzer import AnalyzerModeConfig
from app.utils.time import utc_now


class AnalyzerModeService:
    """JSON ファイルで解析モードを管理する。"""

    def __init__(self, config_path: Path, *, default_mode: str) -> None:
        self.config_path = config_path
        self.default_mode = default_mode

    def ensure_config_file(self) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        if self.config_path.exists():
            return
        self._write_config(
            AnalyzerModeConfig(analyzer_mode=self.default_mode, updated_at=utc_now())
        )

    def get_mode(self) -> str:
        self.ensure_config_file()
        try:
            raw_data = json.loads(self.config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ConfigPersistenceError("解析モード設定の読み込みに失敗しました") from exc

        config = AnalyzerModeConfig.model_validate(raw_data)
        if config.analyzer_mode not in ALLOWED_ANALYZER_MODES:
            allowed = ", ".join(ALLOWED_ANALYZER_MODES)
            raise ValidationError(f"解析モードが不正です: {allowed}")
        return config.analyzer_mode

    def set_mode(self, analyzer_mode: str) -> AnalyzerModeConfig:
        normalized = analyzer_mode.strip().lower()
        if normalized not in ALLOWED_ANALYZER_MODES:
            allowed = ", ".join(ALLOWED_ANALYZER_MODES)
            raise ValidationError(f"切り替え可能な解析モードは {allowed} です")

        config = AnalyzerModeConfig(analyzer_mode=normalized, updated_at=utc_now())
        self._write_config(config)
        return config

    def _write_config(self, config: AnalyzerModeConfig) -> None:
        try:
            self.config_path.write_text(
                json.dumps(config.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        except OSError as exc:
            raise ConfigPersistenceError("解析モード設定の保存に失敗しました") from exc
