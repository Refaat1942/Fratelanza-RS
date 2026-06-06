#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARTIFACTS="${ARTIFACTS_DIR:-/opt/cursor/artifacts}"
RAW_DIR="$ARTIFACTS/demo-video-raw"
OUT_VIDEO="$ARTIFACTS/fratelanza-platform-demo.mp4"
INTRO_SLIDE="$ARTIFACTS/demo-intro.png"

mkdir -p "$ARTIFACTS" "$RAW_DIR"

# Title slide via ImageMagick (fallback: solid color with ffmpeg)
if command -v convert >/dev/null 2>&1; then
  convert -size 1280x720 gradient:'#0f172a-#1e3a5f' \
    -gravity center \
    -fill white -font DejaVu-Sans-Bold -pointsize 52 \
    -annotate 0 'FRATELANZA\nReal Estate Platform' \
    -fill '#94a3b8' -pointsize 24 \
    -annotate +0+90 'ERP • CRM • Finance • HR • Construction' \
    "$INTRO_SLIDE"
else
  ffmpeg -y -f lavfi -i color=c=0x0f172a:s=1280x720:d=1 -frames:v 1 "$INTRO_SLIDE" 2>/dev/null
fi

echo "Recording browser walkthrough..."
cd "$ROOT"
node scripts/record-platform-demo.mjs

RAW_WEBM="$(find "$RAW_DIR" -name '*.webm' | head -1)"
if [[ -z "$RAW_WEBM" ]]; then
  echo "No webm recording found" >&2
  exit 1
fi

echo "Assembling final video..."
ffmpeg -y \
  -loop 1 -t 4 -i "$INTRO_SLIDE" \
  -i "$RAW_WEBM" \
  -filter_complex "\
    [0:v]scale=1280:720,format=yuv420p,fade=t=out:st=3:d=1[v0]; \
    [1:v]scale=1280:720,format=yuv420p,fade=t=in:st=0:d=1[v1]; \
    [v0][v1]concat=n=2:v=1:a=0[v]" \
  -map "[v]" \
  -c:v libx264 -pix_fmt yuv420p -r 30 \
  -movflags +faststart \
  "$OUT_VIDEO"

echo "Done: $OUT_VIDEO"
ls -lh "$OUT_VIDEO"
