#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

set -a; source "$REPO_DIR/.env"; set +a

SPELL="${1:?usage: ./cast.sh spells/<spell>.py}"
SPELL_NAME="$(basename "$SPELL")"
GALAXY_ROOT="$(dirname "${GALAXY_SOURCE%/}")"
VENV="$GALAXY_ROOT/.venv/bin/activate"

echo "[*] Copying $SPELL_NAME -> $GALAXY_SOURCE"
cp "$REPO_DIR/$SPELL" "$GALAXY_SOURCE/$SPELL_NAME"

echo "[*] Activating venv ($GALAXY_ROOT/.venv)"
source "$VENV"

echo "[*] Casting..."
python "$GALAXY_SOURCE/$SPELL_NAME"

deactivate
echo "[*] Done"
