#!/usr/bin/env python3
"""
E2Eテスト (End-to-End Integration Tests)
Task 6.4: 統合テスト（E2E）の実装

このテストスイートは、CLIから実行される完全なフローをテストする。
実際のファイルI/Oと処理パイプライン全体を検証する。
"""

import unittest
import tempfile
import shutil
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import os


class TestE2EBasicFlowWithAudio(unittest.TestCase):
    """Task 6.4: 基本フロー（音声あり）のテスト"""

    def setUp(self):
        """テストごとの初期化"""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.temp_dir) / "output"
        self.output_dir.mkdir(exist_ok=True)

    def tearDown(self):
        """テストごとのクリーンアップ"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('extract_screenshots.ScreenshotExtractor')
    @patch('extract_screenshots.get_whisper_model')
    def test_e2e_audio_and_markdown_flow(self, mock_whisper, mock_extractor):
        """
        End-to-Endテスト: 動画 + 音声 → スクリーンショット + 音声認識 → Markdown生成

        検証項目:
        - output/screenshots/ に画像が生成される
        - output/transcript.json が生成される
        - output/article.md が生成される
        - article.mdの内容が正しい
        """
        # モックの設定
        mock_extractor_instance = mock_extractor.return_value
        mock_extractor_instance.open_video.return_value = True
        mock_extractor_instance.video_duration = 120.0
        mock_extractor_instance.extract_screenshots.return_value = [
            {
                'index': 1,
                'filename': '01_00-15_score87.png',
                'timestamp': 15.0,
                'score': 87.0,
                'transition_magnitude': 42,
                'stability_score': 95.3,
                'ui_importance_score': 65.0,
                'ui_elements': [],
                'detected_texts': []
            },
            {
                'index': 2,
                'filename': '02_00-30_score92.png',
                'timestamp': 30.0,
                'score': 92.0,
                'transition_magnitude': 38,
                'stability_score': 93.5,
                'ui_importance_score': 70.0,
                'ui_elements': [],
                'detected_texts': []
            }
        ]

        # Whisperモデルのモック
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            'text': 'これはテスト音声です。',
            'segments': [
                {'start': 13.0, 'end': 17.0, 'text': 'ログイン画面が表示されます'},
                {'start': 28.0, 'end': 32.0, 'text': 'ホーム画面に遷移します'}
            ]
        }
        mock_whisper.return_value = mock_model

        # 音声ファイルのダミーを作成
        audio_path = Path(self.temp_dir) / "test_audio.mp3"
        audio_path.write_text("dummy audio content")

        # テスト実行
        from extract_screenshots import run_integration_flow

        with patch('subprocess.run') as mock_subprocess:
            # ffprobeのモック（音声長取得）
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "120.0"
            mock_subprocess.return_value = mock_result

            run_integration_flow(
                video_path='test.mp4',
                output_dir=str(self.output_dir),
                audio_path=str(audio_path),
                markdown=True,
                model_size='base',
                threshold=25,
                interval=15.0,
                count=10
            )

        # 検証1: transcript.jsonが生成される
        transcript_path = self.output_dir / "transcript.json"
        self.assertTrue(transcript_path.exists(), "transcript.jsonが生成されていません")

        with open(transcript_path, 'r', encoding='utf-8') as f:
            transcript_data = json.load(f)

        self.assertIn('language', transcript_data)
        self.assertIn('duration', transcript_data)
        self.assertIn('segments', transcript_data)
        self.assertEqual(transcript_data['language'], 'ja')
        self.assertEqual(len(transcript_data['segments']), 2)

        # 検証2: article.mdが生成される
        article_path = self.output_dir / "article.md"
        self.assertTrue(article_path.exists(), "article.mdが生成されていません")

        with open(article_path, 'r', encoding='utf-8') as f:
            article_content = f.read()

        # 検証3: article.mdの内容が正しい
        self.assertIn("# アプリ紹介", article_content)
        self.assertIn("## 00:15", article_content)
        self.assertIn("## 00:30", article_content)
        self.assertIn("![Screenshot](screenshots/01_00-15_score87.png)", article_content)
        self.assertIn("![Screenshot](screenshots/02_00-30_score92.png)", article_content)
        self.assertIn("ログイン画面が表示されます", article_content)
        self.assertIn("ホーム画面に遷移します", article_content)


class TestE2EBasicFlowWithoutAudio(unittest.TestCase):
    """Task 6.4: 基本フロー（音声なし）のテスト"""

    def setUp(self):
        """テストごとの初期化"""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.temp_dir) / "output"
        self.output_dir.mkdir(exist_ok=True)

    def tearDown(self):
        """テストごとのクリーンアップ"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('extract_screenshots.ScreenshotExtractor')
    def test_e2e_markdown_without_audio(self, mock_extractor):
        """
        End-to-Endテスト: 動画のみ → スクリーンショット → Markdown生成（音声なし）

        検証項目:
        - output/article.md が生成される
        - 全セクションに "(説明文なし)"
        - transcript.json は生成されない
        """
        # モックの設定
        mock_extractor_instance = mock_extractor.return_value
        mock_extractor_instance.open_video.return_value = True
        mock_extractor_instance.extract_screenshots.return_value = [
            {
                'index': 1,
                'filename': '01_00-15_score87.png',
                'timestamp': 15.0,
                'score': 87.0,
                'transition_magnitude': 42,
                'stability_score': 95.3,
                'ui_importance_score': 65.0,
                'ui_elements': [],
                'detected_texts': []
            }
        ]

        # テスト実行
        from extract_screenshots import run_integration_flow

        run_integration_flow(
            video_path='test.mp4',
            output_dir=str(self.output_dir),
            audio_path=None,
            markdown=True,
            model_size='base',
            threshold=25,
            interval=15.0,
            count=10
        )

        # 検証1: article.mdが生成される
        article_path = self.output_dir / "article.md"
        self.assertTrue(article_path.exists(), "article.mdが生成されていません")

        with open(article_path, 'r', encoding='utf-8') as f:
            article_content = f.read()

        # 検証2: プレースホルダーが含まれる
        self.assertIn("(説明文なし)", article_content)

        # 検証3: transcript.jsonは生成されない
        transcript_path = self.output_dir / "transcript.json"
        self.assertFalse(transcript_path.exists(), "transcript.jsonが不要に生成されています")


class TestE2EAudioOnlyWithoutMarkdown(unittest.TestCase):
    """Task 6.4: 音声のみ（Markdownなし）のテスト"""

    def setUp(self):
        """テストごとの初期化"""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.temp_dir) / "output"
        self.output_dir.mkdir(exist_ok=True)

    def tearDown(self):
        """テストごとのクリーンアップ"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('extract_screenshots.ScreenshotExtractor')
    @patch('extract_screenshots.get_whisper_model')
    def test_e2e_audio_only_no_markdown(self, mock_whisper, mock_extractor):
        """
        End-to-Endテスト: 動画 + 音声 → スクリーンショット + 音声認識（Markdownなし）

        検証項目:
        - output/transcript.json のみ生成される
        - article.md は生成されない
        """
        # モックの設定
        mock_extractor_instance = mock_extractor.return_value
        mock_extractor_instance.open_video.return_value = True
        mock_extractor_instance.video_duration = 120.0
        mock_extractor_instance.extract_screenshots.return_value = [
            {
                'index': 1,
                'filename': '01_00-15_score87.png',
                'timestamp': 15.0,
                'score': 87.0,
                'transition_magnitude': 42,
                'stability_score': 95.3,
                'ui_importance_score': 65.0,
                'ui_elements': [],
                'detected_texts': []
            }
        ]

        # Whisperモデルのモック
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            'text': 'これはテスト音声です。',
            'segments': [
                {'start': 13.0, 'end': 17.0, 'text': 'テスト音声'}
            ]
        }
        mock_whisper.return_value = mock_model

        # 音声ファイルのダミーを作成
        audio_path = Path(self.temp_dir) / "test_audio.mp3"
        audio_path.write_text("dummy audio content")

        # テスト実行
        from extract_screenshots import run_integration_flow

        with patch('subprocess.run') as mock_subprocess:
            # ffprobeのモック
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "120.0"
            mock_subprocess.return_value = mock_result

            run_integration_flow(
                video_path='test.mp4',
                output_dir=str(self.output_dir),
                audio_path=str(audio_path),
                markdown=False,  # Markdownなし
                model_size='base',
                threshold=25,
                interval=15.0,
                count=10
            )

        # 検証1: transcript.jsonが生成される
        transcript_path = self.output_dir / "transcript.json"
        self.assertTrue(transcript_path.exists(), "transcript.jsonが生成されていません")

        # 検証2: article.mdは生成されない
        article_path = self.output_dir / "article.md"
        self.assertFalse(article_path.exists(), "article.mdが不要に生成されています")


class TestE2EFileNotFoundError(unittest.TestCase):
    """Task 6.4: ファイル不在エラーのテスト"""

    def setUp(self):
        """テストごとの初期化"""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.temp_dir) / "output"
        self.output_dir.mkdir(exist_ok=True)

    def tearDown(self):
        """テストごとのクリーンアップ"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('extract_screenshots.ScreenshotExtractor')
    def test_e2e_audio_file_not_found(self, mock_extractor):
        """
        End-to-Endテスト: 音声ファイル不在エラー

        検証項目:
        - エラーメッセージが表示される
        - 処理が中断される（exit 1）
        """
        # モックの設定
        mock_extractor_instance = mock_extractor.return_value
        mock_extractor_instance.open_video.return_value = True
        mock_extractor_instance.extract_screenshots.return_value = [
            {
                'index': 1,
                'filename': '01_00-15_score87.png',
                'timestamp': 15.0,
                'score': 87.0,
                'transition_magnitude': 42,
                'stability_score': 95.3,
                'ui_importance_score': 65.0,
                'ui_elements': [],
                'detected_texts': []
            }
        ]

        # テスト実行
        from extract_screenshots import run_integration_flow

        with self.assertRaises(SystemExit) as cm:
            run_integration_flow(
                video_path='test.mp4',
                output_dir=str(self.output_dir),
                audio_path='/nonexistent/audio.mp3',  # 存在しないファイル
                markdown=True,
                model_size='base',
                threshold=25,
                interval=15.0,
                count=10
            )

        # exit code 1で終了することを確認
        self.assertEqual(cm.exception.code, 1)


class TestE2EDurationMismatchWarning(unittest.TestCase):
    """Task 6.4: 動画・音声長さ不一致のテスト"""

    def setUp(self):
        """テストごとの初期化"""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.temp_dir) / "output"
        self.output_dir.mkdir(exist_ok=True)

    def tearDown(self):
        """テストごとのクリーンアップ"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('extract_screenshots.ScreenshotExtractor')
    @patch('extract_screenshots.get_whisper_model')
    def test_e2e_duration_mismatch_warning_and_continue(self, mock_whisper, mock_extractor):
        """
        End-to-Endテスト: 動画・音声長さ不一致

        検証項目:
        - 警告メッセージが表示される
        - 処理は継続される
        - article.md が生成される
        """
        # モックの設定
        mock_extractor_instance = mock_extractor.return_value
        mock_extractor_instance.open_video.return_value = True
        mock_extractor_instance.video_duration = 120.0  # 動画120秒
        mock_extractor_instance.extract_screenshots.return_value = [
            {
                'index': 1,
                'filename': '01_00-15_score87.png',
                'timestamp': 15.0,
                'score': 87.0,
                'transition_magnitude': 42,
                'stability_score': 95.3,
                'ui_importance_score': 65.0,
                'ui_elements': [],
                'detected_texts': []
            }
        ]

        # Whisperモデルのモック
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            'text': 'これはテスト音声です。',
            'segments': [
                {'start': 13.0, 'end': 17.0, 'text': 'テスト'}
            ]
        }
        mock_whisper.return_value = mock_model

        # 音声ファイルのダミーを作成
        audio_path = Path(self.temp_dir) / "test_audio.mp3"
        audio_path.write_text("dummy audio content")

        # テスト実行
        from extract_screenshots import run_integration_flow
        import io
        import sys

        captured_output = io.StringIO()
        old_stdout = sys.stdout

        try:
            sys.stdout = captured_output

            with patch('subprocess.run') as mock_subprocess:
                # ffprobeのモック（音声130秒、動画120秒との差異10秒）
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = "130.0"  # 音声130秒
                mock_subprocess.return_value = mock_result

                run_integration_flow(
                    video_path='test.mp4',
                    output_dir=str(self.output_dir),
                    audio_path=str(audio_path),
                    markdown=True,
                    model_size='base',
                    threshold=25,
                    interval=15.0,
                    count=10
                )

        finally:
            sys.stdout = old_stdout

        output = captured_output.getvalue()

        # 検証1: 警告メッセージが表示される
        self.assertIn("Warning", output)
        self.assertIn("Duration mismatch", output)

        # 検証2: 処理が継続され、article.mdが生成される
        article_path = self.output_dir / "article.md"
        self.assertTrue(article_path.exists(), "article.mdが生成されていません")


if __name__ == '__main__':
    unittest.main()
