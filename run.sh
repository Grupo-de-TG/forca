#!/usr/bin/env bash
# Launcher para o Jogo da Forca TUI (Textual)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$SCRIPT_DIR/.venv/bin/python" ]; then
    PYTHON_EXEC="$SCRIPT_DIR/.venv/bin/python"
else
    PYTHON_EXEC="python3"
fi

exec "$PYTHON_EXEC" "$SCRIPT_DIR/forca_app.py" "$@"
