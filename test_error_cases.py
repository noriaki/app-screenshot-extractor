#!/usr/bin/env python3
"""
Error Case Tests for AI Model Upgrade

This script tests error handling for invalid/deprecated model names.
Run this manually to verify error messages are clear and helpful.

Usage:
    python test_error_cases.py

Tests:
    1. Deprecated model name (claude-3-5-sonnet-20241022)
    2. Invalid model name (invalid-model)
    3. Help message shows all models with pricing
"""

import subprocess
import sys
from typing import Dict, List

# Test cases
ERROR_CASES = [
    {
        "name": "Deprecated model (claude-3-5-sonnet-20241022)",
        "model": "claude-3-5-sonnet-20241022",
        "expected_exit_code": 2,
        "expected_in_stderr": [
            "invalid choice",
            "claude-haiku-4-5-20251001",
            "claude-sonnet-4-5-20250929",
            "claude-opus-4-1-20250805"
        ]
    },
    {
        "name": "Invalid model name",
        "model": "invalid-model",
        "expected_exit_code": 2,
        "expected_in_stderr": [
            "invalid choice",
            "claude-haiku-4-5-20251001",
            "claude-sonnet-4-5-20250929",
            "claude-opus-4-1-20250805"
        ]
    }
]


def test_error_case(test_case: Dict) -> bool:
    """Test a single error case."""
    print(f"\n{'='*60}")
    print(f"Testing: {test_case['name']}")
    print(f"{'='*60}")

    cmd = [
        "python", "extract_screenshots.py",
        "-i", "dummy.mp4",  # Doesn't need to exist (argparse fails first)
        "--ai-article",
        "--ai-model", test_case["model"]
    ]

    print(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        # Check exit code
        if result.returncode != test_case["expected_exit_code"]:
            print(f"❌ Exit code mismatch:")
            print(f"   Expected: {test_case['expected_exit_code']}")
            print(f"   Got: {result.returncode}")
            return False

        print(f"✅ Exit code: {result.returncode}")

        # Check stderr content
        stderr = result.stderr
        print(f"\nSTDERR output:")
        print(stderr)

        for expected_text in test_case["expected_in_stderr"]:
            if expected_text not in stderr:
                print(f"❌ Expected text not found in stderr: '{expected_text}'")
                return False

        print(f"\n✅ All expected error messages found")
        return True

    except subprocess.TimeoutExpired:
        print(f"❌ Command timed out")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_help_message() -> bool:
    """Test that help message shows all models with pricing."""
    print(f"\n{'='*60}")
    print("Testing: Help message")
    print(f"{'='*60}")

    cmd = ["python", "extract_screenshots.py", "--help"]

    print(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if result.returncode != 0:
            print(f"❌ Help command failed with exit code {result.returncode}")
            return False

        stdout = result.stdout
        print(f"\nSearching for --ai-model help text...")

        # Expected content in help
        expected_in_help = [
            "--ai-model",
            "claude-haiku-4-5-20251001",
            "claude-sonnet-4-5-20250929",
            "claude-opus-4-1-20250805",
            "haiku",
            "sonnet",
            "opus"
        ]

        for expected_text in expected_in_help:
            if expected_text not in stdout:
                print(f"❌ Expected text not found in help: '{expected_text}'")
                return False

        print(f"✅ All expected help content found")

        # Extract and display --ai-model help section
        lines = stdout.split('\n')
        in_ai_model_section = False
        print(f"\n--ai-model help section:")
        print("-" * 60)
        for line in lines:
            if '--ai-model' in line:
                in_ai_model_section = True
            if in_ai_model_section:
                print(line)
                if line.strip() and not line.startswith(' ') and '--ai-model' not in line:
                    break

        return True

    except subprocess.TimeoutExpired:
        print(f"❌ Command timed out")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def print_summary(results: List[bool]):
    """Print test summary."""
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")

    passed = sum(1 for r in results if r)
    failed = len(results) - passed

    print(f"\nTotal: {len(results)} tests")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")

    print(f"\n{'='*60}")

    if failed == 0:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")

    print(f"{'='*60}")

    return failed == 0


def main():
    """Main entry point."""
    print("Error Case Tests for AI Model Upgrade")
    print("="*60)

    results = []

    # Test error cases
    for test_case in ERROR_CASES:
        result = test_error_case(test_case)
        results.append(result)

    # Test help message
    result = test_help_message()
    results.append(result)

    # Print summary
    all_passed = print_summary(results)

    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
