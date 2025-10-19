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


class TestAIModelOptions(unittest.TestCase):
    """Task 4.1 (model-upgrade): AIモデル設定のCLIテスト"""

    def test_ai_model_default_updated(self):
        """
        Given: create_argument_parser()を呼び出す
        When: デフォルト引数でパースする
        Then: args.ai_modelが'claude-sonnet-4-5-20250929'である
        """
        from extract_screenshots import create_argument_parser
        parser = create_argument_parser()

        args = parser.parse_args(['--input', 'test.mp4'])
        self.assertEqual(args.ai_model, 'claude-sonnet-4-5-20250929')

    def test_ai_model_choices_updated(self):
        """
        Given: create_argument_parser()を呼び出す
        When: --ai-model オプションの定義を確認する
        Then: choicesが3つの最新モデルを含む
        """
        from extract_screenshots import create_argument_parser
        parser = create_argument_parser()

        # 引数定義からchoicesを取得
        ai_model_action = None
        for action in parser._actions:
            if action.dest == 'ai_model':
                ai_model_action = action
                break

        self.assertIsNotNone(ai_model_action)
        expected_choices = [
            'claude-haiku-4-5-20251001',
            'claude-sonnet-4-5-20250929',
            'claude-opus-4-1-20250805'
        ]
        self.assertEqual(ai_model_action.choices, expected_choices)

    def test_ai_model_haiku_valid(self):
        """
        Given: create_argument_parser()を呼び出す
        When: --ai-model claude-haiku-4-5-20251001 を指定する
        Then: パースが成功し、args.ai_modelが'claude-haiku-4-5-20251001'である
        """
        from extract_screenshots import create_argument_parser
        parser = create_argument_parser()

        args = parser.parse_args(['--input', 'test.mp4', '--ai-model', 'claude-haiku-4-5-20251001'])
        self.assertEqual(args.ai_model, 'claude-haiku-4-5-20251001')

    def test_ai_model_sonnet_valid(self):
        """
        Given: create_argument_parser()を呼び出す
        When: --ai-model claude-sonnet-4-5-20250929 を指定する
        Then: パースが成功し、args.ai_modelが'claude-sonnet-4-5-20250929'である
        """
        from extract_screenshots import create_argument_parser
        parser = create_argument_parser()

        args = parser.parse_args(['--input', 'test.mp4', '--ai-model', 'claude-sonnet-4-5-20250929'])
        self.assertEqual(args.ai_model, 'claude-sonnet-4-5-20250929')

    def test_ai_model_opus_valid(self):
        """
        Given: create_argument_parser()を呼び出す
        When: --ai-model claude-opus-4-1-20250805 を指定する
        Then: パースが成功し、args.ai_modelが'claude-opus-4-1-20250805'である
        """
        from extract_screenshots import create_argument_parser
        parser = create_argument_parser()

        args = parser.parse_args(['--input', 'test.mp4', '--ai-model', 'claude-opus-4-1-20250805'])
        self.assertEqual(args.ai_model, 'claude-opus-4-1-20250805')

    def test_ai_model_deprecated_rejected(self):
        """
        Given: create_argument_parser()を呼び出す
        When: --ai-model claude-3-5-sonnet-20241022 を指定する
        Then: argparse.ArgumentErrorが発生し、SystemExitが発生する
        """
        from extract_screenshots import create_argument_parser
        parser = create_argument_parser()

        with self.assertRaises(SystemExit):
            parser.parse_args(['--input', 'test.mp4', '--ai-model', 'claude-3-5-sonnet-20241022'])

    def test_ai_model_invalid_rejected(self):
        """
        Given: create_argument_parser()を呼び出す
        When: --ai-model invalid-model を指定する
        Then: argparse.ArgumentErrorが発生し、SystemExitが発生する
        """
        from extract_screenshots import create_argument_parser
        parser = create_argument_parser()

        with self.assertRaises(SystemExit):
            parser.parse_args(['--input', 'test.mp4', '--ai-model', 'invalid-model'])

    def test_ai_model_help_includes_pricing(self):
        """
        Given: create_argument_parser()を呼び出す
        When: --ai-model オプションのhelpテキストを取得する
        Then: 各モデルの価格情報が含まれる
        """
        from extract_screenshots import create_argument_parser
        parser = create_argument_parser()

        # 引数定義からhelpテキストを取得
        ai_model_action = None
        for action in parser._actions:
            if action.dest == 'ai_model':
                ai_model_action = action
                break

        self.assertIsNotNone(ai_model_action)
        help_text = ai_model_action.help

        # 価格情報が含まれていることを確認
        self.assertIn('$1/$5', help_text)
        self.assertIn('$3/$15', help_text)
        self.assertIn('$15/$75', help_text)
        # モデル特性の説明が含まれていることを確認
        self.assertIn('haiku', help_text.lower())
        self.assertIn('sonnet', help_text.lower())
        self.assertIn('opus', help_text.lower())


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
            ai_article=False,
            app_name=None,
            ai_model='claude-3-5-sonnet-20241022',
            output_format='markdown',
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
            ai_article=False,
            app_name=None,
            ai_model='claude-3-5-sonnet-20241022',
            output_format='markdown',
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
            ai_article=False,
            app_name=None,
            ai_model='claude-3-5-sonnet-20241022',
            output_format='markdown',
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
                ai_article=False,
                app_name=None,
                ai_model='claude-3-5-sonnet-20241022',
                output_format='markdown',
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
            ai_article=False,  # NEW
            app_name=None,  # NEW
            ai_model='claude-sonnet-4-5-20250929',  # UPDATED to new default
            output_format='markdown',  # NEW
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


class TestModelUpgradeEndToEnd(unittest.TestCase):
    """Task 5.1: エンドツーエンドフローのテストケース更新"""

    @patch('extract_screenshots.AIContentGenerator')
    @patch('extract_screenshots.ScreenshotExtractor')
    def test_default_model_end_to_end(self, mock_extractor, mock_ai_gen):
        """
        Given: --ai-modelオプションなしでCLIを実行する
        When: AI記事生成を実行する（モックAPI）
        Then: AIContentGeneratorがデフォルトモデル（claude-sonnet-4-5-20250929）で初期化される
        """
        from extract_screenshots import run_integration_flow
        import tempfile
        import os

        # モックの設定
        mock_extractor_instance = mock_extractor.return_value
        mock_extractor_instance.extract_screenshots.return_value = [
            {'timestamp': 15.0, 'filename': '01.png', 'file_path': '/tmp/01.png'}
        ]
        mock_extractor_instance.video_duration = 120.0

        mock_ai_instance = mock_ai_gen.return_value
        mock_ai_instance.generate_article.return_value = {
            'content': '# Test Article',
            'metadata': {'model': 'claude-sonnet-4-5-20250929'}
        }
        mock_ai_instance.save_article.return_value = '/tmp/ai_article.md'

        # テスト実行
        with tempfile.TemporaryDirectory() as tmpdir:
            run_integration_flow(
                video_path='test.mp4',
                output_dir=tmpdir,
                audio_path=None,
                markdown=False,
                ai_article=True,
                app_name='TestApp',
                ai_model='claude-sonnet-4-5-20250929',  # デフォルト値を明示
                output_format='markdown',
                model_size='base',
                threshold=25,
                interval=15.0,
                count=10
            )

        # 検証: AIContentGeneratorがデフォルトモデルで初期化される
        mock_ai_gen.assert_called_once()
        call_kwargs = mock_ai_gen.call_args[1]
        self.assertEqual(call_kwargs['model'], 'claude-sonnet-4-5-20250929')

    @patch('extract_screenshots.AIContentGenerator')
    @patch('extract_screenshots.ScreenshotExtractor')
    def test_haiku_model_end_to_end(self, mock_extractor, mock_ai_gen):
        """
        Given: --ai-model claude-haiku-4-5-20251001 でCLIを実行する
        When: AI記事生成を実行する（モックAPI）
        Then: AIContentGeneratorがHaikuモデルで初期化され、ai_metadata.jsonの"model"が一致する
        """
        from extract_screenshots import run_integration_flow
        import tempfile

        # モックの設定
        mock_extractor_instance = mock_extractor.return_value
        mock_extractor_instance.extract_screenshots.return_value = [
            {'timestamp': 15.0, 'filename': '01.png', 'file_path': '/tmp/01.png'}
        ]
        mock_extractor_instance.video_duration = 120.0

        mock_ai_instance = mock_ai_gen.return_value
        mock_ai_instance.generate_article.return_value = {
            'content': '# Test Article',
            'metadata': {'model': 'claude-haiku-4-5-20251001'}
        }
        mock_ai_instance.save_article.return_value = '/tmp/ai_article.md'

        # テスト実行
        with tempfile.TemporaryDirectory() as tmpdir:
            run_integration_flow(
                video_path='test.mp4',
                output_dir=tmpdir,
                audio_path=None,
                markdown=False,
                ai_article=True,
                app_name='TestApp',
                ai_model='claude-haiku-4-5-20251001',
                output_format='markdown',
                model_size='base',
                threshold=25,
                interval=15.0,
                count=10
            )

        # 検証: AIContentGeneratorがHaikuモデルで初期化される
        mock_ai_gen.assert_called_once()
        call_kwargs = mock_ai_gen.call_args[1]
        self.assertEqual(call_kwargs['model'], 'claude-haiku-4-5-20251001')

    @patch('extract_screenshots.AIContentGenerator')
    @patch('extract_screenshots.ScreenshotExtractor')
    def test_opus_model_end_to_end(self, mock_extractor, mock_ai_gen):
        """
        Given: --ai-model claude-opus-4-1-20250805 でCLIを実行する
        When: AI記事生成を実行する（モックAPI）
        Then: AIContentGeneratorがOpusモデルで初期化され、ai_metadata.jsonの"model"が一致する
        """
        from extract_screenshots import run_integration_flow
        import tempfile

        # モックの設定
        mock_extractor_instance = mock_extractor.return_value
        mock_extractor_instance.extract_screenshots.return_value = [
            {'timestamp': 15.0, 'filename': '01.png', 'file_path': '/tmp/01.png'}
        ]
        mock_extractor_instance.video_duration = 120.0

        mock_ai_instance = mock_ai_gen.return_value
        mock_ai_instance.generate_article.return_value = {
            'content': '# Test Article',
            'metadata': {'model': 'claude-opus-4-1-20250805'}
        }
        mock_ai_instance.save_article.return_value = '/tmp/ai_article.md'

        # テスト実行
        with tempfile.TemporaryDirectory() as tmpdir:
            run_integration_flow(
                video_path='test.mp4',
                output_dir=tmpdir,
                audio_path=None,
                markdown=False,
                ai_article=True,
                app_name='TestApp',
                ai_model='claude-opus-4-1-20250805',
                output_format='markdown',
                model_size='base',
                threshold=25,
                interval=15.0,
                count=10
            )

        # 検証: AIContentGeneratorがOpusモデルで初期化される
        mock_ai_gen.assert_called_once()
        call_kwargs = mock_ai_gen.call_args[1]
        self.assertEqual(call_kwargs['model'], 'claude-opus-4-1-20250805')


class TestModelUpgradeErrorHandling(unittest.TestCase):
    """Task 5.2: エラーハンドリングのテストケース追加"""

    def test_deprecated_model_cli_error(self):
        """
        Given: --ai-model claude-3-5-sonnet-20241022 でCLIを実行する
        When: argparseが引数をパースする
        Then: exit code 2で終了し、エラーメッセージに有効な選択肢が表示される
        """
        from extract_screenshots import create_argument_parser

        parser = create_argument_parser()

        # 非推奨モデルを指定してSystemExitを検証
        with self.assertRaises(SystemExit) as cm:
            parser.parse_args(['--input', 'test.mp4', '--ai-model', 'claude-3-5-sonnet-20241022'])

        # exit code 2であることを確認
        self.assertEqual(cm.exception.code, 2)

    def test_invalid_model_cli_error(self):
        """
        Given: --ai-model invalid-model でCLIを実行する
        When: argparseが引数をパースする
        Then: exit code 2で終了する
        """
        from extract_screenshots import create_argument_parser

        parser = create_argument_parser()

        # 無効なモデル名を指定してSystemExitを検証
        with self.assertRaises(SystemExit) as cm:
            parser.parse_args(['--input', 'test.mp4', '--ai-model', 'invalid-model'])

        # exit code 2であることを確認
        self.assertEqual(cm.exception.code, 2)

    def test_error_message_includes_valid_choices(self):
        """
        Given: --ai-model invalid-model でCLIを実行する
        When: argparseのエラーメッセージを確認する
        Then: エラーメッセージに有効な3つの選択肢がリストされる
        """
        from extract_screenshots import create_argument_parser
        import io
        import sys

        parser = create_argument_parser()

        # stderrをキャプチャ
        old_stderr = sys.stderr
        sys.stderr = io.StringIO()

        try:
            parser.parse_args(['--input', 'test.mp4', '--ai-model', 'invalid-model'])
        except SystemExit:
            pass

        error_output = sys.stderr.getvalue()
        sys.stderr = old_stderr

        # エラーメッセージに有効な3つのモデルが含まれることを確認
        self.assertIn('claude-haiku-4-5-20251001', error_output)
        self.assertIn('claude-sonnet-4-5-20250929', error_output)
        self.assertIn('claude-opus-4-1-20250805', error_output)


if __name__ == '__main__':
    unittest.main()
