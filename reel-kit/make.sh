#!/usr/bin/env bash
# reel-kit pipeline driver.
#   make.sh <reel_dir> prep      audio extracts, speech-island transcript, screen sync offset
#   make.sh <reel_dir> edl       reel.json -> work/edl.json (prints the edit)
#   make.sh <reel_dir> preview   1080x1920 @30 render + QA   (review with the user first)
#   make.sh <reel_dir> final     export render (default 4K @60) + QA
set -euo pipefail
KIT="$(cd "$(dirname "$0")" && pwd)"
D="$(cd "$1" && pwd)"; STEP="$2"
export NODE_PATH="$(npm root -g)" HF_HUB_DISABLE_XET=1
mkdir -p "$D/work" "$D/out"
face=$(python3 -c "import json;print(json.load(open('$D/reel.json'))['sources']['face'])")
screen=$(python3 -c "import json;print(json.load(open('$D/reel.json'))['sources'].get('screen') or '')")
case "$STEP" in
  prep)
    ffmpeg -v error -y -i "$D/$face" -vn -ac 1 -ar 16000 "$D/work/face_16k.wav"
    python3 "$KIT/transcribe.py" "$D/work/face_16k.wav" "$D/work/face_islands.json" --islands
    camsrc=$(python3 -c "import json;print(json.load(open('$D/reel.json')).get('cam',{}).get('source',''))")
    if [ "$camsrc" = "screen" ]; then   # edited long-form source: find its own cuts (renderer snaps to them)
      crop=$(python3 -c "import json;c=json.load(open('$D/reel.json'))['cam']['crop'];print(f'{c[0]}:{c[1]}:{c[2]}:{c[3]}')")
      python3 "$KIT/source_cuts.py" "$D/$face" "$crop" "$D/work/source_cuts.json"
    fi
    if [ -n "$screen" ]; then
      ffmpeg -v error -y -i "$D/$screen" -vn -ac 1 -ar 16000 "$D/work/screen_16k.wav"
      python3 "$KIT/sync.py" "$D/work/face_16k.wav" "$D/work/screen_16k.wav"
    fi ;;
  edl)     python3 "$KIT/build_edl.py" "$D" ;;
  preview|final)
    python3 "$KIT/build_edl.py" "$D" > /dev/null
    python3 "$KIT/render_video.py" "$D" "$STEP"
    node "$KIT/render_overlay.js" "$D" "$STEP"
    out=$(python3 "$KIT/finish.py" "$D" "$STEP" | tail -1 | awk '{print $1}')
    python3 "$KIT/check.py" "$D" "$out" ;;
  *) echo "unknown step $STEP"; exit 1 ;;
esac
