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
| `--audio` | | なし | 音声ファイルパス（音声認識を有効化） |
| `--markdown` | | なし | Markdown記事を生成する |
| `--model-size` | | `base` | Whisperモデルサイズ（tiny, base, small, medium, large, turbo） |

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
└── article.md           # 生成されたMarkdown記事（--markdownオプション使用時）
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

## ライセンス

MIT License

## 貢献

バグ報告や機能提案は、GitHubのIssuesでお願いします。

プルリクエストも歓迎します！

## 作者

Claude Code assisted implementation

## 更新履歴

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
