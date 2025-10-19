"""
InputValidator - 入力データ検証機能

スクリーンショット画像ファイル、メタデータJSON、音声文字起こしJSONの
存在確認と妥当性検証を行う。
入力データが不正または欠損している場合は適切なエラー処理を実行する。
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import json


class InputValidator:
    """
    入力データの検証を行うクラス

    検証対象:
    - スクリーンショット画像ファイルの存在確認
    - メタデータJSON（metadata.json）の読み込みと検証
    - 音声文字起こしJSON（transcript.json）の存在確認と読み込み
    - 入力データの不正または欠損時のエラー処理
    """

    def __init__(self, output_dir: str) -> None:
        """
        Args:
            output_dir: 出力ディレクトリパス
        """
        self.output_dir = Path(output_dir)
        self.screenshots_dir = self.output_dir / "screenshots"

    def validate_input_data(
        self,
        metadata_path: Path,
        transcript_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        入力データ全体の妥当性を検証

        Args:
            metadata_path: メタデータJSONファイルのパス
            transcript_path: 音声文字起こしJSONファイルのパス（任意）

        Returns:
            {
                "valid": bool,  # 検証成功ならTrue
                "screenshots_count": int,  # スクリーンショット数
                "has_transcript": bool,  # 文字起こしデータの有無
                "warnings": List[str]  # 警告メッセージリスト
            }

        Raises:
            FileNotFoundError: 必須ファイル（metadata.json）が存在しない場合
            ValueError: データ形式が不正な場合
        """
        warnings = []

        # メタデータJSONの読み込みと検証
        metadata = self.load_metadata(metadata_path)

        # メタデータが空でないことを確認
        if not metadata or len(metadata) == 0:
            raise ValueError("メタデータが空です。スクリーンショットが見つかりませんでした。")

        # スクリーンショット画像ファイルの存在確認
        missing_files = self.check_screenshot_files(metadata)
        if missing_files:
            warnings.append(f"{len(missing_files)}個の画像ファイルが見つかりません: {', '.join(missing_files[:3])}")

        # 音声文字起こしJSONの読み込み（任意）
        has_transcript = False
        if transcript_path:
            try:
                transcript = self.load_transcript(transcript_path)
                has_transcript = True
            except FileNotFoundError:
                warnings.append(f"音声文字起こしファイルが見つかりません: {transcript_path}")
                has_transcript = False

        return {
            "valid": True,
            "screenshots_count": len(metadata),
            "has_transcript": has_transcript,
            "warnings": warnings
        }

    def load_metadata(self, metadata_path: Path) -> List[Dict]:
        """
        メタデータJSONを読み込む

        Args:
            metadata_path: メタデータJSONファイルのパス

        Returns:
            メタデータのリスト（各要素はスクリーンショット情報の辞書）

        Raises:
            FileNotFoundError: ファイルが存在しない場合
            ValueError: JSON形式が不正な場合
        """
        if not metadata_path.exists():
            raise FileNotFoundError(f"メタデータファイルが見つかりません: {metadata_path}")

        try:
            metadata_text = metadata_path.read_text(encoding="utf-8")
            metadata = json.loads(metadata_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"メタデータJSONの形式が不正です: {e}")

        if not isinstance(metadata, list):
            raise ValueError("メタデータは配列形式である必要があります。")

        return metadata

    def load_transcript(self, transcript_path: Path) -> Dict:
        """
        音声文字起こしJSONを読み込む

        Args:
            transcript_path: 音声文字起こしJSONファイルのパス

        Returns:
            文字起こしデータの辞書（segments、language、textを含む）

        Raises:
            FileNotFoundError: ファイルが存在しない場合
            ValueError: JSON形式が不正な場合
        """
        if not transcript_path.exists():
            raise FileNotFoundError(f"音声文字起こしファイルが見つかりません: {transcript_path}")

        try:
            transcript_text = transcript_path.read_text(encoding="utf-8")
            transcript = json.loads(transcript_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"音声文字起こしJSONの形式が不正です: {e}")

        if not isinstance(transcript, dict):
            raise ValueError("音声文字起こしデータは辞書形式である必要があります。")

        return transcript

    def check_screenshot_files(self, metadata: List[Dict]) -> List[str]:
        """
        メタデータに記載されたスクリーンショット画像ファイルの存在を確認

        Args:
            metadata: メタデータリスト（各要素にfilenameキーが含まれる）

        Returns:
            欠落しているファイル名のリスト（空なら全て存在）
        """
        missing_files = []

        for item in metadata:
            filename = item.get("filename")
            if not filename:
                continue

            # スクリーンショットディレクトリ内のファイルパス
            file_path = self.screenshots_dir / filename

            if not file_path.exists():
                missing_files.append(filename)

        return missing_files
