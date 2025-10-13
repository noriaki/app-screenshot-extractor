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


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='App Screenshot Extractor - 動画から最適なスクリーンショットを自動抽出',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  %(prog)s -i app_demo.mp4
  %(prog)s -i app_demo.mp4 -c 15 -t 20
  %(prog)s -i app_demo.mp4 -o ~/Documents/screenshots
        """
    )

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

    args = parser.parse_args()

    # バナー表示
    print("=" * 60)
    print("  App Screenshot Extractor")
    print("  Automatically extract optimal screenshots from app videos")
    print("=" * 60)
    print()

    # 抽出実行
    extractor = ScreenshotExtractor(
        video_path=args.input,
        output_dir=args.output,
        transition_threshold=args.threshold,
        min_time_interval=args.interval,
        target_count=args.count
    )

    metadata = extractor.extract_screenshots()

    if len(metadata) == 0:
        print("\nError: No screenshots extracted")
        sys.exit(1)

    print("\nSuccess!")
    sys.exit(0)


if __name__ == '__main__':
    main()
