#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARTIFACTS="${ARTIFACTS_DIR:-/opt/cursor/artifacts}"
RAW_DIR="$ARTIFACTS/comprehensive-demo-raw"
OUT_VIDEO="$ARTIFACTS/fratelanza-comprehensive-demo.mp4"
INTRO="$ARTIFACTS/comprehensive-demo-intro.png"
OUTRO="$ARTIFACTS/comprehensive-demo-outro.png"

mkdir -p "$ARTIFACTS" "$RAW_DIR"

make_slide() {
  local file="$1" title="$2" subtitle="$3" color1="${4:-#0f172a}" color2="${5:-#1e3a8a}"
  if command -v convert >/dev/null 2>&1; then
    convert -size 1280x720 gradient:"${color1}-${color2}" \
      -gravity center -fill white -font DejaVu-Sans-Bold -pointsize 44 \
      -annotate 0 "$title" \
      -fill '#94a3b8' -pointsize 20 \
      -annotate +0+80 "$subtitle" \
      "$file" 2>/dev/null || ffmpeg -y -f lavfi -i color=c=0x0f172a:s=1280x720:d=1 -frames:v 1 "$file"
  else
    ffmpeg -y -f lavfi -i color=c=0x0f172a:s=1280x720:d=1 -frames:v 1 "$file"
  fi
}

make_slide "$INTRO" "FRATELANZA" "Comprehensive Platform Tour — جميع الميزات"
make_slide "$OUTRO" "FRATELANZA" "ERP • CRM • Finance • HR • Construction • Arabic RTL"

echo "Recording comprehensive demo (all features)..."
cd "$ROOT"
node scripts/record-comprehensive-demo.mjs

RAW_WEBM="$(find "$RAW_DIR" -name '*.webm' -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)"
RAW_WEBM="${RAW_WEBM:-$(find "$RAW_DIR" -name '*.webm' | head -1)}"
if [[ -z "$RAW_WEBM" || ! -f "$RAW_WEBM" ]]; then
  echo "No webm recording found in $RAW_DIR" >&2
  exit 1
fi

echo "Assembling final video from $(basename "$RAW_WEBM")..."
ffmpeg -y \
  -loop 1 -t 3 -i "$INTRO" \
  -i "$RAW_WEBM" \
  -loop 1 -t 3 -i "$OUTRO" \
  -filter_complex "\
    [0:v]scale=1280:720,format=yuv420p,fade=t=out:st=2:d=1[v0]; \
    [1:v]scale=1280:720,format=yuv420p,setpts=PTS-STARTPTS[v1]; \
    [2:v]scale=1280:720,format=yuv420p,fade=t=in:st=0:d=1[v2]; \
    [v0][v1][v2]concat=n=3:v=1:a=0[v]" \
  -map "[v]" \
  -c:v libx264 -pix_fmt yuv420p -r 30 -movflags +faststart \
  "$OUT_VIDEO"

DUR="$(ffprobe -v quiet -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$OUT_VIDEO" 2>/dev/null || echo '?')"
echo "Done: $OUT_VIDEO (${DUR}s)"
ls -lh "$OUT_VIDEO"
