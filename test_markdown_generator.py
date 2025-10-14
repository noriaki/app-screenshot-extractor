#!/usr/bin/env python3
"""
MarkdownGenerator のテストスイート
Task 3: Markdown記事生成機能のテスト
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from unittest.mock import patch
import io


class TestMarkdownGeneratorFormatTimestamp(unittest.TestCase):
    """MarkdownGenerator.format_timestamp() のテスト (Task 3.2)"""

    def test_format_timestamp_converts_seconds_to_mm_ss(self):
        """秒数をMM:SS形式に変換する"""
        # Given: 秒数 75.0 (= 1分15秒)
        from extract_screenshots import MarkdownGenerator
        generator = MarkdownGenerator(output_dir="output")

        # When: format_timestampを実行
        result = generator.format_timestamp(75.0)

        # Then: "01:15" を返す
        self.assertEqual(result, "01:15")

    def test_format_timestamp_zero_seconds(self):
        """0秒の場合は00:00を返す"""
        # Given: 秒数 0.0
        from extract_screenshots import MarkdownGenerator
        generator = MarkdownGenerator(output_dir="output")

        # When: format_timestampを実行
        result = generator.format_timestamp(0.0)

        # Then: "00:00" を返す
        self.assertEqual(result, "00:00")

    def test_format_timestamp_boundary_60_seconds(self):
        """60秒ちょうどの場合は01:00を返す"""
        # Given: 秒数 60.0
        from extract_screenshots import MarkdownGenerator
        generator = MarkdownGenerator(output_dir="output")

        # When: format_timestampを実行
        result = generator.format_timestamp(60.0)

        # Then: "01:00" を返す
        self.assertEqual(result, "01:00")

    def test_format_timestamp_over_one_hour(self):
        """1時間以上の場合も正しくフォーマットする"""
        # Given: 秒数 3661.0 (= 61分1秒)
        from extract_screenshots import MarkdownGenerator
        generator = MarkdownGenerator(output_dir="output")

        # When: format_timestampを実行
        result = generator.format_timestamp(3661.0)

        # Then: "61:01" を返す
        self.assertEqual(result, "61:01")

    def test_format_timestamp_with_decimal_seconds(self):
        """小数点以下を含む秒数の場合は切り捨てる"""
        # Given: 秒数 75.7
        from extract_screenshots import MarkdownGenerator
        generator = MarkdownGenerator(output_dir="output")

        # When: format_timestampを実行
        result = generator.format_timestamp(75.7)

        # Then: "01:15" を返す（小数点以下切り捨て）
        self.assertEqual(result, "01:15")


class TestMarkdownGeneratorFormatDescription(unittest.TestCase):
    """MarkdownGenerator.format_description() のテスト (Task 3.3)"""

    def test_format_description_returns_text_when_transcript_exists(self):
        """transcriptがある場合はテキストをそのまま返す"""
        # Given: 音声テキストを含むtranscript
        from extract_screenshots import MarkdownGenerator
        generator = MarkdownGenerator(output_dir="output")
        transcript = {
            'start': 10.0,
            'end': 15.0,
            'text': 'アプリを起動すると、ログイン画面が表示されます。'
        }

        # When: format_descriptionを実行
        result = generator.format_description(transcript)

        # Then: テキストをそのまま返す
        self.assertEqual(result, 'アプリを起動すると、ログイン画面が表示されます。')

    def test_format_description_returns_placeholder_when_transcript_is_none(self):
        """transcriptがNoneの場合は"(説明文なし)"を返す"""
        # Given: transcript = None
        from extract_screenshots import MarkdownGenerator
        generator = MarkdownGenerator(output_dir="output")
        transcript = None

        # When: format_descriptionを実行
        result = generator.format_description(transcript)

        # Then: プレースホルダーを返す
        self.assertEqual(result, "(説明文なし)")

    def test_format_description_handles_empty_text(self):
        """transcriptのtextが空文字列の場合はそのまま返す"""
        # Given: 空のテキストを含むtranscript
        from extract_screenshots import MarkdownGenerator
        generator = MarkdownGenerator(output_dir="output")
        transcript = {
            'start': 10.0,
            'end': 15.0,
            'text': ''
        }

        # When: format_descriptionを実行
        result = generator.format_description(transcript)

        # Then: 空文字列を返す
        self.assertEqual(result, '')


class TestMarkdownGeneratorFormatSectionTitle(unittest.TestCase):
    """MarkdownGenerator.format_section_title() のテスト (Task 3.2)"""

    def test_format_section_title_with_transcript(self):
        """音声テキストから短いタイトルを抽出する"""
        # Given: スクリーンショットとtranscript
        from extract_screenshots import MarkdownGenerator
        generator = MarkdownGenerator(output_dir="output")
        screenshot = {'timestamp': 75.0}
        transcript = {
            'start': 73.0,
            'end': 78.0,
            'text': 'アプリを起動すると、ログイン画面が表示されます。'
        }

        # When: format_section_titleを実行
        result = generator.format_section_title(screenshot, transcript)

        # Then: タイムスタンプと短いタイトルを含む見出しを返す（最大20文字）
        self.assertTrue(result.startswith("## 01:15"))
        # タイトル部分は最大20文字
        title_part = result.split(" - ", 1)[1] if " - " in result else ""
        self.assertLessEqual(len(title_part), 20)

    def test_format_section_title_without_transcript(self):
        """transcriptがNoneの場合のフォールバック処理"""
        # Given: スクリーンショットのみ（transcript=None）
        from extract_screenshots import MarkdownGenerator
        generator = MarkdownGenerator(output_dir="output")
        screenshot = {'timestamp': 75.0}
        transcript = None

        # When: format_section_titleを実行
        result = generator.format_section_title(screenshot, transcript)

        # Then: タイムスタンプとプレースホルダーを含む見出しを返す
        self.assertEqual(result, "## 01:15 - (説明文なし)")

    def test_format_section_title_truncates_long_text(self):
        """音声テキストが長い場合は20文字に制限する"""
        # Given: 長い音声テキスト
        from extract_screenshots import MarkdownGenerator
        generator = MarkdownGenerator(output_dir="output")
        screenshot = {'timestamp': 30.0}
        transcript = {
            'start': 28.0,
            'end': 32.0,
            'text': 'これは非常に長いテキストで、20文字を超える内容が含まれています。'
        }

        # When: format_section_titleを実行
        result = generator.format_section_title(screenshot, transcript)

        # Then: タイトル部分が20文字以内
        title_part = result.split(" - ", 1)[1] if " - " in result else ""
        self.assertLessEqual(len(title_part), 20)


class TestMarkdownGeneratorGenerate(unittest.TestCase):
    """MarkdownGenerator.generate() のテスト (Task 3.1)"""

    def test_generate_creates_markdown_with_title(self):
        """H1見出しで記事タイトルを配置する"""
        # Given: 同期済みデータ
        from extract_screenshots import MarkdownGenerator
        generator = MarkdownGenerator(output_dir="output", title="アプリ紹介")
        synchronized_data = [
            {
                'screenshot': {'timestamp': 15.0, 'filename': '01_00-15_score87.png'},
                'transcript': {'start': 13.0, 'end': 17.0, 'text': 'ログイン画面'},
                'matched': True
            }
        ]

        # When: generateを実行
        result = generator.generate(synchronized_data)

        # Then: H1見出しが含まれる
        self.assertIn("# アプリ紹介", result)

    def test_generate_creates_sections_with_h2_headings(self):
        """各スクリーンショットをH2見出しで区切る"""
        # Given: 複数のスクリーンショットを含む同期済みデータ
        from extract_screenshots import MarkdownGenerator
        generator = MarkdownGenerator(output_dir="output")
        synchronized_data = [
            {
                'screenshot': {'timestamp': 15.0, 'filename': '01_00-15_score87.png'},
                'transcript': {'start': 13.0, 'end': 17.0, 'text': 'ログイン画面'},
                'matched': True
            },
            {
                'screenshot': {'timestamp': 30.0, 'filename': '02_00-30_score92.png'},
                'transcript': {'start': 28.0, 'end': 32.0, 'text': 'ホーム画面'},
                'matched': True
            }
        ]

        # When: generateを実行
        result = generator.generate(synchronized_data)

        # Then: H2見出しが2つ含まれる
        self.assertEqual(result.count("## "), 2)
        self.assertIn("## 00:15", result)
        self.assertIn("## 00:30", result)

    def test_generate_includes_image_links_with_relative_paths(self):
        """画像リンクを相対パスで挿入する"""
        # Given: 同期済みデータ
        from extract_screenshots import MarkdownGenerator
        generator = MarkdownGenerator(output_dir="output")
        synchronized_data = [
            {
                'screenshot': {'timestamp': 15.0, 'filename': '01_00-15_score87.png'},
                'transcript': {'start': 13.0, 'end': 17.0, 'text': 'ログイン画面'},
                'matched': True
            }
        ]

        # When: generateを実行
        result = generator.generate(synchronized_data)

        # Then: 相対パスの画像リンクが含まれる
        self.assertIn("![Screenshot](screenshots/01_00-15_score87.png)", result)

    def test_generate_places_transcript_text_below_images(self):
        """音声テキストを画像の下に配置する"""
        # Given: 同期済みデータ（ユニークなテキストを使用）
        from extract_screenshots import MarkdownGenerator
        generator = MarkdownGenerator(output_dir="output")
        synchronized_data = [
            {
                'screenshot': {'timestamp': 15.0, 'filename': '01_00-15_score87.png'},
                'transcript': {'start': 13.0, 'end': 17.0, 'text': '短いテキスト'},
                'matched': True
            }
        ]

        # When: generateを実行
        result = generator.generate(synchronized_data)

        # Then: H2見出し、画像リンク、説明文の順序を確認
        # 見出しの後に画像があり、画像の後に説明文がある
        heading_index = result.index("## ")
        image_index = result.index("![Screenshot]")
        # 説明文は画像リンクの後に配置される（見出しのタイトルとは別の出現）
        description_section = result.split("![Screenshot]", 1)[1]
        self.assertIn("短いテキスト", description_section)

    def test_generate_handles_unmatched_screenshots(self):
        """音声テキストがない場合はプレースホルダーを配置する"""
        # Given: マッチングしないスクリーンショット
        from extract_screenshots import MarkdownGenerator
        generator = MarkdownGenerator(output_dir="output")
        synchronized_data = [
            {
                'screenshot': {'timestamp': 15.0, 'filename': '01_00-15_score87.png'},
                'transcript': None,
                'matched': False
            }
        ]

        # When: generateを実行
        result = generator.generate(synchronized_data)

        # Then: プレースホルダーが配置される
        self.assertIn("(説明文なし)", result)

    def test_generate_creates_standard_markdown_format(self):
        """標準的なMarkdown形式を使用する"""
        # Given: 同期済みデータ
        from extract_screenshots import MarkdownGenerator
        generator = MarkdownGenerator(output_dir="output")
        synchronized_data = [
            {
                'screenshot': {'timestamp': 15.0, 'filename': '01_00-15_score87.png'},
                'transcript': {'start': 13.0, 'end': 17.0, 'text': 'ログイン画面'},
                'matched': True
            }
        ]

        # When: generateを実行
        result = generator.generate(synchronized_data)

        # Then: 標準的なMarkdown記法を使用
        # H1見出し
        self.assertRegex(result, r'^# .+', msg="H1見出しが含まれていない")
        # H2見出し
        self.assertIn("## ", result)
        # 画像リンク
        self.assertRegex(result, r'!\[Screenshot\]\(.+\)', msg="画像リンクの形式が正しくない")


class TestMarkdownGeneratorSave(unittest.TestCase):
    """MarkdownGenerator.save() のテスト (Task 3.4)"""

    def setUp(self):
        """各テスト前に一時ディレクトリを作成"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """各テスト後に一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir)

    def test_save_creates_markdown_file(self):
        """Markdownファイルを保存する"""
        # Given: Markdownコンテンツ
        from extract_screenshots import MarkdownGenerator
        generator = MarkdownGenerator(output_dir=self.temp_dir)
        markdown_content = "# テスト記事\n\n## セクション1\n\nテキスト"

        # When: saveを実行
        result_path = generator.save(markdown_content)

        # Then: ファイルが作成される
        self.assertTrue(result_path.exists())
        self.assertEqual(result_path.name, "article.md")

    def test_save_uses_utf8_encoding(self):
        """UTF-8エンコーディングでファイルを保存する"""
        # Given: 日本語を含むMarkdownコンテンツ
        from extract_screenshots import MarkdownGenerator
        generator = MarkdownGenerator(output_dir=self.temp_dir)
        markdown_content = "# アプリ紹介\n\n日本語テキスト"

        # When: saveを実行
        result_path = generator.save(markdown_content)

        # Then: UTF-8で読み込める
        with open(result_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, markdown_content)

    def test_save_warns_on_overwrite(self):
        """既存ファイルがある場合は上書き警告を表示する"""
        # Given: 既存のMarkdownファイル
        from extract_screenshots import MarkdownGenerator
        generator = MarkdownGenerator(output_dir=self.temp_dir)
        existing_file = Path(self.temp_dir) / "article.md"
        existing_file.write_text("既存の内容", encoding='utf-8')

        markdown_content = "# 新しい記事"

        # When/Then: 上書き警告が標準出力に表示される
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            result_path = generator.save(markdown_content)
            output = mock_stdout.getvalue()
            self.assertIn("Warning", output)
            self.assertIn("already exists", output)

        # ファイルが上書きされる
        with open(result_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, "# 新しい記事")

    def test_save_creates_output_directory_if_not_exists(self):
        """出力ディレクトリが存在しない場合は作成する"""
        # Given: 存在しないディレクトリパス
        from extract_screenshots import MarkdownGenerator
        non_existent_dir = Path(self.temp_dir) / "nested" / "output"
        generator = MarkdownGenerator(output_dir=str(non_existent_dir))
        markdown_content = "# テスト"

        # When: saveを実行
        result_path = generator.save(markdown_content)

        # Then: ディレクトリが作成され、ファイルが保存される
        self.assertTrue(result_path.parent.exists())
        self.assertTrue(result_path.exists())

    def test_save_custom_filename(self):
        """カスタムファイル名を指定できる"""
        # Given: カスタムファイル名
        from extract_screenshots import MarkdownGenerator
        generator = MarkdownGenerator(output_dir=self.temp_dir)
        markdown_content = "# テスト記事"

        # When: saveを実行（カスタムファイル名）
        result_path = generator.save(markdown_content, filename="custom.md")

        # Then: 指定したファイル名で保存される
        self.assertEqual(result_path.name, "custom.md")
        self.assertTrue(result_path.exists())


class TestMarkdownGeneratorDisplayStatistics(unittest.TestCase):
    """MarkdownGenerator.display_statistics() のテスト (Task 3.4)"""

    def test_display_statistics_shows_image_count(self):
        """画像数を表示する"""
        # Given: 同期済みデータ
        from extract_screenshots import MarkdownGenerator
        generator = MarkdownGenerator(output_dir="output")
        synchronized_data = [
            {'screenshot': {}, 'transcript': {}, 'matched': True},
            {'screenshot': {}, 'transcript': {}, 'matched': True},
            {'screenshot': {}, 'transcript': None, 'matched': False}
        ]

        # When/Then: 標準出力に画像数が表示される
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            generator.display_statistics(synchronized_data)
            output = mock_stdout.getvalue()
            self.assertIn("3", output)  # 総画像数
            self.assertRegex(output, r'(?i)(images?|screenshots?|画像)')

    def test_display_statistics_shows_matching_success_count(self):
        """マッチング成功数を表示する"""
        # Given: 同期済みデータ
        from extract_screenshots import MarkdownGenerator
        generator = MarkdownGenerator(output_dir="output")
        synchronized_data = [
            {'screenshot': {}, 'transcript': {}, 'matched': True},
            {'screenshot': {}, 'transcript': {}, 'matched': True},
            {'screenshot': {}, 'transcript': None, 'matched': False}
        ]

        # When/Then: 標準出力にマッチング成功数が表示される
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            generator.display_statistics(synchronized_data)
            output = mock_stdout.getvalue()
            self.assertIn("2", output)  # マッチング成功数
            self.assertRegex(output, r'(?i)(matched|success|成功)')

    def test_display_statistics_shows_matching_failure_count(self):
        """マッチング失敗数を表示する"""
        # Given: 同期済みデータ
        from extract_screenshots import MarkdownGenerator
        generator = MarkdownGenerator(output_dir="output")
        synchronized_data = [
            {'screenshot': {}, 'transcript': {}, 'matched': True},
            {'screenshot': {}, 'transcript': None, 'matched': False},
            {'screenshot': {}, 'transcript': None, 'matched': False}
        ]

        # When/Then: 標準出力にマッチング失敗数が表示される
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            generator.display_statistics(synchronized_data)
            output = mock_stdout.getvalue()
            self.assertIn("2", output)  # マッチング失敗数
            self.assertRegex(output, r'(?i)(unmatched|failed?|失敗)')

    def test_display_statistics_handles_empty_data(self):
        """空のデータの場合も正しく表示する"""
        # Given: 空の同期済みデータ
        from extract_screenshots import MarkdownGenerator
        generator = MarkdownGenerator(output_dir="output")
        synchronized_data = []

        # When/Then: 標準出力に0件と表示される
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            generator.display_statistics(synchronized_data)
            output = mock_stdout.getvalue()
            self.assertIn("0", output)


class TestMarkdownGeneratorInitialization(unittest.TestCase):
    """MarkdownGenerator の初期化テスト"""

    def test_init_default_title(self):
        """デフォルトのタイトルが"アプリ紹介"であることを確認する"""
        # Given/When: MarkdownGeneratorをデフォルト引数で初期化
        from extract_screenshots import MarkdownGenerator
        generator = MarkdownGenerator(output_dir="output")

        # Then: タイトルが"アプリ紹介"
        self.assertEqual(generator.title, "アプリ紹介")

    def test_init_custom_title(self):
        """カスタムタイトルを設定できることを確認する"""
        # Given/When: MarkdownGeneratorをカスタムタイトルで初期化
        from extract_screenshots import MarkdownGenerator
        generator = MarkdownGenerator(output_dir="output", title="マイアプリ")

        # Then: タイトルが"マイアプリ"
        self.assertEqual(generator.title, "マイアプリ")

    def test_init_sets_output_dir(self):
        """出力ディレクトリが正しく設定されることを確認する"""
        # Given/When: MarkdownGeneratorを初期化
        from extract_screenshots import MarkdownGenerator
        generator = MarkdownGenerator(output_dir="/path/to/output")

        # Then: output_dirが設定される
        self.assertEqual(str(generator.output_dir), "/path/to/output")


if __name__ == '__main__':
    unittest.main()
