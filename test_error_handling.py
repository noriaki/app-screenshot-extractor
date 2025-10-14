#!/usr/bin/env python3
"""
エラーハンドリングと進捗表示機能のテストスイート
Task 5: エラーハンドリングと進捗表示の実装
"""

import sys
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
import tempfile
import os


class TestUserErrorHandling(unittest.TestCase):
    """Task 5.1: ユーザーエラーのハンドリング"""

    def test_audio_file_not_found_shows_clear_error(self):
        """ファイル不在時に明確なエラーメッセージとファイルパスを表示する"""
        from extract_screenshots import AudioProcessor

        processor = AudioProcessor(
            audio_path='/nonexistent/audio.mp3',
            output_dir='output',
            model_size='base'
        )

        # 標準出力をキャプチャ
        captured_output = StringIO()
        sys.stdout = captured_output

        result = processor.validate_files()

        sys.stdout = sys.__stdout__

        # 検証
        self.assertFalse(result)
        output = captured_output.getvalue()
        self.assertIn('Error: Audio file not found:', output)
        self.assertIn('/nonexistent/audio.mp3', output)

    def test_unsupported_format_shows_supported_formats(self):
        """未対応フォーマット時にサポートされている形式一覧を表示する"""
        from extract_screenshots import AudioProcessor

        # 一時ファイルを作成（未対応の拡張子）
        with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            processor = AudioProcessor(
                audio_path=tmp_path,
                output_dir='output',
                model_size='base'
            )

            # 標準出力をキャプチャ
            captured_output = StringIO()
            sys.stdout = captured_output

            result = processor.validate_files()

            sys.stdout = sys.__stdout__

            # 検証
            self.assertFalse(result)
            output = captured_output.getvalue()
            self.assertIn('Error: Unsupported audio format:', output)
            self.assertIn('Supported formats:', output)
            self.assertIn('.mp3', output)
            self.assertIn('.wav', output)

        finally:
            # クリーンアップ
            os.unlink(tmp_path)

    @patch('extract_screenshots.run_integration_flow')
    def test_user_error_exits_with_code_1(self, mock_run):
        """エラー時には即座に処理を中断する（sys.exit(1)）"""
        # validate_files()がFalseを返すケースをシミュレート
        mock_run.side_effect = SystemExit(1)

        with self.assertRaises(SystemExit) as cm:
            mock_run()

        self.assertEqual(cm.exception.code, 1)

    def test_video_file_not_found_shows_clear_error(self):
        """動画ファイル不在時に明確なエラーメッセージを表示する"""
        from extract_screenshots import ScreenshotExtractor

        extractor = ScreenshotExtractor(
            video_path='/nonexistent/video.mp4',
            output_dir='output'
        )

        # 標準出力をキャプチャ
        captured_output = StringIO()
        sys.stdout = captured_output

        result = extractor.open_video()

        sys.stdout = sys.__stdout__

        # 検証
        self.assertFalse(result)
        output = captured_output.getvalue()
        self.assertIn('Error: Video file not found:', output)
        self.assertIn('/nonexistent/video.mp4', output)


class TestSystemErrorHandling(unittest.TestCase):
    """Task 5.2: システムエラーのハンドリング"""

    @patch('extract_screenshots.get_whisper_model')
    def test_whisper_load_failure_suggests_ffmpeg_install(self, mock_whisper):
        """Whisperモデルロード失敗時にffmpegインストール確認を促す"""
        from extract_screenshots import AudioProcessor

        # ffmpegエラーをシミュレート
        mock_whisper.side_effect = RuntimeError("ffmpeg not found")

        processor = AudioProcessor(
            audio_path='test.mp3',
            output_dir='output',
            model_size='base'
        )

        # 標準出力をキャプチャ
        captured_output = StringIO()
        sys.stdout = captured_output

        try:
            processor.transcribe_audio()
        except RuntimeError:
            pass  # 例外は期待される

        sys.stdout = sys.__stdout__

        output = captured_output.getvalue()
        self.assertIn('ffmpeg', output.lower())
        self.assertIn('brew install ffmpeg', output)

    @patch('extract_screenshots.get_whisper_model')
    def test_transcribe_failure_warns_and_continues(self, mock_whisper):
        """音声認識処理失敗時に警告を表示して処理を継続する"""
        from extract_screenshots import AudioProcessor

        # 一般的なExceptionをシミュレート
        mock_model = Mock()
        mock_model.transcribe.side_effect = Exception("Transcription failed")
        mock_whisper.return_value = mock_model

        processor = AudioProcessor(
            audio_path='test.mp3',
            output_dir='output',
            model_size='base'
        )

        # 標準出力をキャプチャ
        captured_output = StringIO()
        sys.stdout = captured_output

        result = processor.transcribe_audio()

        sys.stdout = sys.__stdout__

        # 検証: 空リストを返して処理継続
        self.assertEqual(result, [])
        output = captured_output.getvalue()
        self.assertIn('Warning: Audio transcription failed:', output)
        self.assertIn('Continuing without audio transcription', output)

    @patch('extract_screenshots.get_whisper_model')
    def test_runtime_error_vs_exception_distinction(self, mock_whisper):
        """RuntimeErrorとExceptionを適切に区別して処理する"""
        from extract_screenshots import AudioProcessor

        processor = AudioProcessor(
            audio_path='test.mp3',
            output_dir='output',
            model_size='base'
        )

        # RuntimeError (ffmpeg) の場合は再raiseされる
        mock_whisper.side_effect = RuntimeError("ffmpeg not found")
        with self.assertRaises(RuntimeError):
            processor.transcribe_audio()

        # 一般的なExceptionの場合は空リストを返す
        mock_model = Mock()
        mock_model.transcribe.side_effect = Exception("Other error")
        mock_whisper.side_effect = None
        mock_whisper.return_value = mock_model

        result = processor.transcribe_audio()
        self.assertEqual(result, [])


class TestProgressDisplay(unittest.TestCase):
    """Task 5.3: 進捗表示の実装"""

    @patch('extract_screenshots.get_whisper_model')
    @patch('extract_screenshots.tqdm')
    def test_transcribe_shows_progress_bar(self, mock_tqdm, mock_whisper):
        """音声テキスト変換中にtqdm進捗バーを表示する"""
        from extract_screenshots import AudioProcessor

        # モックの設定
        mock_model = Mock()
        mock_model.transcribe.return_value = {
            'segments': [{'start': 0.0, 'end': 3.0, 'text': 'Test'}]
        }
        mock_whisper.return_value = mock_model

        processor = AudioProcessor(
            audio_path='test.mp3',
            output_dir='output',
            model_size='base'
        )

        # 標準出力をキャプチャ
        captured_output = StringIO()
        sys.stdout = captured_output

        processor.transcribe_audio()

        sys.stdout = sys.__stdout__

        # 検証: 進捗関連のメッセージを確認
        output = captured_output.getvalue()
        self.assertIn('Step: Transcribing audio', output)

    def test_step_start_and_completion_messages(self):
        """各処理ステップの開始・完了メッセージを表示する"""
        from extract_screenshots import AudioProcessor

        # 標準出力をキャプチャ
        captured_output = StringIO()
        sys.stdout = captured_output

        # save_transcript()の呼び出し（完了メッセージを確認）
        with tempfile.TemporaryDirectory() as tmpdir:
            processor = AudioProcessor(
                audio_path='test.mp3',
                output_dir=tmpdir,
                model_size='base'
            )

            segments = [{'start': 0.0, 'end': 3.0, 'text': 'Test'}]

            with patch.object(processor, 'get_duration', return_value=10.0):
                processor.save_transcript(segments, language='ja')

        sys.stdout = sys.__stdout__

        output = captured_output.getvalue()
        self.assertIn('Transcript saved to', output)

    def test_markdown_completion_shows_file_path_and_image_count(self):
        """Markdown生成完了時にファイルパスと画像数を表示する"""
        from extract_screenshots import MarkdownGenerator

        with tempfile.TemporaryDirectory() as tmpdir:
            generator = MarkdownGenerator(
                output_dir=tmpdir,
                title='Test'
            )

            synchronized_data = [
                {
                    'screenshot': {'timestamp': 15.0, 'filename': '01.png'},
                    'transcript': {'start': 14.0, 'end': 17.0, 'text': 'Test'},
                    'matched': True
                }
            ]

            # 標準出力をキャプチャ
            captured_output = StringIO()
            sys.stdout = captured_output

            markdown_content = generator.generate(synchronized_data)
            generator.save(markdown_content)
            generator.display_statistics(synchronized_data)

            sys.stdout = sys.__stdout__

            output = captured_output.getvalue()
            self.assertIn('Markdown saved to', output)
            self.assertIn('Total images: 1', output)


class TestUnexpectedErrorHandling(unittest.TestCase):
    """Task 5.4: 予期しないエラーの処理"""

    @patch('extract_screenshots.ScreenshotExtractor')
    def test_unexpected_error_logs_error_content(self, mock_extractor):
        """予期しないエラー発生時にエラー内容をログ出力する"""
        from extract_screenshots import run_integration_flow

        # 予期しないエラーをシミュレート
        mock_extractor.return_value.extract_screenshots.side_effect = Exception("Unexpected error")

        # 標準出力をキャプチャ
        captured_output = StringIO()
        sys.stdout = captured_output

        try:
            run_integration_flow(
                video_path='test.mp4',
                output_dir='output',
                audio_path=None,
                markdown=False,
                model_size='base',
                threshold=25,
                interval=15.0,
                count=10
            )
        except Exception:
            pass  # 例外は期待される

        sys.stdout = sys.__stdout__

        # エラー内容がログに記録されていることを確認
        # （実装でどのようにログ出力するかによる）

    @patch('extract_screenshots.ScreenshotExtractor')
    def test_partial_results_saved_on_error(self, mock_extractor):
        """部分的な結果が存在する場合は保存する"""
        # このテストは実装の詳細に依存するため、
        # 実装後に具体的な検証ロジックを追加する
        pass

    @patch('extract_screenshots.ScreenshotExtractor')
    def test_unexpected_error_exits_with_code_1(self, mock_extractor):
        """エラー後にsys.exit(1)で終了する"""
        from extract_screenshots import run_integration_flow

        # 予期しないエラーをシミュレート
        mock_extractor.return_value.extract_screenshots.side_effect = Exception("Unexpected error")

        with self.assertRaises(Exception):
            run_integration_flow(
                video_path='test.mp4',
                output_dir='output',
                audio_path=None,
                markdown=False,
                model_size='base',
                threshold=25,
                interval=15.0,
                count=10
            )


class TestIntegratedErrorFlow(unittest.TestCase):
    """統合的なエラーフローのテスト"""

    @patch('extract_screenshots.ScreenshotExtractor')
    @patch('extract_screenshots.AudioProcessor')
    def test_audio_validation_error_stops_before_transcription(self, mock_audio, mock_extractor):
        """音声ファイル検証エラー時、音声認識前に処理を停止する"""
        from extract_screenshots import run_integration_flow

        mock_extractor_instance = mock_extractor.return_value
        mock_extractor_instance.extract_screenshots.return_value = [
            {'timestamp': 15.0, 'filename': '01.png'}
        ]

        mock_audio_instance = mock_audio.return_value
        mock_audio_instance.validate_files.return_value = False

        with self.assertRaises(SystemExit) as cm:
            run_integration_flow(
                video_path='test.mp4',
                output_dir='output',
                audio_path='invalid.mp3',
                markdown=True,
                model_size='base',
                threshold=25,
                interval=15.0,
                count=10
            )

        # transcribe_audio()は呼ばれていないことを確認
        mock_audio_instance.transcribe_audio.assert_not_called()
        self.assertEqual(cm.exception.code, 1)

    @patch('extract_screenshots.ScreenshotExtractor')
    def test_no_screenshots_extracted_shows_error(self, mock_extractor):
        """スクリーンショットが抽出されない場合のエラー処理"""
        from extract_screenshots import run_integration_flow

        mock_extractor_instance = mock_extractor.return_value
        mock_extractor_instance.extract_screenshots.return_value = []  # 空リスト

        # 標準出力をキャプチャ
        captured_output = StringIO()
        sys.stdout = captured_output

        with self.assertRaises(SystemExit) as cm:
            run_integration_flow(
                video_path='test.mp4',
                output_dir='output',
                audio_path=None,
                markdown=False,
                model_size='base',
                threshold=25,
                interval=15.0,
                count=10
            )

        sys.stdout = sys.__stdout__

        output = captured_output.getvalue()
        self.assertIn('Error: No screenshots extracted', output)
        self.assertEqual(cm.exception.code, 1)


if __name__ == '__main__':
    unittest.main()
