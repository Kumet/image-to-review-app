"""解析モード設定スキーマ。"""

from __future__ import annotations

from datetime import datetime

from app.schemas.common import AppSchema


class AnalyzerModeConfig(AppSchema):
    analyzer_mode: str
    updated_at: datetime
