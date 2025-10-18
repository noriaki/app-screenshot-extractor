"""
PromptTemplateManager クラスのユニットテスト

テスト対象:
- プロンプトテンプレートの外部ファイル読み込み
- 音声あり/なし用の2種類テンプレート管理
- デフォルトテンプレートのフォールバック
- str.format()による変数置換
- 必須変数の検証
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, mock_open
from prompt_template_manager import PromptTemplateManager


class TestPromptTemplateManager(unittest.TestCase):
    """PromptTemplateManager クラスのテストケース"""

    def setUp(self):
        """各テストの前に実行される準備処理"""
        # 一時ディレクトリを作成
        self.test_dir = tempfile.mkdtemp()
        self.prompts_dir = Path(self.test_dir) / "prompts"
        self.prompts_dir.mkdir()

    def tearDown(self):
        """各テストの後に実行されるクリーンアップ処理"""
        # 一時ディレクトリを削除
        shutil.rmtree(self.test_dir)

    def test_load_template_with_audio_exists(self):
        """
        音声あり用テンプレート（article_with_audio.txt）が存在する場合、
        正常に読み込めることを確認する
        """
        # Given: 音声あり用テンプレートファイルを作成
        template_content = "あなたは{app_name}の魅力を伝える技術ライターです。\n{total_screenshots}枚のスクリーンショットを分析してください。"
        template_path = self.prompts_dir / "article_with_audio.txt"
        template_path.write_text(template_content, encoding="utf-8")

        # When: PromptTemplateManagerでテンプレートを読み込む
        manager = PromptTemplateManager(template_dir=str(self.prompts_dir))
        loaded_template = manager.load_template("article_with_audio.txt")

        # Then: ファイルの内容がそのまま読み込まれる
        self.assertEqual(loaded_template, template_content)

    def test_load_template_without_audio_exists(self):
        """
        音声なし用テンプレート（article_without_audio.txt）が存在する場合、
        正常に読み込めることを確認する
        """
        # Given: 音声なし用テンプレートファイルを作成
        template_content = "あなたは{app_name}の魅力を伝える技術ライターです。\n音声解説はありません。"
        template_path = self.prompts_dir / "article_without_audio.txt"
        template_path.write_text(template_content, encoding="utf-8")

        # When: PromptTemplateManagerでテンプレートを読み込む
        manager = PromptTemplateManager(template_dir=str(self.prompts_dir))
        loaded_template = manager.load_template("article_without_audio.txt")

        # Then: ファイルの内容がそのまま読み込まれる
        self.assertEqual(loaded_template, template_content)

    def test_load_template_not_exists(self):
        """
        テンプレートファイルが存在しない場合、
        デフォルトテンプレートを使用し、警告ログを出力することを確認する
        """
        # Given: テンプレートファイルが存在しない
        manager = PromptTemplateManager(template_dir=str(self.prompts_dir))

        # When: 存在しないテンプレートファイルを読み込もうとする
        with patch('builtins.print') as mock_print:
            loaded_template = manager.load_template("article_with_audio.txt")

        # Then: デフォルトテンプレートが返却され、警告が表示される
        self.assertIsNotNone(loaded_template)
        self.assertIn("app_name", loaded_template)
        self.assertIn("total_screenshots", loaded_template)
        # 警告ログが出力されている
        mock_print.assert_called()
        warning_message = str(mock_print.call_args)
        self.assertIn("警告", warning_message)

    def test_render_success(self):
        """
        str.format()による変数置換が正しく動作することを確認する
        """
        # Given: 変数プレースホルダーを含むテンプレート
        template = "あなたは{app_name}のライターです。{total_screenshots}枚の画像を分析してください。"
        variables = {
            "app_name": "MyApp",
            "total_screenshots": 10
        }

        # When: renderメソッドで変数を置換
        manager = PromptTemplateManager()
        rendered = manager.render(template, variables)

        # Then: 変数が正しく置換される
        expected = "あなたはMyAppのライターです。10枚の画像を分析してください。"
        self.assertEqual(rendered, expected)

    def test_render_missing_variable(self):
        """
        必須変数が欠落している場合、KeyErrorが発生することを確認する
        """
        # Given: 変数プレースホルダーを含むテンプレート
        template = "あなたは{app_name}のライターです。{total_screenshots}枚の画像を分析してください。"
        # 必須変数 app_name が欠落
        variables = {
            "total_screenshots": 10
        }

        # When/Then: renderメソッドでKeyErrorが発生する
        manager = PromptTemplateManager()
        with self.assertRaises(KeyError):
            manager.render(template, variables)

    def test_get_default_template_with_audio(self):
        """
        音声あり用デフォルトテンプレートの内容が正しいことを確認する
        """
        # When: 音声あり用デフォルトテンプレートを取得
        manager = PromptTemplateManager()
        default_template = manager.get_default_template(with_audio=True)

        # Then: テンプレートに必須要素が含まれている
        self.assertIsNotNone(default_template)
        self.assertIn("{app_name}", default_template)
        self.assertIn("{total_screenshots}", default_template)
        # 音声あり用の特徴的な文言
        self.assertIn("音声解説", default_template)

    def test_get_default_template_without_audio(self):
        """
        音声なし用デフォルトテンプレートの内容が正しいことを確認する
        """
        # When: 音声なし用デフォルトテンプレートを取得
        manager = PromptTemplateManager()
        default_template = manager.get_default_template(with_audio=False)

        # Then: テンプレートに必須要素が含まれている
        self.assertIsNotNone(default_template)
        self.assertIn("{app_name}", default_template)
        self.assertIn("{total_screenshots}", default_template)
        # 音声なし用の特徴的な文言
        self.assertIn("音声解説はありません", default_template)

    def test_template_caching(self):
        """
        同じテンプレートを複数回読み込んだ場合、キャッシュが使用されることを確認する
        """
        # Given: テンプレートファイルを作成
        template_content = "Test template with {app_name}"
        template_path = self.prompts_dir / "article_with_audio.txt"
        template_path.write_text(template_content, encoding="utf-8")

        manager = PromptTemplateManager(template_dir=str(self.prompts_dir))

        # When: 同じテンプレートを2回読み込む
        first_load = manager.load_template("article_with_audio.txt")

        # ファイルを変更してもキャッシュが返される
        template_path.write_text("Modified content", encoding="utf-8")
        second_load = manager.load_template("article_with_audio.txt")

        # Then: キャッシュされた同じ内容が返される
        self.assertEqual(first_load, second_load)
        self.assertEqual(first_load, template_content)

    def test_render_with_extra_variables(self):
        """
        テンプレートに存在しない変数が渡された場合でも、
        正常に動作することを確認する（未使用の変数は無視される）
        """
        # Given: 2つの変数プレースホルダーを含むテンプレート
        template = "App: {app_name}, Screenshots: {total_screenshots}"
        # 追加の変数を含む
        variables = {
            "app_name": "MyApp",
            "total_screenshots": 5,
            "extra_variable": "unused"
        }

        # When: renderメソッドで変数を置換
        manager = PromptTemplateManager()
        rendered = manager.render(template, variables)

        # Then: 使用される変数のみ置換され、エラーは発生しない
        expected = "App: MyApp, Screenshots: 5"
        self.assertEqual(rendered, expected)


if __name__ == '__main__':
    unittest.main()
