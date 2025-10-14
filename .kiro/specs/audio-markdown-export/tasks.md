# 実装タスク

## タスク一覧

- [x] 1. 音声処理基盤の構築
  - AudioProcessorクラスを実装し、音声ファイルの読み込み・検証・長さ取得機能を提供する
  - OpenAI Whisperを使用した音声認識の基本機能を実装する
  - Whisperモデルの遅延初期化パターンを実装する（EasyOCRと同様）
  - 音声ファイルのフォーマット検証機能を実装する（mp3, wav, m4a等）
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 1.1 音声ファイル検証機能の実装
  - 音声ファイルの存在確認を行う`validate_files()`メソッドを実装する
  - サポートされている音声フォーマット（mp3, wav, m4a, aac等）を検証する
  - パストラバーサル攻撃を防ぐためにPath.resolve()を使用してファイルパスを検証する
  - 通常ファイルであることを確認し、ディレクトリやデバイスファイルを除外する
  - エラー時にはサポートされているフォーマット一覧を表示する
  - _Requirements: 1.1, 1.2_

- [x] 1.2 音声長取得とマッチング検証の実装
  - ffprobeを使用して音声ファイルの長さを取得する`get_duration()`を実装する
  - 動画と音声の長さを比較する`validate_duration_match()`を実装する
  - 5秒以上の差異がある場合は警告メッセージを表示する
  - 警告表示後も処理を継続する（ソフトバリデーション）
  - _Requirements: 1.3, 1.4_

- [x] 1.3 音声テキスト変換機能の実装
  - Whisperモデルをロードして音声認識を実行する`transcribe_audio()`を実装する
  - 日本語音声認識（language="ja"）をデフォルトとして設定する
  - 音声認識結果をセグメント単位（タイムスタンプ付き）で取得する
  - 音声認識失敗時には空リストを返して処理を継続する
  - tqdmによる進捗表示を実装する
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 1.4 音声認識結果の保存機能の実装
  - 音声認識結果をJSONファイル（transcript.json）に保存する`save_transcript()`を実装する
  - JSON形式でlanguage, duration, segmentsを含むデータ構造を定義する
  - UTF-8エンコーディングでファイルを保存する
  - ファイルパーミッションを0644に設定する
  - _Requirements: 2.3_

- [x] 2. タイムスタンプ同期機能の実装
  - TimestampSynchronizerクラスを実装する
  - スクリーンショットのタイムスタンプと音声セグメントを対応付ける最近傍マッチングアルゴリズムを実装する
  - 5秒の許容範囲内で最も近い音声セグメントを選択する
  - 対応する音声が見つからない場合はNoneを返す
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 2.1 最近傍検索アルゴリズムの実装
  - スクリーンショットのタイムスタンプに最も近い音声セグメントを検索する`find_nearest_transcript()`を実装する
  - セグメントの中央時間（start + end）/ 2で距離を計算する
  - 許容範囲（tolerance、デフォルト5秒）内の最近傍を優先する
  - 該当するセグメントがない場合はNoneを返す
  - _Requirements: 3.1, 3.2_

- [x] 2.2 同期処理のオーケストレーション
  - metadata.jsonとtranscript.jsonを読み込んで同期処理を実行する`synchronize()`を実装する
  - 全てのスクリーンショットに対して音声セグメントを対応付ける
  - 同期結果をscreenshot, transcript, matchedフラグを含む形式で返す
  - スクリーンショットの順序を維持する
  - _Requirements: 3.3, 3.4_

- [x] 3. Markdown記事生成機能の実装
  - MarkdownGeneratorクラスを実装する
  - 同期済みデータからMarkdown形式の記事を生成する
  - 標準的なMarkdown記法（画像リンク、見出し）を使用する
  - 画像パスは相対パスで記述する
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 3.1 Markdownコンテンツ生成機能の実装
  - 同期済みデータからMarkdown文字列を生成する`generate()`を実装する
  - H1見出しで記事タイトルを配置する
  - 各スクリーンショットをH2見出しで区切る
  - タイムスタンプをMM:SS形式で見出しに含める
  - 画像リンクを`![Screenshot](相対パス)`形式で挿入する
  - 音声テキストを画像の下に配置する
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 3.2 見出しとタイムスタンプのフォーマット
  - タイムスタンプを秒数からMM:SS形式に変換する`format_timestamp()`を実装する
  - 音声テキストから短いタイトルを抽出する`format_section_title()`を実装する
  - 音声テキストがない場合のフォールバック処理を実装する
  - タイトルは最大20文字に制限する
  - _Requirements: 4.4_

- [x] 3.3 説明文とプレースホルダーの処理
  - 音声テキストを整形する`format_description()`を実装する
  - transcriptがNoneの場合は"(説明文なし)"を返す
  - transcriptがある場合はテキストをそのまま返す
  - _Requirements: 4.5_

- [x] 3.4 Markdownファイルの保存と統計表示
  - Markdownファイルを出力ディレクトリに保存する`save()`を実装する
  - UTF-8エンコーディングでファイルを保存する
  - 既存ファイルがある場合は上書き警告を表示する
  - 生成統計情報（画像数、マッチング成功数、失敗数）を表示する`display_statistics()`を実装する
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 4. CLI統合とオーケストレーション
  - main関数にargparseオプションを追加する
  - 既存のスクリーンショット抽出処理と新機能を統合する
  - 条件分岐により音声処理とMarkdown生成を制御する
  - 後方互換性を維持する
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 4.1 CLIオプションの追加
  - `--audio`オプションで音声ファイルパスを受け付ける
  - `--markdown`オプションでMarkdown出力を有効化する
  - `--model-size`オプションでWhisperモデルサイズを選択可能にする（デフォルト: base）
  - CLIヘルプに新しいオプションの説明を追加する
  - _Requirements: 6.1, 6.2, 6.4_

- [x] 4.2 統合処理フローの実装
  - 既存のScreenshotExtractor実行後に音声処理を実行する
  - `--audio`オプション指定時にAudioProcessorを初期化して音声認識を実行する
  - `--markdown`オプション指定時にTimestampSynchronizerとMarkdownGeneratorを実行する
  - 音声なしでもMarkdown生成を可能にする（--markdownのみ指定）
  - _Requirements: 6.3, 6.5_

- [x] 4.3 後方互換性の確保
  - `--audio`および`--markdown`オプションなしの場合、既存の動作を完全に維持する
  - 既存のmetadata.jsonフォーマットを変更しない
  - 既存のオプション（-i, -o, -c, -t, --interval）の動作に影響を与えない
  - _Requirements: 6.5_

- [ ] 5. エラーハンドリングと進捗表示の実装
  - 各処理ステップでのエラーハンドリングを実装する
  - 進捗状況を適切に表示する
  - 予期しないエラー発生時の部分結果保存を実装する
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 5.1 ユーザーエラーのハンドリング
  - ファイル不在時に明確なエラーメッセージとファイルパスを表示する
  - 未対応フォーマット時にサポートされている形式一覧を表示する
  - エラー時には即座に処理を中断する（sys.exit(1)）
  - _Requirements: 7.2, 7.3_

- [ ] 5.2 システムエラーのハンドリング
  - Whisperモデルロード失敗時にffmpegインストール確認を促す
  - 音声認識処理失敗時に警告を表示して処理を継続する
  - RuntimeErrorとExceptionを適切に区別して処理する
  - _Requirements: 7.2_

- [ ] 5.3 進捗表示の実装
  - 音声テキスト変換中にtqdm進捗バーを表示する
  - 各処理ステップの開始・完了メッセージを表示する
  - Markdown生成完了時にファイルパスと画像数を表示する
  - _Requirements: 7.1, 7.4_

- [ ] 5.4 予期しないエラーの処理
  - 予期しないエラー発生時にエラー内容をログ出力する
  - 部分的な結果が存在する場合は保存する
  - エラー後にsys.exit(1)で終了する
  - _Requirements: 7.5_

- [ ] 6. テストの実装
  - AudioProcessor, TimestampSynchronizer, MarkdownGeneratorの単体テストを実装する
  - 統合テスト（E2Eテスト）を実装する
  - パフォーマンステストを実装する
  - _Requirements: すべて_

- [ ] 6.1 AudioProcessor単体テストの実装
  - validate_files()のテスト（存在確認、フォーマット検証）
  - get_duration()のテスト（正常系、ffprobe利用不可）
  - validate_duration_match()のテスト（差異5秒以下、5秒以上）
  - transcribe_audio()のモックテスト（正常系、異常系）
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4_

- [ ] 6.2 TimestampSynchronizer単体テストの実装
  - find_nearest_transcript()のテスト（最近傍選択、tolerance範囲外）
  - synchronize()のテスト（全スクリーンショット含有、マッチングフラグ、順序維持）
  - calculate_distance()のテスト（正しい距離計算）
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [ ] 6.3 MarkdownGenerator単体テストの実装
  - format_timestamp()のテスト（秒数からMM:SS変換、境界値）
  - format_section_title()のテスト（見出し生成、フォールバック）
  - format_description()のテスト（音声テキストあり、なし）
  - generate()のテスト（Markdown構造、相対パス、全スクリーンショット含有）
  - save()のテスト（ファイル保存、上書き警告）
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 6.4 統合テスト（E2E）の実装
  - 基本フロー（音声あり）のテスト
  - 基本フロー（音声なし）のテスト
  - 音声のみ（Markdownなし）のテスト
  - ファイル不在エラーのテスト
  - 動画・音声長さ不一致のテスト
  - _Requirements: すべて_

- [ ] 6.5 パフォーマンステストの実装
  - 音声認識処理時間の測定（1分、5分の音声）
  - エンドツーエンド処理時間の測定（5分の動画+音声）
  - メモリ使用量の測定（baseモデル、EasyOCR+Whisper同時ロード）
  - 長時間音声処理のスケーラビリティテスト（30分、1時間）
  - _Requirements: すべて_

- [ ] 7. ドキュメント整備
  - README.mdに新機能の説明を追加する
  - requirements.txtにopenai-whisperを追加する
  - CHANGELOG.mdを作成する
  - 使用例とコマンドラインサンプルを追加する
  - _Requirements: すべて_

- [ ] 7.1 README.mdの更新
  - 音声・動画統合機能の概要を追加する
  - `--audio`と`--markdown`オプションの使用方法を説明する
  - コマンドライン実行例を3パターン追加する（音声あり、音声なし、音声のみ）
  - 出力ファイル（transcript.json, article.md）の説明を追加する
  - _Requirements: すべて_

- [ ] 7.2 依存関係とChangelog整備
  - requirements.txtにopenai-whisperを追加する
  - CHANGELOG.mdを作成してv2.0.0の変更内容を記載する
  - バージョン情報と新機能一覧を明記する
  - _Requirements: すべて_
