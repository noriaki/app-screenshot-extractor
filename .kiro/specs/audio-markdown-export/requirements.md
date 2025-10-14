# Requirements Document

## Project Description (Input)

画面録画と同時に収録した別ファイルの音声データも活用できるようにする。
画面録画の動画データと音声データは同時に入力され利用される。

ターゲットUse Caseは、アプリ紹介記事の作成。
記事の読者がすぐにその場で試してみたくなるスクリーンショット画像付きのMarkdownテキストを出力したい。

## Requirements

### Requirement 1: 音声・動画の統合入力処理
**Objective:** As a ユーザー, I want 動画ファイルと音声ファイルを同時に入力できる機能, so that 画面録画と音声解説を統合した記事を作成できる

#### Acceptance Criteria
1. WHEN ユーザーがCLIで動画ファイルパスと音声ファイルパスを指定 THEN Screenshot Extractor SHALL 両ファイルの存在を検証する
2. IF 動画ファイルまたは音声ファイルが存在しない THEN Screenshot Extractor SHALL エラーメッセージを表示して処理を終了する
3. WHEN 音声ファイルが指定されている THEN Screenshot Extractor SHALL 音声ファイルを読み込んで動画との時間軸対応を確立する
4. IF 音声ファイルと動画ファイルの長さが5秒以上異なる THEN Screenshot Extractor SHALL 警告メッセージを表示する

### Requirement 2: 音声テキスト変換
**Objective:** As a ユーザー, I want 音声ファイルから自動的にテキストを抽出する機能, so that 音声解説を記事の説明文として活用できる

#### Acceptance Criteria
1. WHEN 音声ファイルが入力される THEN Screenshot Extractor SHALL 音声認識APIまたはライブラリを使用してテキストに変換する
2. WHEN 音声をテキスト変換する THEN Screenshot Extractor SHALL 日本語音声を正確に認識する
3. WHEN 音声テキスト変換が完了 THEN Screenshot Extractor SHALL テキストとタイムスタンプ情報を保持する
4. IF 音声認識に失敗した区間がある THEN Screenshot Extractor SHALL その区間を空白として記録し、処理を継続する

### Requirement 3: スクリーンショットと音声の時間軸同期
**Objective:** As a ユーザー, I want スクリーンショットのタイミングと音声解説を自動的に対応付ける機能, so that 画面と説明文が一致した記事を作成できる

#### Acceptance Criteria
1. WHEN スクリーンショットが抽出される THEN Screenshot Extractor SHALL そのタイムスタンプに最も近い音声テキストを特定する
2. WHEN 音声テキストをスクリーンショットに対応付ける THEN Screenshot Extractor SHALL タイムスタンプの前後数秒の範囲から適切なテキスト区間を選択する
3. IF 対応する音声テキストが存在しない THEN Screenshot Extractor SHALL その画像には空の説明文を割り当てる
4. WHEN 複数のスクリーンショットが短時間に連続する THEN Screenshot Extractor SHALL 音声テキストを適切に分割または共有する

### Requirement 4: Markdown記事生成
**Objective:** As a ユーザー, I want スクリーンショットと音声テキストを統合したMarkdownファイルを自動生成する機能, so that すぐに記事として公開できる形式で出力される

#### Acceptance Criteria
1. WHEN 処理が完了 THEN Screenshot Extractor SHALL Markdownファイルを生成する
2. WHEN Markdownを生成する THEN Screenshot Extractor SHALL 各スクリーンショットを画像リンクとして挿入する
3. WHEN Markdownを生成する THEN Screenshot Extractor SHALL 各画像の下に対応する音声テキストを説明文として配置する
4. WHEN Markdownファイルを出力 THEN Screenshot Extractor SHALL 標準的なMarkdown記法（画像: `![alt](path)`、見出し: `##`）を使用する
5. WHERE 音声テキストが存在しない画像 THE Screenshot Extractor SHALL プレースホルダーテキストまたは空行を配置する

### Requirement 5: 出力ファイル管理
**Objective:** As a ユーザー, I want 生成されたMarkdownファイルとスクリーンショット画像を整理された形で保存する機能, so that 記事作成後の編集や管理が容易になる

#### Acceptance Criteria
1. WHEN 出力を保存 THEN Screenshot Extractor SHALL Markdownファイルとスクリーンショット画像を指定ディレクトリに保存する
2. WHEN 出力ディレクトリを作成 THEN Screenshot Extractor SHALL `output/article.md` と `output/screenshots/` のような構造を作成する
3. WHEN Markdownファイルを生成 THEN Screenshot Extractor SHALL 画像パスを相対パスで記述する
4. IF 出力ディレクトリが既に存在し、ファイルが存在する THEN Screenshot Extractor SHALL 既存ファイルを上書きする前に確認する（オプション）または自動的にタイムスタンプ付きディレクトリを作成する
5. WHEN 出力が完了 THEN Screenshot Extractor SHALL 出力ファイルのパスと統計情報（画像数、テキスト長など）を表示する

### Requirement 6: CLI インターフェース拡張
**Objective:** As a ユーザー, I want 音声ファイル入力とMarkdown出力を制御するCLIオプション, so that 既存の動画処理機能と統合して使用できる

#### Acceptance Criteria
1. WHEN ユーザーがCLIを実行 THEN Screenshot Extractor SHALL `--audio` オプションで音声ファイルパスを受け付ける
2. WHEN ユーザーがCLIを実行 THEN Screenshot Extractor SHALL `--markdown` オプションでMarkdown出力を有効化する
3. IF `--markdown` オプションが指定され、`--audio` が指定されていない THEN Screenshot Extractor SHALL 音声テキストなしでMarkdownを生成する
4. WHEN CLIヘルプを表示 THEN Screenshot Extractor SHALL 新しいオプションの説明を含める
5. WHERE 音声処理とMarkdown生成が有効 THE Screenshot Extractor SHALL 既存のスクリーンショット抽出処理と統合して実行する

### Requirement 7: エラーハンドリングと進捗表示
**Objective:** As a ユーザー, I want 音声処理とMarkdown生成の進捗とエラーを明確に把握できる機能, so that 問題発生時に適切に対処できる

#### Acceptance Criteria
1. WHILE 音声テキスト変換を実行中 THE Screenshot Extractor SHALL 進捗状況を表示する
2. WHEN 音声認識APIエラーが発生 THEN Screenshot Extractor SHALL エラーメッセージとエラー理由を表示する
3. IF 音声ファイルのフォーマットが未対応 THEN Screenshot Extractor SHALL サポートされている形式を提示する
4. WHEN Markdown生成が完了 THEN Screenshot Extractor SHALL 生成されたファイルパスと画像数を表示する
5. IF 処理中に予期しないエラーが発生 THEN Screenshot Extractor SHALL エラー内容を記録し、部分的な結果を保存する
