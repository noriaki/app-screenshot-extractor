# Technology Stack

## Architecture

シングルファイル・コマンドラインツール。動画処理パイプラインは、Scene Detection → Stable Frame Detection → UI Analysis → Scoring → Selection の5ステージで構成。

## Core Technologies

- **Language**: Python 3.11+
- **Video Processing**: OpenCV (cv2)
- **Image Processing**: Pillow, imagehash
- **OCR**: EasyOCR (Japanese/English)
- **Audio Recognition**: OpenAI Whisper (local execution)
- **Platform**: macOS (Apple Silicon optimized)

## Key Libraries

- **opencv-python**: 動画読み込み、フレーム抽出、画像処理
- **imagehash**: Perceptual Hashing (pHash) による画面遷移検出
- **EasyOCR**: 日本語・英語OCRによるUI要素検出（CPU mode）
- **openai-whisper**: 音声認識エンジン（日本語対応、ローカル実行）
- **numpy**: 画像データの数値計算
- **tqdm**: CLI進捗表示

## Development Standards

### Type Safety
- Python 3.11+ の型ヒント (typing module) を使用
- 関数シグネチャには型アノテーションを明示
- 例: `def analyze_ui_importance(self, frame: np.ndarray) -> Tuple[float, List[Dict], List[str]]:`

### Code Quality
- PEP 8 準拠のコーディングスタイル
- Docstrings は日本語で明確な説明を記載
- モジュールレベルの定数は UPPER_CASE (例: `IMPORTANT_UI_KEYWORDS`)

### Git Commit Messages
- **Language**: English (concise and clear)
- **Format**: Imperative mood in subject line (e.g., "Add feature" not "Added feature")
- **Structure**:
  - Subject: Brief summary (50 chars max)
  - Body: Detailed explanation with Changes/Benefits sections (optional)
  - Footer: Claude Code attribution
- **Example**:
  ```
  Improve audio duration handling and add test documentation

  Changes:
  - Refactor: Get audio duration from Whisper result instead of ffprobe
  - Add: Comprehensive test execution section in README.md

  Benefits:
  - Simpler implementation (no subprocess dependency)
  - Better documentation for running tests

  🤖 Generated with [Claude Code](https://claude.com/claude-code)

  Co-Authored-By: Claude <noreply@anthropic.com>
  ```

### Performance
- 高速化のため720pにダウンサンプルして処理（元解像度は保持）
- フレームスキップ（0.5秒ごと）で処理速度向上
- 遅延初期化パターン（EasyOCR、Whisperモデルは初回使用時にロード）
- グローバルキャッシュでモデルの再ロードを回避

## Development Environment

### Required Tools
- **pyenv**: Python 3.11.10
- **venv**: 仮想環境管理
- **pip**: パッケージ管理

### Common Commands
```bash
# Setup: pyenv local 3.11.10 && python -m venv .venv
# Activate: source .venv/bin/activate
# Install: pip install -r requirements.txt
# Run: python extract_screenshots.py -i video.mp4
# Test (all): python -m unittest discover -s . -p "test_*.py" -v
# Test (specific): python -m unittest test_audio_processor -v
```

**Test Execution Guidelines for AI:**
- Always run full test suite (`python -m unittest discover -s . -p "test_*.py" -v`) after implementation changes
- Run specific test file when modifying a particular class (e.g., `python -m unittest test_audio_processor -v` for AudioProcessor changes)
- Verify all tests pass before creating git commits
- Test files follow naming pattern: `test_{class_name}.py` or `test_{feature}.py`

## Key Technical Decisions

### Apple Silicon CPU Mode
- EasyOCR / Whisper は `gpu=False` / CPU mode で動作（Apple Silicon の CPU パフォーマンスで十分）
- GPU モードはセットアップが複雑で、CPU で実用的な速度が得られる
- メモリ効率: EasyOCR + Whisper 同時ロードでも 3GB 以内

### Perceptual Hashing for Scene Detection
- フレーム間の視覚的差分を高速に計算（ピクセル単位の比較より効率的）
- ハミング距離による閾値判定で画面遷移を検出

### 2-Phase Resolution Strategy
- 処理: 720p にダウンサンプル（高速化）
- 保存: 元の解像度を維持（品質保持）

### Composite Scoring
- `final_score = (transition_magnitude * 2.0) + (stability_score * 0.5) + (ui_importance_score * 1.5)`
- 遷移の大きさを重視しつつ、安定性とUI重要度も考慮

### Timestamp Synchronization (v2.0.0)
- 最近傍マッチングアルゴリズム: スクリーンショットのタイムスタンプと音声セグメント中央時間の距離を計算
- 許容範囲: 5秒以内で最も近いセグメントを選択
- 未対応時の処理: 音声がない場合はプレースホルダー "(説明文なし)" を表示

### Lazy Initialization Pattern (v2.0.0)
- グローバル変数でモデルキャッシュ管理: `easyocr_reader`, `whisper_model_cache`
- 初回呼び出し時のみモデルをロード、以降は再利用
- メモリ効率とパフォーマンスのバランスを最適化

---
_Document standards and patterns, not every dependency_

_Updated: 2025-10-14 - Added audio-markdown-export patterns (v2.0.0)_
