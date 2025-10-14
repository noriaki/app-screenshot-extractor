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
└── metadata.json         # スコアリング詳細
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

### Class-Based Pipeline
メインロジックは `ScreenshotExtractor` クラスに集約:
```python
class ScreenshotExtractor:
    def __init__(...)           # 設定初期化
    def open_video(...)         # 動画読み込み
    def detect_scene_transitions(...)  # Stage 1
    def find_stable_frame(...)  # Stage 2
    def analyze_ui_importance(...)     # Stage 3
    def compute_final_score(...)       # Stage 4
    def select_top_screenshots(...)    # Stage 5
    def save_screenshots(...)   # 保存
```

### Stage-Based Processing
5つの処理ステージを順次実行:
1. Scene Transition Detection (画面遷移検出)
2. Stable Frame Detection (安定フレーム検出)
3. UI Importance Analysis (UI重要度分析)
4. Composite Scoring (統合スコアリング)
5. Top Selection with Deduplication (時間的重複排除)

### Global State Management
- OCR Reader は遅延初期化（グローバル変数）
- UI キーワードリストはモジュールレベル定数
- インスタンス変数で動画情報と設定を保持

### CLI Interface
- `argparse` でコマンドライン引数を処理
- 必須: `--input` (入力動画パス)
- オプション: `--output`, `--count`, `--threshold`, `--interval`

## Output File Naming

スクリーンショットのファイル名パターン:
```
{index:02d}_{MM-SS}_score{score}.png
```
例: `01_00-15_score87.png` (1番目、0分15秒、スコア87点)

---
_Document patterns, not file trees. New files following patterns shouldn't require updates_
