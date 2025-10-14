# Project Structure

## Organization Philosophy

シングルファイル・CLI ツール。すべてのロジックは `extract_screenshots.py` に集約。クラスベースの設計で、処理ステージごとにメソッドを分離。

## Directory Patterns

### Root Level
**Location**: `/`
**Purpose**: 実行可能スクリプト、設定ファイル、ドキュメント
**Example**: `extract_screenshots.py` (メインスクリプト), `requirements.txt`, `README.md`

### Output Directory
**Location**: `./output/` (デフォルト)
**Purpose**: 抽出結果の保存
**Structure**:
```
output/
├── screenshots/          # 抽出された画像
│   └── {index}_{timestamp}_score{score}.png
├── metadata.json         # スコアリング詳細
├── transcript.json       # 音声認識結果（--audioオプション使用時）
└── article.md           # Markdown記事（--markdownオプション使用時）
```

### Virtual Environment
**Location**: `.venv/`
**Purpose**: Python 依存パッケージの隔離
**Management**: `python -m venv .venv`, `source .venv/bin/activate`

### Settings and Memory
**Location**: `.kiro/`
**Purpose**: プロジェクトメモリ（steering）とスペック管理
**Example**: `.kiro/steering/`, `.kiro/specs/`

## Naming Conventions

- **Files**: `snake_case.py` (Python標準)
- **Classes**: `PascalCase` (例: `ScreenshotExtractor`)
- **Functions/Methods**: `snake_case` (例: `detect_scene_transitions`)
- **Constants**: `UPPER_SNAKE_CASE` (例: `IMPORTANT_UI_KEYWORDS`)
- **Private Methods**: Leading underscore は使用しない（単一ファイルのため）

## Code Organization Principles

### Class-Based Architecture
複数の責任ごとにクラスを分離（v2.0.0でクラス拡張）:

**ScreenshotExtractor**: 動画処理・スクリーンショット抽出
```python
class ScreenshotExtractor:
    def detect_scene_transitions(...)  # Stage 1
    def find_stable_frame(...)         # Stage 2
    def analyze_ui_importance(...)     # Stage 3
    def compute_final_score(...)       # Stage 4
    def select_top_screenshots(...)    # Stage 5
```

**AudioProcessor** (v2.0.0): 音声ファイル処理・認識
```python
class AudioProcessor:
    def validate_files(...)           # ファイル検証
    def transcribe_audio(...)         # Whisper実行
    def save_transcript(...)          # JSON保存
```

**TimestampSynchronizer** (v2.0.0): タイムスタンプ同期
```python
class TimestampSynchronizer:
    def synchronize(...)              # 最近傍マッチング
    def find_nearest_transcript(...)  # セグメント検索
```

**MarkdownGenerator** (v2.0.0): Markdown記事生成
```python
class MarkdownGenerator:
    def generate(...)                 # Markdown文字列生成
    def save(...)                     # ファイル保存
```

### Stage-Based Processing
5つの処理ステージを順次実行:
1. Scene Transition Detection (画面遷移検出)
2. Stable Frame Detection (安定フレーム検出)
3. UI Importance Analysis (UI重要度分析)
4. Composite Scoring (統合スコアリング)
5. Top Selection with Deduplication (時間的重複排除)

### Global State Management
- モデルキャッシュは遅延初期化（グローバル変数: `easyocr_reader`, `whisper_model_cache`）
- UI キーワードリストはモジュールレベル定数
- インスタンス変数で動画情報と設定を保持
- Helper関数でモデル取得を抽象化: `get_ocr_reader()`, `get_whisper_model(model_size)`

### CLI Interface
- `argparse` でコマンドライン引数を処理
- 必須: `--input` (入力動画パス)
- 既存オプション: `--output`, `--count`, `--threshold`, `--interval`
- 新規オプション (v2.0.0): `--audio`, `--markdown`, `--model-size`
- 統合フロー: `run_integration_flow()` で全機能をオーケストレーション

## Output File Naming

### Screenshots
ファイル名パターン: `{index:02d}_{MM-SS}_score{score}.png`
例: `01_00-15_score87.png` (1番目、0分15秒、スコア87点)

### JSON Files
- `metadata.json`: スクリーンショット詳細（スコア、UI要素、タイムスタンプ）
- `transcript.json` (v2.0.0): 音声認識結果（セグメント、タイムスタンプ、言語）

### Markdown Files
- `article.md` (v2.0.0): 統合記事（H1タイトル、H2セクション、画像リンク、説明文）

## Testing Patterns (v2.0.0)

### Test Organization
- Unit tests: `test_{class_name}.py` (各クラスごと)
- Integration tests: `test_cli_integration.py`, `test_e2e_integration.py`
- Error handling tests: `test_error_handling.py`

### Test Style
- Given-When-Then 構造でテストケースを記述
- Mock を使用して外部依存を隔離（`@patch` デコレータ）
- Docstring に日本語でテスト目的を明記

---
_Document patterns, not file trees. New files following patterns shouldn't require updates_

_Updated: 2025-10-14 - Added audio-markdown-export structure patterns (v2.0.0)_
