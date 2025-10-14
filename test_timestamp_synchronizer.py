#!/usr/bin/env python3
"""
TimestampSynchronizer のテストスイート
Task 2: タイムスタンプ同期機能のテスト
"""

import unittest
from typing import List, Dict, Optional


class TestTimestampSynchronizerFindNearestTranscript(unittest.TestCase):
    """TimestampSynchronizer.find_nearest_transcript() のテスト"""

    def test_find_nearest_transcript_returns_closest_segment(self):
        """最も近い音声セグメントを返す"""
        # Given: スクリーンショット時刻15.0秒と3つの音声セグメント
        screenshot_time = 15.0
        transcripts = [
            {'start': 10.0, 'end': 13.0, 'text': 'セグメント1'},
            {'start': 14.0, 'end': 17.0, 'text': 'セグメント2'},
            {'start': 20.0, 'end': 23.0, 'text': 'セグメント3'}
        ]

        # When: find_nearest_transcriptを実行
        from extract_screenshots import TimestampSynchronizer
        synchronizer = TimestampSynchronizer(tolerance=5.0)
        result = synchronizer.find_nearest_transcript(screenshot_time, transcripts)

        # Then: セグメント2が最も近い（中央時刻15.5秒、距離0.5秒）
        self.assertIsNotNone(result)
        self.assertEqual(result['text'], 'セグメント2')

    def test_find_nearest_transcript_returns_none_when_outside_tolerance(self):
        """許容範囲外の場合はNoneを返す"""
        # Given: スクリーンショット時刻15.0秒と遠い音声セグメント
        screenshot_time = 15.0
        transcripts = [
            {'start': 25.0, 'end': 28.0, 'text': 'セグメント1'},  # 中央21.5秒、距離10.5秒
            {'start': 30.0, 'end': 33.0, 'text': 'セグメント2'}   # 中央31.5秒、距離16.5秒
        ]

        # When: find_nearest_transcriptを実行（tolerance=5.0）
        from extract_screenshots import TimestampSynchronizer
        synchronizer = TimestampSynchronizer(tolerance=5.0)
        result = synchronizer.find_nearest_transcript(screenshot_time, transcripts)

        # Then: Noneを返す
        self.assertIsNone(result)

    def test_find_nearest_transcript_returns_none_for_empty_transcripts(self):
        """音声セグメントが空の場合はNoneを返す"""
        # Given: 空の音声セグメントリスト
        screenshot_time = 15.0
        transcripts = []

        # When: find_nearest_transcriptを実行
        from extract_screenshots import TimestampSynchronizer
        synchronizer = TimestampSynchronizer(tolerance=5.0)
        result = synchronizer.find_nearest_transcript(screenshot_time, transcripts)

        # Then: Noneを返す
        self.assertIsNone(result)

    def test_find_nearest_transcript_uses_segment_center_time(self):
        """セグメントの中央時刻で距離を計算する"""
        # Given: スクリーンショット時刻10.0秒と音声セグメント
        screenshot_time = 10.0
        transcripts = [
            {'start': 8.0, 'end': 12.0, 'text': 'セグメント1'}  # 中央10.0秒、距離0.0秒
        ]

        # When: find_nearest_transcriptを実行
        from extract_screenshots import TimestampSynchronizer
        synchronizer = TimestampSynchronizer(tolerance=5.0)
        result = synchronizer.find_nearest_transcript(screenshot_time, transcripts)

        # Then: セグメント1を返す（中央時刻が一致）
        self.assertIsNotNone(result)
        self.assertEqual(result['text'], 'セグメント1')

    def test_find_nearest_transcript_boundary_exactly_tolerance(self):
        """許容範囲ちょうどの場合はセグメントを返す"""
        # Given: スクリーンショット時刻10.0秒と音声セグメント（距離ちょうど5.0秒）
        screenshot_time = 10.0
        transcripts = [
            {'start': 13.0, 'end': 17.0, 'text': 'セグメント1'}  # 中央15.0秒、距離5.0秒
        ]

        # When: find_nearest_transcriptを実行（tolerance=5.0）
        from extract_screenshots import TimestampSynchronizer
        synchronizer = TimestampSynchronizer(tolerance=5.0)
        result = synchronizer.find_nearest_transcript(screenshot_time, transcripts)

        # Then: セグメント1を返す（ちょうど許容範囲内）
        self.assertIsNotNone(result)
        self.assertEqual(result['text'], 'セグメント1')

    def test_find_nearest_transcript_selects_closest_when_multiple_within_tolerance(self):
        """複数が許容範囲内にある場合は最も近いものを返す"""
        # Given: スクリーンショット時刻15.0秒と複数の音声セグメント
        screenshot_time = 15.0
        transcripts = [
            {'start': 10.0, 'end': 12.0, 'text': 'セグメント1'},  # 中央11.0秒、距離4.0秒
            {'start': 13.0, 'end': 15.0, 'text': 'セグメント2'},  # 中央14.0秒、距離1.0秒
            {'start': 16.0, 'end': 20.0, 'text': 'セグメント3'}   # 中央18.0秒、距離3.0秒
        ]

        # When: find_nearest_transcriptを実行
        from extract_screenshots import TimestampSynchronizer
        synchronizer = TimestampSynchronizer(tolerance=5.0)
        result = synchronizer.find_nearest_transcript(screenshot_time, transcripts)

        # Then: 最も近いセグメント2を返す
        self.assertIsNotNone(result)
        self.assertEqual(result['text'], 'セグメント2')


class TestTimestampSynchronizerSynchronize(unittest.TestCase):
    """TimestampSynchronizer.synchronize() のテスト"""

    def test_synchronize_matches_all_screenshots_with_transcripts(self):
        """全てのスクリーンショットに音声セグメントを対応付ける"""
        # Given: 3つのスクリーンショットと3つの音声セグメント
        screenshots = [
            {'timestamp': 10.0, 'filename': 'shot1.png'},
            {'timestamp': 20.0, 'filename': 'shot2.png'},
            {'timestamp': 30.0, 'filename': 'shot3.png'}
        ]
        transcripts = [
            {'start': 8.0, 'end': 12.0, 'text': 'テキスト1'},   # 中央10.0秒
            {'start': 18.0, 'end': 22.0, 'text': 'テキスト2'},  # 中央20.0秒
            {'start': 28.0, 'end': 32.0, 'text': 'テキスト3'}   # 中央30.0秒
        ]

        # When: synchronizeを実行
        from extract_screenshots import TimestampSynchronizer
        synchronizer = TimestampSynchronizer(tolerance=5.0)
        result = synchronizer.synchronize(screenshots, transcripts)

        # Then: 全てのスクリーンショットがマッチング成功
        self.assertEqual(len(result), 3)
        self.assertTrue(result[0]['matched'])
        self.assertTrue(result[1]['matched'])
        self.assertTrue(result[2]['matched'])
        self.assertEqual(result[0]['transcript']['text'], 'テキスト1')
        self.assertEqual(result[1]['transcript']['text'], 'テキスト2')
        self.assertEqual(result[2]['transcript']['text'], 'テキスト3')

    def test_synchronize_returns_none_for_unmatched_screenshots(self):
        """対応する音声がないスクリーンショットはtranscript=Noneを返す"""
        # Given: 2つのスクリーンショットと1つの音声セグメント
        screenshots = [
            {'timestamp': 10.0, 'filename': 'shot1.png'},
            {'timestamp': 30.0, 'filename': 'shot2.png'}  # マッチングしない
        ]
        transcripts = [
            {'start': 8.0, 'end': 12.0, 'text': 'テキスト1'}  # 中央10.0秒
        ]

        # When: synchronizeを実行
        from extract_screenshots import TimestampSynchronizer
        synchronizer = TimestampSynchronizer(tolerance=5.0)
        result = synchronizer.synchronize(screenshots, transcripts)

        # Then: shot1はマッチング成功、shot2は失敗
        self.assertEqual(len(result), 2)
        self.assertTrue(result[0]['matched'])
        self.assertEqual(result[0]['transcript']['text'], 'テキスト1')
        self.assertFalse(result[1]['matched'])
        self.assertIsNone(result[1]['transcript'])

    def test_synchronize_preserves_screenshot_order(self):
        """スクリーンショットの順序を維持する"""
        # Given: タイムスタンプ順のスクリーンショット
        screenshots = [
            {'timestamp': 10.0, 'filename': 'shot1.png'},
            {'timestamp': 20.0, 'filename': 'shot2.png'},
            {'timestamp': 30.0, 'filename': 'shot3.png'}
        ]
        transcripts = [
            {'start': 8.0, 'end': 12.0, 'text': 'テキスト1'}
        ]

        # When: synchronizeを実行
        from extract_screenshots import TimestampSynchronizer
        synchronizer = TimestampSynchronizer(tolerance=5.0)
        result = synchronizer.synchronize(screenshots, transcripts)

        # Then: スクリーンショットの順序が維持される
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]['screenshot']['timestamp'], 10.0)
        self.assertEqual(result[1]['screenshot']['timestamp'], 20.0)
        self.assertEqual(result[2]['screenshot']['timestamp'], 30.0)

    def test_synchronize_includes_all_screenshots(self):
        """結果リストに全てのスクリーンショットが含まれる"""
        # Given: 3つのスクリーンショットと空の音声セグメント
        screenshots = [
            {'timestamp': 10.0, 'filename': 'shot1.png'},
            {'timestamp': 20.0, 'filename': 'shot2.png'},
            {'timestamp': 30.0, 'filename': 'shot3.png'}
        ]
        transcripts = []

        # When: synchronizeを実行
        from extract_screenshots import TimestampSynchronizer
        synchronizer = TimestampSynchronizer(tolerance=5.0)
        result = synchronizer.synchronize(screenshots, transcripts)

        # Then: 全てのスクリーンショットが結果に含まれる（transcript=None）
        self.assertEqual(len(result), 3)
        self.assertFalse(result[0]['matched'])
        self.assertFalse(result[1]['matched'])
        self.assertFalse(result[2]['matched'])
        self.assertIsNone(result[0]['transcript'])
        self.assertIsNone(result[1]['transcript'])
        self.assertIsNone(result[2]['transcript'])

    def test_synchronize_handles_empty_screenshots(self):
        """スクリーンショットが空の場合は空リストを返す"""
        # Given: 空のスクリーンショットリスト
        screenshots = []
        transcripts = [
            {'start': 8.0, 'end': 12.0, 'text': 'テキスト1'}
        ]

        # When: synchronizeを実行
        from extract_screenshots import TimestampSynchronizer
        synchronizer = TimestampSynchronizer(tolerance=5.0)
        result = synchronizer.synchronize(screenshots, transcripts)

        # Then: 空リストを返す
        self.assertEqual(result, [])

    def test_synchronize_matched_flag_consistency(self):
        """matchedフラグとtranscriptの整合性を確認する"""
        # Given: スクリーンショットと音声セグメント
        screenshots = [
            {'timestamp': 10.0, 'filename': 'shot1.png'},
            {'timestamp': 30.0, 'filename': 'shot2.png'}
        ]
        transcripts = [
            {'start': 8.0, 'end': 12.0, 'text': 'テキスト1'}  # shot1のみマッチング
        ]

        # When: synchronizeを実行
        from extract_screenshots import TimestampSynchronizer
        synchronizer = TimestampSynchronizer(tolerance=5.0)
        result = synchronizer.synchronize(screenshots, transcripts)

        # Then: matched=Trueの場合はtranscriptが非None、matched=Falseの場合はNone
        for item in result:
            if item['matched']:
                self.assertIsNotNone(item['transcript'])
            else:
                self.assertIsNone(item['transcript'])


class TestTimestampSynchronizerCalculateDistance(unittest.TestCase):
    """TimestampSynchronizer.calculate_distance() のテスト"""

    def test_calculate_distance_returns_absolute_difference(self):
        """2つのタイムスタンプ間の絶対距離を返す"""
        # Given: 2つのタイムスタンプ
        time1 = 10.0
        time2 = 15.0

        # When: calculate_distanceを実行
        from extract_screenshots import TimestampSynchronizer
        synchronizer = TimestampSynchronizer()
        distance = synchronizer.calculate_distance(time1, time2)

        # Then: 絶対距離5.0を返す
        self.assertAlmostEqual(distance, 5.0, places=1)

    def test_calculate_distance_handles_negative_difference(self):
        """time1 > time2の場合も正しい絶対距離を返す"""
        # Given: time1がtime2より大きい
        time1 = 20.0
        time2 = 12.0

        # When: calculate_distanceを実行
        from extract_screenshots import TimestampSynchronizer
        synchronizer = TimestampSynchronizer()
        distance = synchronizer.calculate_distance(time1, time2)

        # Then: 絶対距離8.0を返す
        self.assertAlmostEqual(distance, 8.0, places=1)

    def test_calculate_distance_zero_when_equal(self):
        """同じ時刻の場合は距離0を返す"""
        # Given: 同じタイムスタンプ
        time1 = 15.0
        time2 = 15.0

        # When: calculate_distanceを実行
        from extract_screenshots import TimestampSynchronizer
        synchronizer = TimestampSynchronizer()
        distance = synchronizer.calculate_distance(time1, time2)

        # Then: 距離0を返す
        self.assertAlmostEqual(distance, 0.0, places=1)


class TestTimestampSynchronizerInitialization(unittest.TestCase):
    """TimestampSynchronizer の初期化テスト"""

    def test_init_default_tolerance(self):
        """デフォルトのtoleranceが5.0秒であることを確認する"""
        # Given/When: TimestampSynchronizerをデフォルト引数で初期化
        from extract_screenshots import TimestampSynchronizer
        synchronizer = TimestampSynchronizer()

        # Then: toleranceが5.0秒
        self.assertEqual(synchronizer.tolerance, 5.0)

    def test_init_custom_tolerance(self):
        """カスタムtoleranceを設定できることを確認する"""
        # Given/When: TimestampSynchronizerをカスタムtolerance=10.0で初期化
        from extract_screenshots import TimestampSynchronizer
        synchronizer = TimestampSynchronizer(tolerance=10.0)

        # Then: toleranceが10.0秒
        self.assertEqual(synchronizer.tolerance, 10.0)


if __name__ == '__main__':
    unittest.main()
