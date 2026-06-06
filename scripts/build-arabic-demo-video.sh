#!/usr/bin/env bash
set -euo pipefail

ARTIFACTS="${ARTIFACTS_DIR:-/opt/cursor/artifacts}"
RAW_DIR="$ARTIFACTS/arabic-demo-raw"
OUT_VIDEO="$ARTIFACTS/fratelanza-arabic-demo.mp4"
INTRO="$ARTIFACTS/arabic-demo-intro.png"

mkdir -p "$ARTIFACTS" "$RAW_DIR"

if command -v convert >/dev/null 2>&1; then
  convert -size 1280x720 gradient:'#1e3a8a-#0ea5e9' \
    -gravity center -fill white -font DejaVu-Sans-Bold -pointsize 48 \
    -annotate 0 'فراتيلانزا\nمنصة العقارات المتكاملة' \
    -fill '#e0f2fe' -pointsize 22 \
    -annotate +0+100 'ERP • CRM • مالية • موارد بشرية • عربي كامل' \
    "$INTRO" 2>/dev/null || ffmpeg -y -f lavfi -i color=c=0x1e3a8a:s=1280x720:d=1 -frames:v 1 "$INTRO"
else
  ffmpeg -y -f lavfi -i color=c=0x1e3a8a:s=1280x720:d=1 -frames:v 1 "$INTRO"
fi

echo "Recording Arabic company demo..."
node "$(dirname "$0")/record-arabic-demo.mjs"

echo "Capturing illustrated Arabic screenshots..."
node "$(dirname "$0")/capture-arabic-screenshots.mjs"

RAW_WEBM="$(find "$RAW_DIR" -name '*.webm' | head -1)"
if [[ -z "$RAW_WEBM" ]]; then
  echo "No webm found" >&2
  exit 1
fi

ffmpeg -y \
  -loop 1 -t 4 -i "$INTRO" \
  -i "$RAW_WEBM" \
  -filter_complex "[0:v]scale=1280:720,format=yuv420p,fade=t=out:st=3:d=1[v0];[1:v]scale=1280:720,format=yuv420p,fade=t=in:st=0:d=1[v1];[v0][v1]concat=n=2:v=1:a=0[v]" \
  -map "[v]" -c:v libx264 -pix_fmt yuv420p -r 30 -movflags +faststart \
  "$OUT_VIDEO"

echo "Video: $OUT_VIDEO"
ls -lh "$OUT_VIDEO"
ls -lh "$ARTIFACTS/arabic-screenshots/" 2>/dev/null || true
