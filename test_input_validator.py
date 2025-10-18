"""
InputValidator クラスのユニットテスト

テスト対象:
- スクリーンショット画像ファイルの存在確認
- メタデータJSONファイル（metadata.json）の読み込みと検証
- 音声文字起こしデータ（transcript.json）の存在確認と読み込み
- 入力データが不正または欠損している場合のエラー処理
"""

import unittest
import tempfile
import shutil
import json
from pathlib import Path
from input_validator import InputValidator


class TestInputValidator(unittest.TestCase):
    """InputValidator クラスのテストケース"""

    def setUp(self):
        """各テストの前に実行される準備処理"""
        # 一時ディレクトリを作成
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.test_dir) / "output"
        self.output_dir.mkdir()
        self.screenshots_dir = self.output_dir / "screenshots"
        self.screenshots_dir.mkdir()

    def tearDown(self):
        """各テストの後に実行されるクリーンアップ処理"""
        # 一時ディレクトリを削除
        shutil.rmtree(self.test_dir)

    def _create_test_metadata(self, screenshots_count: int = 3) -> Path:
        """
        テスト用のメタデータJSONファイルを作成するヘルパーメソッド

        Args:
            screenshots_count: スクリーンショット数

        Returns:
            作成したメタデータファイルのパス
        """
        metadata = []
        for i in range(screenshots_count):
            metadata.append({
                "index": i + 1,
                "timestamp": i * 10.0,
                "filename": f"{i+1:02d}_{i*10:02d}-00_score85.png",
                "score": 85.0,
                "ui_elements": ["Button", "Text"]
            })

        metadata_path = self.output_dir / "metadata.json"
        metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
        return metadata_path

    def _create_test_transcript(self, segments_count: int = 3) -> Path:
        """
        テスト用の音声文字起こしJSONファイルを作成するヘルパーメソッド

        Args:
            segments_count: セグメント数

        Returns:
            作成した文字起こしファイルのパス
        """
        transcript = {
            "segments": [],
            "language": "ja",
            "text": "テスト用音声文字起こし"
        }

        for i in range(segments_count):
            transcript["segments"].append({
                "id": i,
                "start": i * 10.0,
                "end": (i + 1) * 10.0,
                "text": f"セグメント{i+1}のテキスト"
            })

        transcript_path = self.output_dir / "transcript.json"
        transcript_path.write_text(json.dumps(transcript, indent=2, ensure_ascii=False), encoding="utf-8")
        return transcript_path

    def _create_test_screenshot(self, filename: str) -> Path:
        """
        テスト用のスクリーンショット画像ファイルを作成するヘルパーメソッド

        Args:
            filename: ファイル名

        Returns:
            作成した画像ファイルのパス
        """
        from PIL import Image
        image_path = self.screenshots_dir / filename
        image = Image.new("RGB", (800, 600), color=(255, 0, 0))
        image.save(image_path, format="PNG")
        return image_path

    def test_validate_input_data_success_with_audio(self):
        """
        正常な入力データ（音声あり）の検証が成功することを確認する
        """
        # Given: 正常なメタデータ、文字起こし、スクリーンショット画像
        metadata_path = self._create_test_metadata(3)
        transcript_path = self._create_test_transcript(3)

        # スクリーンショット画像を作成
        self._create_test_screenshot("01_00-00_score85.png")
        self._create_test_screenshot("02_10-00_score85.png")
        self._create_test_screenshot("03_20-00_score85.png")

        # When: InputValidatorで検証
        validator = InputValidator(str(self.output_dir))
        result = validator.validate_input_data(
            metadata_path=metadata_path,
            transcript_path=transcript_path
        )

        # Then: 検証成功
        self.assertTrue(result["valid"])
        self.assertEqual(result["screenshots_count"], 3)
        self.assertTrue(result["has_transcript"])
        self.assertEqual(len(result["warnings"]), 0)

    def test_validate_input_data_success_without_audio(self):
        """
        正常な入力データ（音声なし）の検証が成功することを確認する
        """
        # Given: 正常なメタデータとスクリーンショット画像（音声文字起こしなし）
        metadata_path = self._create_test_metadata(2)

        # スクリーンショット画像を作成
        self._create_test_screenshot("01_00-00_score85.png")
        self._create_test_screenshot("02_10-00_score85.png")

        # When: InputValidatorで検証（transcript_pathなし）
        validator = InputValidator(str(self.output_dir))
        result = validator.validate_input_data(
            metadata_path=metadata_path,
            transcript_path=None
        )

        # Then: 検証成功（音声なしでも問題なし）
        self.assertTrue(result["valid"])
        self.assertEqual(result["screenshots_count"], 2)
        self.assertFalse(result["has_transcript"])

    def test_validate_input_data_metadata_not_found(self):
        """
        メタデータJSONファイルが存在しない場合、FileNotFoundErrorが発生することを確認する
        """
        # Given: 存在しないメタデータパス
        non_existent_path = self.output_dir / "non_existent_metadata.json"

        # When/Then: FileNotFoundErrorが発生
        validator = InputValidator(str(self.output_dir))
        with self.assertRaises(FileNotFoundError) as context:
            validator.validate_input_data(metadata_path=non_existent_path)

        # エラーメッセージにファイル名が含まれる
        self.assertIn("metadata", str(context.exception).lower())

    def test_validate_input_data_transcript_not_found(self):
        """
        音声文字起こしJSONファイルが存在しない場合、警告を発して継続することを確認する
        """
        # Given: 正常なメタデータと、存在しない文字起こしパス
        metadata_path = self._create_test_metadata(2)
        self._create_test_screenshot("01_00-00_score85.png")
        self._create_test_screenshot("02_10-00_score85.png")

        non_existent_transcript = self.output_dir / "non_existent_transcript.json"

        # When: InputValidatorで検証
        validator = InputValidator(str(self.output_dir))
        result = validator.validate_input_data(
            metadata_path=metadata_path,
            transcript_path=non_existent_transcript
        )

        # Then: 検証は成功するが、警告が含まれる
        self.assertTrue(result["valid"])
        self.assertFalse(result["has_transcript"])
        self.assertGreater(len(result["warnings"]), 0)
        # 警告メッセージに文字起こしファイルが見つからないことが含まれる
        self.assertTrue(any("transcript" in w.lower() for w in result["warnings"]))

    def test_validate_input_data_empty_metadata(self):
        """
        メタデータが空の場合、ValueErrorが発生することを確認する
        """
        # Given: 空のメタデータJSON
        empty_metadata_path = self.output_dir / "empty_metadata.json"
        empty_metadata_path.write_text("[]", encoding="utf-8")

        # When/Then: ValueErrorが発生
        validator = InputValidator(str(self.output_dir))
        with self.assertRaises(ValueError) as context:
            validator.validate_input_data(metadata_path=empty_metadata_path)

        # エラーメッセージに「空」または「スクリーンショット」が含まれる
        error_message = str(context.exception)
        self.assertTrue("スクリーンショット" in error_message or "空" in error_message)

    def test_validate_input_data_invalid_json_format(self):
        """
        メタデータJSONの形式が不正な場合、ValueErrorが発生することを確認する
        """
        # Given: 不正なJSON形式のメタデータ
        invalid_json_path = self.output_dir / "invalid_metadata.json"
        invalid_json_path.write_text("{ invalid json }", encoding="utf-8")

        # When/Then: ValueErrorまたはJSONDecodeErrorが発生
        validator = InputValidator(str(self.output_dir))
        with self.assertRaises((ValueError, json.JSONDecodeError)):
            validator.validate_input_data(metadata_path=invalid_json_path)

    def test_validate_input_data_missing_screenshot_files(self):
        """
        メタデータに記載されたスクリーンショット画像が存在しない場合、
        警告を発することを確認する
        """
        # Given: メタデータに3個の画像が記載されているが、実際は1個のみ存在
        metadata_path = self._create_test_metadata(3)
        # 1つだけ作成
        self._create_test_screenshot("01_00-00_score85.png")

        # When: InputValidatorで検証
        validator = InputValidator(str(self.output_dir))
        result = validator.validate_input_data(metadata_path=metadata_path)

        # Then: 検証は成功するが、警告が含まれる
        self.assertTrue(result["valid"])
        self.assertGreater(len(result["warnings"]), 0)
        # 警告メッセージに欠落した画像に関する情報が含まれる
        self.assertTrue(any("画像" in w or "見つかりません" in w for w in result["warnings"]))

    def test_load_metadata_success(self):
        """
        メタデータJSONの読み込みが正常に動作することを確認する
        """
        # Given: 正常なメタデータJSON
        metadata_path = self._create_test_metadata(3)

        # When: メタデータを読み込む
        validator = InputValidator(str(self.output_dir))
        metadata = validator.load_metadata(metadata_path)

        # Then: 正しく読み込まれる
        self.assertIsInstance(metadata, list)
        self.assertEqual(len(metadata), 3)
        self.assertEqual(metadata[0]["index"], 1)

    def test_load_transcript_success(self):
        """
        音声文字起こしJSONの読み込みが正常に動作することを確認する
        """
        # Given: 正常な文字起こしJSON
        transcript_path = self._create_test_transcript(3)

        # When: 文字起こしを読み込む
        validator = InputValidator(str(self.output_dir))
        transcript = validator.load_transcript(transcript_path)

        # Then: 正しく読み込まれる
        self.assertIsInstance(transcript, dict)
        self.assertIn("segments", transcript)
        self.assertEqual(len(transcript["segments"]), 3)

    def test_check_screenshot_files_all_exist(self):
        """
        すべてのスクリーンショット画像が存在する場合、
        空の欠落リストが返されることを確認する
        """
        # Given: メタデータとすべての画像ファイル
        metadata = [
            {"filename": "01.png"},
            {"filename": "02.png"}
        ]
        self._create_test_screenshot("01.png")
        self._create_test_screenshot("02.png")

        # When: 画像ファイルの存在を確認
        validator = InputValidator(str(self.output_dir))
        missing_files = validator.check_screenshot_files(metadata)

        # Then: 欠落ファイルなし
        self.assertEqual(len(missing_files), 0)

    def test_check_screenshot_files_some_missing(self):
        """
        一部のスクリーンショット画像が欠落している場合、
        欠落ファイルのリストが返されることを確認する
        """
        # Given: メタデータに3個、実際は2個のみ存在
        metadata = [
            {"filename": "01.png"},
            {"filename": "02.png"},
            {"filename": "03.png"}
        ]
        self._create_test_screenshot("01.png")
        self._create_test_screenshot("02.png")
        # 03.pngは作成しない

        # When: 画像ファイルの存在を確認
        validator = InputValidator(str(self.output_dir))
        missing_files = validator.check_screenshot_files(metadata)

        # Then: 1個の欠落ファイルが検出される
        self.assertEqual(len(missing_files), 1)
        self.assertEqual(missing_files[0], "03.png")


if __name__ == '__main__':
    unittest.main()
