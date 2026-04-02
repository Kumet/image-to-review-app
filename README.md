# image-to-review-app

FastAPI + HTMX で構成した複数画像アップロードアプリです。画像を複数選択して送信すると、
サーバー側でローカル保存とダミー解析を行い、HTML partial を返して結果領域だけを更新します。

## セットアップ

```bash
uv sync --extra dev
```

## 開発サーバー起動

```bash
uv run uvicorn app.main:app --reload
```

## テスト

```bash
uv run pytest
```

## 主な構成

- `app/main.py`: FastAPI アプリ生成、static mount、例外ハンドラ登録
- `app/routes/`: ページ表示、アップロード、ヘルスチェック
- `app/services/`: 保存、ダミー解析、表示整形、アップロード統合処理
- `app/templates/`: Jinja2 テンプレートと partial
- `tests/`: ルート・サービスの基本テスト
