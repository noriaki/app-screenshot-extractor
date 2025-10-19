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

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

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
        self.audio_duration = None  # 音声認識時に取得

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

    def get_duration(self) -> Optional[float]:
        """
        音声ファイルの長さを取得

        transcribe_audio()実行後に利用可能になります。

        Returns:
            音声ファイルの長さ（秒）、または None（未実行の場合）
        """
        return self.audio_duration

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
            - transcribe_audio()が実行済みでaudio_durationが設定されている

        Postconditions:
            - 差異が5秒以上の場合、警告メッセージが標準出力に表示される
        """
        audio_duration = self.get_duration()

        if audio_duration is None:
            print("Warning: Audio duration not available yet (transcribe_audio not executed)")
            return True  # 警告を表示して処理継続

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
            - self.audio_durationが設定される
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

            # 音声の長さを取得（Whisperの結果から）
            # 1. resultに'duration'キーがあればそれを使用
            # 2. なければ最後のセグメントのendから取得
            # 3. セグメントもなければ0.0
            if 'duration' in result:
                self.audio_duration = result['duration']
            elif segments and len(segments) > 0:
                self.audio_duration = segments[-1]['end']
            else:
                self.audio_duration = 0.0

            print(f"  Transcribed {len(segments)} segments\n")
            print(f"  Audio duration: {self.audio_duration:.2f}s")
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
            - transcribe_audio()が実行済み

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


class QualityValidator:
    """
    生成記事の品質を自動検証するクラス
    Task 5: 記事品質検証機能の実装
    """

    def __init__(self,
                 min_chars: int = 500,
                 require_h1: bool = True,
                 require_h2: bool = True,
                 require_images: bool = True) -> None:
        """
        Args:
            min_chars: 最低文字数
            require_h1: H1見出し必須フラグ
            require_h2: H2見出し必須フラグ
            require_images: 画像リンク必須フラグ
        """
        self.min_chars = min_chars
        self.require_h1 = require_h1
        self.require_h2 = require_h2
        self.require_images = require_images

    def validate_quality(self, content: str, screenshot_paths: List[Path]) -> Dict[str, any]:
        """
        Markdown記事の品質を検証

        Args:
            content: 検証対象のMarkdownテキスト
            screenshot_paths: 参照すべき画像パスリスト

        Returns:
            {
                "valid": bool,  # 全検証項目合格ならTrue
                "warnings": List[str],  # 警告メッセージリスト
                "metrics": {
                    "char_count": int,
                    "h1_count": int,
                    "h2_count": int,
                    "image_count": int,
                    "broken_links": List[str]
                }
            }
        """
        warnings = []

        # 文字数計測
        char_count = len(content)

        # 見出しカウント（改行で区切られたものと、ファイル先頭のものを考慮）
        h1_count = content.count('\n# ')
        if content.startswith('# '):
            h1_count += 1

        h2_count = content.count('\n## ')
        if content.startswith('## '):
            h2_count += 1

        # 画像リンク抽出とカウント
        import re
        image_pattern = r'!\[.*?\]\((.*?)\)'
        image_links = re.findall(image_pattern, content)
        image_count = len(image_links)

        # 画像リンク検証
        broken_links = self.validate_image_links(content, screenshot_paths)

        # 構造検証
        structure_valid = self.validate_structure(content)

        # 検証結果の判定
        valid = True

        # 文字数検証
        if char_count < self.min_chars:
            valid = False
            warnings.append(f"文字数不足: {char_count}文字（最低{self.min_chars}文字必要）")

        # 構造検証失敗時の警告
        if not structure_valid:
            valid = False
            if self.require_h1 and h1_count == 0:
                warnings.append("H1見出しが見つかりません")
            if self.require_h2 and h2_count == 0:
                warnings.append("H2見出しが見つかりません")

        # 画像リンク検証
        if self.require_images and image_count == 0:
            valid = False
            warnings.append("画像リンクが見つかりません")

        if broken_links:
            valid = False
            warnings.append(f"壊れた画像リンク: {len(broken_links)}件")

        return {
            "valid": valid,
            "warnings": warnings,
            "metrics": {
                "char_count": char_count,
                "h1_count": h1_count,
                "h2_count": h2_count,
                "image_count": image_count,
                "broken_links": broken_links
            }
        }

    def validate_structure(self, content: str) -> bool:
        """
        Markdown構造の妥当性を検証（H1, H2, 画像リンク）

        Args:
            content: Markdownテキスト

        Returns:
            構造が有効ならTrue
        """
        # H1見出しチェック
        if self.require_h1:
            if '\n# ' not in content and not content.startswith('# '):
                return False

        # H2見出しチェック
        if self.require_h2:
            if '\n## ' not in content:
                return False

        return True

    def validate_image_links(self, content: str, screenshot_paths: List[Path]) -> List[str]:
        """
        画像リンクの存在確認

        Args:
            content: Markdownテキスト
            screenshot_paths: 実在する画像パス

        Returns:
            壊れたリンクのリスト（空なら全て有効）
        """
        import re

        # Markdownの画像リンクを抽出
        image_pattern = r'!\[.*?\]\((.*?)\)'
        image_links = re.findall(image_pattern, content)

        # 実在する画像ファイル名のセット作成
        valid_filenames = set()
        for path in screenshot_paths:
            valid_filenames.add(path.name)
            # 相対パス形式も追加（screenshots/ファイル名）
            valid_filenames.add(f"screenshots/{path.name}")

        # 壊れたリンクを検出
        broken_links = []
        for link in image_links:
            # リンクからファイル名を抽出
            link_basename = Path(link).name

            # ファイル名または相対パスが実在するかチェック
            if link not in valid_filenames and link_basename not in valid_filenames:
                broken_links.append(link)

        return broken_links


class PromptTemplateManager:
    """
    プロンプトテンプレートを管理し、str.format()で変数置換を行う
    Task 1: プロンプトテンプレート管理機能の実装
    """

    def __init__(self, template_dir: str = "prompts") -> None:
        """
        Args:
            template_dir: テンプレートファイル格納ディレクトリ
        """
        self.template_dir = Path(template_dir)

    def load_template(self, template_name: str) -> str:
        """
        外部ファイルからテンプレートを読み込み

        Args:
            template_name: テンプレートファイル名
                - "article_with_audio.txt": 音声文字起こしがある場合
                - "article_without_audio.txt": 音声文字起こしがない場合

        Returns:
            テンプレート文字列（プレーンテキスト、{変数名}形式）

        Raises:
            FileNotFoundError: ファイルが存在しない場合（警告ログ後デフォルト返却）
        """
        template_path = self.template_dir / template_name

        try:
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            print(f"WARN: テンプレートファイル読み込みエラー ({template_path}): {e}")

        # ファイルが存在しないか読み込みエラーの場合はデフォルトを使用
        print(f"INFO: デフォルトテンプレートを使用します (template={template_name})")
        with_audio = "with_audio" in template_name
        return self.get_default_template(with_audio=with_audio)

    def render(self, template: str, variables: Dict[str, any]) -> str:
        """
        テンプレートに変数を適用してレンダリング（str.format()使用）

        Args:
            template: プレーンテキストテンプレート文字列
            variables: 置換変数辞書
                {
                    "app_name": str,
                    "total_screenshots": int,
                    ...
                }

        Returns:
            レンダリング済みプロンプトテキスト

        Raises:
            KeyError: 必須変数が欠落している場合
        """
        return template.format(**variables)

    def get_default_template(self, with_audio: bool = True) -> str:
        """
        デフォルトプロンプトテンプレートを返却（フォールバック用）

        Args:
            with_audio: 音声文字起こしあり用のテンプレートを返すか

        Returns:
            デフォルトテンプレート文字列
        """
        if with_audio:
            return """あなたは{app_name}の魅力を伝える技術ライターです。

以下の{total_screenshots}枚のスクリーンショット画像を分析してください。
各スクリーンショットには音声解説のテキストが付与されています。画像の視覚情報と音声解説を統合して、アプリの機能と価値提案を分析してください。

## タスク
1. 各画像のUI特徴と機能を分析する
2. 音声解説から開発者の意図やアプリの価値提案を抽出する
3. 読者がワクワクする文章で、ストーリー性のある記事を構成する

## 記事構成
- H1: 魅力的なタイトル（アプリ名を含む）
- H2: 論理的なセクション区切り（導入 → 機能紹介 → まとめの流れ）
- 各スクリーンショットに対してコンテキストに沿った説明文を生成
- 技術仕様ではなくユーザー体験と利点に焦点を当てる

## 出力形式
Markdown形式で出力してください。画像リンクは `![説明](screenshots/ファイル名.png)` 形式で記述してください。
"""
        else:
            return """あなたは{app_name}の魅力を伝える技術ライターです。

以下の{total_screenshots}枚のスクリーンショット画像を分析してください。
音声解説はありません。画像の視覚情報のみから、UIの特徴と機能を推測して記事を作成してください。

## タスク
1. 各画像のUI要素と機能を分析する
2. 画像から機能の目的を推測する
3. 読者がワクワクする文章で、ストーリー性のある記事を構成する

## 記事構成
- H1: 魅力的なタイトル（アプリ名を含む）
- H2: 論理的なセクション区切り（導入 → 機能紹介 → まとめの流れ）
- 各スクリーンショットに対してコンテキストに沿った説明文を生成
- 技術仕様ではなくユーザー体験と利点に焦点を当てる

## 出力形式
Markdown形式で出力してください。画像リンクは `![説明](screenshots/ファイル名.png)` 形式で記述してください。
"""


class AIContentGenerator:
    """
    マルチモーダルAI（Claude API）を使用して高品質なアプリ紹介記事を生成するクラス
    Task 4.1: Claude API呼び出し機能の実装
    """

    def __init__(self,
                 output_dir: str,
                 api_key: Optional[str] = None,
                 model: str = "claude-sonnet-4-5-20250929",
                 max_tokens: int = 4000) -> None:
        """
        Args:
            output_dir: 出力ディレクトリパス
            api_key: Claude APIキー（Noneの場合は環境変数から取得）
            model: 使用するClaudeモデル名（デフォルト: claude-sonnet-4-5-20250929）
            max_tokens: 最大出力トークン数

        Raises:
            ValueError: APIキーが未設定の場合
        """
        self.output_dir = Path(output_dir)
        self.model = model
        self.max_tokens = max_tokens

        # APIキーの取得と検証
        if api_key:
            # 明示的に渡されたAPIキーを使用
            self.api_key = api_key
        else:
            # 環境変数から取得
            self.api_key = os.environ.get('ANTHROPIC_API_KEY')
            if not self.api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY environment variable is not set. "
                    "Please set it or pass api_key parameter."
                )

        # Anthropicクライアントの初期化
        try:
            import anthropic
            self.anthropic = anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError(
                "anthropic package is not installed. "
                "Please install it with: pip install anthropic"
            )

    def call_api_with_retry(self,
                           request_data: Dict,
                           max_retries: int = 3) -> any:
        """
        シンプルなリトライ戦略でClaude APIを呼び出し
        Task 4.2: エラーハンドリングとリトライ戦略の実装

        Args:
            request_data: APIリクエストパラメータ
            max_retries: 最大リトライ回数（デフォルト: 3）

        Returns:
            Claude APIレスポンス

        Raises:
            anthropic.RateLimitError: レート制限超過（リトライ上限到達）
            anthropic.AuthenticationError: 認証エラー（リトライ不可）
            anthropic.APIError: その他のAPIエラー
        """
        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(**request_data)
                return response

            except self.anthropic.RateLimitError as e:
                # 429レート制限エラー: リトライ対象
                if attempt == max_retries - 1:
                    # 最大リトライ回数に到達
                    print(f"ERROR: レート制限超過。最大リトライ回数（{max_retries}）に到達しました。")
                    raise

                # retry-afterヘッダーを優先、なければ3秒待機
                retry_after = 3.0  # デフォルト
                if hasattr(e, 'response') and hasattr(e.response, 'headers'):
                    retry_after_header = e.response.headers.get('retry-after')
                    if retry_after_header:
                        retry_after = float(retry_after_header)

                print(f"WARN: レート制限到達。{retry_after}秒後にリトライ（試行 {attempt + 1}/{max_retries}）")
                time.sleep(retry_after)

            except self.anthropic.ServiceUnavailableError as e:
                # 529サーバー過負荷エラー: リトライ対象
                if attempt == max_retries - 1:
                    # 最大リトライ回数に到達
                    print(f"ERROR: APIサーバー過負荷。最大リトライ回数（{max_retries}）に到達しました。")
                    raise

                print(f"WARN: APIサーバー過負荷。3秒後にリトライ（試行 {attempt + 1}/{max_retries}）")
                time.sleep(3.0)

            except self.anthropic.AuthenticationError as e:
                # 401認証エラー: リトライ不可、即座にエラー終了
                print(f"ERROR: Claude API認証エラー。ANTHROPIC_API_KEYを確認してください: {e}")
                raise

            except self.anthropic.APIError as e:
                # その他のAPIエラー（4xx、5xx）: リトライ不可、詳細ログ出力
                error_details = f"status_code={getattr(e, 'status_code', 'unknown')}, message={str(e)}"
                print(f"ERROR: Claude APIエラー - {error_details}")
                raise

        # ここには到達しないはず（すべてのケースでreturnまたはraise）
        raise RuntimeError("Unexpected error in call_api_with_retry")

    def generate_article(self,
                        synchronized_data: List[Dict],
                        app_name: str = "アプリ",
                        output_format: str = "markdown") -> Dict[str, any]:
        """
        スクリーンショット・メタデータ・音声文字起こしから高品質記事を生成
        Task 7: AIContentGeneratorクラスの統合実装

        Args:
            synchronized_data: タイムスタンプ同期済みデータ
                [{"screenshot": {...}, "transcript": {...}, "matched": bool}, ...]
            app_name: アプリ名（プロンプトテンプレート変数）
            output_format: 出力形式（"markdown" or "html"）

        Returns:
            {
                "content": str,  # 生成された記事テキスト
                "metadata": {
                    "model": str,
                    "prompt_version": str,
                    "generated_at": str,
                    "total_screenshots": int,
                    "transcript_available": bool,
                    "quality_score": float
                }
            }

        Raises:
            ValueError: 入力データが不正な場合
            anthropic.APIError: API呼び出し失敗（リトライ後）
        """
        from datetime import datetime
        import base64

        # 入力データ検証
        if not synchronized_data:
            raise ValueError("synchronized_data is empty")

        # スクリーンショット画像パスと音声文字起こしを抽出
        screenshot_paths = []
        transcript_available = False

        for item in synchronized_data:
            screenshot_info = item.get("screenshot")
            if screenshot_info and "file_path" in screenshot_info:
                screenshot_paths.append(Path(screenshot_info["file_path"]))

            transcript_info = item.get("transcript")
            if transcript_info and transcript_info.get("text"):
                transcript_available = True

        if not screenshot_paths:
            raise ValueError("No valid screenshot paths found in synchronized_data")

        # 画像をbase64エンコード
        content_blocks = []
        for img_path in screenshot_paths:
            if not img_path.exists():
                print(f"WARN: 画像ファイルが見つかりません: {img_path}")
                continue

            # 画像を読み込んでbase64エンコード
            with open(img_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')

            content_blocks.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": image_data
                }
            })

        # プロンプトテンプレートを選択・レンダリング
        prompt_manager = PromptTemplateManager()

        if transcript_available:
            template_name = "article_with_audio.txt"
        else:
            template_name = "article_without_audio.txt"

        template = prompt_manager.load_template(template_name)
        prompt_text = prompt_manager.render(template, {
            "app_name": app_name,
            "total_screenshots": len(screenshot_paths)
        })

        # テキストプロンプトブロックを追加
        content_blocks.append({
            "type": "text",
            "text": prompt_text
        })

        # Claude APIリクエスト作成
        request_data = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": content_blocks
                }
            ]
        }

        # API呼び出し（リトライあり）
        print(f"INFO: Claude APIに記事生成をリクエスト中... (model={self.model}, screenshots={len(screenshot_paths)})")
        response = self.call_api_with_retry(request_data)

        # 記事テキストを抽出
        article_content = response.content[0].text

        # 品質検証
        validator = QualityValidator()
        quality_result = validator.validate_quality(article_content, screenshot_paths)

        # API使用統計の計算
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        # コスト計算: Input $3/MTok, Output $15/MTok (2025年現在の概算)
        total_cost_usd = (input_tokens * 3 + output_tokens * 15) / 1_000_000

        # メタデータ構築
        metadata = {
            "model": self.model,
            "prompt_version": "1.0.0",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "total_screenshots": len(screenshot_paths),
            "transcript_available": transcript_available,
            "quality_valid": quality_result["valid"],
            "quality_warnings": quality_result["warnings"],
            "quality_metrics": quality_result["metrics"],
            "api_usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_cost_usd": round(total_cost_usd, 6)
            }
        }

        return {
            "content": article_content,
            "metadata": metadata
        }

    def save_article(self, content: str, metadata: Dict) -> Path:
        """
        生成記事とメタデータをファイルに保存
        Task 6: 記事生成メタデータ管理機能の実装

        Args:
            content: 記事テキスト
            metadata: 生成メタデータ

        Returns:
            保存先ファイルパス（ai_article.md）
        """
        # ai_article.mdとして保存
        article_path = self.output_dir / "ai_article.md"
        with open(article_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # ai_metadata.jsonとして保存
        metadata_path = self.output_dir / "ai_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        return article_path


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

    # NEW: AI記事生成オプション（Task 8）
    parser.add_argument('--ai-article', action='store_true',
                       help='AI（Claude API）による高品質記事を生成（任意）')
    parser.add_argument('--app-name', type=str, default=None,
                       help='アプリ名（任意、未指定時は動画ファイル名から推測）')
    parser.add_argument('--ai-model', type=str,
                       default='claude-sonnet-4-5-20250929',
                       choices=['claude-haiku-4-5-20251001',
                                'claude-sonnet-4-5-20250929',
                                'claude-opus-4-1-20250805'],
                       help='使用するClaudeモデル（デフォルト: claude-sonnet-4-5-20250929）\n'
                            '  - haiku-4-5: 高速・安価（$1/$5 per MTok）\n'
                            '  - sonnet-4-5: 安定・中庸（$3/$15 per MTok、推奨）\n'
                            '  - opus-4-1: 高精度・高価（$15/$75 per MTok）')
    parser.add_argument('--output-format', type=str,
                       default='markdown',
                       choices=['markdown', 'html'],
                       help='AI記事の出力形式（デフォルト: markdown）')

    return parser


def run_integration_flow(video_path: str,
                         output_dir: str,
                         audio_path: Optional[str],
                         markdown: bool,
                         ai_article: bool,  # NEW (Task 8)
                         app_name: Optional[str],  # NEW (Task 8)
                         ai_model: str,  # NEW (Task 8)
                         output_format: str,  # NEW (Task 8)
                         model_size: str,
                         threshold: int,
                         interval: float,
                         count: int) -> None:
    """
    統合処理フローを実行（Task 4.2, Task 8）

    Args:
        video_path: 入力動画ファイルパス
        output_dir: 出力ディレクトリ
        audio_path: 音声ファイルパス（None可）
        markdown: Markdown生成フラグ
        ai_article: AI記事生成フラグ（NEW - Task 8）
        app_name: アプリ名（NEW - Task 8、未指定時は動画ファイル名から推測）
        ai_model: Claude APIモデル名（NEW - Task 8）
        output_format: 出力形式（NEW - Task 8）
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

    # Add file_path to each metadata item for AI article generation
    screenshots_dir = Path(output_dir) / "screenshots"
    for m in metadata:
        m["file_path"] = str(screenshots_dir / m["filename"])

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

        # 音声認識実行
        transcript_data = audio_processor.transcribe_audio(language="ja")

        # 動画・音声長さの検証（音声認識後に実行）
        video_duration = extractor.video_duration
        if not audio_processor.validate_duration_match(video_duration):
            sys.exit(1)

        # 音声認識結果を保存
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

    # NEW: AI記事生成（Task 8, 9）
    if ai_article:
        print("\n" + "=" * 60)
        print("  AI Article Generation")
        print("=" * 60)
        print()

        # 同期処理（markdown未実行の場合）
        if not markdown:
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

        # アプリ名を決定（Task 8）
        if app_name:
            final_app_name = app_name
        else:
            # 動画ファイル名から拡張子を除去してアプリ名として使用
            final_app_name = Path(video_path).stem
            if not final_app_name or final_app_name.startswith('.'):
                # ファイル名が無効な場合はデフォルトを使用
                final_app_name = "アプリ"
                print(f"⚠️  Warning: 動画ファイル名からアプリ名を推測できませんでした。デフォルト値 '{final_app_name}' を使用します。")

        # AI記事生成器の初期化
        try:
            ai_generator = AIContentGenerator(
                output_dir=output_dir,
                model=ai_model,
                max_tokens=4000
            )

            # 記事生成
            result = ai_generator.generate_article(
                synchronized_data=synchronized,
                app_name=final_app_name,
                output_format=output_format
            )

            # 記事とメタデータの保存（Task 9）
            ai_generator.save_article(result["content"], result["metadata"])

            # 品質検証結果表示
            if not result["metadata"].get("quality_valid", True):
                print("⚠️  Warning: 生成記事が品質基準を満たしていない可能性があります")
                for warning in result["metadata"].get("quality_warnings", []):
                    print(f"  - {warning}")

            print(f"\n✓ AI記事生成完了: {output_dir}/ai_article.md")
            print(f"✓ メタデータ保存完了: {output_dir}/ai_metadata.json")

        except ValueError as e:
            print(f"\n✗ AI記事生成エラー: {e}")
            print("ヒント: ANTHROPIC_API_KEY環境変数を設定してください")
            # 既存機能は影響を受けない（フォールスルー）
        except Exception as e:
            print(f"\n✗ AI記事生成エラー: {e}")
            # 既存機能は影響を受けない（フォールスルー）


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

    # 統合処理フローを実行（Task 4.2, 4.3, Task 8）
    run_integration_flow(
        video_path=args.input,
        output_dir=args.output,
        audio_path=args.audio,
        markdown=args.markdown,
        ai_article=args.ai_article,  # NEW (Task 8)
        app_name=args.app_name,  # NEW (Task 8)
        ai_model=args.ai_model,  # NEW (Task 8)
        output_format=args.output_format,  # NEW (Task 8)
        model_size=args.model_size,
        threshold=args.threshold,
        interval=args.interval,
        count=args.count
    )

    print("\nSuccess!")
    sys.exit(0)


if __name__ == '__main__':
    main()
