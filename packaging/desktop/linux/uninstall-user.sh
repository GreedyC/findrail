#!/bin/sh
set -eu
DEST=${XDG_DATA_HOME:-"$HOME/.local/share"}/applications/findrail.desktop
rm -f "$DEST"
printf 'Removed Findrail menu entry. User data was not changed.\n'
