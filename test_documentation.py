#!/usr/bin/env python3
"""
Documentation Validation Test Suite
Task 7: ドキュメント整備の検証

このテストは、ドキュメントの完全性と一貫性を確認します。
"""

import json
import os
from pathlib import Path


def test_readme_has_audio_markdown_section():
    """README.mdに音声・Markdown統合機能のセクションが存在するか確認"""
    readme_path = Path(__file__).parent / "README.md"
    assert readme_path.exists(), "README.md が存在しません"

    content = readme_path.read_text(encoding='utf-8')

    # 音声・Markdown機能のセクションが存在することを確認
    assert "音声" in content or "audio" in content, "音声機能の説明がありません"
    assert "Markdown" in content, "Markdown機能の説明がありません"
    assert "--audio" in content, "--audioオプションの説明がありません"
    assert "--markdown" in content, "--markdownオプションの説明がありません"

    print("✓ README.mdに音声・Markdown統合機能のセクションが存在します")


def test_readme_has_command_examples():
    """README.mdにコマンドライン実行例が3パターン以上あるか確認"""
    readme_path = Path(__file__).parent / "README.md"
    content = readme_path.read_text(encoding='utf-8')

    # コマンド例のパターンをカウント
    command_patterns = [
        "--audio",  # 音声あり
        "python extract_screenshots.py",  # 基本コマンド
    ]

    # 最低3つの実行例があることを確認
    command_count = content.count("python extract_screenshots.py")
    assert command_count >= 3, f"コマンド実行例が不足しています（現在: {command_count}, 必要: 3以上）"

    print(f"✓ README.mdにコマンドライン実行例が{command_count}個存在します")


def test_readme_has_output_file_descriptions():
    """README.mdに出力ファイル（transcript.json, article.md）の説明があるか確認"""
    readme_path = Path(__file__).parent / "README.md"
    content = readme_path.read_text(encoding='utf-8')

    assert "transcript.json" in content, "transcript.jsonの説明がありません"
    assert "article.md" in content, "article.mdの説明がありません"

    print("✓ README.mdに出力ファイル（transcript.json, article.md）の説明が存在します")


def test_requirements_has_openai_whisper():
    """requirements.txtにopenai-whisperが含まれているか確認"""
    requirements_path = Path(__file__).parent / "requirements.txt"
    assert requirements_path.exists(), "requirements.txt が存在しません"

    content = requirements_path.read_text(encoding='utf-8')
    assert "openai-whisper" in content, "openai-whisperがrequirements.txtに追加されていません"

    print("✓ requirements.txtにopenai-whisperが含まれています")


def test_changelog_exists():
    """CHANGELOG.mdが存在するか確認"""
    changelog_path = Path(__file__).parent / "CHANGELOG.md"
    assert changelog_path.exists(), "CHANGELOG.md が存在しません"

    print("✓ CHANGELOG.mdが存在します")


def test_changelog_has_version_info():
    """CHANGELOG.mdにv2.0.0のバージョン情報が記載されているか確認"""
    changelog_path = Path(__file__).parent / "CHANGELOG.md"
    content = changelog_path.read_text(encoding='utf-8')

    assert "2.0.0" in content, "v2.0.0のバージョン情報がありません"
    assert "音声" in content or "audio" in content, "音声機能の変更内容がありません"
    assert "Markdown" in content, "Markdown機能の変更内容がありません"

    print("✓ CHANGELOG.mdにv2.0.0のバージョン情報が記載されています")


def test_changelog_has_feature_list():
    """CHANGELOG.mdに新機能一覧が記載されているか確認"""
    changelog_path = Path(__file__).parent / "CHANGELOG.md"
    content = changelog_path.read_text(encoding='utf-8')

    # 主要な新機能がリストされていることを確認
    features = [
        "音声認識",
        "Markdown",
        "タイムスタンプ",
    ]

    missing_features = [f for f in features if f not in content]
    assert len(missing_features) == 0, f"以下の新機能の説明がありません: {', '.join(missing_features)}"

    print("✓ CHANGELOG.mdに新機能一覧が記載されています")


def test_documentation_consistency():
    """すべてのドキュメントが一貫性を持っているか確認"""
    readme_path = Path(__file__).parent / "README.md"
    changelog_path = Path(__file__).parent / "CHANGELOG.md"

    readme_content = readme_path.read_text(encoding='utf-8')
    changelog_content = changelog_path.read_text(encoding='utf-8')

    # バージョン番号の一貫性を確認
    assert "v2.0.0" in readme_content or "2.0.0" in readme_content, "README.mdにバージョン情報がありません"
    assert "2.0.0" in changelog_content, "CHANGELOG.mdにバージョン情報がありません"

    print("✓ すべてのドキュメントが一貫性を持っています")


def test_all_docs_in_japanese():
    """すべてのドキュメントが日本語で記載されているか確認（プロジェクトガイドラインに従う）"""
    readme_path = Path(__file__).parent / "README.md"
    changelog_path = Path(__file__).parent / "CHANGELOG.md"

    # 日本語文字が含まれていることを確認（簡易チェック）
    readme_content = readme_path.read_text(encoding='utf-8')
    changelog_content = changelog_path.read_text(encoding='utf-8')

    def has_japanese(text):
        """日本語文字が含まれているか確認"""
        return any('\u3040' <= c <= '\u309F' or '\u30A0' <= c <= '\u30FF' or '\u4E00' <= c <= '\u9FFF' for c in text)

    assert has_japanese(readme_content), "README.mdに日本語が含まれていません"
    assert has_japanese(changelog_content), "CHANGELOG.mdに日本語が含まれていません"

    print("✓ すべてのドキュメントが日本語で記載されています")


def run_all_tests():
    """すべてのテストを実行"""
    tests = [
        test_readme_has_audio_markdown_section,
        test_readme_has_command_examples,
        test_readme_has_output_file_descriptions,
        test_requirements_has_openai_whisper,
        test_changelog_exists,
        test_changelog_has_version_info,
        test_changelog_has_feature_list,
        test_documentation_consistency,
        test_all_docs_in_japanese,
    ]

    print("\n" + "="*60)
    print("Documentation Validation Test Suite")
    print("="*60 + "\n")

    failed_tests = []

    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"✗ {test.__name__}: {e}")
            failed_tests.append((test.__name__, str(e)))
        except Exception as e:
            print(f"✗ {test.__name__}: Unexpected error: {e}")
            failed_tests.append((test.__name__, f"Unexpected error: {e}"))

    print("\n" + "="*60)
    if failed_tests:
        print(f"Failed: {len(failed_tests)}/{len(tests)} tests")
        print("="*60)
        for test_name, error in failed_tests:
            print(f"\n  {test_name}:")
            print(f"    {error}")
        return False
    else:
        print(f"Success: All {len(tests)} tests passed!")
        print("="*60)
        return True


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
