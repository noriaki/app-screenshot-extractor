# 変更履歴

このドキュメントには、App Screenshot Extractorの主要な変更内容が記録されています。

## [3.1.0] - 2025-10-19

### AIモデルアップグレード

Claude AIモデルを最新の4.5ファミリーにアップグレードし、3段階のモデル選択機能を追加しました。

#### 主な変更

**モデル更新:**

- **デフォルトモデルの変更**: `claude-3-5-sonnet-20241022` (Deprecated) → `claude-sonnet-4-5-20250929` (最新)
  - Claude 3.5 Sonnetは2025年10月22日に廃止予定
  - Anthropic公式の推奨移行先モデルを採用
  - 安定した品質とコストバランスを維持

- **3段階モデル選択の追加**: 用途に応じて最適なモデルを選択可能
  - **Haiku 4.5** (`claude-haiku-4-5-20251001`): 高速・安価 ($1/$5 per MTok)
  - **Sonnet 4.5** (`claude-sonnet-4-5-20250929`): 安定・中庸 ($3/$15 per MTok、デフォルト)
  - **Opus 4.1** (`claude-opus-4-1-20250805`): 高精度・高価 ($15/$75 per MTok)

**機能強化:**

- **CLI引数の拡張**: `--ai-model` オプションで3つのモデルから選択可能
  - ヘルプメッセージに各モデルの特性（速度・品質・コスト）を表示
  - 無効なモデル名を指定した場合、有効な選択肢を明示的に案内

- **可視性の向上**:
  - AI記事生成開始時に使用モデル名を標準出力に表示
  - `ai_metadata.json`の`"model"`フィールドに使用モデル名を記録
  - トークン使用量から実際のコストを計算可能

**SDK要件:**

- `anthropic >= 0.43.0`: Claude 4.5ファミリーをサポート
  - 既存の`requirements.txt`は最新版を指定済み
  - 新規インストール時は自動的に対応バージョンが導入される

#### 移行ガイド

**自動移行（推奨）:**

`--ai-model`オプションを指定していない既存ユーザーは、次回実行時に自動的にSonnet 4.5を使用します。コマンドの変更は不要です。

```bash
# 変更前（v3.0.0）
python extract_screenshots.py -i video.mp4 --ai-article

# 変更後（v3.1.0）- 同じコマンドで自動的にSonnet 4.5を使用
python extract_screenshots.py -i video.mp4 --ai-article
```

**手動移行（明示的にモデルを指定している場合）:**

スクリプトやCI/CDで旧モデルを明示的に指定している場合は、以下のように更新してください。

| 旧モデル | 推奨移行先 | 特性 |
|---------|----------|------|
| `claude-3-5-sonnet-20241022` | `claude-sonnet-4-5-20250929` | 同等の品質・コストバランス（推奨） |
| `claude-3-5-sonnet-20241022` | `claude-haiku-4-5-20251001` | コスト削減（約1/3）、高速 |
| `claude-3-5-sonnet-20241022` | `claude-opus-4-1-20250805` | 品質優先、高コスト（5倍） |

```bash
# 変更前
python extract_screenshots.py -i video.mp4 --ai-article --ai-model claude-3-5-sonnet-20241022

# 変更後（推奨: Sonnet 4.5）
python extract_screenshots.py -i video.mp4 --ai-article --ai-model claude-sonnet-4-5-20250929

# 変更後（コスト重視: Haiku 4.5）
python extract_screenshots.py -i video.mp4 --ai-article --ai-model claude-haiku-4-5-20251001

# 変更後（品質優先: Opus 4.1）
python extract_screenshots.py -i video.mp4 --ai-article --ai-model claude-opus-4-1-20250805
```

**エラーメッセージ:**

旧モデルを指定すると、以下のエラーメッセージが表示されます。

```
extract_screenshots.py: error: argument --ai-model: invalid choice: 'claude-3-5-sonnet-20241022'
(choose from 'claude-haiku-4-5-20251001', 'claude-sonnet-4-5-20250929', 'claude-opus-4-1-20250805')
```

#### 後方互換性

- **CLI引数**: `--ai-model`オプションの名前と型は維持（文字列型）
- **デフォルト動作**: オプション省略時は新しいSonnet 4.5を使用（品質は維持またはそれ以上）
- **メタデータ形式**: `ai_metadata.json`の構造は変更なし（`"model"`フィールドの値のみ更新）
- **その他のオプション**: `--ai-article`, `--app-name`, `--output-format`などの動作は完全に維持

#### 注意事項

- **廃止予定日**: Claude 3.5 Sonnetは2025年10月22日に廃止（Anthropic公式発表）
- **API互換性**: 新モデルは既存のMessages APIと完全互換（コード変更は最小限）
- **コスト**: Sonnet 4.5はSonnet 3.5と同等の価格帯（$3/$15 per MTok）

---

## [2.0.0] - 2025-10-14

### 追加機能

#### 音声・動画統合Markdown記事生成機能

画面録画動画と別録音声ファイルを統合し、スクリーンショットと音声解説を組み合わせたMarkdown記事を自動生成する機能を追加しました。

**主な新機能:**

- **音声認識機能** (`--audio`オプション)
  - OpenAI Whisperを使用した高精度な日本語音声認識
  - タイムスタンプ付きセグメント単位でテキスト変換
  - ローカル実行でプライバシー保護
  - 音声認識結果をtranscript.jsonに保存

- **タイムスタンプ同期機能**
  - スクリーンショットのタイムスタンプと音声セグメントを自動対応付け
  - 最近傍マッチングアルゴリズムによる高精度な同期
  - 5秒の許容範囲内で最も近い音声テキストを選択

- **Markdown記事生成機能** (`--markdown`オプション)
  - スクリーンショットと音声解説を統合したMarkdown記事を自動生成
  - タイムスタンプ付き見出しで構造化
  - 画像リンクと説明文を自動配置
  - 標準Markdown形式で即座に公開可能

- **柔軟な実行オプション**
  - 音声あり/なしでMarkdown生成可能
  - Whisperモデルサイズを選択可能（`--model-size`オプション）
  - 既存のスクリーンショット抽出機能と完全に統合

**技術詳細:**

- 新規コンポーネント:
  - `AudioProcessor`: 音声ファイル処理と認識
  - `TimestampSynchronizer`: タイムスタンプ同期
  - `MarkdownGenerator`: Markdown記事生成

- 依存パッケージ追加:
  - `openai-whisper>=20231117`: 音声認識エンジン

- 出力ファイル:
  - `transcript.json`: 音声認識結果（セグメント、タイムスタンプ）
  - `article.md`: 生成されたMarkdown記事

**ユースケース:**

- アプリ紹介記事の作成: デモ動画と音声解説から即座に公開可能な記事を生成
- ドキュメント作成の効率化: 手動でのスクリーンショット配置とテキスト入力を大幅に削減
- プレゼンテーション資料作成: 動画から構造化されたMarkdownドキュメントを自動生成

### 変更内容

- CLI引数の拡張:
  - `--audio`: 音声ファイルパスを指定（任意）
  - `--markdown`: Markdown記事生成を有効化（任意）
  - `--model-size`: Whisperモデルサイズを選択（デフォルト: base）

- エラーハンドリングの強化:
  - ファイル不在時の明確なエラーメッセージ
  - 動画・音声長さ不一致の警告表示
  - 音声認識失敗時の適切な処理

- 進捗表示の改善:
  - 音声テキスト変換中の進捗バー表示
  - 各処理ステップの開始・完了メッセージ
  - Markdown生成完了時の統計情報表示

### 後方互換性

- 既存のコマンドライン引数（`-i`, `-o`, `-c`, `-t`, `--interval`）の動作は完全に維持
- `--audio`および`--markdown`オプションなしの場合、v1.0.0と完全に同一の動作
- 既存の`metadata.json`フォーマットは変更なし

### パフォーマンス

- 音声認識処理時間: 音声長の約1/7（baseモデル使用時）
- メモリ使用量: EasyOCR + Whisper同時ロード時でも3GB以内
- エンドツーエンド処理時間: 5分の動画+音声で約2分以内

### セキュリティ

- ローカル音声認識: 音声データを外部APIに送信せず、プライバシーを保護
- ファイルパーミッション: 生成ファイルは適切なパーミッション（0644）で保存
- パストラバーサル防止: ファイルパスの検証を強化

---

## [1.0.0] - 2025-10-13

### 初回リリース

**コア機能:**

- 画面遷移検出 (Perceptual Hashing)
- 安定フレーム抽出
- OCRベースUI重要度分析 (EasyOCR)
- 統合スコアリング
- 時間的重複排除
- 4K動画対応
- Apple Silicon最適化

**技術スタック:**

- Python 3.11+
- OpenCV (動画処理)
- EasyOCR (日本語・英語OCR)
- Pillow (画像処理)
- imagehash (Perceptual Hashing)

**出力形式:**

- スクリーンショット画像 (PNG)
- メタデータ (metadata.json)

---

## バージョニング方針

このプロジェクトは [Semantic Versioning](https://semver.org/) に従います:

- **MAJOR**: 互換性のない変更
- **MINOR**: 後方互換性のある機能追加
- **PATCH**: 後方互換性のあるバグ修正
