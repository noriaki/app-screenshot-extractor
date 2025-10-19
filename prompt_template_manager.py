"""
PromptTemplateManager - プロンプトテンプレート管理クラス

外部ファイルからプロンプトテンプレートを読み込み、
str.format()による変数置換を行う。
音声あり用・音声なし用の2種類のテンプレートを管理し、
テンプレートが存在しない場合はデフォルトテンプレートを使用する。
"""

from typing import Dict, Optional, Any
from pathlib import Path


class PromptTemplateManager:
    """
    プロンプトテンプレートを管理し、str.format()で変数置換を行う

    Attributes:
        template_dir: テンプレートファイル格納ディレクトリ
        _template_cache: テンプレートキャッシュ（ファイル名 -> テンプレート文字列）
    """

    def __init__(self, template_dir: str = "prompts") -> None:
        """
        Args:
            template_dir: テンプレートファイル格納ディレクトリ
        """
        self.template_dir = Path(template_dir)
        self._template_cache: Dict[str, str] = {}

    def load_template(self, template_name: str) -> str:
        """
        外部ファイルからテンプレートを読み込み

        Args:
            template_name: テンプレートファイル名
                - "article_with_audio.txt": 音声文字起こしがある場合
                - "article_without_audio.txt": 音声文字起こしがない場合

        Returns:
            テンプレート文字列（プレーンテキスト、{変数名}形式）

        Raises:
            FileNotFoundError: ファイルが存在しない場合（警告ログ後デフォルト返却）
        """
        # キャッシュをチェック
        if template_name in self._template_cache:
            return self._template_cache[template_name]

        # テンプレートファイルパス
        template_path = self.template_dir / template_name

        # ファイルが存在するか確認
        if template_path.exists():
            # ファイルから読み込み
            template = template_path.read_text(encoding="utf-8")
            # キャッシュに保存
            self._template_cache[template_name] = template
            return template
        else:
            # ファイルが存在しない場合は警告を表示し、デフォルトを使用
            print(f"⚠️  警告: テンプレートファイル '{template_path}' が見つかりません。デフォルトテンプレートを使用します。")

            # テンプレート名から音声あり/なしを判定
            with_audio = "with_audio" in template_name
            default_template = self.get_default_template(with_audio=with_audio)

            # デフォルトテンプレートをキャッシュに保存
            self._template_cache[template_name] = default_template
            return default_template

    def render(self, template: str, variables: Dict[str, Any]) -> str:
        """
        テンプレートに変数を適用してレンダリング（str.format()使用）

        Args:
            template: プレーンテキストテンプレート文字列
            variables: 置換変数辞書
                {
                    "app_name": str,
                    "total_screenshots": int,
                    ...
                }

        Returns:
            レンダリング済みプロンプトテキスト

        Raises:
            KeyError: 必須変数が欠落している場合
        """
        # str.format()で変数を置換
        # KeyErrorは自動的に発生するため、明示的な検証は不要
        return template.format(**variables)

    def get_default_template(self, with_audio: bool = True) -> str:
        """
        デフォルトプロンプトテンプレートを返却（フォールバック用）

        Args:
            with_audio: 音声文字起こしあり用のテンプレートを返すか

        Returns:
            デフォルトテンプレート文字列
        """
        if with_audio:
            # 音声あり用デフォルトテンプレート
            return """あなたは{app_name}の魅力を伝える技術ライターです。

以下の{total_screenshots}枚のスクリーンショット画像を分析してください。
各スクリーンショットには音声解説のテキストが付与されています。画像の視覚情報と音声解説を統合して、アプリの機能と価値提案を分析してください。

## タスク
1. 各画像のUI特徴と機能を分析する
2. 音声解説から開発者の意図やアプリの価値提案を抽出する
3. 読者がワクワクする文章で、ストーリー性のある記事を構成する

## 記事構成
- H1: 魅力的なタイトル（アプリ名を含む）
- H2: 論理的なセクション区切り（導入 → 機能紹介 → まとめの流れ）
- 各スクリーンショットに対してコンテキストに沿った説明文を生成
- 技術仕様ではなくユーザー体験と利点に焦点を当てる

## 出力形式
Markdown形式で出力してください。画像リンクは `![説明](screenshots/ファイル名.png)` 形式で記述してください。
"""
        else:
            # 音声なし用デフォルトテンプレート
            return """あなたは{app_name}の魅力を伝える技術ライターです。

以下の{total_screenshots}枚のスクリーンショット画像を分析してください。
音声解説はありません。画像の視覚情報のみから、UIの特徴と機能を推測して記事を作成してください。

## タスク
1. 各画像のUI要素と機能を分析する
2. 画像から機能の目的を推測する
3. 読者がワクワクする文章で、ストーリー性のある記事を構成する

## 記事構成
- H1: 魅力的なタイトル（アプリ名を含む）
- H2: 論理的なセクション区切り（導入 → 機能紹介 → まとめの流れ）
- 各スクリーンショットに対してコンテキストに沿った説明文を生成
- 技術仕様ではなくユーザー体験と利点に焦点を当てる

## 出力形式
Markdown形式で出力してください。画像リンクは `![説明](screenshots/ファイル名.png)` 形式で記述してください。
"""
