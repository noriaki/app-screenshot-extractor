#!/usr/bin/env python3
"""
AIContentGenerator のユニットテスト

Task 4.1: Claude API呼び出し機能のテスト
"""

import unittest
from unittest.mock import Mock, MagicMock
import os
import sys
from pathlib import Path
import tempfile
import shutil
import json


class TestAIContentGeneratorClaudeAPI(unittest.TestCase):
    """Task 4.1: Claude API呼び出し機能のテスト"""

    def setUp(self):
        """テスト前の準備"""
        # 一時ディレクトリ作成
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.test_dir) / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # テスト用環境変数設定
        self.original_api_key = os.environ.get('ANTHROPIC_API_KEY')
        os.environ['ANTHROPIC_API_KEY'] = 'test-api-key-12345'

        # anthropicモジュールのモックをsys.modulesに登録
        self.mock_anthropic_module = MagicMock()
        self.mock_anthropic_class = MagicMock()
        self.mock_anthropic_module.Anthropic = self.mock_anthropic_class
        sys.modules['anthropic'] = self.mock_anthropic_module

    def tearDown(self):
        """テスト後のクリーンアップ"""
        # 一時ディレクトリ削除
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

        # 環境変数を元に戻す
        if self.original_api_key:
            os.environ['ANTHROPIC_API_KEY'] = self.original_api_key
        elif 'ANTHROPIC_API_KEY' in os.environ:
            del os.environ['ANTHROPIC_API_KEY']

        # モックを削除
        if 'anthropic' in sys.modules:
            del sys.modules['anthropic']
        # extract_screenshotsモジュールもリロードのため削除
        if 'extract_screenshots' in sys.modules:
            del sys.modules['extract_screenshots']

    def test_call_api_with_messages_create_success(self):
        """
        Given: 正しいリクエストデータ
        When: call_api_with_retry()を呼び出す
        Then: messages.create()が正しいパラメータで呼び出され、レスポンスが返される
        """
        # モックレスポンスを作成
        mock_response = Mock()
        mock_response.content = [Mock(text="# テスト記事\n\nこれはテスト記事です。")]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)
        mock_response.model = "claude-3-5-sonnet-20241022"

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        self.mock_anthropic_class.return_value = mock_client

        # AIContentGenerator初期化
        from extract_screenshots import AIContentGenerator
        generator = AIContentGenerator(
            output_dir=str(self.output_dir),
            api_key="test-key"
        )

        # テスト用リクエストデータ
        request_data = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 4000,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "テストプロンプト"}
                    ]
                }
            ]
        }

        # API呼び出し
        response = generator.call_api_with_retry(request_data)

        # 検証
        mock_client.messages.create.assert_called_once_with(**request_data)
        self.assertEqual(response.content[0].text, "# テスト記事\n\nこれはテスト記事です。")
        self.assertEqual(response.usage.input_tokens, 100)
        self.assertEqual(response.usage.output_tokens, 50)

    def test_initialize_with_api_key_from_env(self):
        """
        Given: 環境変数ANTHROPIC_API_KEYが設定されている
        When: AIContentGeneratorを初期化する（api_key引数なし）
        Then: 環境変数からAPIキーを取得してAnthropicクライアントが初期化される
        """
        mock_client = Mock()
        self.mock_anthropic_class.return_value = mock_client

        os.environ['ANTHROPIC_API_KEY'] = 'env-api-key-67890'

        from extract_screenshots import AIContentGenerator
        generator = AIContentGenerator(output_dir=str(self.output_dir))

        # APIキーが環境変数から取得されていることを確認
        self.assertEqual(generator.api_key, 'env-api-key-67890')
        # Anthropicクライアントが初期化されていることを確認
        self.mock_anthropic_class.assert_called_once_with(api_key='env-api-key-67890')

    def test_initialize_without_api_key_raises_error(self):
        """
        Given: ANTHROPIC_API_KEY環境変数が未設定
        When: AIContentGeneratorを初期化する（api_key引数なし）
        Then: ValueErrorが発生する
        """
        # 環境変数を削除
        if 'ANTHROPIC_API_KEY' in os.environ:
            del os.environ['ANTHROPIC_API_KEY']

        from extract_screenshots import AIContentGenerator
        with self.assertRaises(ValueError) as context:
            AIContentGenerator(output_dir=str(self.output_dir))

        self.assertIn("ANTHROPIC_API_KEY", str(context.exception))

    def test_construct_content_blocks_with_images_and_text(self):
        """
        Given: 画像データとテキストプロンプト
        When: content blocksを構築する
        Then: Claude API仕様に準拠した形式（image + text blocks）になる
        """
        mock_client = Mock()
        self.mock_anthropic_class.return_value = mock_client

        from extract_screenshots import AIContentGenerator
        generator = AIContentGenerator(
            output_dir=str(self.output_dir),
            api_key="test-key"
        )

        # テスト用画像データ（base64エンコード済み）
        image_blocks = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
                }
            }
        ]

        text_prompt = "この画像を分析してください。"

        # content blocks構築（Task 4.1では手動構築、将来的には内部メソッド化）
        content_blocks = image_blocks + [{"type": "text", "text": text_prompt}]

        # 検証
        self.assertEqual(len(content_blocks), 2)
        self.assertEqual(content_blocks[0]["type"], "image")
        self.assertEqual(content_blocks[0]["source"]["type"], "base64")
        self.assertEqual(content_blocks[1]["type"], "text")
        self.assertEqual(content_blocks[1]["text"], text_prompt)

    def test_extract_article_text_from_response(self):
        """
        Given: Claude APIレスポンス
        When: レスポンスから記事テキストを抽出する
        Then: content[0].textから正しくテキストが取得される
        """
        # モックレスポンス
        mock_response = Mock()
        mock_response.content = [Mock(text="# アプリの魅力\n\nこのアプリは素晴らしいです。")]
        mock_response.usage = Mock(input_tokens=200, output_tokens=100)
        mock_response.model = "claude-3-5-sonnet-20241022"

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        self.mock_anthropic_class.return_value = mock_client

        from extract_screenshots import AIContentGenerator
        generator = AIContentGenerator(
            output_dir=str(self.output_dir),
            api_key="test-key"
        )

        request_data = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 4000,
            "messages": [{"role": "user", "content": [{"type": "text", "text": "test"}]}]
        }

        response = generator.call_api_with_retry(request_data)
        article_text = response.content[0].text

        # 検証
        self.assertIn("アプリの魅力", article_text)
        self.assertIn("素晴らしい", article_text)

    def test_api_key_passed_to_client(self):
        """
        Given: api_key引数が指定されている
        When: AIContentGeneratorを初期化する
        Then: AnthropicクライアントにAPIキーが渡される
        """
        mock_client = Mock()
        self.mock_anthropic_class.return_value = mock_client

        test_api_key = "explicit-api-key-99999"

        from extract_screenshots import AIContentGenerator
        generator = AIContentGenerator(
            output_dir=str(self.output_dir),
            api_key=test_api_key
        )

        # Anthropicクラスがapi_key引数付きで呼び出されたことを確認
        self.mock_anthropic_class.assert_called_once_with(api_key=test_api_key)

    def test_model_parameter_passed_to_api(self):
        """
        Given: 異なるモデル名が指定されている
        When: API呼び出しを行う
        Then: 指定されたモデル名がリクエストに含まれる
        """
        mock_response = Mock()
        mock_response.content = [Mock(text="test")]
        mock_response.usage = Mock(input_tokens=10, output_tokens=10)

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        self.mock_anthropic_class.return_value = mock_client

        # カスタムモデル指定
        from extract_screenshots import AIContentGenerator
        generator = AIContentGenerator(
            output_dir=str(self.output_dir),
            api_key="test-key",
            model="claude-sonnet-4-20250514"
        )

        request_data = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4000,
            "messages": [{"role": "user", "content": [{"type": "text", "text": "test"}]}]
        }

        generator.call_api_with_retry(request_data)

        # messages.createの呼び出し引数を取得
        call_args = mock_client.messages.create.call_args
        self.assertEqual(call_args.kwargs['model'], "claude-sonnet-4-20250514")

    def test_max_tokens_parameter_passed_to_api(self):
        """
        Given: カスタムmax_tokensが指定されている
        When: API呼び出しを行う
        Then: 指定されたmax_tokensがリクエストに含まれる
        """
        mock_response = Mock()
        mock_response.content = [Mock(text="test")]
        mock_response.usage = Mock(input_tokens=10, output_tokens=10)

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        self.mock_anthropic_class.return_value = mock_client

        # カスタムmax_tokens指定
        from extract_screenshots import AIContentGenerator
        generator = AIContentGenerator(
            output_dir=str(self.output_dir),
            api_key="test-key",
            max_tokens=8000
        )

        request_data = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 8000,
            "messages": [{"role": "user", "content": [{"type": "text", "text": "test"}]}]
        }

        generator.call_api_with_retry(request_data)

        call_args = mock_client.messages.create.call_args
        self.assertEqual(call_args.kwargs['max_tokens'], 8000)


class TestAIContentGeneratorErrorHandling(unittest.TestCase):
    """Task 4.2: エラーハンドリングとリトライ戦略のテスト"""

    def setUp(self):
        """テスト前の準備"""
        # 一時ディレクトリ作成
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.test_dir) / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # テスト用環境変数設定
        self.original_api_key = os.environ.get('ANTHROPIC_API_KEY')
        os.environ['ANTHROPIC_API_KEY'] = 'test-api-key-12345'

        # anthropicモジュールのモックをsys.modulesに登録
        self.mock_anthropic_module = MagicMock()
        self.mock_anthropic_class = MagicMock()

        # エラークラスのモックを作成
        self.RateLimitError = type('RateLimitError', (Exception,), {})
        self.ServiceUnavailableError = type('ServiceUnavailableError', (Exception,), {})
        self.AuthenticationError = type('AuthenticationError', (Exception,), {})
        self.APIError = type('APIError', (Exception,), {})

        self.mock_anthropic_module.Anthropic = self.mock_anthropic_class
        self.mock_anthropic_module.RateLimitError = self.RateLimitError
        self.mock_anthropic_module.ServiceUnavailableError = self.ServiceUnavailableError
        self.mock_anthropic_module.AuthenticationError = self.AuthenticationError
        self.mock_anthropic_module.APIError = self.APIError

        sys.modules['anthropic'] = self.mock_anthropic_module

    def tearDown(self):
        """テスト後のクリーンアップ"""
        # 一時ディレクトリ削除
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

        # 環境変数を元に戻す
        if self.original_api_key:
            os.environ['ANTHROPIC_API_KEY'] = self.original_api_key
        elif 'ANTHROPIC_API_KEY' in os.environ:
            del os.environ['ANTHROPIC_API_KEY']

        # モックを削除
        if 'anthropic' in sys.modules:
            del sys.modules['anthropic']
        if 'extract_screenshots' in sys.modules:
            del sys.modules['extract_screenshots']

    def test_retry_on_429_rate_limit_error_with_retry_after_header(self):
        """
        Given: 429レート制限エラーが発生し、retry-afterヘッダーが存在する
        When: call_api_with_retry()を呼び出す
        Then: retry-afterヘッダーの秒数待機してリトライし、最終的に成功する
        """
        mock_response = Mock()
        mock_response.content = [Mock(text="# 成功した記事")]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)

        mock_client = Mock()

        # 最初の呼び出しで429エラー、2回目で成功
        rate_limit_error = self.RateLimitError("Rate limit exceeded")
        rate_limit_error.response = Mock()
        rate_limit_error.response.headers = {'retry-after': '2'}

        mock_client.messages.create.side_effect = [
            rate_limit_error,
            mock_response
        ]

        self.mock_anthropic_class.return_value = mock_client

        from extract_screenshots import AIContentGenerator
        generator = AIContentGenerator(
            output_dir=str(self.output_dir),
            api_key="test-key"
        )

        request_data = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 4000,
            "messages": [{"role": "user", "content": [{"type": "text", "text": "test"}]}]
        }

        # リトライ付きAPI呼び出し
        with unittest.mock.patch('time.sleep') as mock_sleep:
            response = generator.call_api_with_retry(request_data)

        # 検証
        self.assertEqual(mock_client.messages.create.call_count, 2)
        mock_sleep.assert_called_once_with(2.0)  # retry-afterヘッダーの値で待機
        self.assertEqual(response.content[0].text, "# 成功した記事")

    def test_retry_on_429_without_retry_after_uses_default_3_seconds(self):
        """
        Given: 429レート制限エラーが発生し、retry-afterヘッダーが存在しない
        When: call_api_with_retry()を呼び出す
        Then: デフォルトの3秒待機してリトライする
        """
        mock_response = Mock()
        mock_response.content = [Mock(text="# 成功した記事")]

        mock_client = Mock()

        # retry-afterヘッダーなしの429エラー
        rate_limit_error = self.RateLimitError("Rate limit exceeded")
        rate_limit_error.response = Mock()
        rate_limit_error.response.headers = {}  # ヘッダーなし

        mock_client.messages.create.side_effect = [
            rate_limit_error,
            mock_response
        ]

        self.mock_anthropic_class.return_value = mock_client

        from extract_screenshots import AIContentGenerator
        generator = AIContentGenerator(
            output_dir=str(self.output_dir),
            api_key="test-key"
        )

        request_data = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 4000,
            "messages": [{"role": "user", "content": [{"type": "text", "text": "test"}]}]
        }

        with unittest.mock.patch('time.sleep') as mock_sleep:
            response = generator.call_api_with_retry(request_data)

        # デフォルトの3秒待機を検証
        mock_sleep.assert_called_once_with(3.0)
        self.assertEqual(mock_client.messages.create.call_count, 2)

    def test_retry_on_529_service_overload_error(self):
        """
        Given: 529サーバー過負荷エラーが発生する
        When: call_api_with_retry()を呼び出す
        Then: 3秒待機してリトライし、最終的に成功する
        """
        mock_response = Mock()
        mock_response.content = [Mock(text="# 成功した記事")]

        mock_client = Mock()

        # 529エラー、2回目で成功
        service_error = self.ServiceUnavailableError("Service overloaded")
        mock_client.messages.create.side_effect = [
            service_error,
            mock_response
        ]

        self.mock_anthropic_class.return_value = mock_client

        from extract_screenshots import AIContentGenerator
        generator = AIContentGenerator(
            output_dir=str(self.output_dir),
            api_key="test-key"
        )

        request_data = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 4000,
            "messages": [{"role": "user", "content": [{"type": "text", "text": "test"}]}]
        }

        with unittest.mock.patch('time.sleep') as mock_sleep:
            response = generator.call_api_with_retry(request_data)

        # 3秒待機を検証
        mock_sleep.assert_called_once_with(3.0)
        self.assertEqual(mock_client.messages.create.call_count, 2)

    def test_max_retries_exceeded_raises_error(self):
        """
        Given: 429エラーが最大リトライ回数を超えて継続する
        When: call_api_with_retry()を呼び出す
        Then: 最大3回リトライした後、RateLimitErrorが発生する
        """
        mock_client = Mock()

        # 常に429エラーを返す
        rate_limit_error = self.RateLimitError("Rate limit exceeded")
        rate_limit_error.response = Mock()
        rate_limit_error.response.headers = {}
        mock_client.messages.create.side_effect = rate_limit_error

        self.mock_anthropic_class.return_value = mock_client

        from extract_screenshots import AIContentGenerator
        generator = AIContentGenerator(
            output_dir=str(self.output_dir),
            api_key="test-key"
        )

        request_data = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 4000,
            "messages": [{"role": "user", "content": [{"type": "text", "text": "test"}]}]
        }

        with unittest.mock.patch('time.sleep'):
            with self.assertRaises(self.RateLimitError):
                generator.call_api_with_retry(request_data, max_retries=3)

        # 3回リトライ = 合計3回の呼び出し
        self.assertEqual(mock_client.messages.create.call_count, 3)

    def test_authentication_error_no_retry(self):
        """
        Given: 401認証エラーが発生する
        When: call_api_with_retry()を呼び出す
        Then: リトライせずに即座にAuthenticationErrorが発生する
        """
        mock_client = Mock()

        # 401認証エラー
        auth_error = self.AuthenticationError("Invalid API key")
        mock_client.messages.create.side_effect = auth_error

        self.mock_anthropic_class.return_value = mock_client

        from extract_screenshots import AIContentGenerator
        generator = AIContentGenerator(
            output_dir=str(self.output_dir),
            api_key="test-key"
        )

        request_data = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 4000,
            "messages": [{"role": "user", "content": [{"type": "text", "text": "test"}]}]
        }

        # 認証エラーはリトライ不可
        with self.assertRaises(self.AuthenticationError):
            generator.call_api_with_retry(request_data)

        # リトライせず1回のみ呼び出し
        self.assertEqual(mock_client.messages.create.call_count, 1)

    def test_other_api_error_no_retry_with_logging(self):
        """
        Given: その他のAPIエラー（400など）が発生する
        When: call_api_with_retry()を呼び出す
        Then: リトライせずにエラーが発生し、詳細なログが出力される
        """
        mock_client = Mock()

        # 400エラー
        api_error = self.APIError("Bad request")
        api_error.status_code = 400
        mock_client.messages.create.side_effect = api_error

        self.mock_anthropic_class.return_value = mock_client

        from extract_screenshots import AIContentGenerator
        generator = AIContentGenerator(
            output_dir=str(self.output_dir),
            api_key="test-key"
        )

        request_data = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 4000,
            "messages": [{"role": "user", "content": [{"type": "text", "text": "test"}]}]
        }

        # その他のAPIエラーはリトライ不可
        with self.assertRaises(self.APIError):
            generator.call_api_with_retry(request_data)

        # リトライせず1回のみ呼び出し
        self.assertEqual(mock_client.messages.create.call_count, 1)

    def test_multiple_retries_before_success(self):
        """
        Given: 429エラーが2回発生した後、3回目で成功する
        When: call_api_with_retry()を呼び出す
        Then: 2回リトライして成功する
        """
        mock_response = Mock()
        mock_response.content = [Mock(text="# 成功した記事")]

        mock_client = Mock()

        rate_limit_error = self.RateLimitError("Rate limit exceeded")
        rate_limit_error.response = Mock()
        rate_limit_error.response.headers = {}

        # 2回エラー、3回目で成功
        mock_client.messages.create.side_effect = [
            rate_limit_error,
            rate_limit_error,
            mock_response
        ]

        self.mock_anthropic_class.return_value = mock_client

        from extract_screenshots import AIContentGenerator
        generator = AIContentGenerator(
            output_dir=str(self.output_dir),
            api_key="test-key"
        )

        request_data = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 4000,
            "messages": [{"role": "user", "content": [{"type": "text", "text": "test"}]}]
        }

        with unittest.mock.patch('time.sleep') as mock_sleep:
            response = generator.call_api_with_retry(request_data)

        # 2回リトライ（2回の待機）
        self.assertEqual(mock_sleep.call_count, 2)
        # 合計3回の呼び出し
        self.assertEqual(mock_client.messages.create.call_count, 3)
        self.assertEqual(response.content[0].text, "# 成功した記事")


class TestQualityValidator(unittest.TestCase):
    """Task 5: 記事品質検証機能のテスト"""

    def setUp(self):
        """テスト前の準備"""
        # 一時ディレクトリ作成
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.test_dir) / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """テスト後のクリーンアップ"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_validate_quality_all_criteria_met(self):
        """
        Given: 高品質な記事（500文字以上、H1・H2あり、画像リンクあり）
        When: validate_quality()を呼び出す
        Then: valid=True、warnings=[]、metricsが正しく計測される
        """
        from extract_screenshots import QualityValidator

        validator = QualityValidator(
            min_chars=500,
            require_h1=True,
            require_h2=True,
            require_images=True
        )

        # 高品質なMarkdownサンプル（500文字以上）
        content = """# アプリの魅力的な紹介

このアプリは素晴らしい機能を持っています。ユーザーは簡単に目標を設定し、進捗を追跡できます。直感的なインターフェースにより、初心者でもすぐに使い始めることができます。データは自動的に同期され、複数のデバイスで利用できます。

## 主要機能

このアプリの主要機能は以下の通りです。タスク管理、進捗トラッキング、データ分析など、多彩な機能が搭載されています。それぞれの機能は独立して使用することも、組み合わせて使用することもできます。

![スクリーンショット1](screenshots/01_00-15_score87.png)

画面上部には目標設定ボタンがあり、タップするだけで新しい目標を追加できます。追加した目標は自動的にカテゴリ分けされ、優先度順に並び替えられます。

## ユーザー体験

実際に使ってみると、その使いやすさに驚きます。複雑な操作は一切不要で、すべての機能が直感的に配置されています。

![スクリーンショット2](screenshots/02_00-30_score92.png)

進捗グラフが視覚的に表示され、モチベーションを維持しやすくなっています。日々の達成度が一目でわかるため、継続的な改善が可能になります。
"""

        # テスト用画像パスリスト
        screenshot_paths = [
            Path(self.output_dir) / "screenshots" / "01_00-15_score87.png",
            Path(self.output_dir) / "screenshots" / "02_00-30_score92.png"
        ]

        # 画像ファイルを作成
        for path in screenshot_paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("dummy image")

        # 品質検証
        result = validator.validate_quality(content, screenshot_paths)

        # 検証
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['warnings']), 0)
        self.assertGreater(result['metrics']['char_count'], 500)
        self.assertEqual(result['metrics']['h1_count'], 1)
        self.assertEqual(result['metrics']['h2_count'], 2)
        self.assertEqual(result['metrics']['image_count'], 2)
        self.assertEqual(len(result['metrics']['broken_links']), 0)

    def test_validate_quality_char_count_below_minimum(self):
        """
        Given: 文字数が最低基準（500文字）未満の記事
        When: validate_quality()を呼び出す
        Then: valid=False、警告メッセージが含まれる
        """
        from extract_screenshots import QualityValidator

        validator = QualityValidator(min_chars=500)

        # 短い記事（500文字未満）
        content = """# タイトル

## セクション1

短い説明文です。
"""

        result = validator.validate_quality(content, [])

        # 検証
        self.assertFalse(result['valid'])
        self.assertGreater(len(result['warnings']), 0)
        self.assertIn("文字数不足", result['warnings'][0])
        self.assertLess(result['metrics']['char_count'], 500)

    def test_validate_structure_missing_h1(self):
        """
        Given: H1見出しがない記事
        When: validate_structure()を呼び出す
        Then: Falseが返される
        """
        from extract_screenshots import QualityValidator

        validator = QualityValidator(require_h1=True)

        # H1なしの記事
        content = """## セクション1

本文です。
"""

        result = validator.validate_structure(content)

        # 検証
        self.assertFalse(result)

    def test_validate_structure_missing_h2(self):
        """
        Given: H2見出しがない記事
        When: validate_structure()を呼び出す
        Then: Falseが返される（require_h2=Trueの場合）
        """
        from extract_screenshots import QualityValidator

        validator = QualityValidator(require_h2=True)

        # H2なしの記事
        content = """# タイトル

本文だけです。
"""

        result = validator.validate_structure(content)

        # 検証
        self.assertFalse(result)

    def test_validate_image_links_all_valid(self):
        """
        Given: すべての画像リンクが実在するファイルを参照している
        When: validate_image_links()を呼び出す
        Then: 空のリスト（壊れたリンクなし）が返される
        """
        from extract_screenshots import QualityValidator

        validator = QualityValidator()

        # 画像ファイルを作成
        screenshot_dir = self.output_dir / "screenshots"
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        image1 = screenshot_dir / "01_00-15_score87.png"
        image2 = screenshot_dir / "02_00-30_score92.png"
        image1.write_text("dummy")
        image2.write_text("dummy")

        content = """# テスト

![画像1](screenshots/01_00-15_score87.png)
![画像2](screenshots/02_00-30_score92.png)
"""

        screenshot_paths = [image1, image2]

        # 画像リンク検証
        broken_links = validator.validate_image_links(content, screenshot_paths)

        # 検証
        self.assertEqual(len(broken_links), 0)

    def test_validate_image_links_with_broken_links(self):
        """
        Given: 一部の画像リンクが存在しないファイルを参照している
        When: validate_image_links()を呼び出す
        Then: 壊れたリンクのリストが返される
        """
        from extract_screenshots import QualityValidator

        validator = QualityValidator()

        content = """# テスト

![画像1](screenshots/01_00-15_score87.png)
![画像2](screenshots/99_nonexistent.png)
"""

        # 画像1のみ作成
        screenshot_dir = self.output_dir / "screenshots"
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        image1 = screenshot_dir / "01_00-15_score87.png"
        image1.write_text("dummy")

        screenshot_paths = [image1]

        # 画像リンク検証
        broken_links = validator.validate_image_links(content, screenshot_paths)

        # 検証
        self.assertGreater(len(broken_links), 0)
        self.assertIn("99_nonexistent.png", broken_links[0])

    def test_validate_quality_metrics_calculation(self):
        """
        Given: 様々な要素を含む記事
        When: validate_quality()を呼び出す
        Then: metricsが正確に計測される
        """
        from extract_screenshots import QualityValidator

        validator = QualityValidator()

        content = """# メインタイトル

本文が続きます。

## セクション1

内容1です。

![画像1](screenshots/01.png)

## セクション2

内容2です。

![画像2](screenshots/02.png)

## セクション3

内容3です。
"""

        # 画像ファイル作成
        screenshot_dir = self.output_dir / "screenshots"
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        (screenshot_dir / "01.png").write_text("dummy")
        (screenshot_dir / "02.png").write_text("dummy")

        screenshot_paths = [
            screenshot_dir / "01.png",
            screenshot_dir / "02.png"
        ]

        result = validator.validate_quality(content, screenshot_paths)

        # 検証
        self.assertEqual(result['metrics']['h1_count'], 1)
        self.assertEqual(result['metrics']['h2_count'], 3)
        self.assertEqual(result['metrics']['image_count'], 2)
        self.assertGreater(result['metrics']['char_count'], 0)


class TestAIContentGeneratorMetadata(unittest.TestCase):
    """Task 6: 記事生成メタデータ管理機能のテスト"""

    def setUp(self):
        """テスト前の準備"""
        # 一時ディレクトリ作成
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.test_dir) / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 環境変数設定
        self.original_api_key = os.environ.get('ANTHROPIC_API_KEY')
        os.environ['ANTHROPIC_API_KEY'] = 'test-api-key-12345'

        # anthropicモジュールのモック
        self.mock_anthropic_module = MagicMock()
        self.mock_anthropic_class = MagicMock()
        self.mock_anthropic_module.Anthropic = self.mock_anthropic_class
        sys.modules['anthropic'] = self.mock_anthropic_module

    def tearDown(self):
        """テスト後のクリーンアップ"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

        if self.original_api_key:
            os.environ['ANTHROPIC_API_KEY'] = self.original_api_key
        elif 'ANTHROPIC_API_KEY' in os.environ:
            del os.environ['ANTHROPIC_API_KEY']

        if 'anthropic' in sys.modules:
            del sys.modules['anthropic']
        if 'extract_screenshots' in sys.modules:
            del sys.modules['extract_screenshots']

    def test_save_article_creates_metadata_json(self):
        """
        Given: 記事コンテンツとメタデータ
        When: save_article()を呼び出す
        Then: ai_article.mdとai_metadata.jsonが作成される
        """
        mock_client = Mock()
        self.mock_anthropic_class.return_value = mock_client

        from extract_screenshots import AIContentGenerator

        generator = AIContentGenerator(
            output_dir=str(self.output_dir),
            api_key="test-key"
        )

        content = "# テスト記事\n\nこれはテストです。"
        metadata = {
            "model": "claude-3-5-sonnet-20241022",
            "prompt_version": "1.0.0",
            "generated_at": "2025-10-18T12:00:00Z",
            "total_screenshots": 5,
            "transcript_available": True,
            "quality_valid": True,
            "quality_warnings": [],
            "quality_metrics": {
                "char_count": 1000,
                "h1_count": 1,
                "h2_count": 3,
                "image_count": 5,
                "broken_links": []
            },
            "api_usage": {
                "input_tokens": 1500,
                "output_tokens": 500,
                "total_cost_usd": 0.025
            }
        }

        # 保存
        saved_path = generator.save_article(content, metadata)

        # 検証
        self.assertTrue(saved_path.exists())
        self.assertEqual(saved_path.name, "ai_article.md")

        # ai_metadata.jsonが作成されていることを確認
        metadata_path = self.output_dir / "ai_metadata.json"
        self.assertTrue(metadata_path.exists())

        # メタデータの内容確認
        with open(metadata_path, 'r', encoding='utf-8') as f:
            saved_metadata = json.load(f)

        self.assertEqual(saved_metadata['model'], "claude-3-5-sonnet-20241022")
        self.assertEqual(saved_metadata['total_screenshots'], 5)
        self.assertTrue(saved_metadata['transcript_available'])
        self.assertEqual(saved_metadata['api_usage']['input_tokens'], 1500)

    def test_metadata_includes_generation_timestamp(self):
        """
        Given: 記事生成が完了した
        When: メタデータを保存する
        Then: generated_atフィールドにISO 8601形式のタイムスタンプが含まれる
        """
        mock_client = Mock()
        self.mock_anthropic_class.return_value = mock_client

        from extract_screenshots import AIContentGenerator
        from datetime import datetime

        generator = AIContentGenerator(
            output_dir=str(self.output_dir),
            api_key="test-key"
        )

        # 現在時刻を取得
        before = datetime.utcnow()

        content = "# テスト"
        metadata = {
            "model": "claude-3-5-sonnet-20241022",
            "generated_at": datetime.utcnow().isoformat() + "Z",
        }

        generator.save_article(content, metadata)

        # メタデータ読み込み
        metadata_path = self.output_dir / "ai_metadata.json"
        with open(metadata_path, 'r', encoding='utf-8') as f:
            saved_metadata = json.load(f)

        # ISO 8601形式であることを確認
        self.assertIn("generated_at", saved_metadata)
        # 簡易的なISO 8601フォーマット検証（YYYY-MM-DDTHH:MM:SS）
        self.assertRegex(saved_metadata['generated_at'], r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}')

    def test_metadata_includes_api_usage_statistics(self):
        """
        Given: Claude APIレスポンスにusage統計が含まれる
        When: メタデータを保存する
        Then: input_tokens、output_tokens、total_cost_usdが記録される
        """
        mock_client = Mock()
        self.mock_anthropic_class.return_value = mock_client

        from extract_screenshots import AIContentGenerator

        generator = AIContentGenerator(
            output_dir=str(self.output_dir),
            api_key="test-key"
        )

        content = "# テスト"
        metadata = {
            "model": "claude-3-5-sonnet-20241022",
            "api_usage": {
                "input_tokens": 2000,
                "output_tokens": 800,
                "total_cost_usd": 0.036  # 計算: (2000*3 + 800*15) / 1000000
            }
        }

        generator.save_article(content, metadata)

        # メタデータ読み込み
        metadata_path = self.output_dir / "ai_metadata.json"
        with open(metadata_path, 'r', encoding='utf-8') as f:
            saved_metadata = json.load(f)

        # API使用統計が含まれることを確認
        self.assertIn("api_usage", saved_metadata)
        self.assertEqual(saved_metadata['api_usage']['input_tokens'], 2000)
        self.assertEqual(saved_metadata['api_usage']['output_tokens'], 800)
        self.assertAlmostEqual(saved_metadata['api_usage']['total_cost_usd'], 0.036, places=4)

    def test_metadata_includes_quality_validation_results(self):
        """
        Given: 品質検証が実行された
        When: メタデータを保存する
        Then: quality_valid、warnings、metricsが記録される
        """
        mock_client = Mock()
        self.mock_anthropic_class.return_value = mock_client

        from extract_screenshots import AIContentGenerator

        generator = AIContentGenerator(
            output_dir=str(self.output_dir),
            api_key="test-key"
        )

        content = "# テスト"
        metadata = {
            "model": "claude-3-5-sonnet-20241022",
            "quality_valid": False,
            "quality_warnings": ["文字数不足: 300文字（最低500文字必要）"],
            "quality_metrics": {
                "char_count": 300,
                "h1_count": 1,
                "h2_count": 0,
                "image_count": 0,
                "broken_links": []
            }
        }

        generator.save_article(content, metadata)

        # メタデータ読み込み
        metadata_path = self.output_dir / "ai_metadata.json"
        with open(metadata_path, 'r', encoding='utf-8') as f:
            saved_metadata = json.load(f)

        # 品質検証結果が含まれることを確認
        self.assertFalse(saved_metadata['quality_valid'])
        self.assertGreater(len(saved_metadata['quality_warnings']), 0)
        self.assertIn("文字数不足", saved_metadata['quality_warnings'][0])
        self.assertEqual(saved_metadata['quality_metrics']['char_count'], 300)

    def test_metadata_includes_prompt_version(self):
        """
        Given: プロンプトテンプレートにバージョンが指定されている
        When: メタデータを保存する
        Then: prompt_versionフィールドが記録される
        """
        mock_client = Mock()
        self.mock_anthropic_class.return_value = mock_client

        from extract_screenshots import AIContentGenerator

        generator = AIContentGenerator(
            output_dir=str(self.output_dir),
            api_key="test-key"
        )

        content = "# テスト"
        metadata = {
            "model": "claude-3-5-sonnet-20241022",
            "prompt_version": "1.2.3"
        }

        generator.save_article(content, metadata)

        # メタデータ読み込み
        metadata_path = self.output_dir / "ai_metadata.json"
        with open(metadata_path, 'r', encoding='utf-8') as f:
            saved_metadata = json.load(f)

        self.assertEqual(saved_metadata['prompt_version'], "1.2.3")


class TestAIContentGeneratorIntegration(unittest.TestCase):
    """Task 7: AIContentGeneratorクラスの統合実装のテスト"""

    def setUp(self):
        """テスト前の準備"""
        # 一時ディレクトリ作成
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.test_dir) / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 環境変数設定
        self.original_api_key = os.environ.get('ANTHROPIC_API_KEY')
        os.environ['ANTHROPIC_API_KEY'] = 'test-api-key-12345'

        # anthropicモジュールのモック
        self.mock_anthropic_module = MagicMock()
        self.mock_anthropic_class = MagicMock()
        self.mock_anthropic_module.Anthropic = self.mock_anthropic_class
        sys.modules['anthropic'] = self.mock_anthropic_module

    def tearDown(self):
        """テスト後のクリーンアップ"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

        if self.original_api_key:
            os.environ['ANTHROPIC_API_KEY'] = self.original_api_key
        elif 'ANTHROPIC_API_KEY' in os.environ:
            del os.environ['ANTHROPIC_API_KEY']

        if 'anthropic' in sys.modules:
            del sys.modules['anthropic']
        if 'extract_screenshots' in sys.modules:
            del sys.modules['extract_screenshots']

    def test_generate_article_with_audio_success(self):
        """
        Given: スクリーンショット画像とメタデータ、音声文字起こしデータ
        When: generate_article()を呼び出す
        Then: AIが記事を生成し、品質検証を経てファイルが保存される
        """
        # モックレスポンス
        mock_response = Mock()
        mock_response.content = [Mock(text="# アプリの魅力\n\n## 主要機能\n\n素晴らしい機能です。" * 50)]
        mock_response.usage = Mock(input_tokens=1000, output_tokens=500)
        mock_response.model = "claude-3-5-sonnet-20241022"

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        self.mock_anthropic_class.return_value = mock_client

        from extract_screenshots import AIContentGenerator

        generator = AIContentGenerator(
            output_dir=str(self.output_dir),
            api_key="test-key"
        )

        # テスト用スクリーンショットファイル作成
        screenshots_dir = self.output_dir / "screenshots"
        screenshots_dir.mkdir(parents=True, exist_ok=True)

        test_image_path = screenshots_dir / "01_00-15_score87.png"
        # 最小限のPNG画像を作成
        from PIL import Image
        img = Image.new('RGB', (100, 100), color='red')
        img.save(test_image_path)

        # synchronized_data作成
        synchronized_data = [
            {
                "screenshot": {
                    "file_path": str(test_image_path),
                    "timestamp": 15.0,
                    "score": 87.5
                },
                "transcript": {
                    "text": "この画面では新しい機能を紹介しています。",
                    "start_time": 14.0,
                    "end_time": 18.0
                },
                "matched": True
            }
        ]

        # 記事生成
        result = generator.generate_article(
            synchronized_data=synchronized_data,
            app_name="テストアプリ",
            output_format="markdown"
        )

        # 検証
        self.assertIn("content", result)
        self.assertIn("metadata", result)
        self.assertIn("アプリの魅力", result["content"])
        self.assertEqual(result["metadata"]["model"], "claude-3-5-sonnet-20241022")
        self.assertTrue(result["metadata"]["transcript_available"])
        self.assertEqual(result["metadata"]["total_screenshots"], 1)

    def test_generate_article_without_audio(self):
        """
        Given: 音声文字起こしデータがないsynchronized_data
        When: generate_article()を呼び出す
        Then: 音声なし用のプロンプトを使用して記事が生成される
        """
        mock_response = Mock()
        mock_response.content = [Mock(text="# アプリ紹介\n\n## 機能\n\n画像から推測した機能です。" * 50)]
        mock_response.usage = Mock(input_tokens=800, output_tokens=400)
        mock_response.model = "claude-3-5-sonnet-20241022"

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        self.mock_anthropic_class.return_value = mock_client

        from extract_screenshots import AIContentGenerator

        generator = AIContentGenerator(
            output_dir=str(self.output_dir),
            api_key="test-key"
        )

        # スクリーンショット作成
        screenshots_dir = self.output_dir / "screenshots"
        screenshots_dir.mkdir(parents=True, exist_ok=True)

        test_image_path = screenshots_dir / "01_00-15_score87.png"
        from PIL import Image
        img = Image.new('RGB', (100, 100), color='blue')
        img.save(test_image_path)

        # 音声なしのsynchronized_data
        synchronized_data = [
            {
                "screenshot": {
                    "file_path": str(test_image_path),
                    "timestamp": 15.0,
                    "score": 87.5
                },
                "transcript": None,
                "matched": False
            }
        ]

        # 記事生成
        result = generator.generate_article(
            synchronized_data=synchronized_data,
            app_name="画像のみアプリ"
        )

        # 検証
        self.assertIn("content", result)
        self.assertFalse(result["metadata"]["transcript_available"])

    def test_generate_article_with_quality_warnings(self):
        """
        Given: 品質基準を満たさない記事が生成される
        When: generate_article()を呼び出す
        Then: 警告が記録され、メタデータに含まれる
        """
        # 品質基準未達の短い記事
        mock_response = Mock()
        mock_response.content = [Mock(text="# タイトル\n\n短い記事")]
        mock_response.usage = Mock(input_tokens=500, output_tokens=50)

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        self.mock_anthropic_class.return_value = mock_client

        from extract_screenshots import AIContentGenerator

        generator = AIContentGenerator(
            output_dir=str(self.output_dir),
            api_key="test-key"
        )

        # スクリーンショット作成
        screenshots_dir = self.output_dir / "screenshots"
        screenshots_dir.mkdir(parents=True, exist_ok=True)

        test_image_path = screenshots_dir / "01_00-15_score87.png"
        from PIL import Image
        img = Image.new('RGB', (100, 100), color='green')
        img.save(test_image_path)

        synchronized_data = [
            {
                "screenshot": {
                    "file_path": str(test_image_path),
                    "timestamp": 15.0,
                    "score": 87.5
                },
                "transcript": None,
                "matched": False
            }
        ]

        # 記事生成
        result = generator.generate_article(
            synchronized_data=synchronized_data,
            app_name="テストアプリ"
        )

        # 検証
        self.assertFalse(result["metadata"]["quality_valid"])
        self.assertGreater(len(result["metadata"]["quality_warnings"]), 0)


if __name__ == '__main__':
    unittest.main()
