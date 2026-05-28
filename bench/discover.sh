#!/bin/bash
# One-shot Bluetooth discovery for the Ditoo.
#   - Triggers the macOS Bluetooth permission prompt (click Allow the first time)
#   - Lists paired Divoom devices
#   - Runs an SDP query to find the RFCOMM/serial channel used for pixel control
#
# Usage:  ./bench/discover.sh [MAC]
# Default MAC is the Ditoo Pro audio device.

set -u
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
BRIDGE="$HERE/ditoo_bridge/DitooBridge.app/Contents/MacOS/DitooBridge"
MAC="${1:-AA:BB:CC:DD:EE:FF}"   # DitooPro-Audio

if [ ! -x "$BRIDGE" ]; then
    echo "Bridge binary not found/executable: $BRIDGE" >&2
    exit 1
fi

echo "================================================================"
echo " 1) Paired Divoom devices"
echo "================================================================"
"$BRIDGE" list
echo
echo "================================================================"
echo " 2) SDP services on $MAC"
echo "    (looking for a 'Serial Port' / SPP service + its RFCOMM channel)"
echo "================================================================"
"$BRIDGE" services "$MAC"
echo
echo "Done. Copy everything above and paste it back to Claude."
