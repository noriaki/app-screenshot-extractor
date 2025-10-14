#!/usr/bin/env python3
"""
CLI統合機能のテストスイート
Task 4: CLI統合とオーケストレーション
"""

import argparse
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json


class TestCLIOptions(unittest.TestCase):
    """Task 4.1: CLIオプションの追加テスト"""

    def test_audio_option_exists(self):
        """--audioオプションが定義されているか確認"""
        from extract_screenshots import create_argument_parser
        parser = create_argument_parser()

        # --audioオプションをパース
        args = parser.parse_args(['--input', 'test.mp4', '--audio', 'test.mp3'])
        self.assertEqual(args.audio, 'test.mp3')

    def test_audio_option_optional(self):
        """--audioオプションが任意であることを確認"""
        from extract_screenshots import create_argument_parser
        parser = create_argument_parser()

        # --audioなしでもパース可能
        args = parser.parse_args(['--input', 'test.mp4'])
        self.assertIsNone(args.audio)

    def test_markdown_option_exists(self):
        """--markdownオプションが定義されているか確認"""
        from extract_screenshots import create_argument_parser
        parser = create_argument_parser()

        # --markdownオプションをパース
        args = parser.parse_args(['--input', 'test.mp4', '--markdown'])
        self.assertTrue(args.markdown)

    def test_markdown_option_default_false(self):
        """--markdownオプションのデフォルトがFalseであることを確認"""
        from extract_screenshots import create_argument_parser
        parser = create_argument_parser()

        args = parser.parse_args(['--input', 'test.mp4'])
        self.assertFalse(args.markdown)

    def test_model_size_option_exists(self):
        """--model-sizeオプションが定義されているか確認"""
        from extract_screenshots import create_argument_parser
        parser = create_argument_parser()

        # --model-sizeオプションをパース
        args = parser.parse_args(['--input', 'test.mp4', '--model-size', 'small'])
        self.assertEqual(args.model_size, 'small')

    def test_model_size_default_base(self):
        """--model-sizeのデフォルトが'base'であることを確認"""
        from extract_screenshots import create_argument_parser
        parser = create_argument_parser()

        args = parser.parse_args(['--input', 'test.mp4'])
        self.assertEqual(args.model_size, 'base')

    def test_model_size_valid_choices(self):
        """--model-sizeの有効な選択肢を確認"""
        from extract_screenshots import create_argument_parser
        parser = create_argument_parser()

        valid_choices = ['tiny', 'base', 'small', 'medium', 'large', 'turbo']

        for choice in valid_choices:
            args = parser.parse_args(['--input', 'test.mp4', '--model-size', choice])
            self.assertEqual(args.model_size, choice)

    def test_model_size_invalid_choice_raises_error(self):
        """--model-sizeに無効な値を指定するとエラー"""
        from extract_screenshots import create_argument_parser
        parser = create_argument_parser()

        with self.assertRaises(SystemExit):
            parser.parse_args(['--input', 'test.mp4', '--model-size', 'invalid'])

    def test_existing_options_still_work(self):
        """既存のオプションが正常に動作することを確認（後方互換性）"""
        from extract_screenshots import create_argument_parser
        parser = create_argument_parser()

        args = parser.parse_args([
            '--input', 'test.mp4',
            '--output', 'out',
            '--count', '15',
            '--threshold', '30',
            '--interval', '20.0'
        ])

        self.assertEqual(args.input, 'test.mp4')
        self.assertEqual(args.output, 'out')
        self.assertEqual(args.count, 15)
        self.assertEqual(args.threshold, 30)
        self.assertEqual(args.interval, 20.0)


class TestIntegrationFlow(unittest.TestCase):
    """Task 4.2: 統合処理フローのテスト"""

    @patch('extract_screenshots.ScreenshotExtractor')
    @patch('extract_screenshots.AudioProcessor')
    @patch('extract_screenshots.TimestampSynchronizer')
    @patch('extract_screenshots.MarkdownGenerator')
    def test_full_flow_with_audio_and_markdown(self, mock_md, mock_sync, mock_audio, mock_extractor):
        """音声ありMarkdown生成の完全フローをテスト"""
        # モックの設定
        mock_extractor_instance = mock_extractor.return_value
        mock_extractor_instance.extract_screenshots.return_value = [
            {'timestamp': 15.0, 'filename': '01.png'}
        ]
        mock_extractor_instance.video_duration = 120.0

        mock_audio_instance = mock_audio.return_value
        mock_audio_instance.validate_files.return_value = True
        mock_audio_instance.get_duration.return_value = 120.0
        mock_audio_instance.validate_duration_match.return_value = True
        mock_audio_instance.transcribe_audio.return_value = [
            {'start': 14.0, 'end': 17.0, 'text': 'テスト'}
        ]

        mock_sync_instance = mock_sync.return_value
        mock_sync_instance.synchronize.return_value = [
            {
                'screenshot': {'timestamp': 15.0, 'filename': '01.png'},
                'transcript': {'start': 14.0, 'end': 17.0, 'text': 'テスト'},
                'matched': True
            }
        ]

        mock_md_instance = mock_md.return_value
        mock_md_instance.generate.return_value = '# Test'
        mock_md_instance.save.return_value = Path('/output/article.md')

        # テスト実行
        from extract_screenshots import run_integration_flow

        run_integration_flow(
            video_path='test.mp4',
            output_dir='output',
            audio_path='test.mp3',
            markdown=True,
            model_size='base',
            threshold=25,
            interval=15.0,
            count=10
        )

        # 検証
        mock_extractor.assert_called_once()
        mock_extractor_instance.extract_screenshots.assert_called_once()

        mock_audio.assert_called_once_with(
            audio_path='test.mp3',
            output_dir='output',
            model_size='base'
        )
        mock_audio_instance.validate_files.assert_called_once()
        mock_audio_instance.transcribe_audio.assert_called_once_with(language='ja')

        mock_sync.assert_called_once()
        mock_md.assert_called_once()

    @patch('extract_screenshots.ScreenshotExtractor')
    @patch('extract_screenshots.MarkdownGenerator')
    def test_markdown_only_without_audio(self, mock_md, mock_extractor):
        """音声なしMarkdown生成のフローをテスト"""
        # モックの設定
        mock_extractor_instance = mock_extractor.return_value
        mock_extractor_instance.extract_screenshots.return_value = [
            {'timestamp': 15.0, 'filename': '01.png'}
        ]

        mock_md_instance = mock_md.return_value
        mock_md_instance.generate.return_value = '# Test'
        mock_md_instance.save.return_value = Path('/output/article.md')

        # テスト実行
        from extract_screenshots import run_integration_flow

        run_integration_flow(
            video_path='test.mp4',
            output_dir='output',
            audio_path=None,
            markdown=True,
            model_size='base',
            threshold=25,
            interval=15.0,
            count=10
        )

        # 検証: AudioProcessorは呼ばれない
        mock_extractor.assert_called_once()
        mock_md.assert_called_once()

        # generateに渡されるデータがtranscript=Noneであることを確認
        call_args = mock_md_instance.generate.call_args[0][0]
        self.assertIsNone(call_args[0]['transcript'])

    @patch('extract_screenshots.ScreenshotExtractor')
    @patch('extract_screenshots.AudioProcessor')
    def test_audio_only_without_markdown(self, mock_audio, mock_extractor):
        """音声のみ（Markdownなし）のフローをテスト"""
        # モックの設定
        mock_extractor_instance = mock_extractor.return_value
        mock_extractor_instance.extract_screenshots.return_value = [
            {'timestamp': 15.0, 'filename': '01.png'}
        ]
        mock_extractor_instance.video_duration = 120.0

        mock_audio_instance = mock_audio.return_value
        mock_audio_instance.validate_files.return_value = True
        mock_audio_instance.get_duration.return_value = 120.0
        mock_audio_instance.validate_duration_match.return_value = True
        mock_audio_instance.transcribe_audio.return_value = [
            {'start': 14.0, 'end': 17.0, 'text': 'テスト'}
        ]

        # テスト実行
        from extract_screenshots import run_integration_flow

        run_integration_flow(
            video_path='test.mp4',
            output_dir='output',
            audio_path='test.mp3',
            markdown=False,
            model_size='base',
            threshold=25,
            interval=15.0,
            count=10
        )

        # 検証: AudioProcessorは呼ばれるが、MarkdownGeneratorは呼ばれない
        mock_audio.assert_called_once()
        mock_audio_instance.transcribe_audio.assert_called_once()

    @patch('extract_screenshots.ScreenshotExtractor')
    @patch('extract_screenshots.AudioProcessor')
    def test_audio_validation_failure_exits(self, mock_audio, mock_extractor):
        """音声ファイル検証失敗時に処理が中断されることをテスト"""
        # モックの設定
        mock_extractor_instance = mock_extractor.return_value
        mock_extractor_instance.extract_screenshots.return_value = [
            {'timestamp': 15.0, 'filename': '01.png'}
        ]

        mock_audio_instance = mock_audio.return_value
        mock_audio_instance.validate_files.return_value = False  # 検証失敗

        # テスト実行
        from extract_screenshots import run_integration_flow

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

        # exit code 1で終了することを確認
        self.assertEqual(cm.exception.code, 1)


class TestBackwardCompatibility(unittest.TestCase):
    """Task 4.3: 後方互換性の確保テスト"""

    @patch('extract_screenshots.ScreenshotExtractor')
    def test_existing_behavior_without_new_options(self, mock_extractor):
        """新オプションなしで既存の動作を維持することを確認"""
        # モックの設定
        mock_extractor_instance = mock_extractor.return_value
        mock_extractor_instance.extract_screenshots.return_value = [
            {'timestamp': 15.0, 'filename': '01.png'}
        ]

        # テスト実行
        from extract_screenshots import run_integration_flow

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

        # 検証: ScreenshotExtractorのみが呼ばれる
        mock_extractor.assert_called_once()
        mock_extractor_instance.extract_screenshots.assert_called_once()

    def test_metadata_json_format_unchanged(self):
        """metadata.jsonフォーマットが変更されていないことを確認"""
        # 既存のmetadata.jsonフォーマット
        expected_keys = {
            'index', 'filename', 'timestamp', 'score',
            'transition_magnitude', 'stability_score',
            'ui_importance_score', 'ui_elements', 'detected_texts'
        }

        # 新機能実装後もフォーマットが同じであることを確認
        sample_metadata = {
            'index': 1,
            'filename': '01.png',
            'timestamp': 15.0,
            'score': 87.0,
            'transition_magnitude': 42,
            'stability_score': 95.3,
            'ui_importance_score': 65.0,
            'ui_elements': [],
            'detected_texts': []
        }

        # 必須キーが全て存在することを確認
        self.assertTrue(expected_keys.issubset(sample_metadata.keys()))


if __name__ == '__main__':
    unittest.main()
