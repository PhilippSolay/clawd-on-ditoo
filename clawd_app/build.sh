#!/bin/bash
# Build Clawd.app — the menu-bar controller + settings UI.
# Produces clawd_app/Clawd.app (LSUIElement; no Dock icon).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

APP="Clawd.app"
MACOS="$APP/Contents/MacOS"
BIN="$MACOS/Clawd"

echo "compiling…"
mkdir -p "$MACOS" "$APP/Contents/Resources"
swiftc -O -parse-as-library \
    -framework SwiftUI -framework AppKit -framework ServiceManagement \
    Sources/main.swift -o "$BIN"

echo "bundling Info.plist…"
cp Info.plist "$APP/Contents/Info.plist"

echo "signing (ad-hoc, stable identifier so TCC grants survive rebuilds)…"
codesign --force --sign - --identifier local.divoompet.clawd-app \
    --options runtime "$APP" 2>/dev/null || \
    codesign --force --sign - --identifier local.divoompet.clawd-app "$APP"

echo "done: clawd_app/$APP"
echo "Run it once from Finder (or: open clawd_app/$APP) and grant Bluetooth + Microphone when asked."
