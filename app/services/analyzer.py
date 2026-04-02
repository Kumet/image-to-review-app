"""解析サービス共通 interface。"""

from __future__ import annotations

from typing import Protocol

from app.schemas.result import DummyAnalysisResult
from app.schemas.upload import UploadJob


class Analyzer(Protocol):
    """解析器の共通 protocol。"""

    def analyze(self, job: UploadJob) -> DummyAnalysisResult: ...
