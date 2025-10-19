# App Screenshot Extractor

アプリ操作動画から最適なスクリーンショットを自動抽出するPythonツールです。

音声データは使用せず、**映像データのみ**で以下を自動的に判定します：
- 画面遷移の検出
- 安定フレームの選択
- UI要素の重要度分析（OCR）
- 総合スコアリングによる最適な画像の選択

## 特徴

- **自動画面遷移検出**: Perceptual Hashingで画面の切り替わりを正確に検出
- **安定フレーム抽出**: アニメーション完了後の静止画面を自動選択
- **UI重要度分析**: EasyOCR（日本語・英語対応）でボタン、メニュー、タイトルを検出
- **統合スコアリング**: 複数の要素を組み合わせて最適な画像を選択
- **時間的重複排除**: 類似した画面を排除し、バラエティのある画像セットを生成
- **4K動画対応**: 元の解像度を維持しながら高速処理
- **Apple Silicon最適化**: M1/M2/M3/M4チップで効率的に動作
- **音声認識統合**: OpenAI Whisperで音声から自動的にテキストを抽出（日本語対応）
- **Markdown記事生成**: スクリーンショットと音声解説を統合した記事を自動生成
- **AI記事生成**: Claude APIによる高品質なアプリ紹介記事の自動生成（v2.1.0+）

## 必要な環境

- **OS**: macOS（Apple Silicon推奨）
- **Python**: 3.11以上
- **メモリ**: 8GB以上推奨（4K動画処理には16GB以上推奨）
- **ストレージ**: 空き容量 5GB以上（モデルダウンロード + 動画処理用）

## セットアップ手順

### 1. pyenvのインストール（未インストールの場合）

```bash
# Homebrewでpyenvをインストール
brew install pyenv

# シェルの設定ファイルに追加（例：~/.zshrc）
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc

# シェルを再起動
exec $SHELL
```

### 2. プロジェクトのセットアップ

```bash
# リポジトリをクローン（またはダウンロード）
cd ~/projects
git clone <repository-url>
cd app-screenshot-extractor

# Python 3.11.10をインストール
pyenv install 3.11.10

# プロジェクトディレクトリでPythonバージョンを設定
pyenv local 3.11.10

# 仮想環境を作成
python -m venv .venv

# 仮想環境を有効化
source .venv/bin/activate

# pipをアップグレード
pip install --upgrade pip

# 依存パッケージをインストール
pip install -r requirements.txt
```

**注意**: 初回実行時、EasyOCRが自動的にOCRモデル（約500MB）をダウンロードします。インターネット接続が必要です。

### 4. AI記事生成機能の環境設定（オプション、v2.1.0+）

AI記事生成機能を使用する場合は、Claude APIキーの設定が必要です。

```bash
# .env.exampleをコピー
cp .env.example .env

# .envファイルを編集してAPIキーを設定
# ANTHROPIC_API_KEY=your_api_key_here
```

Claude APIキーは[Anthropic Console](https://console.anthropic.com/settings/keys)から取得できます。

### 5. 動作確認

```bash
# ヘルプを表示
python extract_screenshots.py --help
```

## 使い方

### 基本的な使い方

```bash
# 仮想環境を有効化（新しいターミナルセッションの場合）
source .venv/bin/activate

# 動画から10枚のスクリーンショットを抽出
python extract_screenshots.py --input app_demo.mp4
```

### コマンドライン引数

| 引数 | 短縮形 | デフォルト | 説明 |
|------|--------|-----------|------|
| `--input` | `-i` | （必須） | 入力動画ファイルパス |
| `--output` | `-o` | `./output` | 出力ディレクトリ |
| `--count` | `-c` | `10` | 抽出する画像の枚数 |
| `--threshold` | `-t` | `25` | 画面遷移検出の閾値（大きいほど鈍感） |
| `--interval` | | `15` | スクリーンショット間の最小時間間隔（秒） |
| `--audio` | | なし | 音声ファイルパス（音声認識を有効化） |
| `--markdown` | | なし | Markdown記事を生成する |
| `--model-size` | | `base` | Whisperモデルサイズ（tiny, base, small, medium, large, turbo） |
| `--ai-article` | | なし | AI（Claude API）による高品質記事を生成（v2.1.0+） |
| `--app-name` | | 動画ファイル名 | アプリ名（AI記事生成用、v2.1.0+） |
| `--ai-model` | | `claude-sonnet-4-5-20250929` | 使用するClaudeモデル（v3.1.0+、haiku-4-5/sonnet-4-5/opus-4-1から選択） |
| `--output-format` | | `markdown` | AI記事の出力形式（markdown/html、v2.1.0+） |

### 使用例

#### 基本的なスクリーンショット抽出

```bash
# 15枚抽出（より多くの画像が必要な場合）
python extract_screenshots.py -i sample_app.mp4 -c 15

# 敏感に画面遷移を検出（閾値を下げる）
python extract_screenshots.py -i sample_app.mp4 -t 20

# カスタム出力先とより密な間隔
python extract_screenshots.py -i sample_app.mp4 -o ~/Documents/screenshots --interval 10

# すべてのオプションを組み合わせ
python extract_screenshots.py -i app_demo.mp4 -o ./results -c 12 -t 22 --interval 12
```

#### 音声・Markdown統合機能（v2.0.0+）

```bash
# パターン1: 音声認識とMarkdown記事生成（音声あり）
python extract_screenshots.py -i app_demo.mp4 --audio demo_audio.mp3 --markdown

# パターン2: Markdown記事生成のみ（音声なし、画像のみ）
python extract_screenshots.py -i app_demo.mp4 --markdown

# パターン3: 音声認識のみ（Markdown生成なし）
python extract_screenshots.py -i app_demo.mp4 --audio demo_audio.mp3

# Whisperモデルサイズを指定（高精度だが処理時間が増加）
python extract_screenshots.py -i app_demo.mp4 --audio demo_audio.mp3 --markdown --model-size small

# すべてのオプションを組み合わせ
python extract_screenshots.py -i app_demo.mp4 --audio demo_audio.mp3 --markdown -c 15 -o ./article --model-size base
```

#### AI記事生成機能（v2.1.0+）

```bash
# 音声あり + AI記事生成（推奨、デフォルトでSonnet 4.5を使用）
python extract_screenshots.py -i app_demo.mp4 --audio demo_audio.mp3 --ai-article --app-name "MyApp"

# 音声なし + AI記事生成（画像のみから推測）
python extract_screenshots.py -i app_demo.mp4 --ai-article --app-name "MyApp"

# 既存Markdown + AI記事の両方を生成
python extract_screenshots.py -i app_demo.mp4 --audio demo_audio.mp3 --markdown --ai-article

# モデル選択（v3.1.0+）
# Haiku 4.5: 高速・安価（コスト重視）
python extract_screenshots.py -i app_demo.mp4 --audio demo_audio.mp3 --ai-article --ai-model claude-haiku-4-5-20251001

# Sonnet 4.5: 安定・中庸（デフォルト、推奨）
python extract_screenshots.py -i app_demo.mp4 --audio demo_audio.mp3 --ai-article --ai-model claude-sonnet-4-5-20250929

# Opus 4.1: 高精度・高価（品質優先）
python extract_screenshots.py -i app_demo.mp4 --audio demo_audio.mp3 --ai-article --ai-model claude-opus-4-1-20250805
```

## テストの実行

プロジェクトには包括的なテストスイートが含まれています。

### すべてのテストを実行

```bash
# 仮想環境を有効化
source .venv/bin/activate

# すべてのテストを実行
python -m unittest discover -s . -p "test_*.py" -v
```

### テストスイート

| テストファイル | 説明 |
|--------------|------|
| `test_audio_processor.py` | AudioProcessorクラスの単体テスト（音声ファイル検証、音声認識、保存機能） |
| `test_timestamp_synchronizer.py` | TimestampSynchronizerクラスの単体テスト（最近傍検索、同期処理） |
| `test_markdown_generator.py` | MarkdownGeneratorクラスの単体テスト（Markdown生成、フォーマット、保存） |
| `test_ai_content_generator.py` | AIContentGeneratorクラスの単体テスト（Claude API呼び出し、モデル選択、品質検証） |
| `test_cli_integration.py` | CLI統合テスト（オプション解析、統合フロー、後方互換性、モデル選択） |
| `test_e2e_integration.py` | エンドツーエンドテスト（音声あり/なし、エラーケース） |
| `test_error_handling.py` | エラーハンドリングテスト（ファイル不在、フォーマット不正、ffmpeg不在） |
| `test_performance.py` | パフォーマンステスト（処理時間、メモリ使用量、スケーラビリティ） |
| `test_error_cases.py` | **手動テスト**: エラーケースの検証（非推奨モデル、無効なモデル名、ヘルプメッセージ） |
| `test_manual_e2e.py` | **手動テスト**: 実際のClaude APIでのE2Eテスト（3つのモデルで記事生成） |

### 特定のテストファイルを実行

```bash
# AudioProcessorのテストのみ実行
python -m unittest test_audio_processor -v

# TimestampSynchronizerのテストのみ実行
python -m unittest test_timestamp_synchronizer -v

# パフォーマンステストのみ実行
python -m unittest test_performance -v
```

### テスト実行例

```bash
$ python -m unittest discover -s . -p "test_*.py" -v
test_format_description_with_none (test_markdown_generator.TestMarkdownGenerator) ... ok
test_format_description_with_text (test_markdown_generator.TestMarkdownGenerator) ... ok
test_format_section_title_fallback (test_markdown_generator.TestMarkdownGenerator) ... ok
...
----------------------------------------------------------------------
Ran 199 tests in 5.254s

OK (skipped=2)
```

### 手動E2Eテストの実行

AIモデルアップグレードの動作確認のため、手動E2Eテストスクリプトが用意されています。

#### エラーケースのテスト

```bash
# 非推奨モデル・無効なモデル名のエラーメッセージを確認
python test_error_cases.py
```

このテストは以下を検証します:
- 非推奨モデル（`claude-3-5-sonnet-20241022`）指定時のエラーメッセージ
- 無効なモデル名指定時のエラーメッセージ
- ヘルプメッセージに各モデルの説明が含まれること

#### 実際のClaude APIでのテスト

**前提条件**:
- `ANTHROPIC_API_KEY` 環境変数が設定されていること
- サンプル動画ファイル（`sample_video/demo.mp4`）が存在すること

```bash
# 3つのモデル（Haiku、Sonnet、Opus）で実際にAI記事生成を実行
python test_manual_e2e.py
```

このテストは以下を検証します:
- Haiku 4.5モデルでのAI記事生成
- Sonnet 4.5モデル（デフォルト）でのAI記事生成
- Opus 4.1モデルでのAI記事生成
- 各モデルで `ai_metadata.json` に正しいモデル名が記録されること
- 品質メタデータが正常に記録されること

**注意**: このテストは実際にClaude APIを呼び出すため、APIクレジットを消費します。

## 出力形式

### ディレクトリ構造

```
output/
├── screenshots/
│   ├── 01_00-15_score87.png
│   ├── 02_00-32_score85.png
│   ├── 03_01-05_score82.png
│   └── ...
├── metadata.json
├── transcript.json       # 音声認識結果（--audioオプション使用時）
├── article.md           # 生成されたMarkdown記事（--markdownオプション使用時）
├── ai_article.md        # AI生成記事（--ai-articleオプション使用時、v2.1.0+）
└── ai_metadata.json     # AI生成メタデータ（--ai-articleオプション使用時、v2.1.0+）
```

### ファイル命名規則

スクリーンショットのファイル名: `{連番:02d}_{タイムスタンプ}_score{スコア}.png`

例: `01_00-15_score87.png`
- `01`: 連番（時系列順）
- `00-15`: タイムスタンプ（00分15秒）
- `score87`: 重要度スコア（87点）

### メタデータ（metadata.json）

```json
[
  {
    "index": 1,
    "filename": "01_00-15_score87.png",
    "timestamp": 15.3,
    "score": 87.5,
    "transition_magnitude": 35,
    "stability_score": 95.2,
    "ui_importance_score": 30,
    "ui_elements": [
      {"type": "button", "text": "ホーム", "confidence": 0.95},
      {"type": "title", "text": "メイン画面", "confidence": 0.92}
    ],
    "detected_texts": ["ホーム", "メニュー", "設定", "..."]
  }
]
```

### 音声認識結果（transcript.json）

`--audio`オプション使用時に生成されます。

```json
{
  "language": "ja",
  "duration": 125.3,
  "segments": [
    {
      "start": 0.0,
      "end": 3.5,
      "text": "アプリを起動すると、ログイン画面が表示されます。"
    },
    {
      "start": 3.5,
      "end": 7.8,
      "text": "ユーザー名とパスワードを入力してログインボタンをタップします。"
    }
  ]
}
```

**フィールド説明:**
- `language`: 認識された言語コード（ja: 日本語）
- `duration`: 音声ファイル全体の長さ（秒）
- `segments`: 音声セグメントのリスト
  - `start`: セグメント開始時刻（秒）
  - `end`: セグメント終了時刻（秒）
  - `text`: 認識されたテキスト内容

### Markdown記事（article.md）

`--markdown`オプション使用時に生成されます。

```markdown
# アプリ紹介

## 00:15 - ログイン画面

![Screenshot](screenshots/01_00-15_score87.png)

アプリを起動すると、ログイン画面が表示されます。

## 00:32 - ログイン処理

![Screenshot](screenshots/02_00-32_score92.png)

ユーザー名とパスワードを入力してログインボタンをタップします。

## 00:48 - (説明文なし)

![Screenshot](screenshots/03_00-48_score78.png)

(説明文なし)
```

**構造:**
- H1見出し: 記事タイトル
- H2見出し: タイムスタンプ（MM:SS形式）+ 音声テキストから抽出した短いタイトル
- 画像リンク: `![Screenshot](相対パス)`形式
- 説明文: 音声テキスト、または音声がない場合は"(説明文なし)"

### AI生成記事（ai_article.md）とメタデータ（v2.1.0+）

`--ai-article`オプション使用時に生成されます。

#### AI生成記事の特徴

- **マルチモーダル分析**: Claude APIがスクリーンショット画像と音声文字起こしを統合分析
- **高品質な文章**: 単なる羅列ではなく、読者が「使ってみたい」と思えるストーリー性のある記事
- **柔軟なカスタマイズ**: プロンプトテンプレートを編集することで記事の構成や文体を変更可能

#### AI生成記事の例

```markdown
# MyAppの魅力的な機能紹介

このアプリは、直感的なインターフェースと強力な機能を兼ね備えています。

## 主要機能

ログイン画面では、シンプルかつ洗練されたUIが特徴です。ユーザー名とパスワードの入力フィールドが明確に配置され、初めて使う方でも迷うことなく操作できます。

![スクリーンショット1](screenshots/01_00-15_score87.png)

セキュリティにも配慮されており、パスワードは自動的にマスクされます。

## 便利な操作性

メイン画面に移ると、豊富な機能が一目で分かるように整理されています...
```

#### AIメタデータ（ai_metadata.json）

AI記事生成のメタデータを記録します。

```json
{
  "model": "claude-sonnet-4-5-20250929",
  "prompt_version": "1.0.0",
  "generated_at": "2025-10-18T12:34:56Z",
  "total_screenshots": 10,
  "transcript_available": true,
  "quality_valid": true,
  "quality_warnings": [],
  "quality_metrics": {
    "char_count": 1250,
    "h1_count": 1,
    "h2_count": 4,
    "image_count": 10,
    "broken_links": []
  },
  "api_usage": {
    "input_tokens": 15234,
    "output_tokens": 1456,
    "total_cost_usd": 0.068
  }
}
```

**フィールド説明:**
- `model`: 使用したClaudeモデル名
- `prompt_version`: プロンプトテンプレートのバージョン
- `generated_at`: 記事生成日時（ISO 8601形式）
- `total_screenshots`: 入力されたスクリーンショット枚数
- `transcript_available`: 音声文字起こしデータの有無
- `quality_valid`: 品質検証結果（true/false）
- `quality_warnings`: 品質警告メッセージのリスト
- `quality_metrics`: 品質メトリクス（文字数、見出し数、画像数など）
- `api_usage`: Claude API使用統計（トークン数、コスト）

#### プロンプトテンプレートのカスタマイズ

AI記事の内容は`prompts/`ディレクトリのテンプレートファイルを編集することでカスタマイズできます。

**音声あり用テンプレート** (`prompts/article_with_audio.txt`):
```
あなたは{app_name}の魅力を伝える技術ライターです。

以下の{total_screenshots}枚のスクリーンショット画像を分析してください。
各スクリーンショットには音声解説のテキストが付与されています。

タスク:
1. 各画像のUI特徴と機能を分析する
2. 音声解説から開発者の意図やアプリの価値提案を抽出する
3. 読者がワクワクする文章で、ストーリー性のある記事を構成する

フォーマット: Markdown（H1タイトル、H2セクション、画像リンク）
```

**音声なし用テンプレート** (`prompts/article_without_audio.txt`):
```
あなたは{app_name}の魅力を伝える技術ライターです。

以下の{total_screenshots}枚のスクリーンショット画像を分析してください。
音声解説はありません。画像の視覚情報のみから、UIの特徴と機能を推測して記事を作成してください。

...
```

**変数:**
- `{app_name}`: アプリ名（`--app-name`オプションまたは動画ファイル名から自動設定）
- `{total_screenshots}`: スクリーンショット枚数（自動設定）

テンプレートを編集後、再度`--ai-article`オプションで実行すると、カスタマイズされたプロンプトで記事が生成されます。

### AIモデル選択ガイド（v3.1.0+）

AI記事生成では、用途に応じて3つのClaudeモデルから選択できます。

#### モデル比較表

| モデル | 速度 | 品質 | コスト（入力/出力 per MTok） | 推奨用途 |
|--------|------|------|------------------------------|----------|
| **Haiku 4.5**<br/>`claude-haiku-4-5-20251001` | 最速 | 標準 | $1 / $5 | コスト重視、大量処理、プロトタイプ作成 |
| **Sonnet 4.5**<br/>`claude-sonnet-4-5-20250929` | 中速 | 高品質 | $3 / $15 | バランス重視、ほとんどの用途（**デフォルト**） |
| **Opus 4.1**<br/>`claude-opus-4-1-20250805` | 低速 | 最高品質 | $15 / $75 | 品質最優先、公式ドキュメント、マーケティング資料 |

**価格例（10枚のスクリーンショットで記事生成した場合の概算）:**
- **Haiku 4.5**: 約 $0.10 - $0.15 per 記事
- **Sonnet 4.5**: 約 $0.30 - $0.50 per 記事（**デフォルト**）
- **Opus 4.1**: 約 $1.50 - $2.50 per 記事

#### モデル選択の判断基準

**Haiku 4.5を選ぶべき場合:**
- 大量の記事を一度に生成する必要がある
- プロトタイプや下書きの段階
- コストを最小限に抑えたい
- 生成速度を重視する

**Sonnet 4.5を選ぶべき場合（推奨）:**
- ほとんどのユースケースで最適なバランス
- 公開用の記事だが、予算も気にする
- 品質とコストのトレードオフを重視
- デフォルトで迷ったらこれを選択

**Opus 4.1を選ぶべき場合:**
- 公式ドキュメントやマーケティング資料など、最高品質が必要
- 詳細で説得力のある文章が求められる
- コストよりも品質を最優先する
- 複雑なUI分析や専門的な記事が必要

#### モデル移行ガイド（v3.0.0からv3.1.0へ）

**背景:**
- Claude 3.5 Sonnet (`claude-3-5-sonnet-20241022`) は2025年10月22日に廃止（Anthropic公式発表）
- 新しいClaude 4.5ファミリーへの移行が推奨されています

**自動移行:**

`--ai-model`オプションを指定していない場合、自動的にSonnet 4.5を使用します。コマンドの変更は不要です。

```bash
# v3.0.0でもv3.1.0でも同じコマンド
python extract_screenshots.py -i video.mp4 --ai-article
# → v3.1.0では自動的にclaude-sonnet-4-5-20250929を使用
```

**手動移行（スクリプトやCI/CD）:**

旧モデルを明示的に指定している場合は、以下のように更新してください。

| 旧モデル（v3.0.0） | 推奨移行先 | 特性 |
|-------------------|----------|------|
| `claude-3-5-sonnet-20241022` | `claude-sonnet-4-5-20250929` | 同等の品質・コストバランス（**推奨**） |
| `claude-3-5-sonnet-20241022` | `claude-haiku-4-5-20251001` | コスト削減（約1/3）、高速 |
| `claude-3-5-sonnet-20241022` | `claude-opus-4-1-20250805` | 品質優先、高コスト（5倍） |

```bash
# 変更前（v3.0.0）
python extract_screenshots.py -i video.mp4 --ai-article --ai-model claude-3-5-sonnet-20241022

# 変更後（v3.1.0、推奨）
python extract_screenshots.py -i video.mp4 --ai-article --ai-model claude-sonnet-4-5-20250929
```

**エラーメッセージ:**

旧モデルを指定すると、以下のエラーが表示されます。

```
extract_screenshots.py: error: argument --ai-model: invalid choice: 'claude-3-5-sonnet-20241022'
(choose from 'claude-haiku-4-5-20251001', 'claude-sonnet-4-5-20250929', 'claude-opus-4-1-20250805')
```

有効な3つのモデルから選択して再実行してください。

## 処理アルゴリズム

### 1. 画面遷移検出（Scene Transition Detection）

- Perceptual Hash (pHash) を使用して連続フレーム間の差分を計算
- ハミング距離が閾値（デフォルト: 25）を超えたら画面遷移と判定
- 処理高速化のため720pにダウンサンプルして計算

### 2. 安定フレーム検出（Stable Frame Detection）

- 画面遷移の0.5秒後から1.5秒後の範囲で探索
- 連続フレーム間の差分が最小のフレームを選択
- アニメーション完了後の静止画面を抽出

### 3. UI重要度分析（UI Importance Analysis）

EasyOCR（日本語・英語対応）でテキストを検出し、以下をスコアリング：

- 重要なボタン・メニュー項目: +15点
- タイトルバー・見出し: +20点
- テキスト量が多い（>5個）: +10点

### 4. 統合スコアリング

最終スコア = (遷移の大きさ × 2.0) + (安定性 × 0.5) + (UI重要度 × 1.5)

### 5. 時間的重複排除

- スコア上位から選択
- 既に選択された画像と15秒以上離れているもののみ追加
- 目標枚数に達するまで繰り返し

## パフォーマンス

### 処理時間の目安（Apple M4 Pro, 48GB RAM）

| 動画の長さ | 解像度 | 処理時間 |
|-----------|--------|---------|
| 1分 | 1080p | 約1分 |
| 5分 | 4K | 約5-7分 |
| 10分 | 4K | 約10-15分 |

処理時間は動画の複雑さ（画面遷移の頻度）によって変動します。

### メモリ使用量

- 4K動画: 約2-4GB
- 1080p動画: 約1-2GB

## トラブルシューティング

### エラー: `ModuleNotFoundError: No module named 'cv2'`

仮想環境が有効化されていない可能性があります。

```bash
source .venv/bin/activate
```

### エラー: `Video file not found`

入力ファイルパスが正しいか確認してください。相対パスまたは絶対パスを使用できます。

```bash
# 絶対パス
python extract_screenshots.py -i /Users/username/Videos/app_demo.mp4

# 相対パス
python extract_screenshots.py -i ./videos/app_demo.mp4
```

### エラー: `Cannot open video`

動画ファイルが破損しているか、対応していないフォーマットの可能性があります。

対応フォーマット: MP4, MOV, AVI, MKV など（OpenCV対応形式）

### スクリーンショットの枚数が目標より少ない

以下を試してください：

1. **閾値を下げる**: より敏感に画面遷移を検出
   ```bash
   python extract_screenshots.py -i video.mp4 -t 20
   ```

2. **最小時間間隔を短くする**: より密に画像を抽出
   ```bash
   python extract_screenshots.py -i video.mp4 --interval 10
   ```

3. **動画の内容を確認**: 画面遷移が少ない動画では抽出枚数が制限されます

### OCRモデルのダウンロードに失敗する

初回実行時、EasyOCRが自動的にモデルをダウンロードします。

- インターネット接続を確認
- ファイアウォール/プロキシ設定を確認
- 手動でモデルをダウンロード:
  ```bash
  python -c "import easyocr; reader = easyocr.Reader(['ja', 'en'])"
  ```

### Apple Silicon で動作が遅い

このツールはCPUモードで動作します（`gpu=False`）。これは意図的な設定で、Apple SiliconのCPUは十分高速です。

さらなる高速化:
- 動画の解像度を下げる（1080pなど）
- `--threshold` を大きくして処理フレーム数を減らす

### 音声認識が失敗する（v2.0.0+）

**エラー: `RuntimeError: ffmpeg not found`**

ffmpegがインストールされていない可能性があります。

```bash
# macOSの場合
brew install ffmpeg

# インストール確認
ffmpeg -version
```

**音声ファイルが認識されない**

サポートされている音声フォーマットを確認してください:
- 対応形式: mp3, mp4, mpeg, mpga, m4a, wav, webm

```bash
# ファイル形式を確認
file demo_audio.mp3
```

**日本語の認識精度が低い**

より高精度なモデルを使用してください:

```bash
# smallモデル（高精度）
python extract_screenshots.py -i video.mp4 --audio audio.mp3 --markdown --model-size small

# mediumモデル（さらに高精度）
python extract_screenshots.py -i video.mp4 --audio audio.mp3 --markdown --model-size medium
```

### 動画と音声の長さが合わない（v2.0.0+）

**警告: `Duration mismatch`**

動画と音声ファイルの長さが5秒以上異なる場合、警告が表示されますが処理は継続されます。

対処法:
1. 録音開始/停止のタイミングを揃えて再撮影
2. 動画編集ソフトで音声と動画の開始時刻を合わせる
3. 警告を無視して処理を継続（精度は低下する可能性があります）

### Markdown記事に説明文が含まれない

**症状: `(説明文なし)`が多数表示される**

原因:
- スクリーンショットのタイムスタンプと音声セグメントが5秒以上離れている
- 音声ファイルが短すぎる、または無音区間が多い

対処法:
1. 音声解説を密に録音する（画面遷移ごとに解説を入れる）
2. スクリーンショットの枚数を減らす（`-c`オプションで調整）
3. 閾値を調整して画面遷移の検出感度を変更（`-t`オプション）

### AI記事生成のトラブルシューティング（v2.1.0+）

**エラー: `ANTHROPIC_API_KEY環境変数が設定されていません`**

APIキーが未設定です。

```bash
# .envファイルを作成
cp .env.example .env

# エディタで.envを開いてAPIキーを設定
# ANTHROPIC_API_KEY=your_api_key_here
```

または、環境変数として直接設定:

```bash
export ANTHROPIC_API_KEY="your_api_key_here"
python extract_screenshots.py -i video.mp4 --ai-article
```

**エラー: `Claude API認証エラー`**

APIキーが無効、または期限切れです。

- [Anthropic Console](https://console.anthropic.com/settings/keys)でAPIキーを確認
- 新しいAPIキーを生成して `.env` ファイルを更新

**警告: `品質検証警告 - 文字数不足`**

生成された記事が品質基準（500文字以上）を満たしていません。

原因:
- スクリーンショット枚数が少ない
- 音声文字起こしデータが少ない

対処法:
1. スクリーンショット枚数を増やす（`-c`オプションで調整）
2. 音声解説をより詳細に録音する
3. プロンプトテンプレートをカスタマイズして詳細な記事を生成するよう指示

**エラー: `レート制限超過`**

Claude APIのレート制限に到達しました。

対処法:
1. 数分待ってから再実行
2. Anthropicアカウントのプランを確認（Free/Pro/Enterprise）
3. リトライは自動で行われます（最大3回）

**プロンプトテンプレートが見つからない警告**

`prompts/`ディレクトリまたはテンプレートファイルが存在しません。

```bash
# promptsディレクトリが存在することを確認
ls prompts/

# ファイルが存在しない場合はデフォルトテンプレートが使用されます（警告は無視可）
```

デフォルトテンプレートでも動作しますが、カスタマイズしたい場合は`prompts/`ディレクトリを作成してテンプレートファイルを配置してください。

## 音声・Markdown統合機能の詳細（v2.0.0+）

### 概要

動画ファイルと音声ファイルを統合し、スクリーンショットと音声解説を組み合わせたMarkdown記事を自動生成します。

### 処理フロー

1. **スクリーンショット抽出**: 既存の画面遷移検出アルゴリズムで最適な画像を選択
2. **音声認識**: OpenAI Whisperで音声からテキストを抽出（タイムスタンプ付き）
3. **タイムスタンプ同期**: スクリーンショットと音声セグメントを時間軸で自動対応付け
4. **Markdown生成**: 構造化された記事を自動生成（画像 + 説明文）

### 音声認識の仕組み

- **エンジン**: OpenAI Whisper（ローカル実行、プライバシー保護）
- **対応言語**: 日本語、英語（他の言語も対応可能）
- **モデルサイズ**:
  - `tiny`: 最速（約40MB、精度は低め）
  - `base`: バランス型（約140MB、デフォルト）
  - `small`: 高精度（約460MB）
  - `medium`: さらに高精度（約1.5GB）
  - `large`: 最高精度（約2.9GB、処理時間が長い）
  - `turbo`: 高速・高精度（約1.5GB、最新モデル）

### タイムスタンプ同期

- **アルゴリズム**: 最近傍マッチング（Nearest Neighbor Matching）
- **許容範囲**: 5秒以内で最も近い音声セグメントを選択
- **対応付け**: 各スクリーンショットに最大1つの音声セグメントを割り当て
- **未対応時**: 音声がない場合は"(説明文なし)"を表示

### ユースケース

1. **アプリ紹介記事の作成**
   - デモ動画と音声解説から即座に公開可能な記事を生成
   - 手動でのスクリーンショット配置とテキスト入力を大幅に削減

2. **ドキュメント作成の効率化**
   - 操作手順動画から構造化されたマニュアルを自動生成
   - タイムスタンプ付きで動画参照が容易

3. **プレゼンテーション資料作成**
   - アプリデモ動画から説得力のある資料を自動生成
   - Markdownから他の形式（HTML、PDF）への変換も可能

### 注意事項

- **初回実行時**: Whisperモデル（約140MB）が自動ダウンロードされます
- **処理時間**: 音声認識は音声長の約1/7の時間（baseモデル使用時）
- **メモリ使用量**: EasyOCR + Whisper同時ロード時で約3GB
- **動画・音声の同期**: 録音開始/停止のタイミングが5秒以上ずれている場合、警告が表示されます

## 技術スタック

### コア機能
- **opencv-python**: 動画処理とフレーム抽出
- **Pillow**: 画像処理
- **imagehash**: Perceptual Hashing（pHash）
- **EasyOCR**: OCR（日本語・英語対応）
- **numpy**: 数値計算
- **tqdm**: 進捗表示

### 音声・Markdown統合機能（v2.0.0+）
- **openai-whisper**: 音声認識エンジン（日本語対応）

### AI記事生成機能（v2.1.0+）
- **anthropic**: Claude API公式Python SDK（マルチモーダルAI）

## ライセンス

MIT License

## 貢献

バグ報告や機能提案は、GitHubのIssuesでお願いします。

プルリクエストも歓迎します！

## 作者

Claude Code assisted implementation

## 更新履歴

### v3.1.0 (2025-10-19)
- **AIモデルアップグレード**: Claude 3.5 Sonnet → Claude 4.5ファミリーへ移行
- **3段階モデル選択**: Haiku 4.5（高速・安価）、Sonnet 4.5（安定・中庸）、Opus 4.1（高精度・高価）
- **デフォルトモデル変更**: `claude-sonnet-4-5-20250929`（Anthropic推奨移行先）
- **モデル可視性向上**: 使用モデル名を標準出力とメタデータに記録
- **自動移行**: 既存ユーザーは次回実行時に自動的にSonnet 4.5を使用
- **詳細な移行ガイド**: CHANGELOG.mdとREADME.mdに移行手順を記載

### v2.0.0 (2025-10-14)
- **音声認識機能の追加**: OpenAI Whisperによる音声テキスト変換
- **Markdown記事生成機能の追加**: スクリーンショットと音声解説を統合した記事を自動生成
- **タイムスタンプ同期**: 最近傍マッチングアルゴリズムで画像と音声を自動対応付け
- **新規CLIオプション**: `--audio`, `--markdown`, `--model-size`
- **新規出力ファイル**: `transcript.json`（音声認識結果）, `article.md`（Markdown記事）
- **後方互換性**: 既存のコマンドライン引数の動作を完全に維持

詳細は[CHANGELOG.md](./CHANGELOG.md)を参照してください。

### v1.0.0 (2025-10-13)
- 初回リリース
- 画面遷移検出
- 安定フレーム抽出
- OCRベースUI重要度分析
- 統合スコアリング
- 時間的重複排除
- 4K動画対応
- Apple Silicon最適化
