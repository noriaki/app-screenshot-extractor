#!/usr/bin/env python3
"""
App Screenshot Extractor
自動的にアプリ操作動画から最適なスクリーンショットを抽出するツール
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Tuple, Optional

import cv2
import numpy as np
import imagehash
from PIL import Image
from tqdm import tqdm

# EasyOCRは初回実行時にモデルをダウンロードするため、遅延インポート
easyocr_reader = None


def get_ocr_reader():
    """OCRリーダーを遅延初期化（初回実行時のみモデルダウンロード）"""
    global easyocr_reader
    if easyocr_reader is None:
        import easyocr
        print("Initializing OCR model (first time may download models)...")
        easyocr_reader = easyocr.Reader(['ja', 'en'], gpu=False)  # Apple Silicon: CPU mode
    return easyocr_reader


# Whisperモデルのキャッシュ（遅延初期化パターン）
whisper_model_cache = {}


def get_whisper_model(model_size: str):
    """Whisperモデルを遅延初期化（初回のみロード）"""
    global whisper_model_cache

    if model_size not in whisper_model_cache:
        print(f"Loading Whisper model '{model_size}' (first time may download model)...")
        import whisper
        whisper_model_cache[model_size] = whisper.load_model(model_size)
        print(f"Model '{model_size}' loaded successfully.")

    return whisper_model_cache[model_size]


# UI重要度判定用キーワード
IMPORTANT_UI_KEYWORDS = [
    # ナビゲーション
    'ホーム', 'メニュー', '設定', '戻る', '閉じる',
    # アクション
    '完了', '保存', '送信', '追加', '削除', '編集',
    '新規', '作成', '検索', '選択', '確認',
    # 状態
    'ログイン', 'サインアップ', 'スタート', '次へ', 'OK', 'キャンセル',
    # 機能
    'プロフィール', 'マイページ', 'お気に入り', '通知', 'シェア',
    # English equivalents
    'Home', 'Menu', 'Settings', 'Back', 'Close',
    'Done', 'Save', 'Submit', 'Add', 'Delete', 'Edit',
    'New', 'Create', 'Search', 'Select', 'Confirm',
    'Login', 'Sign up', 'Start', 'Next', 'OK', 'Cancel',
    'Profile', 'My Page', 'Favorite', 'Notification', 'Share'
]

TITLE_KEYWORDS = [
    'タイトル', 'ヘッダー', '画面', 'ページ',
    'Title', 'Header', 'Screen', 'Page'
]


class ScreenshotExtractor:
    """動画からスクリーンショットを抽出するメインクラス"""

    def __init__(self, video_path: str, output_dir: str,
                 transition_threshold: int = 25,
                 min_time_interval: float = 15.0,
                 target_count: int = 10):
        """
        Args:
            video_path: 入力動画ファイルパス
            output_dir: 出力ディレクトリ
            transition_threshold: 画面遷移検出の閾値（ハミング距離）
            min_time_interval: スクリーンショット間の最小時間間隔（秒）
            target_count: 抽出する目標枚数
        """
        self.video_path = video_path
        self.output_dir = Path(output_dir)
        self.transition_threshold = transition_threshold
        self.min_time_interval = min_time_interval
        self.target_count = target_count

        # 出力ディレクトリの作成
        self.screenshots_dir = self.output_dir / "screenshots"
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)

        # 動画情報の初期化
        self.cap = None
        self.fps = None
        self.total_frames = None
        self.video_duration = None
        self.original_width = None
        self.original_height = None

        # 処理用の解像度（高速化のため）
        self.process_width = 1280
        self.process_height = 720

    def open_video(self) -> bool:
        """動画ファイルを開き、情報を取得"""
        if not os.path.exists(self.video_path):
            print(f"Error: Video file not found: {self.video_path}")
            return False

        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            print(f"Error: Cannot open video: {self.video_path}")
            return False

        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.video_duration = self.total_frames / self.fps
        self.original_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.original_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        print(f"Video Info:")
        print(f"  Resolution: {self.original_width}x{self.original_height}")
        print(f"  FPS: {self.fps:.2f}")
        print(f"  Duration: {self.video_duration:.2f}s ({self.total_frames} frames)")
        print()

        return True

    def close_video(self):
        """動画ファイルを閉じる"""
        if self.cap is not None:
            self.cap.release()

    def resize_for_processing(self, frame: np.ndarray) -> np.ndarray:
        """処理用に720pにリサイズ"""
        return cv2.resize(frame, (self.process_width, self.process_height))

    def compute_phash(self, frame: np.ndarray) -> imagehash.ImageHash:
        """フレームのperceptual hashを計算"""
        # OpenCV (BGR) -> PIL (RGB)
        pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        return imagehash.phash(pil_image)

    def detect_scene_transitions(self) -> List[Dict]:
        """画面遷移を検出"""
        print("Step 1: Detecting scene transitions...")

        transitions = []
        prev_hash = None
        frame_idx = 0

        # フレームを間引いて処理（毎フレームは不要、0.5秒ごとなど）
        skip_frames = max(1, int(self.fps * 0.5))

        with tqdm(total=self.total_frames, desc="Scanning frames") as pbar:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    break

                # フレームスキップ
                if frame_idx % skip_frames != 0:
                    frame_idx += 1
                    pbar.update(1)
                    continue

                # 処理用にリサイズ
                small_frame = self.resize_for_processing(frame)
                current_hash = self.compute_phash(small_frame)

                # 前フレームとの差分を計算
                if prev_hash is not None:
                    hamming_distance = current_hash - prev_hash

                    # 閾値を超えたら画面遷移
                    if hamming_distance > self.transition_threshold:
                        timestamp = frame_idx / self.fps
                        transitions.append({
                            'frame_idx': frame_idx,
                            'timestamp': timestamp,
                            'magnitude': hamming_distance
                        })

                prev_hash = current_hash
                frame_idx += 1
                pbar.update(1)

        print(f"  Found {len(transitions)} scene transitions\n")
        return transitions

    def find_stable_frame(self, start_frame: int) -> Optional[Dict]:
        """画面遷移後の安定フレームを検出"""
        # 遷移の0.5秒後から1.5秒後の範囲を探索
        search_start = start_frame + int(self.fps * 0.5)
        search_end = start_frame + int(self.fps * 1.5)

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, search_start)

        best_frame = None
        best_stability = -1
        prev_frame = None

        for frame_idx in range(search_start, min(search_end, self.total_frames)):
            ret, frame = self.cap.read()
            if not ret:
                break

            small_frame = self.resize_for_processing(frame)

            if prev_frame is not None:
                # フレーム差分を計算
                diff = cv2.absdiff(small_frame, prev_frame)
                mean_diff = np.mean(diff)
                stability_score = 100 - mean_diff

                if stability_score > best_stability:
                    best_stability = stability_score
                    best_frame = {
                        'frame_idx': frame_idx,
                        'timestamp': frame_idx / self.fps,
                        'stability_score': stability_score,
                        'frame': frame  # 元の解像度を保持
                    }

            prev_frame = small_frame

        return best_frame

    def analyze_ui_importance(self, frame: np.ndarray) -> Tuple[float, List[Dict], List[str]]:
        """UI重要度を解析（OCRベース）"""
        reader = get_ocr_reader()

        # フレームをRGBに変換
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # OCR実行
        results = reader.readtext(rgb_frame)

        detected_texts = []
        ui_elements = []
        importance_score = 0.0

        for bbox, text, confidence in results:
            if confidence < 0.3:  # 信頼度が低いものは除外
                continue

            detected_texts.append(text)

            # 重要なキーワードを検出
            for keyword in IMPORTANT_UI_KEYWORDS:
                if keyword.lower() in text.lower():
                    ui_elements.append({
                        'type': 'button',
                        'text': text,
                        'confidence': confidence
                    })
                    importance_score += 15
                    break

            # タイトル・見出しを検出
            for keyword in TITLE_KEYWORDS:
                if keyword.lower() in text.lower():
                    ui_elements.append({
                        'type': 'title',
                        'text': text,
                        'confidence': confidence
                    })
                    importance_score += 20
                    break

        # テキスト量が多い（説明画面・機能紹介の可能性）
        if len(detected_texts) > 5:
            importance_score += 10

        return importance_score, ui_elements, detected_texts

    def compute_final_score(self, transition_magnitude: float,
                           stability_score: float,
                           ui_importance_score: float) -> float:
        """最終スコアを計算"""
        return (
            transition_magnitude * 2.0 +
            stability_score * 0.5 +
            ui_importance_score * 1.5
        )

    def extract_screenshots(self) -> List[Dict]:
        """メイン処理：スクリーンショットを抽出"""
        start_time = time.time()

        # 動画を開く
        if not self.open_video():
            return []

        try:
            # ステップ1: 画面遷移を検出
            transitions = self.detect_scene_transitions()

            if len(transitions) == 0:
                print("Warning: No scene transitions detected")
                return []

            # ステップ2: 各遷移で安定フレームを検出し、スコアリング
            print("Step 2: Finding stable frames and scoring...")
            candidates = []

            for trans in tqdm(transitions, desc="Processing transitions"):
                # 動画を巻き戻して遷移位置に移動
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, trans['frame_idx'])

                # 安定フレームを検出
                stable_frame = self.find_stable_frame(trans['frame_idx'])

                if stable_frame is None:
                    continue

                # UI重要度を解析
                ui_score, ui_elements, detected_texts = self.analyze_ui_importance(
                    stable_frame['frame']
                )

                # 最終スコアを計算
                final_score = self.compute_final_score(
                    trans['magnitude'],
                    stable_frame['stability_score'],
                    ui_score
                )

                candidates.append({
                    'frame_idx': stable_frame['frame_idx'],
                    'timestamp': stable_frame['timestamp'],
                    'score': final_score,
                    'transition_magnitude': trans['magnitude'],
                    'stability_score': stable_frame['stability_score'],
                    'ui_importance_score': ui_score,
                    'ui_elements': ui_elements,
                    'detected_texts': detected_texts,
                    'frame': stable_frame['frame']
                })

            print(f"  Found {len(candidates)} candidates\n")

            # ステップ3: 時間的重複を排除して上位を選択
            print("Step 3: Selecting top screenshots...")
            selected = self.select_top_screenshots(candidates)

            # ステップ4: 画像を保存
            print("Step 4: Saving screenshots...")
            metadata = self.save_screenshots(selected)

            elapsed = time.time() - start_time
            print(f"\nCompleted in {elapsed:.1f}s")
            print(f"Saved {len(selected)} screenshots to {self.screenshots_dir}")

            return metadata

        finally:
            self.close_video()

    def select_top_screenshots(self, candidates: List[Dict]) -> List[Dict]:
        """時間的重複を排除して上位スクリーンショットを選択"""
        # スコアでソート
        sorted_candidates = sorted(candidates, key=lambda x: x['score'], reverse=True)

        selected = []

        for candidate in sorted_candidates:
            # 既に目標枚数に達したら終了
            if len(selected) >= self.target_count:
                break

            # 既に選択されたフレームと時間的に近すぎないかチェック
            too_close = False
            for sel in selected:
                time_diff = abs(candidate['timestamp'] - sel['timestamp'])
                if time_diff < self.min_time_interval:
                    too_close = True
                    break

            if not too_close:
                selected.append(candidate)

        # タイムスタンプでソート（時系列順）
        selected.sort(key=lambda x: x['timestamp'])

        return selected

    def save_screenshots(self, screenshots: List[Dict]) -> List[Dict]:
        """スクリーンショットを保存しメタデータを生成"""
        metadata = []

        for idx, shot in enumerate(screenshots, 1):
            # ファイル名を生成
            timestamp_str = self.format_timestamp(shot['timestamp'])
            score_str = f"{shot['score']:.0f}"
            filename = f"{idx:02d}_{timestamp_str}_score{score_str}.png"
            filepath = self.screenshots_dir / filename

            # PNG形式で保存（高品質、圧縮レベル1）
            cv2.imwrite(str(filepath), shot['frame'],
                       [cv2.IMWRITE_PNG_COMPRESSION, 1])

            # メタデータを記録
            metadata.append({
                'index': idx,
                'filename': filename,
                'timestamp': shot['timestamp'],
                'score': shot['score'],
                'transition_magnitude': shot['transition_magnitude'],
                'stability_score': shot['stability_score'],
                'ui_importance_score': shot['ui_importance_score'],
                'ui_elements': shot['ui_elements'],
                'detected_texts': shot['detected_texts']
            })

        # メタデータをJSONに保存
        metadata_path = self.output_dir / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        print(f"  Metadata saved to {metadata_path}")

        return metadata

    @staticmethod
    def format_timestamp(seconds: float) -> str:
        """秒数を MM-SS 形式の文字列に変換"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}-{secs:02d}"


# サポートされている音声フォーマット
SUPPORTED_AUDIO_FORMATS = ['.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm', '.aac']


class AudioProcessor:
    """音声ファイル処理クラス"""

    def __init__(self, audio_path: str, output_dir: str, model_size: str = "base"):
        """
        Args:
            audio_path: 音声ファイルパス
            output_dir: 出力ディレクトリ
            model_size: Whisperモデルサイズ（tiny, base, small, medium, large, turbo）

        Raises:
            FileNotFoundError: 音声ファイルが存在しない場合
        """
        self.audio_path = audio_path
        self.output_dir = Path(output_dir)
        self.model_size = model_size

    def validate_files(self) -> bool:
        """
        音声ファイルの存在とフォーマットを検証

        Returns:
            True: 検証成功
            False: 検証失敗

        Raises:
            FileNotFoundError: ファイルが存在しない
            ValueError: サポートされていないフォーマット
        """
        # パストラバーサル攻撃を防ぐためにパスを正規化
        audio_path = Path(self.audio_path).resolve()

        # 存在確認
        if not audio_path.exists():
            print(f"Error: Audio file not found: {audio_path}")
            return False

        # 通常ファイル確認（ディレクトリやデバイスファイルを除外）
        if not audio_path.is_file():
            print(f"Error: Path is not a regular file: {audio_path}")
            return False

        # フォーマット検証
        ext = audio_path.suffix.lower()
        if ext not in SUPPORTED_AUDIO_FORMATS:
            print(f"Error: Unsupported audio format: {ext}")
            print(f"Supported formats: {', '.join(SUPPORTED_AUDIO_FORMATS)}")
            return False

        return True

    def get_duration(self) -> float:
        """
        音声ファイルの長さを取得

        Returns:
            音声ファイルの長さ（秒）

        Raises:
            RuntimeError: ffprobeが利用できない、または実行に失敗した場合
        """
        import subprocess

        try:
            # ffprobeを使用して音声ファイルの長さを取得
            result = subprocess.run(
                [
                    'ffprobe',
                    '-v', 'error',
                    '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1',
                    self.audio_path
                ],
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode != 0:
                raise RuntimeError(f"ffprobe failed: {result.stderr}")

            duration = float(result.stdout.strip())
            return duration

        except FileNotFoundError:
            raise RuntimeError(
                "ffprobe is not installed or not found in PATH. "
                "Please install ffmpeg:\n"
                "  macOS: brew install ffmpeg\n"
                "  Ubuntu/Debian: sudo apt install ffmpeg"
            )
        except ValueError as e:
            raise RuntimeError(f"Failed to parse duration from ffprobe output: {e}")

    def validate_duration_match(self, video_duration: float) -> bool:
        """
        動画と音声の長さを検証

        Args:
            video_duration: 動画の長さ（秒）

        Returns:
            True: 処理継続可能（差異が5秒以下、または警告表示済み）

        Preconditions:
            - audio_pathが存在し、有効な音声ファイルである
            - video_durationが正の値である

        Postconditions:
            - 差異が5秒以上の場合、警告メッセージが標準出力に表示される
        """
        audio_duration = self.get_duration()
        diff = abs(video_duration - audio_duration)

        if diff > 5.0:
            print(f"Warning: Duration mismatch - Video: {video_duration:.1f}s, "
                  f"Audio: {audio_duration:.1f}s (diff: {diff:.1f}s)")
            print("Proceeding with synchronization, but results may be inaccurate.")
            print("Consider re-recording with synchronized start/stop times.")

        return True  # 常に処理継続（ソフトバリデーション）

    def transcribe_audio(self, language: str = "ja") -> List[Dict]:
        """
        音声ファイルをテキストに変換

        Args:
            language: 言語コード（ja, en等）

        Returns:
            セグメントリスト: [
                {
                    "start": 0.0,
                    "end": 3.5,
                    "text": "テキスト内容"
                },
                ...
            ]

        Raises:
            RuntimeError: Whisperモデルのロードに失敗
            Exception: 音声認識処理中のエラー（警告表示して空リスト返却）

        Preconditions:
            - Whisperモデルがロード済み（遅延初期化）
            - 音声ファイルが読み込み可能

        Postconditions:
            - セグメントはタイムスタンプ順にソート済み
        """
        print("Step: Transcribing audio...")
        print(f"  Model: {self.model_size}")
        print(f"  Language: {language}")

        try:
            # Whisperモデルをロード（遅延初期化）
            model = get_whisper_model(self.model_size)

            # 音声認識を実行
            result = model.transcribe(self.audio_path, language=language)

            # セグメント情報を取得
            segments = result.get('segments', [])

            print(f"  Transcribed {len(segments)} segments\n")
            return segments

        except RuntimeError as e:
            # ffmpegエラーなどの RuntimeError は詳細なインストール案内を表示して再raise
            if "ffmpeg" in str(e).lower():
                print("\nError: ffmpeg is not installed or not found in PATH.")
                print("Please install ffmpeg:")
                print("  macOS: brew install ffmpeg")
                print("  Ubuntu/Debian: sudo apt install ffmpeg\n")
            raise  # RuntimeErrorは再raiseして処理を中断

        except Exception as e:
            # 一般的なExceptionは警告を表示して空リストを返す（処理継続）
            print(f"Warning: Audio transcription failed: {e}")
            print("Continuing without audio transcription.")
            return []  # 空リストを返して処理継続

    def save_transcript(self, segments: List[Dict], language: str = "ja") -> Path:
        """
        音声認識結果をJSONファイルに保存

        Args:
            segments: transcribe_audio()の戻り値
            language: 言語コード（デフォルト: ja）

        Returns:
            保存したファイルのパス（output_dir/transcript.json）

        Preconditions:
            - output_dirが設定されている

        Postconditions:
            - transcript.jsonファイルがUTF-8エンコーディングで保存される
            - ファイルパーミッションが0644に設定される
        """
        # 出力パスを生成
        output_path = Path(self.output_dir) / "transcript.json"

        # 出力ディレクトリが存在しない場合は作成
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 音声ファイルの長さを取得
        duration = self.get_duration()

        # JSON形式でデータを構築
        transcript_data = {
            "language": language,
            "duration": duration,
            "segments": segments
        }

        # UTF-8エンコーディングでJSONファイルに保存
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(transcript_data, f, ensure_ascii=False, indent=2)

        # ファイルパーミッションを0644に設定
        output_path.chmod(0o644)

        print(f"  Transcript saved to {output_path}")

        return output_path


class TimestampSynchronizer:
    """タイムスタンプ同期クラス"""

    def __init__(self, tolerance: float = 5.0):
        """
        Args:
            tolerance: 同期許容範囲（秒）、この範囲内の最近傍を選択
        """
        self.tolerance = tolerance

    def synchronize(self,
                    screenshots: List[Dict],
                    transcripts: List[Dict]) -> List[Dict]:
        """
        スクリーンショットと音声セグメントを同期

        Args:
            screenshots: metadata.jsonのスクリーンショット情報
            transcripts: transcript.jsonの音声セグメント情報

        Returns:
            同期結果リスト: [
                {
                    "screenshot": {...},  # 元のスクリーンショット情報
                    "transcript": {...} | None,  # 対応する音声セグメント
                    "matched": bool  # マッチング成功フラグ
                },
                ...
            ]

        Preconditions:
            - screenshotsとtranscriptsは共にタイムスタンプでソート済み
            - timestampキーが存在する

        Postconditions:
            - 全てのスクリーンショットが結果に含まれる
            - 対応する音声がない場合、transcriptはNone
            - 結果はスクリーンショットの順序を維持

        Invariants:
            - 戻り値の長さ == len(screenshots)
        """
        result = []

        for screenshot in screenshots:
            # 最も近い音声セグメントを検索
            nearest_transcript = self.find_nearest_transcript(
                screenshot['timestamp'],
                transcripts
            )

            # 同期結果を構築
            if nearest_transcript is not None:
                result.append({
                    'screenshot': screenshot,
                    'transcript': nearest_transcript,
                    'matched': True
                })
            else:
                result.append({
                    'screenshot': screenshot,
                    'transcript': None,
                    'matched': False
                })

        return result

    def find_nearest_transcript(self,
                                screenshot_time: float,
                                transcripts: List[Dict]) -> Optional[Dict]:
        """
        スクリーンショットのタイムスタンプに最も近い音声セグメントを検索

        Args:
            screenshot_time: スクリーンショットのタイムスタンプ（秒）
            transcripts: 音声セグメントリスト

        Returns:
            最も近いセグメント、またはNone

        Preconditions:
            - screenshot_timeは0以上
            - transcriptsの各要素にstart, endキーが存在

        Postconditions:
            - 戻り値がNoneでない場合、toleranceの範囲内
            - 複数候補がある場合、最も近いものを返す
        """
        if not transcripts:
            return None

        min_distance = float('inf')
        nearest = None

        for segment in transcripts:
            # セグメントの中央時間を計算
            segment_center = (segment['start'] + segment['end']) / 2

            # 距離を計算
            distance = self.calculate_distance(screenshot_time, segment_center)

            # 許容範囲内で最も近いものを選択
            if distance <= self.tolerance and distance < min_distance:
                min_distance = distance
                nearest = segment

        return nearest

    def calculate_distance(self, time1: float, time2: float) -> float:
        """
        2つのタイムスタンプ間の距離を計算

        Args:
            time1: タイムスタンプ1（秒）
            time2: タイムスタンプ2（秒）

        Returns:
            絶対距離（秒）
        """
        return abs(time1 - time2)


class MarkdownGenerator:
    """Markdown記事生成クラス"""

    def __init__(self, output_dir: str, title: str = "アプリ紹介"):
        """
        Args:
            output_dir: 出力ディレクトリ
            title: 記事タイトル（H1見出し）
        """
        self.output_dir = Path(output_dir)
        self.title = title

    def generate(self, synchronized_data: List[Dict]) -> str:
        """
        同期済みデータからMarkdown文字列を生成

        Args:
            synchronized_data: TimestampSynchronizer.synchronize()の戻り値

        Returns:
            Markdown形式の文字列

        Preconditions:
            - synchronized_dataが有効なリスト
            - 各要素にscreenshotキーが存在

        Postconditions:
            - 標準Markdown形式（画像: ![alt](path), 見出し: ##）
            - 画像パスは相対パス
            - 音声テキストがない場合はプレースホルダー
        """
        lines = []

        # H1見出しで記事タイトルを配置
        lines.append(f"# {self.title}\n\n")

        # 各スクリーンショットをH2見出しで区切る
        for item in synchronized_data:
            screenshot = item['screenshot']
            transcript = item.get('transcript')

            # H2見出し: タイムスタンプとタイトル
            section_title = self.format_section_title(screenshot, transcript)
            lines.append(f"{section_title}\n\n")

            # 画像リンク（相対パス）
            image_path = self.get_relative_image_path(screenshot)
            lines.append(f"![Screenshot]({image_path})\n\n")

            # 音声テキストを画像の下に配置
            description = self.format_description(transcript)
            lines.append(f"{description}\n\n")

        return "".join(lines)

    def format_section_title(self, screenshot: Dict, transcript: Optional[Dict]) -> str:
        """
        セクション見出しを生成

        Args:
            screenshot: スクリーンショット情報
            transcript: 音声セグメント情報（None可）

        Returns:
            H2見出し文字列（例: "## 00:15 - 起動画面"）

        Preconditions:
            - screenshot['timestamp']が存在

        Postconditions:
            - タイムスタンプはMM:SS形式
            - 音声テキストから適切な短いタイトルを抽出（最大20文字）
        """
        timestamp_str = self.format_timestamp(screenshot['timestamp'])

        if transcript is None or 'text' not in transcript:
            return f"## {timestamp_str} - (説明文なし)"

        # 音声テキストから短いタイトルを抽出（最大20文字）
        text = transcript['text']
        if len(text) > 20:
            title = text[:20]
        else:
            title = text

        return f"## {timestamp_str} - {title}"

    def format_timestamp(self, seconds: float) -> str:
        """
        秒数をMM:SS形式に変換

        Args:
            seconds: タイムスタンプ（秒）

        Returns:
            MM:SS形式の文字列
        """
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    def get_relative_image_path(self, screenshot: Dict) -> str:
        """
        画像の相対パスを取得

        Args:
            screenshot: スクリーンショット情報

        Returns:
            相対パス（例: "screenshots/01_00-15_score87.png"）
        """
        filename = screenshot.get('filename', '')
        return f"screenshots/{filename}"

    def format_description(self, transcript: Optional[Dict]) -> str:
        """
        説明文を整形

        Args:
            transcript: 音声セグメント情報（None可）

        Returns:
            説明文テキスト、またはプレースホルダー

        Postconditions:
            - transcriptがNoneの場合: "(説明文なし)"
            - transcriptがある場合: テキストをそのまま返す
        """
        if transcript is None:
            return "(説明文なし)"

        text = transcript.get('text', '')
        return text

    def save(self, markdown_content: str, filename: str = "article.md") -> Path:
        """
        Markdownファイルを保存

        Args:
            markdown_content: generate()の戻り値
            filename: ファイル名

        Returns:
            保存したファイルのパス

        Preconditions:
            - output_dirが存在する（存在しない場合は作成）

        Postconditions:
            - ファイルがUTF-8エンコーディングで保存される
            - 既存ファイルがある場合は上書き（警告表示）
        """
        # 出力ディレクトリが存在しない場合は作成
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 保存パスを生成
        output_path = self.output_dir / filename

        # 既存ファイルがある場合は警告
        if output_path.exists():
            print(f"Warning: File already exists and will be overwritten: {output_path}")

        # UTF-8エンコーディングでファイルを保存
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        print(f"  Markdown saved to {output_path}")

        return output_path

    def display_statistics(self, synchronized_data: List[Dict]) -> None:
        """
        生成統計情報を表示

        Args:
            synchronized_data: TimestampSynchronizer.synchronize()の戻り値

        Postconditions:
            - 標準出力に統計情報が表示される
            - 画像数、マッチング成功数、マッチング失敗数
        """
        total_images = len(synchronized_data)
        matched_count = sum(1 for item in synchronized_data if item.get('matched', False))
        unmatched_count = total_images - matched_count

        print("\n=== Markdown Generation Statistics ===")
        print(f"  Total images: {total_images}")
        print(f"  Matched (with transcript): {matched_count}")
        print(f"  Unmatched (no transcript): {unmatched_count}")
        print("=" * 40)


def create_argument_parser() -> argparse.ArgumentParser:
    """引数パーサーを作成（テスト可能にするため分離）"""
    parser = argparse.ArgumentParser(
        description='App Screenshot Extractor - 動画から最適なスクリーンショットを自動抽出',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  %(prog)s -i app_demo.mp4
  %(prog)s -i app_demo.mp4 -c 15 -t 20
  %(prog)s -i app_demo.mp4 -o ~/Documents/screenshots
  %(prog)s -i app_demo.mp4 --audio demo.mp3 --markdown
  %(prog)s -i app_demo.mp4 --audio demo.mp3 --markdown --model-size small
        """
    )

    # 既存のオプション
    parser.add_argument('-i', '--input', required=True,
                       help='入力動画ファイルパス（必須）')
    parser.add_argument('-o', '--output', default='./output',
                       help='出力ディレクトリ（デフォルト: ./output）')
    parser.add_argument('-c', '--count', type=int, default=10,
                       help='抽出する画像の枚数（デフォルト: 10）')
    parser.add_argument('-t', '--threshold', type=int, default=25,
                       help='画面遷移検出の閾値（デフォルト: 25）')
    parser.add_argument('--interval', type=float, default=15.0,
                       help='最小時間間隔（秒）（デフォルト: 15）')

    # 新規オプション（Task 4.1）
    parser.add_argument('--audio', type=str, default=None,
                       help='音声ファイルパス（任意）')
    parser.add_argument('--markdown', action='store_true',
                       help='Markdown記事を生成する（任意）')
    parser.add_argument('--model-size', type=str, default='base',
                       choices=['tiny', 'base', 'small', 'medium', 'large', 'turbo'],
                       help='Whisperモデルサイズ（デフォルト: base）')

    return parser


def run_integration_flow(video_path: str,
                         output_dir: str,
                         audio_path: Optional[str],
                         markdown: bool,
                         model_size: str,
                         threshold: int,
                         interval: float,
                         count: int) -> None:
    """
    統合処理フローを実行（Task 4.2）

    Args:
        video_path: 入力動画ファイルパス
        output_dir: 出力ディレクトリ
        audio_path: 音声ファイルパス（None可）
        markdown: Markdown生成フラグ
        model_size: Whisperモデルサイズ
        threshold: 画面遷移検出の閾値
        interval: 最小時間間隔
        count: 抽出する画像の枚数
    """
    # 既存のスクリーンショット抽出処理
    extractor = ScreenshotExtractor(
        video_path=video_path,
        output_dir=output_dir,
        transition_threshold=threshold,
        min_time_interval=interval,
        target_count=count
    )

    metadata = extractor.extract_screenshots()

    if len(metadata) == 0:
        print("\nError: No screenshots extracted")
        sys.exit(1)

    # 新機能: 音声処理（Task 4.2）
    transcript_data = None
    if audio_path:
        print("\n" + "=" * 60)
        print("  Audio Processing")
        print("=" * 60)
        print()

        audio_processor = AudioProcessor(
            audio_path=audio_path,
            output_dir=output_dir,
            model_size=model_size
        )

        # 音声ファイル検証
        if not audio_processor.validate_files():
            sys.exit(1)

        # 動画・音声長さの検証
        video_duration = extractor.video_duration
        if not audio_processor.validate_duration_match(video_duration):
            sys.exit(1)

        # 音声認識実行
        transcript_data = audio_processor.transcribe_audio(language="ja")
        audio_processor.save_transcript(transcript_data, language="ja")

    # 新機能: Markdown生成（Task 4.2）
    if markdown:
        print("\n" + "=" * 60)
        print("  Markdown Generation")
        print("=" * 60)
        print()

        # 同期処理
        if audio_path and transcript_data:
            # 音声あり: タイムスタンプ同期
            synchronizer = TimestampSynchronizer(tolerance=5.0)
            synchronized = synchronizer.synchronize(metadata, transcript_data)
        else:
            # 音声なし: スクリーンショットのみ
            synchronized = [
                {
                    "screenshot": m,
                    "transcript": None,
                    "matched": False
                }
                for m in metadata
            ]

        # Markdown生成
        md_generator = MarkdownGenerator(
            output_dir=output_dir,
            title="アプリ紹介"
        )
        markdown_content = md_generator.generate(synchronized)
        output_path = md_generator.save(markdown_content)
        md_generator.display_statistics(synchronized)

        print(f"\nMarkdown article saved to {output_path}")


def main():
    """メイン関数"""
    parser = create_argument_parser()
    args = parser.parse_args()

    # バナー表示
    print("=" * 60)
    print("  App Screenshot Extractor")
    print("  Automatically extract optimal screenshots from app videos")
    print("=" * 60)
    print()

    # 統合処理フローを実行（Task 4.2, 4.3）
    run_integration_flow(
        video_path=args.input,
        output_dir=args.output,
        audio_path=args.audio,
        markdown=args.markdown,
        model_size=args.model_size,
        threshold=args.threshold,
        interval=args.interval,
        count=args.count
    )

    print("\nSuccess!")
    sys.exit(0)


if __name__ == '__main__':
    main()
