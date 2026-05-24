#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=/dev/null
source "$SCRIPT_DIR/.venv/bin/activate"

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <directory> [object_key]"
    exit 1
fi

DIR="$1"
KEY="${2:-}"

if [[ ! -d "$DIR" ]]; then
    echo "Error: '$DIR' is not a directory"
    exit 1
fi

LATEST_FILE="$(ls -t "$DIR" | head -n 1)"

if [[ -z "$LATEST_FILE" ]]; then
    echo "Error: no files found in '$DIR'"
    exit 1
fi

FILE_PATH="$DIR/$LATEST_FILE"
echo "Latest file: $FILE_PATH"

if [[ -n "$KEY" ]]; then
    python3 "$SCRIPT_DIR/upload.py" "$FILE_PATH" "$KEY"
else
    python3 "$SCRIPT_DIR/upload.py" "$FILE_PATH"
fi

echo "Deleting files older than 7 days in '$DIR'..."
find "$DIR" -maxdepth 1 -type f -mtime +7 -print -delete
echo "Cleanup done."
