# Technology Stack

## Architecture

シングルファイル・コマンドラインツール。動画処理パイプラインは、Scene Detection → Stable Frame Detection → UI Analysis → Scoring → Selection の5ステージで構成。

## Core Technologies

- **Language**: Python 3.11+
- **Video Processing**: OpenCV (cv2)
- **Image Processing**: Pillow, imagehash
- **OCR**: EasyOCR (Japanese/English)
- **Platform**: macOS (Apple Silicon optimized)

## Key Libraries

- **opencv-python**: 動画読み込み、フレーム抽出、画像処理
- **imagehash**: Perceptual Hashing (pHash) による画面遷移検出
- **EasyOCR**: 日本語・英語OCRによるUI要素検出（CPU mode）
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

### Performance
- 高速化のため720pにダウンサンプルして処理（元解像度は保持）
- フレームスキップ（0.5秒ごと）で処理速度向上
- 遅延初期化（EasyOCRモデルは初回使用時にロード）

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
```

## Key Technical Decisions

### Apple Silicon CPU Mode
- EasyOCR は `gpu=False` で動作（Apple Silicon の CPU パフォーマンスで十分）
- GPU モードはセットアップが複雑で、CPU で実用的な速度が得られる

### Perceptual Hashing for Scene Detection
- フレーム間の視覚的差分を高速に計算（ピクセル単位の比較より効率的）
- ハミング距離による閾値判定で画面遷移を検出

### 2-Phase Resolution Strategy
- 処理: 720p にダウンサンプル（高速化）
- 保存: 元の解像度を維持（品質保持）

### Composite Scoring
- `final_score = (transition_magnitude * 2.0) + (stability_score * 0.5) + (ui_importance_score * 1.5)`
- 遷移の大きさを重視しつつ、安定性とUI重要度も考慮

---
_Document standards and patterns, not every dependency_
