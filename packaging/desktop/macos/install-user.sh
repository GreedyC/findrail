#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
DEST=${HOME}/Applications
mkdir -p "$DEST"
cp -R "$HERE/Findrail.app" "$DEST/Findrail.app"
printf 'Installed Findrail.app for this user. User data was not changed.\n'
