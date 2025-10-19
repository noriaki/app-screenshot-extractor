# Requirements Document

## Project Description (Input)

## 現在の課題

使用しているClaude AI modelが古くDeprecatedになっている。

- **現在使用中**: `claude-3-5-sonnet-20241022`
- **廃止予定日**: 2025年10月22日（Legacy End Date）
- **ステータス**: Deprecated（既存ユーザーは廃止日まで利用可能、新規ユーザーは利用不可）

## 期待する要件

価格と性能を考慮した安定的・中庸のモデルをデフォルトとして使用し、高価・高精度なモデルと安価・高速なモデルをオプションとして指定できるようにする。

### 関連する情報

以下の公式Webページから最新情報を取得済み（2025年10月19日確認）。

**Model Deprecations**:
- ドキュメント: https://docs.claude.com/en/docs/about-claude/model-deprecations
- Claude Sonnet 3.5 (`claude-3-5-sonnet-20240620`, `claude-3-5-sonnet-20241022`) は **2025年10月22日廃止**
- 推奨移行先: Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`)
- ステータス定義:
  - **Legacy**: 更新終了、将来的に廃止予定
  - **Deprecated**: 新規ユーザーは利用不可、既存ユーザーは廃止日まで利用可能
  - **Retired**: 完全に利用不可、APIリクエストは失敗

**Pricing** (Per Million Tokens):
- ドキュメント: https://docs.claude.com/en/docs/about-claude/pricing
- 公式価格ページ: https://www.anthropic.com/pricing
- Claude Haiku 4.5: $1 input / $5 output
- Claude Sonnet 4.5: $3 input / $15 output
- Claude Opus 4.1: $15 input / $75 output
- 追加機能: Prompt Caching (cache read: 0.1x), Batch API (50% discount)

## Requirements

### Requirement 1: モデル設定の更新

**Objective:** As a システム管理者, I want deprecatedモデルを最新の推奨モデルに置き換える, so that APIの安定性とサポートを確保できる

**背景情報**:
- Anthropic公式発表（2025年8月13日）により、Claude Sonnet 3.5モデルは2025年10月22日に廃止
- 推奨移行先: Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`)

#### Acceptance Criteria

1. WHEN システムが起動する THEN AIContentGenerator SHALL デフォルトモデルとして `claude-sonnet-4-5-20250929` を使用する
2. IF ユーザーがモデルを明示的に指定しない THEN AIContentGenerator SHALL `claude-sonnet-4-5-20250929` で記事を生成する
3. WHEN 既存のdeprecatedモデル名 (`claude-3-5-sonnet-20241022`) が設定に含まれる THEN システム SHALL CLI引数パーサーでエラーを表示し有効なモデル名を案内する

### Requirement 2: 3段階モデル選択機能

**Objective:** As a ユーザー, I want コスト・速度・品質のトレードオフに応じてモデルを選択できる, so that 用途に最適なバランスで記事生成できる

**背景情報**:
- Claude 4.5ファミリーは3つのモデル階層を提供（2025年10月時点）
- 価格情報はClaude公式サイト（anthropic.com/pricing）より取得

#### Acceptance Criteria

1. WHEN ユーザーが `--ai-model` オプションを指定する THEN システム SHALL 以下の3つのカテゴリからモデルを選択可能にする
   - **高速・安価モデル**: `claude-haiku-4-5-20251001` ($1/$5 per MTok, 2025年10月15日リリース)
   - **安定・中庸モデル（デフォルト）**: `claude-sonnet-4-5-20250929` ($3/$15 per MTok, 2025年9月29日リリース)
   - **高精度・高価モデル**: `claude-opus-4-1-20250805` ($15/$75 per MTok, 2025年8月5日リリース)
2. IF ユーザーがサポート外のモデル名を指定した THEN システム SHALL argparseエラーメッセージを表示し有効な3つの選択肢を案内して終了する
3. WHEN AI記事生成が実行される THEN AIContentGenerator SHALL ユーザーが指定したモデル名をClaude APIに渡す

### Requirement 3: モデル設定の可視性向上

**Objective:** As a ユーザー, I want 使用中のモデルと関連情報を確認できる, so that 生成コストとAPI使用状況を把握できる

#### Acceptance Criteria

1. WHEN AI記事生成が開始される THEN システム SHALL 使用するモデル名を標準出力に表示する
2. WHEN 記事生成が完了する THEN システム SHALL `ai_metadata.json` に使用モデル名を記録する
3. WHERE メタデータファイル内で THE システム SHALL モデル名を `"model"` キーに文字列として保存する
4. IF ヘルプメッセージが表示される THEN システム SHALL 各モデルの特性（速度・品質・コスト）を説明文に含める

### Requirement 4: 下位互換性の確保

**Objective:** As a 既存ユーザー, I want 既存のスクリプトやワークフローが引き続き動作する, so that システム更新による影響を最小限に抑えられる

#### Acceptance Criteria

1. WHEN ユーザーが `--ai-model` オプションを省略する THEN システム SHALL デフォルトモデルで正常に動作する
2. IF 既存のテストケースが実行される THEN 全てのテストケース SHALL モデル更新後も合格する
3. WHERE CLI引数の構造 THE システム SHALL 既存のオプション名と引数順序を維持する
4. WHEN 環境変数 `ANTHROPIC_API_KEY` が設定されている THEN システム SHALL 既存の認証フローで動作する

### Requirement 5: ドキュメント更新

**Objective:** As a ユーザー, I want 最新のモデル情報とベストプラクティスを参照できる, so that 適切なモデルを選択できる

#### Acceptance Criteria

1. WHEN README.mdが更新される THEN ドキュメント SHALL 3つのモデルカテゴリの説明を含む
2. WHERE 使用例セクション THE ドキュメント SHALL 各モデルを使用するCLIコマンド例を提供する
3. WHEN CLIヘルプが表示される THEN システム SHALL `--ai-model` オプションの説明に推奨用途を記載する
4. IF モデル選択ガイドが提供される THEN ドキュメント SHALL コスト・速度・品質の比較表を含む
