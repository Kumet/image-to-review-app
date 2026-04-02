from __future__ import annotations

import pytest

from app.core.config import Settings


def test_settings_accepts_supported_analyzer_mode() -> None:
    settings = Settings(analyzer_mode="dummy")

    assert settings.analyzer_mode == "dummy"


def test_settings_rejects_unsupported_analyzer_mode() -> None:
    with pytest.raises(ValueError):
        Settings(analyzer_mode="unknown-mode")
