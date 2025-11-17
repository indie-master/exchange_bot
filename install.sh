#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR"

info() { printf "[INFO] %s\n" "$*"; }
warn() { printf "[WARN] %s\n" "$*"; }
err() { printf "[ERROR] %s\n" "$*" >&2; }

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    err "Command '$1' is required but not found. Please install it and rerun."
    exit 1
  fi
}

info "Exchange Bot installer starting..."
require_cmd python3
require_cmd git

PYTHON=python3
PIP="$PYTHON -m pip"

if ! $PIP --version >/dev/null 2>&1; then
  err "pip for Python 3 is not available. Please install it and rerun."
  exit 1
fi

VENV_DIR="$REPO_ROOT/venv"
if [ ! -d "$VENV_DIR" ]; then
  info "Creating virtual environment at $VENV_DIR"
  $PYTHON -m venv "$VENV_DIR"
fi
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

REQ_FILE="$REPO_ROOT/requirements.txt"
if [ -f "$REQ_FILE" ]; then
  info "Installing Python dependencies from requirements.txt"
  pip install --upgrade pip >/dev/null 2>&1 || warn "Could not upgrade pip; continuing with existing version."
  pip install -r "$REQ_FILE"
elif [ -f "$REPO_ROOT/pyproject.toml" ]; then
  info "Installing project via pyproject.toml"
  pip install "$REPO_ROOT"
else
  warn "No dependency manifest found. Creating minimal requirements.txt."
  cat <<'REQ' > "$REQ_FILE"
python-telegram-bot>=20.8,<21.0
requests>=2.31.0
python-dotenv>=1.0.0
REQ
  pip install -r "$REQ_FILE"
fi

CLI_ENTRY="$REPO_ROOT/CBR-rates"
if [ ! -f "$CLI_ENTRY" ]; then
  err "CBR-rates entrypoint not found at $CLI_ENTRY"
  exit 1
fi

info "Ensuring CBR-rates is executable"
chmod +x "$CLI_ENTRY"

TARGET="$(realpath "$CLI_ENTRY")"
LINK="/usr/local/bin/CBR-rates"

if [ -e "$LINK" ] && [ "$(realpath "$LINK" 2>/dev/null || true)" != "$TARGET" ]; then
  BACKUP="${LINK}.bak-$(date +%s)"
  warn "Existing CBR-rates at $LINK differs; backing up to $BACKUP"
  mv "$LINK" "$BACKUP"
fi

info "Linking $LINK -> $TARGET"
ln -sf "$TARGET" "$LINK"

cat <<EOM
Installation completed.

You can now run the CLI from any directory:
  CBR-rates status

If you prefer to pin the repository location, add this to your shell profile:
  export EXCHANGE_BOT_ROOT="$REPO_ROOT"
EOM
