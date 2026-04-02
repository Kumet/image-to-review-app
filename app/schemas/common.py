"""共通 Pydantic モデル。"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class AppSchema(BaseModel):
    """共通設定付き BaseModel。"""

    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)
