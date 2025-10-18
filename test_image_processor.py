"""
ImageProcessor クラスのユニットテスト

テスト対象:
- スクリーンショット画像ファイルの読み込み
- 画像のbase64エンコード
- Claude API仕様に準拠したリクエスト形式への変換
- 画像サイズ制限（3.75MB、8000px）の検証
- 最大20枚までの画像制限の検証
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from PIL import Image
import base64
from io import BytesIO
import numpy as np
from image_processor import ImageProcessor


class TestImageProcessor(unittest.TestCase):
    """ImageProcessor クラスのテストケース"""

    def setUp(self):
        """各テストの前に実行される準備処理"""
        # 一時ディレクトリを作成
        self.test_dir = tempfile.mkdtemp()
        self.test_images_dir = Path(self.test_dir) / "screenshots"
        self.test_images_dir.mkdir()

    def tearDown(self):
        """各テストの後に実行されるクリーンアップ処理"""
        # 一時ディレクトリを削除
        shutil.rmtree(self.test_dir)

    def _create_test_image(self, filename: str, size: tuple = (800, 600), format: str = "PNG") -> Path:
        """
        テスト用の画像ファイルを作成するヘルパーメソッド

        Args:
            filename: ファイル名
            size: 画像サイズ (width, height)
            format: 画像形式 (PNG, JPEG, etc.)

        Returns:
            作成した画像ファイルのパス
        """
        image_path = self.test_images_dir / filename
        image = Image.new("RGB", size, color=(255, 0, 0))
        image.save(image_path, format=format)
        return image_path

    def _create_large_image(self, filename: str, size_mb: float) -> Path:
        """
        指定サイズの画像ファイルを作成するヘルパーメソッド

        Args:
            filename: ファイル名
            size_mb: 目標サイズ（MB）

        Returns:
            作成した画像ファイルのパス
        """
        # 非圧縮形式(BMP)を使用して確実に大きなファイルを作成
        # または、十分に大きなランダムデータの画像を作成

        # ランダムデータで圧縮が効きにくい画像を生成
        target_bytes = int(size_mb * 1024 * 1024)
        # RGB画像なので3バイト/ピクセル
        target_pixels = target_bytes // 3
        dimension = int(target_pixels ** 0.5)

        # ランダムな画像データを生成（圧縮が効きにくい）
        random_data = np.random.randint(0, 256, (dimension, dimension, 3), dtype=np.uint8)
        image = Image.fromarray(random_data, mode='RGB')

        image_path = self.test_images_dir / filename
        # PNG形式で保存し、圧縮レベルを最低に設定
        image.save(image_path, format="PNG", compress_level=0)
        return image_path

    def test_prepare_images_base64_success(self):
        """
        正常な画像のbase64エンコードとClaude API形式への変換を確認する
        """
        # Given: 正常なサイズの画像ファイルを作成
        image_path1 = self._create_test_image("test1.png")
        image_path2 = self._create_test_image("test2.png")
        screenshot_paths = [image_path1, image_path2]

        # When: ImageProcessorで画像を処理
        processor = ImageProcessor()
        result = processor.prepare_images_base64(screenshot_paths)

        # Then: Claude API形式のリストが返される
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

        # 各要素の形式を確認
        for item in result:
            self.assertEqual(item["type"], "image")
            self.assertEqual(item["source"]["type"], "base64")
            self.assertIn(item["source"]["media_type"], ["image/png", "image/jpeg"])
            self.assertIsInstance(item["source"]["data"], str)
            # base64文字列であることを確認
            self.assertTrue(len(item["source"]["data"]) > 0)

    def test_prepare_images_base64_file_not_found(self):
        """
        画像ファイルが存在しない場合、FileNotFoundErrorが発生することを確認する
        """
        # Given: 存在しないファイルパス
        non_existent_path = Path(self.test_images_dir) / "non_existent.png"
        screenshot_paths = [non_existent_path]

        # When/Then: FileNotFoundErrorが発生
        processor = ImageProcessor()
        with self.assertRaises(FileNotFoundError) as context:
            processor.prepare_images_base64(screenshot_paths)

        # エラーメッセージにファイル名が含まれる
        self.assertIn("non_existent.png", str(context.exception))

    def test_prepare_images_base64_size_limit_exceeded(self):
        """
        画像サイズが3.75MBを超える場合、ValueErrorが発生することを確認する
        """
        # Given: 3.75MBを超える画像を作成
        large_image_path = self._create_large_image("large.png", 4.0)
        screenshot_paths = [large_image_path]

        # When/Then: ValueErrorが発生
        processor = ImageProcessor()
        with self.assertRaises(ValueError) as context:
            processor.prepare_images_base64(screenshot_paths)

        # エラーメッセージにサイズ制限が含まれる
        error_message = str(context.exception)
        self.assertIn("3.75MB", error_message)

    def test_prepare_images_base64_dimension_limit_exceeded(self):
        """
        画像の幅または高さが8000pxを超える場合、ValueErrorが発生することを確認する
        """
        # Given: 8000pxを超える画像を作成
        image_path = self._create_test_image("huge.png", size=(8500, 6000))
        screenshot_paths = [image_path]

        # When/Then: ValueErrorが発生
        processor = ImageProcessor()
        with self.assertRaises(ValueError) as context:
            processor.prepare_images_base64(screenshot_paths)

        # エラーメッセージに寸法制限が含まれる
        error_message = str(context.exception)
        self.assertIn("8000px", error_message)

    def test_prepare_images_base64_max_count_limit(self):
        """
        画像枚数が20枚を超える場合、ValueErrorが発生することを確認する
        """
        # Given: 21枚の画像を作成
        screenshot_paths = []
        for i in range(21):
            image_path = self._create_test_image(f"image_{i:02d}.png")
            screenshot_paths.append(image_path)

        # When/Then: ValueErrorが発生
        processor = ImageProcessor()
        with self.assertRaises(ValueError) as context:
            processor.prepare_images_base64(screenshot_paths)

        # エラーメッセージに枚数制限が含まれる
        error_message = str(context.exception)
        self.assertIn("20", error_message)

    def test_prepare_images_base64_jpeg_format(self):
        """
        JPEG形式の画像も正しく処理されることを確認する
        """
        # Given: JPEG形式の画像ファイルを作成
        image_path = self._create_test_image("test.jpg", format="JPEG")
        screenshot_paths = [image_path]

        # When: ImageProcessorで画像を処理
        processor = ImageProcessor()
        result = processor.prepare_images_base64(screenshot_paths)

        # Then: JPEG形式として認識される
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["source"]["media_type"], "image/jpeg")

    def test_prepare_images_base64_empty_list(self):
        """
        空のリストが渡された場合、空のリストが返されることを確認する
        """
        # Given: 空のリスト
        screenshot_paths = []

        # When: ImageProcessorで処理
        processor = ImageProcessor()
        result = processor.prepare_images_base64(screenshot_paths)

        # Then: 空のリストが返される
        self.assertEqual(result, [])

    def test_validate_image_size_success(self):
        """
        画像サイズ検証が正常に動作することを確認する（制限内）
        """
        # Given: 正常なサイズの画像
        image_path = self._create_test_image("normal.png", size=(1920, 1080))

        # When: 画像サイズを検証
        processor = ImageProcessor()
        # Then: 例外が発生しない（正常終了）
        try:
            processor.validate_image_size(image_path)
        except Exception as e:
            self.fail(f"検証が失敗しました: {e}")

    def test_get_media_type_png(self):
        """
        PNG画像のメディアタイプが正しく取得されることを確認する
        """
        # Given: PNG画像
        image_path = self._create_test_image("test.png", format="PNG")

        # When: メディアタイプを取得
        processor = ImageProcessor()
        media_type = processor.get_media_type(image_path)

        # Then: image/pngが返される
        self.assertEqual(media_type, "image/png")

    def test_get_media_type_jpeg(self):
        """
        JPEG画像のメディアタイプが正しく取得されることを確認する
        """
        # Given: JPEG画像
        image_path = self._create_test_image("test.jpg", format="JPEG")

        # When: メディアタイプを取得
        processor = ImageProcessor()
        media_type = processor.get_media_type(image_path)

        # Then: image/jpegが返される
        self.assertEqual(media_type, "image/jpeg")


if __name__ == '__main__':
    unittest.main()
