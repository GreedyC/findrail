#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
DEST=${HOME}/Applications
mkdir -p "$DEST"
if [ -L "$DEST/Findrail.app" ] || { [ -e "$DEST/Findrail.app" ] && [ ! -d "$DEST/Findrail.app" ]; }; then
  echo 'Existing Findrail.app must be a directory, not a symlink or file.' >&2
  exit 1
fi
mkdir -p "$DEST/Findrail.app"
cp -R "$HERE/Findrail.app/." "$DEST/Findrail.app"
printf 'Installed Findrail.app for this user. User data was not changed.\n'
