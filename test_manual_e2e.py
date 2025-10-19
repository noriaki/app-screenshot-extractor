#!/usr/bin/env python3
"""
Manual E2E Test for AI Model Upgrade

This script tests actual Claude API calls with all three models (Haiku, Sonnet, Opus).
Run this manually after code changes to verify:
- All three models can generate articles successfully
- ai_metadata.json records correct model names
- Quality metadata is properly recorded

Usage:
    python test_manual_e2e.py

Prerequisites:
    - ANTHROPIC_API_KEY environment variable must be set
    - Sample video file must exist at: sample_video/demo.mp4
"""

import json
import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, List

# Test configuration
MODELS = [
    "claude-haiku-4-5-20251001",
    "claude-sonnet-4-5-20250929",
    "claude-opus-4-1-20250805"
]

SAMPLE_VIDEO = "sample_video/demo.mp4"
OUTPUT_BASE_DIR = "output_e2e_test"


def check_prerequisites() -> bool:
    """Check if prerequisites are met."""
    print("Checking prerequisites...")

    # Check API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY environment variable is not set")
        return False
    print("✅ ANTHROPIC_API_KEY is set")

    # Check sample video
    if not Path(SAMPLE_VIDEO).exists():
        print(f"❌ Sample video not found: {SAMPLE_VIDEO}")
        print("   Please provide a sample video file for testing")
        return False
    print(f"✅ Sample video found: {SAMPLE_VIDEO}")

    return True


def run_test_for_model(model_name: str) -> Dict:
    """Run AI article generation test for a specific model."""
    print(f"\n{'='*60}")
    print(f"Testing model: {model_name}")
    print(f"{'='*60}")

    output_dir = f"{OUTPUT_BASE_DIR}/{model_name.replace('claude-', '').replace('-', '_')}"

    # Clean up previous test output
    if Path(output_dir).exists():
        import shutil
        shutil.rmtree(output_dir)

    # Build command
    cmd = [
        "python", "extract_screenshots.py",
        "-i", SAMPLE_VIDEO,
        "-o", output_dir,
        "--ai-article",
        "--ai-model", model_name,
        "--count", "3"  # Limit screenshots for faster testing
    ]

    print(f"Running: {' '.join(cmd)}")

    # Execute command
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode != 0:
            print(f"❌ Command failed with exit code {result.returncode}")
            print(f"STDERR: {result.stderr}")
            return {
                "model": model_name,
                "success": False,
                "error": result.stderr
            }

        print(f"✅ Command succeeded")

        # Validate output files
        metadata_path = Path(output_dir) / "ai_metadata.json"
        article_path = Path(output_dir) / "ai_article.md"

        if not metadata_path.exists():
            print(f"❌ ai_metadata.json not found")
            return {
                "model": model_name,
                "success": False,
                "error": "ai_metadata.json not found"
            }

        if not article_path.exists():
            print(f"❌ ai_article.md not found")
            return {
                "model": model_name,
                "success": False,
                "error": "ai_article.md not found"
            }

        # Read and validate metadata
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        # Verify model name in metadata
        if metadata.get("model") != model_name:
            print(f"❌ Model name mismatch in metadata:")
            print(f"   Expected: {model_name}")
            print(f"   Got: {metadata.get('model')}")
            return {
                "model": model_name,
                "success": False,
                "error": f"Model name mismatch: expected {model_name}, got {metadata.get('model')}"
            }

        print(f"✅ Model name in metadata: {metadata['model']}")

        # Verify usage information
        if "usage" not in metadata:
            print(f"❌ Usage information not found in metadata")
            return {
                "model": model_name,
                "success": False,
                "error": "Usage information not found in metadata"
            }

        input_tokens = metadata["usage"].get("input_tokens", 0)
        output_tokens = metadata["usage"].get("output_tokens", 0)
        print(f"✅ Token usage: {input_tokens} input, {output_tokens} output")

        # Verify article content
        with open(article_path, 'r', encoding='utf-8') as f:
            article_content = f.read()

        if len(article_content) < 100:
            print(f"❌ Article content too short: {len(article_content)} chars")
            return {
                "model": model_name,
                "success": False,
                "error": f"Article content too short: {len(article_content)} chars"
            }

        print(f"✅ Article content length: {len(article_content)} chars")

        # Success
        return {
            "model": model_name,
            "success": True,
            "metadata": metadata,
            "article_length": len(article_content),
            "output_dir": output_dir
        }

    except subprocess.TimeoutExpired:
        print(f"❌ Command timed out (>300s)")
        return {
            "model": model_name,
            "success": False,
            "error": "Command timed out"
        }
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return {
            "model": model_name,
            "success": False,
            "error": str(e)
        }


def print_summary(results: List[Dict]):
    """Print test summary."""
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")

    passed = sum(1 for r in results if r.get("success"))
    failed = len(results) - passed

    print(f"\nTotal: {len(results)} tests")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")

    if failed > 0:
        print(f"\nFailed tests:")
        for r in results:
            if not r.get("success"):
                print(f"  - {r['model']}: {r.get('error', 'Unknown error')}")

    print(f"\n{'='*60}")

    if failed == 0:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")

    print(f"{'='*60}")

    return failed == 0


def main():
    """Main entry point."""
    print("Manual E2E Test for AI Model Upgrade")
    print("="*60)

    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Exiting.")
        sys.exit(1)

    # Run tests for all models
    results = []
    for model in MODELS:
        result = run_test_for_model(model)
        results.append(result)

    # Print summary
    all_passed = print_summary(results)

    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
