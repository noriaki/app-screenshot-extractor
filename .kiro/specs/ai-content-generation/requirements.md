# Requirements Document

## Introduction

本仕様書は、動画から抽出されたスクリーンショット画像、メタデータ、音声文字起こしデータを用いて、高品質なアプリ紹介・レビュー記事を自動生成する機能の要件を定義します。

### 背景と現状の課題

- 動画から特徴シーンを抽出した画像とそのメタデータ、音声全体を文字起こしした transcript データの作成までは問題ない（ここは変更しない）
- これらの生成物から Markdown 記事を作成する部分について、作成された Markdown 記事の品質が著しく低い。現状はただ文字起こしテキストと動画シーク時間をスクリーンショット画像と並べるただけの文書でしかない

### 実現したいこと

特徴シーン画像ファイル群、画像ファイルのメタデータ、音声文字起こし transcript データの3種をマルチモーダル AI への入力として、ただの事実の羅列ではないアプリ紹介・レビュー記事 Markdown を出力するようにする。出力される Markdown 記事は、読者が紹介されているアプリを自分でも使ってみようと思えるような高品質でワクワクする内容にする。このためのマルチモーダル AI に対するプロンプトを作成することも対象範囲としたい。

## Requirements

### Requirement 1: マルチモーダル AI 統合

**Objective:** 開発者として、スクリーンショット画像群・メタデータ・音声文字起こしデータをマルチモーダル AI に入力できる仕組みが欲しい。そうすることで、AI が視覚情報とテキスト情報を組み合わせて高品質な記事を生成できるようにするため。

#### Acceptance Criteria

1. WHEN マルチモーダル AI 統合機能が呼び出される THEN Content Generation System SHALL スクリーンショット画像ファイル群を読み込む
2. WHEN スクリーンショット画像が読み込まれる THEN Content Generation System SHALL 各画像の metadata.json から関連メタデータ（スコア、タイムスタンプ、UI 要素）を取得する
3. WHEN メタデータが取得される THEN Content Generation System SHALL transcript.json から音声文字起こしデータを読み込む
4. WHEN すべての入力データが準備される THEN Content Generation System SHALL マルチモーダル AI API（例: Claude API）に画像データとテキストデータを送信する
5. IF 画像ファイルまたは JSON ファイルが存在しない THEN Content Generation System SHALL エラーメッセージを表示し処理を中断する

### Requirement 2: AI プロンプト設計

**Objective:** 開発者として、マルチモーダル AI に高品質な記事生成を指示するプロンプトテンプレートが欲しい。そうすることで、事実の羅列ではなく、読者の興味を引く魅力的なアプリ紹介記事を生成できるようにするため。

#### Acceptance Criteria

1. WHEN AI プロンプトが構築される THEN Content Generation System SHALL 「アプリの魅力を伝える紹介記事を作成する」という役割定義を含める
2. WHEN プロンプトに役割定義が含まれる THEN Content Generation System SHALL 「スクリーンショット画像から UI の特徴と機能を分析する」指示を含める
3. WHEN 分析指示が含まれる THEN Content Generation System SHALL 「音声解説から開発者の意図やアプリの価値提案を抽出する」指示を含める
4. WHEN 抽出指示が含まれる THEN Content Generation System SHALL 「読者が使ってみたいと思えるようなワクワクする文章で書く」という文体指示を含める
5. WHEN 文体指示が含まれる THEN Content Generation System SHALL Markdown フォーマット（H1 タイトル、H2 セクション、画像リンク、説明文）での出力形式を指定する
6. WHERE プロンプト設計において THE Content Generation System SHALL 技術仕様ではなくユーザー体験と利点に焦点を当てた内容生成を指示する

### Requirement 3: 高品質記事生成

**Objective:** 開発者として、AI が生成した Markdown 記事が高品質で読者に訴求力のある内容であることを確認したい。そうすることで、単なる事実の羅列ではなく、読者がアプリを試したいと思える記事を提供するため。

#### Acceptance Criteria

1. WHEN AI が記事を生成する THEN Content Generation System SHALL 魅力的なタイトル（H1）を含む Markdown 記事を出力する
2. WHEN 記事が構造化される THEN Content Generation System SHALL 論理的なセクション区切り（H2）で内容を整理する
3. WHEN スクリーンショット画像が配置される THEN Content Generation System SHALL 各画像に対してコンテキストに沿った説明文を生成する
4. WHEN 説明文が生成される THEN Content Generation System SHALL 画像の視覚的特徴と音声解説を統合した文章を作成する
5. WHERE 記事全体において THE Content Generation System SHALL 読者がアプリの価値を理解しやすい流れ（導入→機能紹介→まとめ）を構成する
6. WHERE 記事全体において THE Content Generation System SHALL 単なるスクリーンショットの羅列ではなく、ストーリー性のある文章展開を含める

### Requirement 4: 既存パイプライン統合

**Objective:** 開発者として、新しい AI コンテンツ生成機能を既存のスクリーンショット抽出・音声認識パイプラインにシームレスに統合したい。そうすることで、ユーザーが1つのコマンドで動画から高品質記事まで生成できるようにするため。

#### Acceptance Criteria

1. WHEN ユーザーが AI 記事生成を有効化するコマンドを実行する THEN Content Generation System SHALL 既存の `--markdown` オプションを拡張または新規オプション（例: `--ai-article`）を追加する
2. WHEN AI 記事生成オプションが指定される AND スクリーンショット抽出・音声認識が完了する THEN Content Generation System SHALL 自動的に AI 記事生成処理を開始する
3. WHEN AI 記事生成が完了する THEN Content Generation System SHALL 生成された記事を指定出力ディレクトリ（デフォルト: `./output/`）に保存する
4. WHERE 出力ファイル命名において THE Content Generation System SHALL 既存命名規則に従い（例: `ai_article.md` または `article_ai.md`）、既存の `article.md` と区別する
5. IF スクリーンショット抽出または音声認識が失敗している THEN Content Generation System SHALL AI 記事生成をスキップし、エラーメッセージを表示する

### Requirement 5: エラーハンドリングとフォールバック

**Objective:** 開発者として、マルチモーダル AI API の障害や入力データの不備に対して適切なエラーハンドリングを実装したい。そうすることで、システムが予期しない状況でも安全に動作し、ユーザーに明確なフィードバックを提供するため。

#### Acceptance Criteria

1. IF マルチモーダル AI API が利用不可（ネットワークエラー、API 制限など） THEN Content Generation System SHALL エラーメッセージを表示し、処理を安全に中断する
2. IF 画像ファイルが部分的に欠損している THEN Content Generation System SHALL 利用可能な画像のみで記事を生成し、警告メッセージを表示する
3. IF transcript.json が存在しないまたは空 THEN Content Generation System SHALL 画像とメタデータのみで記事を生成し、音声解説なしで処理を継続する
4. WHEN API 呼び出しが失敗する THEN Content Generation System SHALL 失敗理由（レート制限、認証エラー、タイムアウトなど）を具体的にログ出力する
5. WHERE API キー管理において THE Content Generation System SHALL 環境変数または設定ファイルから API キーを読み込み、コード内にハードコードしない

### Requirement 6: 設定とカスタマイズ

**Objective:** 開発者として、プロンプトテンプレートや出力形式をカスタマイズ可能にしたい。そうすることで、異なるユースケース（技術記事、マーケティング記事など）に柔軟に対応できるようにするため。

#### Acceptance Criteria

1. WHEN AI 記事生成機能が初期化される THEN Content Generation System SHALL プロンプトテンプレートを外部ファイル（例: `prompts/article_generation.txt`）から読み込む
2. IF プロンプトテンプレートファイルが存在しない THEN Content Generation System SHALL デフォルトのプロンプトテンプレートを使用し、警告メッセージを表示する
3. WHEN ユーザーが出力形式を指定する THEN Content Generation System SHALL コマンドライン引数（例: `--output-format markdown|html`）で形式を選択可能にする
4. WHERE プロンプトカスタマイズにおいて THE Content Generation System SHALL 変数置換（例: `{APP_NAME}`, `{TOTAL_SCREENSHOTS}`）をサポートし、動的なプロンプト生成を可能にする
5. WHERE 設定管理において THE Content Generation System SHALL AI モデル選択（例: Claude 3.5 Sonnet、GPT-4V など）をオプションで指定可能にする

### Requirement 7: 出力品質の検証

**Objective:** 開発者として、生成された記事の品質を自動的に検証する仕組みが欲しい。そうすることで、低品質な出力を検出し、必要に応じて再生成または警告を表示できるようにするため。

#### Acceptance Criteria

1. WHEN AI 記事が生成される THEN Content Generation System SHALL 生成された Markdown の構造（H1、H2、画像リンク）を検証する
2. WHEN 構造検証が実行される THEN Content Generation System SHALL 最低限の文字数（例: 500文字以上）を満たすか確認する
3. IF 生成された記事が構造検証または文字数要件を満たさない THEN Content Generation System SHALL 警告メッセージを表示し、記事を保存する前にユーザーに確認を求める
4. WHEN 記事が保存される THEN Content Generation System SHALL 生成メタデータ（生成日時、使用モデル、プロンプトバージョン）を JSON ファイル（例: `ai_metadata.json`）に記録する
5. WHERE 品質検証において THE Content Generation System SHALL 画像リンクが有効（実在するファイルパス）であることを確認する

