#!/bin/sh
set -eu
BIN=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)/findrail-desktop
DEST=${XDG_DATA_HOME:-"$HOME/.local/share"}/applications
INSTALL_DIR=$(dirname "$BIN")
NL='
'
CR=$(printf '\r')
case "$INSTALL_DIR" in *"$NL"*|*"$CR"*) echo 'Install path cannot contain a newline.' >&2; exit 1 ;; esac
ESCAPED_DIR=$(printf '%s' "$INSTALL_DIR" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e 's/%/%%/g')
mkdir -p "$DEST"
while IFS= read -r line; do
  case "$line" in
    Exec=*) printf 'Exec="%s/findrail-desktop"\n' "$ESCAPED_DIR" ;;
    *) printf '%s\n' "$line" ;;
  esac
done < "$(dirname "$0")/findrail.desktop" > "$DEST/findrail.desktop"
chmod 644 "$DEST/findrail.desktop"
printf 'Installed user menu entry: %s\n' "$DEST/findrail.desktop"
