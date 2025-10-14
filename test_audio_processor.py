#!/usr/bin/env python3
"""
AudioProcessor のテストスイート
Task 1.1: 音声ファイル検証機能のテスト
"""

import unittest
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestAudioProcessorValidateFiles(unittest.TestCase):
    """AudioProcessor.validate_files() のテスト"""

    def setUp(self):
        """テストごとの初期化"""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = tempfile.mkdtemp()

    def tearDown(self):
        """テストごとのクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        shutil.rmtree(self.output_dir, ignore_errors=True)

    def test_validate_files_with_existing_mp3_file(self):
        """存在するmp3ファイルでTrueを返す"""
        # Given: 存在するmp3ファイル
        audio_path = os.path.join(self.temp_dir, "test_audio.mp3")
        with open(audio_path, 'w') as f:
            f.write("dummy audio content")

        # When: AudioProcessorを初期化してvalidate_filesを実行
        from extract_screenshots import AudioProcessor
        processor = AudioProcessor(audio_path, self.output_dir)
        result = processor.validate_files()

        # Then: Trueを返す
        self.assertTrue(result)

    def test_validate_files_with_nonexistent_file(self):
        """存在しないファイルでFalseを返す"""
        # Given: 存在しないファイルパス
        audio_path = os.path.join(self.temp_dir, "nonexistent.mp3")

        # When: AudioProcessorを初期化してvalidate_filesを実行
        from extract_screenshots import AudioProcessor
        processor = AudioProcessor(audio_path, self.output_dir)
        result = processor.validate_files()

        # Then: Falseを返す
        self.assertFalse(result)

    def test_validate_files_with_supported_formats(self):
        """サポートされている全フォーマットでTrueを返す"""
        # Given: サポートされている各フォーマットのファイル
        supported_formats = ['.mp3', '.wav', '.m4a', '.aac', '.mp4', '.mpeg', '.mpga', '.webm']

        for ext in supported_formats:
            with self.subTest(format=ext):
                audio_path = os.path.join(self.temp_dir, f"test_audio{ext}")
                with open(audio_path, 'w') as f:
                    f.write("dummy content")

                # When: validate_filesを実行
                from extract_screenshots import AudioProcessor
                processor = AudioProcessor(audio_path, self.output_dir)
                result = processor.validate_files()

                # Then: Trueを返す
                self.assertTrue(result, f"{ext} should be supported")

    def test_validate_files_with_unsupported_format(self):
        """サポートされていないフォーマットでFalseを返す"""
        # Given: サポートされていないフォーマットのファイル
        audio_path = os.path.join(self.temp_dir, "test_audio.ogg")
        with open(audio_path, 'w') as f:
            f.write("dummy content")

        # When: validate_filesを実行
        from extract_screenshots import AudioProcessor
        processor = AudioProcessor(audio_path, self.output_dir)
        result = processor.validate_files()

        # Then: Falseを返す
        self.assertFalse(result)

    def test_validate_files_with_directory(self):
        """ディレクトリパスでFalseを返す"""
        # Given: ディレクトリパス
        audio_path = self.temp_dir

        # When: validate_filesを実行
        from extract_screenshots import AudioProcessor
        processor = AudioProcessor(audio_path, self.output_dir)
        result = processor.validate_files()

        # Then: Falseを返す（通常ファイルではない）
        self.assertFalse(result)

    def test_validate_files_with_path_traversal_protection(self):
        """パストラバーサル攻撃を防ぐためにPath.resolve()を使用する"""
        # Given: 相対パスを含むファイルパス
        audio_path = os.path.join(self.temp_dir, "../test_audio.mp3")
        # 実際のファイルを作成（resolve後のパス）
        resolved_path = Path(audio_path).resolve()
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        with open(resolved_path, 'w') as f:
            f.write("dummy content")

        # When: validate_filesを実行
        from extract_screenshots import AudioProcessor
        processor = AudioProcessor(str(audio_path), self.output_dir)

        # Then: パスが正規化されて処理される
        # （エラーにならず、存在確認が正しく行われる）
        result = processor.validate_files()
        self.assertTrue(result)

    @patch('builtins.print')
    def test_validate_files_prints_error_message_for_nonexistent_file(self, mock_print):
        """存在しないファイルのエラーメッセージを表示する"""
        # Given: 存在しないファイルパス
        audio_path = os.path.join(self.temp_dir, "nonexistent.mp3")

        # When: validate_filesを実行
        from extract_screenshots import AudioProcessor
        processor = AudioProcessor(audio_path, self.output_dir)
        processor.validate_files()

        # Then: エラーメッセージが表示される
        mock_print.assert_any_call(f"Error: Audio file not found: {Path(audio_path).resolve()}")

    @patch('builtins.print')
    def test_validate_files_prints_supported_formats_for_unsupported_file(self, mock_print):
        """未対応フォーマットのエラーメッセージにサポートされている形式一覧を表示する"""
        # Given: サポートされていないフォーマットのファイル
        audio_path = os.path.join(self.temp_dir, "test_audio.ogg")
        with open(audio_path, 'w') as f:
            f.write("dummy content")

        # When: validate_filesを実行
        from extract_screenshots import AudioProcessor
        processor = AudioProcessor(audio_path, self.output_dir)
        processor.validate_files()

        # Then: サポートされているフォーマット一覧が表示される
        call_args_list = [str(call) for call in mock_print.call_args_list]
        found_supported_formats = any("Supported formats:" in str(call) for call in call_args_list)
        self.assertTrue(found_supported_formats, "Should display supported formats list")


class TestAudioProcessorGetDuration(unittest.TestCase):
    """AudioProcessor.get_duration() のテスト (Whisper結果から取得)"""

    def setUp(self):
        """テストごとの初期化"""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = tempfile.mkdtemp()

    def tearDown(self):
        """テストごとのクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        shutil.rmtree(self.output_dir, ignore_errors=True)

    def test_get_duration_returns_none_before_transcribe(self):
        """transcribe_audio実行前はNoneを返す"""
        # Given: 音声ファイル
        audio_path = os.path.join(self.temp_dir, "test_audio.mp3")
        with open(audio_path, 'w') as f:
            f.write("dummy content")

        # When: get_durationを実行（transcribe前）
        from extract_screenshots import AudioProcessor
        processor = AudioProcessor(audio_path, self.output_dir)
        duration = processor.get_duration()

        # Then: Noneを返す
        self.assertIsNone(duration)

    @patch('extract_screenshots.get_whisper_model')
    def test_get_duration_returns_correct_duration_after_transcribe(self, mock_get_model):
        """transcribe_audio実行後は正しい長さを返す"""
        # Given: 音声ファイルとWhisperの結果
        audio_path = os.path.join(self.temp_dir, "test_audio.mp3")
        with open(audio_path, 'w') as f:
            f.write("dummy content")

        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            'duration': 125.5,
            'segments': [
                {'start': 0.0, 'end': 2.5, 'text': 'これはテスト'}
            ]
        }
        mock_get_model.return_value = mock_model

        # When: transcribe_audioを実行してからget_durationを実行
        from extract_screenshots import AudioProcessor
        processor = AudioProcessor(audio_path, self.output_dir)
        processor.transcribe_audio()
        duration = processor.get_duration()

        # Then: 正しい長さを返す
        self.assertAlmostEqual(duration, 125.5, places=1)

    @patch('extract_screenshots.get_whisper_model')
    def test_get_duration_uses_whisper_result_duration(self, mock_get_model):
        """Whisperの結果から長さを取得する"""
        # Given: Whisperが様々な長さを返す
        audio_path = os.path.join(self.temp_dir, "test_audio.mp3")
        with open(audio_path, 'w') as f:
            f.write("dummy content")

        test_durations = [10.5, 60.0, 125.3, 270.18]

        for expected_duration in test_durations:
            with self.subTest(duration=expected_duration):
                mock_model = MagicMock()
                mock_model.transcribe.return_value = {
                    'duration': expected_duration,
                    'segments': []
                }
                mock_get_model.return_value = mock_model

                # When: transcribe_audioを実行
                from extract_screenshots import AudioProcessor
                processor = AudioProcessor(audio_path, self.output_dir)
                processor.transcribe_audio()

                # Then: Whisperの結果から長さを取得する
                duration = processor.get_duration()
                self.assertAlmostEqual(duration, expected_duration, places=2)

    @patch('extract_screenshots.get_whisper_model')
    def test_get_duration_handles_missing_duration_in_result(self, mock_get_model):
        """Whisperの結果にdurationがない場合は0.0を返す"""
        # Given: durationキーがないWhisperの結果
        audio_path = os.path.join(self.temp_dir, "test_audio.mp3")
        with open(audio_path, 'w') as f:
            f.write("dummy content")

        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            'segments': []
            # duration キーなし
        }
        mock_get_model.return_value = mock_model

        # When: transcribe_audioを実行
        from extract_screenshots import AudioProcessor
        processor = AudioProcessor(audio_path, self.output_dir)
        processor.transcribe_audio()

        # Then: 0.0を返す
        duration = processor.get_duration()
        self.assertEqual(duration, 0.0)


class TestAudioProcessorValidateDurationMatch(unittest.TestCase):
    """AudioProcessor.validate_duration_match() のテスト"""

    def setUp(self):
        """テストごとの初期化"""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = tempfile.mkdtemp()

    def tearDown(self):
        """テストごとのクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        shutil.rmtree(self.output_dir, ignore_errors=True)

    @patch('extract_screenshots.AudioProcessor.get_duration')
    @patch('builtins.print')
    def test_validate_duration_match_no_warning_when_diff_under_5_seconds(self, mock_print, mock_get_duration):
        """差異が5秒以下の場合は警告なしでTrueを返す"""
        # Given: 音声125.0秒、動画127.0秒（差異2.0秒）
        audio_path = os.path.join(self.temp_dir, "test_audio.mp3")
        with open(audio_path, 'w') as f:
            f.write("dummy content")

        mock_get_duration.return_value = 125.0

        # When: validate_duration_matchを実行
        from extract_screenshots import AudioProcessor
        processor = AudioProcessor(audio_path, self.output_dir)
        result = processor.validate_duration_match(video_duration=127.0)

        # Then: Trueを返す
        self.assertTrue(result)

        # 警告メッセージは表示されない
        warning_calls = [call for call in mock_print.call_args_list if 'Warning' in str(call)]
        self.assertEqual(len(warning_calls), 0)

    @patch('extract_screenshots.AudioProcessor.get_duration')
    @patch('builtins.print')
    def test_validate_duration_match_shows_warning_when_diff_over_5_seconds(self, mock_print, mock_get_duration):
        """差異が5秒以上の場合は警告を表示してTrueを返す"""
        # Given: 音声125.0秒、動画132.0秒（差異7.0秒）
        audio_path = os.path.join(self.temp_dir, "test_audio.mp3")
        with open(audio_path, 'w') as f:
            f.write("dummy content")

        mock_get_duration.return_value = 125.0

        # When: validate_duration_matchを実行
        from extract_screenshots import AudioProcessor
        processor = AudioProcessor(audio_path, self.output_dir)
        result = processor.validate_duration_match(video_duration=132.0)

        # Then: Trueを返す（処理継続）
        self.assertTrue(result)

        # 警告メッセージが表示される
        call_args_list = [str(call) for call in mock_print.call_args_list]
        found_warning = any("Warning" in call and "Duration mismatch" in call for call in call_args_list)
        self.assertTrue(found_warning, "Should display duration mismatch warning")

    @patch('extract_screenshots.AudioProcessor.get_duration')
    @patch('builtins.print')
    def test_validate_duration_match_shows_warning_with_correct_values(self, mock_print, mock_get_duration):
        """警告メッセージに正しい動画・音声の長さと差異を表示する"""
        # Given: 音声120.5秒、動画132.3秒（差異11.8秒）
        audio_path = os.path.join(self.temp_dir, "test_audio.mp3")
        with open(audio_path, 'w') as f:
            f.write("dummy content")

        mock_get_duration.return_value = 120.5

        # When: validate_duration_matchを実行
        from extract_screenshots import AudioProcessor
        processor = AudioProcessor(audio_path, self.output_dir)
        processor.validate_duration_match(video_duration=132.3)

        # Then: 警告メッセージに正しい値が含まれる
        call_args_list = [str(call) for call in mock_print.call_args_list]
        found_values = any(
            "132.3" in call and "120.5" in call and "11.8" in call
            for call in call_args_list
        )
        self.assertTrue(found_values, "Warning message should contain correct duration values")

    @patch('extract_screenshots.AudioProcessor.get_duration')
    @patch('builtins.print')
    def test_validate_duration_match_boundary_exactly_5_seconds(self, mock_print, mock_get_duration):
        """差異がちょうど5秒の場合は警告なしでTrueを返す"""
        # Given: 音声125.0秒、動画130.0秒（差異ちょうど5.0秒）
        audio_path = os.path.join(self.temp_dir, "test_audio.mp3")
        with open(audio_path, 'w') as f:
            f.write("dummy content")

        mock_get_duration.return_value = 125.0

        # When: validate_duration_matchを実行
        from extract_screenshots import AudioProcessor
        processor = AudioProcessor(audio_path, self.output_dir)
        result = processor.validate_duration_match(video_duration=130.0)

        # Then: Trueを返す
        self.assertTrue(result)

        # 警告メッセージは表示されない（5秒は閾値内）
        warning_calls = [call for call in mock_print.call_args_list if 'Warning' in str(call)]
        self.assertEqual(len(warning_calls), 0)

    @patch('extract_screenshots.AudioProcessor.get_duration')
    @patch('builtins.print')
    def test_validate_duration_match_audio_longer_than_video(self, mock_print, mock_get_duration):
        """音声が動画より長い場合も正しく警告を表示する"""
        # Given: 音声135.0秒、動画120.0秒（差異15.0秒、音声が長い）
        audio_path = os.path.join(self.temp_dir, "test_audio.mp3")
        with open(audio_path, 'w') as f:
            f.write("dummy content")

        mock_get_duration.return_value = 135.0

        # When: validate_duration_matchを実行
        from extract_screenshots import AudioProcessor
        processor = AudioProcessor(audio_path, self.output_dir)
        result = processor.validate_duration_match(video_duration=120.0)

        # Then: Trueを返す（処理継続）
        self.assertTrue(result)

        # 警告メッセージが表示される
        call_args_list = [str(call) for call in mock_print.call_args_list]
        found_warning = any("Warning" in call and "Duration mismatch" in call for call in call_args_list)
        self.assertTrue(found_warning, "Should display warning when audio is longer than video")


class TestAudioProcessorTranscribeAudio(unittest.TestCase):
    """AudioProcessor.transcribe_audio() のテスト"""

    def setUp(self):
        """テストごとの初期化"""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = tempfile.mkdtemp()

    def tearDown(self):
        """テストごとのクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        shutil.rmtree(self.output_dir, ignore_errors=True)

    @patch('extract_screenshots.get_whisper_model')
    def test_transcribe_audio_returns_segments_list(self, mock_get_model):
        """音声認識結果をセグメントリストで返す"""
        # Given: 音声ファイルとWhisperモデルのモック
        audio_path = os.path.join(self.temp_dir, "test_audio.mp3")
        with open(audio_path, 'w') as f:
            f.write("dummy content")

        # Whisperモデルのモック（transcribeメソッドを持つ）
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            'text': 'これはテスト音声です。',
            'duration': 4.0,
            'segments': [
                {'start': 0.0, 'end': 2.5, 'text': 'これはテスト'},
                {'start': 2.5, 'end': 4.0, 'text': '音声です。'}
            ]
        }
        mock_get_model.return_value = mock_model

        # When: transcribe_audioを実行
        from extract_screenshots import AudioProcessor
        processor = AudioProcessor(audio_path, self.output_dir)
        segments = processor.transcribe_audio(language="ja")

        # Then: セグメントリストを返す
        self.assertIsInstance(segments, list)
        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0]['start'], 0.0)
        self.assertEqual(segments[0]['end'], 2.5)
        self.assertEqual(segments[0]['text'], 'これはテスト')

        # Whisperモデルが正しく呼び出される
        mock_get_model.assert_called_once_with('base')
        mock_model.transcribe.assert_called_once_with(audio_path, language='ja')

    @patch('extract_screenshots.get_whisper_model')
    def test_transcribe_audio_uses_specified_language(self, mock_get_model):
        """指定された言語コードでWhisperを呼び出す"""
        # Given: 音声ファイルと英語指定
        audio_path = os.path.join(self.temp_dir, "test_audio.mp3")
        with open(audio_path, 'w') as f:
            f.write("dummy content")

        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            'segments': [{'start': 0.0, 'end': 2.0, 'text': 'Hello'}]
        }
        mock_get_model.return_value = mock_model

        # When: transcribe_audioを英語で実行
        from extract_screenshots import AudioProcessor
        processor = AudioProcessor(audio_path, self.output_dir)
        processor.transcribe_audio(language="en")

        # Then: language="en"で呼び出される
        mock_model.transcribe.assert_called_once_with(audio_path, language='en')

    @patch('extract_screenshots.get_whisper_model')
    def test_transcribe_audio_uses_model_size(self, mock_get_model):
        """指定されたモデルサイズでWhisperをロードする"""
        # Given: 音声ファイルとsmallモデル指定
        audio_path = os.path.join(self.temp_dir, "test_audio.mp3")
        with open(audio_path, 'w') as f:
            f.write("dummy content")

        mock_model = MagicMock()
        mock_model.transcribe.return_value = {'segments': []}
        mock_get_model.return_value = mock_model

        # When: model_size="small"で初期化してtranscribe_audioを実行
        from extract_screenshots import AudioProcessor
        processor = AudioProcessor(audio_path, self.output_dir, model_size="small")
        processor.transcribe_audio()

        # Then: model_size="small"でモデルをロードする
        mock_get_model.assert_called_once_with('small')

    @patch('extract_screenshots.get_whisper_model')
    @patch('builtins.print')
    def test_transcribe_audio_returns_empty_list_on_exception(self, mock_print, mock_get_model):
        """音声認識失敗時には空リストを返して処理を継続する"""
        # Given: 音声ファイルとWhisperモデルのエラー
        audio_path = os.path.join(self.temp_dir, "test_audio.mp3")
        with open(audio_path, 'w') as f:
            f.write("dummy content")

        mock_get_model.side_effect = Exception("Whisper model load failed")

        # When: transcribe_audioを実行
        from extract_screenshots import AudioProcessor
        processor = AudioProcessor(audio_path, self.output_dir)
        segments = processor.transcribe_audio()

        # Then: 空リストを返す
        self.assertEqual(segments, [])

        # 警告メッセージが表示される
        call_args_list = [str(call) for call in mock_print.call_args_list]
        found_warning = any("Warning" in call and "transcription failed" in call for call in call_args_list)
        self.assertTrue(found_warning, "Should display warning when transcription fails")

    @patch('extract_screenshots.get_whisper_model')
    @patch('builtins.print')
    def test_transcribe_audio_displays_progress(self, mock_print, mock_get_model):
        """音声認識中に進捗メッセージを表示する"""
        # Given: 音声ファイル
        audio_path = os.path.join(self.temp_dir, "test_audio.mp3")
        with open(audio_path, 'w') as f:
            f.write("dummy content")

        mock_model = MagicMock()
        mock_model.transcribe.return_value = {'segments': []}
        mock_get_model.return_value = mock_model

        # When: transcribe_audioを実行
        from extract_screenshots import AudioProcessor
        processor = AudioProcessor(audio_path, self.output_dir)
        processor.transcribe_audio()

        # Then: 進捗メッセージが表示される
        call_args_list = [str(call) for call in mock_print.call_args_list]
        found_transcribing = any("Transcribing audio" in call for call in call_args_list)
        self.assertTrue(found_transcribing, "Should display transcribing message")

    @patch('extract_screenshots.get_whisper_model')
    def test_transcribe_audio_default_language_is_japanese(self, mock_get_model):
        """デフォルト言語が日本語であることを確認する"""
        # Given: 音声ファイル
        audio_path = os.path.join(self.temp_dir, "test_audio.mp3")
        with open(audio_path, 'w') as f:
            f.write("dummy content")

        mock_model = MagicMock()
        mock_model.transcribe.return_value = {'segments': [], 'duration': 0.0}
        mock_get_model.return_value = mock_model

        # When: languageを指定せずにtranscribe_audioを実行
        from extract_screenshots import AudioProcessor
        processor = AudioProcessor(audio_path, self.output_dir)
        processor.transcribe_audio()

        # Then: デフォルトでlanguage="ja"が使用される
        mock_model.transcribe.assert_called_once_with(audio_path, language='ja')

    @patch('extract_screenshots.get_whisper_model')
    def test_transcribe_audio_sets_duration_from_result(self, mock_get_model):
        """音声認識結果からdurationを設定する"""
        # Given: 音声ファイルとWhisperの結果
        audio_path = os.path.join(self.temp_dir, "test_audio.mp3")
        with open(audio_path, 'w') as f:
            f.write("dummy content")

        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            'duration': 270.18,
            'segments': [
                {'start': 0.0, 'end': 2.5, 'text': 'テスト'}
            ]
        }
        mock_get_model.return_value = mock_model

        # When: transcribe_audioを実行
        from extract_screenshots import AudioProcessor
        processor = AudioProcessor(audio_path, self.output_dir)
        processor.transcribe_audio()

        # Then: audio_durationが設定される
        self.assertIsNotNone(processor.audio_duration)
        self.assertAlmostEqual(processor.audio_duration, 270.18, places=2)

    @patch('extract_screenshots.get_whisper_model')
    @patch('builtins.print')
    def test_transcribe_audio_displays_duration(self, mock_print, mock_get_model):
        """音声認識後に音声の長さを表示する"""
        # Given: 音声ファイル
        audio_path = os.path.join(self.temp_dir, "test_audio.mp3")
        with open(audio_path, 'w') as f:
            f.write("dummy content")

        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            'duration': 125.5,
            'segments': []
        }
        mock_get_model.return_value = mock_model

        # When: transcribe_audioを実行
        from extract_screenshots import AudioProcessor
        processor = AudioProcessor(audio_path, self.output_dir)
        processor.transcribe_audio()

        # Then: 音声の長さが表示される
        call_args_list = [str(call) for call in mock_print.call_args_list]
        found_duration = any("Audio duration" in call and "125.5" in call for call in call_args_list)
        self.assertTrue(found_duration, "Should display audio duration")


class TestAudioProcessorSaveTranscript(unittest.TestCase):
    """AudioProcessor.save_transcript() のテスト"""

    def setUp(self):
        """テストごとの初期化"""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = tempfile.mkdtemp()

    def tearDown(self):
        """テストごとのクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        shutil.rmtree(self.output_dir, ignore_errors=True)

    @patch('extract_screenshots.AudioProcessor.get_duration')
    def test_save_transcript_creates_json_file(self, mock_get_duration):
        """transcript.jsonファイルを作成する"""
        # Given: 音声ファイルとセグメントデータ
        audio_path = os.path.join(self.temp_dir, "test_audio.mp3")
        with open(audio_path, 'w') as f:
            f.write("dummy content")

        mock_get_duration.return_value = 125.5

        segments = [
            {'start': 0.0, 'end': 2.5, 'text': 'これはテスト'},
            {'start': 2.5, 'end': 4.0, 'text': '音声です。'}
        ]

        # When: save_transcriptを実行
        from extract_screenshots import AudioProcessor
        processor = AudioProcessor(audio_path, self.output_dir)
        result_path = processor.save_transcript(segments)

        # Then: transcript.jsonが作成される
        self.assertTrue(result_path.exists())
        self.assertEqual(result_path.name, "transcript.json")
        self.assertEqual(result_path.parent, Path(self.output_dir))

    @patch('extract_screenshots.AudioProcessor.get_duration')
    def test_save_transcript_correct_json_structure(self, mock_get_duration):
        """正しいJSON構造でデータを保存する"""
        # Given: 音声ファイルとセグメントデータ
        audio_path = os.path.join(self.temp_dir, "test_audio.mp3")
        with open(audio_path, 'w') as f:
            f.write("dummy content")

        mock_get_duration.return_value = 125.5

        segments = [
            {'start': 0.0, 'end': 2.5, 'text': 'これはテスト'},
            {'start': 2.5, 'end': 4.0, 'text': '音声です。'}
        ]

        # When: save_transcriptを実行
        from extract_screenshots import AudioProcessor
        processor = AudioProcessor(audio_path, self.output_dir)
        result_path = processor.save_transcript(segments)

        # Then: JSONファイルに正しい構造でデータが保存される
        with open(result_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertIn('language', data)
        self.assertIn('duration', data)
        self.assertIn('segments', data)
        self.assertEqual(data['language'], 'ja')
        self.assertAlmostEqual(data['duration'], 125.5, places=1)
        self.assertEqual(len(data['segments']), 2)
        self.assertEqual(data['segments'][0]['start'], 0.0)
        self.assertEqual(data['segments'][0]['end'], 2.5)
        self.assertEqual(data['segments'][0]['text'], 'これはテスト')

    @patch('extract_screenshots.AudioProcessor.get_duration')
    def test_save_transcript_utf8_encoding(self, mock_get_duration):
        """UTF-8エンコーディングでファイルを保存する"""
        # Given: 日本語テキストを含むセグメント
        audio_path = os.path.join(self.temp_dir, "test_audio.mp3")
        with open(audio_path, 'w') as f:
            f.write("dummy content")

        mock_get_duration.return_value = 10.0

        segments = [
            {'start': 0.0, 'end': 2.5, 'text': '日本語テキスト😀'},
            {'start': 2.5, 'end': 4.0, 'text': 'English text'}
        ]

        # When: save_transcriptを実行
        from extract_screenshots import AudioProcessor
        processor = AudioProcessor(audio_path, self.output_dir)
        result_path = processor.save_transcript(segments)

        # Then: UTF-8で読み込み可能
        with open(result_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertEqual(data['segments'][0]['text'], '日本語テキスト😀')
        self.assertEqual(data['segments'][1]['text'], 'English text')

    @patch('extract_screenshots.AudioProcessor.get_duration')
    def test_save_transcript_file_permissions(self, mock_get_duration):
        """ファイルパーミッションを0644に設定する"""
        # Given: 音声ファイルとセグメント
        audio_path = os.path.join(self.temp_dir, "test_audio.mp3")
        with open(audio_path, 'w') as f:
            f.write("dummy content")

        mock_get_duration.return_value = 10.0

        segments = [{'start': 0.0, 'end': 2.5, 'text': 'テスト'}]

        # When: save_transcriptを実行
        from extract_screenshots import AudioProcessor
        processor = AudioProcessor(audio_path, self.output_dir)
        result_path = processor.save_transcript(segments)

        # Then: ファイルパーミッションが0644
        import stat
        file_stat = os.stat(result_path)
        file_mode = stat.S_IMODE(file_stat.st_mode)
        self.assertEqual(file_mode, 0o644)

    @patch('extract_screenshots.AudioProcessor.get_duration')
    def test_save_transcript_with_empty_segments(self, mock_get_duration):
        """空のセグメントリストでも正しく保存する"""
        # Given: 空のセグメントリスト
        audio_path = os.path.join(self.temp_dir, "test_audio.mp3")
        with open(audio_path, 'w') as f:
            f.write("dummy content")

        mock_get_duration.return_value = 10.0

        segments = []

        # When: save_transcriptを実行
        from extract_screenshots import AudioProcessor
        processor = AudioProcessor(audio_path, self.output_dir)
        result_path = processor.save_transcript(segments)

        # Then: JSONファイルが作成され、空のセグメントリストが保存される
        self.assertTrue(result_path.exists())

        with open(result_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertEqual(data['segments'], [])
        self.assertEqual(data['language'], 'ja')
        self.assertAlmostEqual(data['duration'], 10.0, places=1)

    @patch('extract_screenshots.AudioProcessor.get_duration')
    def test_save_transcript_creates_output_directory_if_not_exists(self, mock_get_duration):
        """出力ディレクトリが存在しない場合は作成する"""
        # Given: 存在しない出力ディレクトリ
        audio_path = os.path.join(self.temp_dir, "test_audio.mp3")
        with open(audio_path, 'w') as f:
            f.write("dummy content")

        non_existent_dir = os.path.join(self.temp_dir, "non_existent_output")
        mock_get_duration.return_value = 10.0

        segments = [{'start': 0.0, 'end': 2.5, 'text': 'テスト'}]

        # When: save_transcriptを実行
        from extract_screenshots import AudioProcessor
        processor = AudioProcessor(audio_path, non_existent_dir)
        result_path = processor.save_transcript(segments)

        # Then: ディレクトリが作成され、ファイルが保存される
        self.assertTrue(Path(non_existent_dir).exists())
        self.assertTrue(result_path.exists())


if __name__ == '__main__':
    unittest.main()
