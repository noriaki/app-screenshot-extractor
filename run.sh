#!/bin/bash
# App Screenshot Extractor - 実行スクリプト

# スクリプトのディレクトリを取得
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 仮想環境をアクティベート
source "$SCRIPT_DIR/.venv/bin/activate"

# Pythonスクリプトを実行（引数をそのまま渡す）
python "$SCRIPT_DIR/extract_screenshots.py" "$@"
