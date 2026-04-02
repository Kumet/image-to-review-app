"""アプリケーション全体で使う定数。"""

from __future__ import annotations

DEFAULT_ALLOWED_EXTENSIONS: tuple[str, ...] = (".jpg", ".jpeg", ".png", ".webp")
DEFAULT_ALLOWED_CONTENT_TYPES: tuple[str, ...] = (
    "image/jpeg",
    "image/png",
    "image/webp",
)

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

DUMMY_LABELS: tuple[str, ...] = (
    "受理済み",
    "レビュー候補",
    "要確認",
    "サンプル解析",
)

DUMMY_COMMENTS: tuple[str, ...] = (
    "サンプル画像として受理しました。",
    "明るい印象のダミー結果です。",
    "画像サイズに基づく仮スコアを算出しました。",
    "将来の AI 解析へ差し替えやすい構造で返却しています。",
)

DEFAULT_EXTRACTION_FIELDS: tuple[dict[str, object], ...] = (
    {
        "field_id": "field_product_name",
        "key": "product_name",
        "label": "商品名",
        "field_type": "text",
        "enabled": True,
        "required": True,
        "sort_order": 1,
        "placeholder": "商品ラベルに記載された名称",
        "description": "商品パッケージ上の名称を想定した抽出項目です。",
    },
    {
        "field_id": "field_ingredients",
        "key": "ingredients",
        "label": "原材料",
        "field_type": "long_text",
        "enabled": True,
        "required": False,
        "sort_order": 2,
        "placeholder": "原材料一覧",
        "description": "原材料表示欄を想定した抽出項目です。",
    },
    {
        "field_id": "field_calories",
        "key": "calories",
        "label": "カロリー",
        "field_type": "text",
        "enabled": True,
        "required": False,
        "sort_order": 3,
        "placeholder": "例: 245 kcal",
        "description": "栄養成分表示から取得する想定です。",
    },
    {
        "field_id": "field_price",
        "key": "price",
        "label": "値段",
        "field_type": "currency",
        "enabled": True,
        "required": False,
        "sort_order": 4,
        "placeholder": "例: 198円",
        "description": "値札や商品画像に含まれる価格を想定します。",
    },
    {
        "field_id": "field_summary",
        "key": "summary",
        "label": "商品概要",
        "field_type": "long_text",
        "enabled": True,
        "required": False,
        "sort_order": 5,
        "placeholder": "商品特徴の要約",
        "description": "商品画像全体から生成する説明文を想定します。",
    },
)

ALLOWED_FIELD_TYPES: tuple[str, ...] = ("text", "long_text", "number", "currency")

DEFAULT_ARTICLE_TEMPLATES: tuple[dict[str, object], ...] = (
    {
        "template_id": "template_blog_intro",
        "name": "商品紹介ブログ",
        "description": "商品を紹介するシンプルなブログ向けテンプレートです。",
        "title_template": "{product_name} を紹介",
        "body_template": (
            "今回紹介するのは {product_name} です。\n\n"
            "原材料は {ingredients}。\n"
            "カロリーは {calories}、価格は {price} です。\n\n"
            "商品概要:\n{summary}\n\n"
            "気になった方はぜひチェックしてみてください。"
        ),
        "enabled": True,
        "sort_order": 1,
    },
    {
        "template_id": "template_short_review",
        "name": "レビュー風テンプレート",
        "description": "商品特徴を短くまとめるレビュー向けテンプレートです。",
        "title_template": "{product_name} の簡単レビュー",
        "body_template": (
            "{product_name} は {summary}\n"
            "原材料は {ingredients}。\n"
            "カロリーは {calories}、価格は {price} でした。"
        ),
        "enabled": True,
        "sort_order": 2,
    },
)
