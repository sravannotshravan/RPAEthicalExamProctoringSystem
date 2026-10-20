#!/usr/bin/env bash
# Ethical Online Exam Proctoring POC - Startup Script
# Usage: ./start.sh [--port 5000] [--seed] [--test] [--skip-install]
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PORT="${PORT:-5000}"
SEED=0
RUN_TESTS=0
SKIP_INSTALL=0
while [ $# -gt 0 ]; do
    case "$1" in
        --port) PORT="$2"; shift 2 ;;
        --seed) SEED=1; shift ;;
        --test) RUN_TESTS=1; shift ;;
        --skip-install) SKIP_INSTALL=1; shift ;;
        *) echo "[ERROR] Unknown option: $1"; exit 1 ;;
    esac
done

echo "=========================================================="
echo "   Ethical Online Exam Proctoring POC - Startup Script   "
echo "=========================================================="

# 1. Virtual environment check
if [ ! -d ".venv" ]; then
    echo "[*] Virtual environment not found. Creating .venv..."
    python3 -m venv .venv 2>/dev/null || python -m venv .venv
fi

# Detect Python inside venv (supports Unix and Windows Git Bash / Cygwin)
if [ -f ".venv/Scripts/python.exe" ]; then
    PYTHON=".venv/Scripts/python.exe"
elif [ -f ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
else
    echo "[ERROR] Could not find python executable in .venv"
    exit 1
fi

# 2. Dependencies: reinstall when requirements.txt is newer than the last install stamp
STAMP=".venv/.requirements-installed"
if [ "$SKIP_INSTALL" -eq 0 ]; then
    if [ ! -f "$STAMP" ] || [ requirements.txt -nt "$STAMP" ] \
        || ! "$PYTHON" -c "import flask, flask_sqlalchemy, cv2, numpy" 2>/dev/null; then
        echo "[*] Installing dependencies from requirements.txt..."
        "$PYTHON" -m pip install --disable-pip-version-check -r requirements.txt
        date > "$STAMP"
    else
        echo "[OK] Dependencies up to date."
    fi
fi

# 3. .env: add missing keys only. The UiPath key must match uipath/ExamProctoring/Data/config.json.
touch .env
UIPATH_KEY="$("$PYTHON" -c "import json; print(json.load(open('uipath/ExamProctoring/Data/config.json'))['ApiKey'])" 2>/dev/null || echo poc-uipath-local-key)"
if ! grep -q '^[[:space:]]*UIPATH_API_KEY[[:space:]]*=' .env; then
    echo "UIPATH_API_KEY=${UIPATH_KEY}" >> .env
    echo "[OK] Added UIPATH_API_KEY to .env"
fi
if ! grep -q '^[[:space:]]*SECRET_KEY[[:space:]]*=' .env; then
    echo "SECRET_KEY=$("$PYTHON" -c "import secrets; print(secrets.token_hex(32))")" >> .env
    echo "[OK] Added SECRET_KEY to .env"
fi

# 4. Database initialization / seed
if [ "$SEED" -eq 1 ] || [ ! -s "instance/exam.db" ]; then
    echo "[*] Initializing and seeding demo exam database..."
    "$PYTHON" seed.py
fi

# 5. Optional test run
if [ "$RUN_TESTS" -eq 1 ]; then
    echo "[*] Running test suite..."
    "$PYTHON" -m pytest -q tests
fi

# 6. Port availability
if "$PYTHON" -c "import socket,sys; s=socket.socket(); sys.exit(0 if s.connect_ex(('127.0.0.1', int(sys.argv[1]))) == 0 else 1)" "$PORT"; then
    echo "[ERROR] Port ${PORT} is already in use. Stop that process or pass --port <other>."
    exit 1
fi

# 7. Launch Flask server
export PORT
echo ""
echo "[OK] Starting server on http://127.0.0.1:${PORT} ..."
echo " - Student Portal: http://127.0.0.1:${PORT}/student"
echo " - Faculty Portal: http://127.0.0.1:${PORT}/faculty"
echo " - API Health:     http://127.0.0.1:${PORT}/api/health"
echo ""
"$PYTHON" run.py
