#!/bin/sh
set -eu
BIN=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)/findrail-desktop
DEST=${XDG_DATA_HOME:-"$HOME/.local/share"}/applications
mkdir -p "$DEST"
sed "s|@INSTALL_DIR@|$(dirname "$BIN")|g" "$(dirname "$0")/findrail.desktop" > "$DEST/findrail.desktop"
chmod 644 "$DEST/findrail.desktop"
printf 'Installed user menu entry: %s\n' "$DEST/findrail.desktop"
