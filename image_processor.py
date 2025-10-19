"""
ImageProcessor - 画像データ準備とbase64エンコード機能

スクリーンショット画像ファイルを読み込み、base64形式にエンコードして
Claude API仕様に準拠したリクエスト形式に変換する。
画像サイズ制限（3.75MB、8000px）および最大20枚までの画像制限を検証する。
"""

from typing import List, Dict
from pathlib import Path
from PIL import Image
import base64
from io import BytesIO


class ImageProcessor:
    """
    画像データを準備し、Claude API形式にエンコードするクラス

    Claude API制限:
    - 最大20画像/リクエスト
    - 各画像: 3.75MB以下、8000px以下
    - 対応形式: PNG, JPEG, GIF, WebP
    """

    # Claude API制限定数
    MAX_IMAGE_COUNT = 20
    MAX_FILE_SIZE_MB = 3.75
    MAX_DIMENSION_PX = 8000

    def __init__(self) -> None:
        """ImageProcessorの初期化"""
        pass

    def prepare_images_base64(self, screenshot_paths: List[Path]) -> List[Dict]:
        """
        スクリーンショット画像をbase64エンコードしてClaude APIリクエスト形式に変換

        Args:
            screenshot_paths: 画像ファイルパスのリスト

        Returns:
            [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": "base64文字列"
                    }
                },
                ...
            ]

        Raises:
            FileNotFoundError: 画像ファイルが存在しない場合
            ValueError: 画像が制限超過（3.75MB, 8000px, 20枚）の場合
        """
        # 空のリストの場合はそのまま返す
        if not screenshot_paths:
            return []

        # 画像枚数制限チェック
        if len(screenshot_paths) > self.MAX_IMAGE_COUNT:
            raise ValueError(
                f"画像枚数が制限を超えています。最大{self.MAX_IMAGE_COUNT}枚まで処理できますが、{len(screenshot_paths)}枚が指定されました。"
            )

        result = []
        for image_path in screenshot_paths:
            # ファイル存在チェック
            if not image_path.exists():
                raise FileNotFoundError(
                    f"画像ファイルが見つかりません: {image_path}"
                )

            # 画像サイズ検証（ファイルサイズと寸法）
            self.validate_image_size(image_path)

            # 画像を読み込み、base64エンコード
            with Image.open(image_path) as img:
                # 画像をバッファに保存
                buffer = BytesIO()
                # 元の形式を保持して保存
                img_format = img.format if img.format else "PNG"
                img.save(buffer, format=img_format)
                buffer.seek(0)

                # base64エンコード
                base64_data = base64.b64encode(buffer.read()).decode('utf-8')

                # メディアタイプを取得
                media_type = self.get_media_type(image_path)

                # Claude API形式のオブジェクトを作成
                image_block = {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": base64_data
                    }
                }

                result.append(image_block)

        return result

    def validate_image_size(self, image_path: Path) -> None:
        """
        画像のファイルサイズと寸法を検証

        Args:
            image_path: 検証対象の画像ファイルパス

        Raises:
            ValueError: 画像が制限超過（3.75MB, 8000px）の場合
        """
        # ファイルサイズチェック
        file_size_mb = image_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.MAX_FILE_SIZE_MB:
            raise ValueError(
                f"画像ファイルサイズが制限を超えています。{image_path.name}: {file_size_mb:.2f}MB（最大{self.MAX_FILE_SIZE_MB}MB）"
            )

        # 画像寸法チェック
        with Image.open(image_path) as img:
            width, height = img.size
            if width > self.MAX_DIMENSION_PX or height > self.MAX_DIMENSION_PX:
                raise ValueError(
                    f"画像寸法が制限を超えています。{image_path.name}: {width}x{height}px（最大{self.MAX_DIMENSION_PX}px）"
                )

    def get_media_type(self, image_path: Path) -> str:
        """
        画像ファイルのメディアタイプを取得

        Args:
            image_path: 画像ファイルパス

        Returns:
            メディアタイプ文字列（例: "image/png", "image/jpeg"）
        """
        with Image.open(image_path) as img:
            img_format = img.format

            # 形式に応じてメディアタイプを返す
            format_mapping = {
                "PNG": "image/png",
                "JPEG": "image/jpeg",
                "JPG": "image/jpeg",
                "GIF": "image/gif",
                "WEBP": "image/webp"
            }

            return format_mapping.get(img_format, "image/png")
