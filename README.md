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

### 3. 動作確認

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

### 使用例

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

## 出力形式

### ディレクトリ構造

```
output/
├── screenshots/
│   ├── 01_00-15_score87.png
│   ├── 02_00-32_score85.png
│   ├── 03_01-05_score82.png
│   └── ...
└── metadata.json
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

## 技術スタック

- **opencv-python**: 動画処理とフレーム抽出
- **Pillow**: 画像処理
- **imagehash**: Perceptual Hashing（pHash）
- **EasyOCR**: OCR（日本語・英語対応）
- **numpy**: 数値計算
- **tqdm**: 進捗表示

## ライセンス

MIT License

## 貢献

バグ報告や機能提案は、GitHubのIssuesでお願いします。

プルリクエストも歓迎します！

## 作者

Claude Code assisted implementation

## 更新履歴

### v1.0.0 (2025-10-13)
- 初回リリース
- 画面遷移検出
- 安定フレーム抽出
- OCRベースUI重要度分析
- 統合スコアリング
- 時間的重複排除
- 4K動画対応
- Apple Silicon最適化
