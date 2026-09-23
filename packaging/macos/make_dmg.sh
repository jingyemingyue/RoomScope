#!/bin/sh
# Wrap RoomScope.app in an unsigned UDZO disk image (ARCHITECTURE_V1.md §6.2).
set -eu
APP="${1:-dist/RoomScope.app}"
OUT="${2:-dist/RoomScope.dmg}"
if [ ! -d "$APP" ]; then
  echo "missing $APP" >&2
  exit 1
fi
rm -f "$OUT"
hdiutil create -volname RoomScope -srcfolder "$APP" -ov -format UDZO "$OUT"
echo "wrote $OUT"
