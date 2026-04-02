"""アプリケーション独自例外。"""

from __future__ import annotations


class AppError(Exception):
    """ユーザー向けメッセージと HTTP ステータスを持つ基底例外。"""

    default_message = "画像の処理に失敗しました"
    default_status_code = 400

    def __init__(
        self,
        user_message: str | None = None,
        *,
        status_code: int | None = None,
    ) -> None:
        self.user_message = user_message or self.default_message
        self.status_code = status_code or self.default_status_code
        super().__init__(self.user_message)


class ValidationError(AppError):
    default_message = "入力内容を確認してください"


class UnsupportedFileTypeError(AppError):
    default_message = "対応していない画像形式です"


class TooManyFilesError(AppError):
    default_message = "アップロード上限を超えています"


class FileTooLargeError(AppError):
    default_message = "画像サイズが上限を超えています"


class CorruptedImageError(AppError):
    default_message = "画像の処理に失敗しました"


class SaveFileError(AppError):
    default_message = "画像の保存に失敗しました"
    default_status_code = 500


class AnalyzeError(AppError):
    default_message = "画像解析に失敗しました"
    default_status_code = 500


class ConfigPersistenceError(AppError):
    default_message = "設定の保存に失敗しました"
    default_status_code = 500
