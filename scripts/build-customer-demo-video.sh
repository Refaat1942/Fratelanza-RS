#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARTIFACTS="${ARTIFACTS_DIR:-/opt/cursor/artifacts}"
RAW_DIR="$ARTIFACTS/customer-demo-raw"
OUT_VIDEO="$ARTIFACTS/fratelanza-customer-demo.mp4"
INTRO="$ARTIFACTS/customer-demo-intro.png"
OUTRO="$ARTIFACTS/customer-demo-outro.png"

mkdir -p "$ARTIFACTS" "$RAW_DIR"

make_slide() {
  local file="$1" title="$2" subtitle="$3" c1="${4:-#072849}" c2="${5:-#0ea5e9}"
  if command -v convert >/dev/null 2>&1; then
    convert -size 1280x720 gradient:"${c1}-${c2}" \
      -gravity center -fill white -font DejaVu-Sans-Bold -pointsize 42 \
      -annotate 0 "$title" \
      -fill '#e0f2fe' -pointsize 18 \
      -annotate +0+90 "$subtitle" \
      "$file" 2>/dev/null || ffmpeg -y -f lavfi -i color=c=0x072849:s=1280x720:d=1 -frames:v 1 -update 1 "$file"
  else
    ffmpeg -y -f lavfi -i color=c=0x072849:s=1280x720:d=1 -frames:v 1 -update 1 "$file"
  fi
}

make_slide "$INTRO" "FRATELANZA" "Customer Demo — عرض تفصيلي لجميع الميزات"
make_slide "$OUTRO" "شكراً لكم" "support@fratelanza.com · rs.fratelanza.com"

echo "Recording detailed customer demo (no admin control)..."
cd "$ROOT"
node scripts/record-customer-demo.mjs

RAW_WEBM="$(find "$RAW_DIR" -name '*.webm' -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)"
RAW_WEBM="${RAW_WEBM:-$(find "$RAW_DIR" -name '*.webm' | head -1)}"
if [[ -z "$RAW_WEBM" || ! -f "$RAW_WEBM" ]]; then
  echo "No webm recording found" >&2
  exit 1
fi

echo "Assembling final video..."
ffmpeg -y \
  -loop 1 -t 4 -i "$INTRO" \
  -i "$RAW_WEBM" \
  -loop 1 -t 4 -i "$OUTRO" \
  -filter_complex "\
    [0:v]scale=1280:720,format=yuv420p,fade=t=out:st=3:d=1[v0]; \
    [1:v]scale=1280:720,format=yuv420p,fade=t=in:st=0:d=1[v1]; \
    [2:v]scale=1280:720,format=yuv420p,fade=t=in:st=0:d=1,fade=t=out:st=3:d=1[v2]; \
    [v0][v1][v2]concat=n=3:v=1:a=0[v]" \
  -map "[v]" -c:v libx264 -pix_fmt yuv420p -r 30 -movflags +faststart \
  "$OUT_VIDEO"

DUR="$(ffprobe -v quiet -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$OUT_VIDEO" 2>/dev/null || echo '?')"
echo "Done: $OUT_VIDEO (${DUR}s)"
ls -lh "$OUT_VIDEO"

# Also copy to marketing folder
cp -f "$OUT_VIDEO" "$ROOT/docs/marketing/fratelanza-customer-demo.mp4" 2>/dev/null || true
