#!/usr/bin/env bash
# render.sh: build the house from plan.json, render both shots, stitch, render stills, contact sheet.
#
#   ./render.sh                 final quality (1280x720, 128 samples, every frame)
#   PREVIEW=1 ./render.sh       fast check (640x360, 32 samples, every 3rd frame, stitched at 8 fps)
#
# Environment overrides:
#   BLENDER=/path/to/blender    Blender 4.2+ binary (auto-detected if unset)
#   DEVICE=CPU|METAL|CUDA|OPTIX|HIP   Cycles device (default: METAL on macOS, CPU elsewhere)
#   RES=1920x1080 SAMPLES=256   override resolution / samples
#   STAGE=phase1|phase2         force the box model or the staged house (default: auto)
#   SHOTS="main_floor basement" which shots to render
#   OUT=renders                 output directory
#   SKIP_FRAMES=1               skip shot rendering, only stitch + stills + sheet
set -euo pipefail
cd "$(dirname "$0")"

# ---------------------------------------------------------------- locate blender
if [ -z "${BLENDER:-}" ]; then
  for cand in blender42 /opt/blender-4.2.11-linux-x64/blender \
              /Applications/Blender.app/Contents/MacOS/Blender \
              "$HOME/Applications/Blender.app/Contents/MacOS/Blender" blender; do
    if command -v "$cand" >/dev/null 2>&1; then BLENDER="$(command -v "$cand")"; break; fi
    if [ -x "$cand" ]; then BLENDER="$cand"; break; fi
  done
fi
if [ -z "${BLENDER:-}" ]; then
  echo "Blender not found. Install Blender 4.2 LTS or newer and set BLENDER=/path/to/blender" >&2
  exit 1
fi
command -v ffmpeg >/dev/null || { echo "ffmpeg not found (brew install ffmpeg / apt-get install ffmpeg)" >&2; exit 1; }

if [ -z "${DEVICE:-}" ]; then
  case "$(uname -s)" in Darwin) DEVICE=METAL ;; *) DEVICE=CPU ;; esac
fi

OUT="${OUT:-renders}"
STAGE="${STAGE:-auto}"
SHOTS="${SHOTS:-main_floor basement}"
FPS=$(python3 -c "import json;print(json.load(open('plan.json')).get('fps',24))")

if [ "${PREVIEW:-0}" = "1" ]; then
  RES="${RES:-640x360}"; SAMPLES="${SAMPLES:-32}"; STEP=3; OUT_FPS=8; TAG="_preview"
  STILL_SAMPLES=${STILL_SAMPLES:-48}
else
  RES="${RES:-1280x720}"; SAMPLES="${SAMPLES:-128}"; STEP=1; OUT_FPS=$FPS; TAG=""
  STILL_SAMPLES=${STILL_SAMPLES:-$((SAMPLES * 2))}
fi

echo "== blender: $BLENDER"
echo "== device: $DEVICE   res: $RES   samples: $SAMPLES   step: $STEP   stage: $STAGE   out: $OUT"
mkdir -p "$OUT"
T0=$(date +%s)

# ---------------------------------------------------------------- shots
if [ "${SKIP_FRAMES:-0}" != "1" ]; then
  for SHOT in $SHOTS; do
    echo "== rendering shot $SHOT"
    "$BLENDER" -b -P build_scene.py -- --shot "$SHOT" --res "$RES" --samples "$SAMPLES" \
        --frame-step "$STEP" --device "$DEVICE" --stage "$STAGE" --out "$OUT" 2>&1 \
        | grep -E "^\[build\]|Error|Traceback|Fra:" | grep -v "^Fra:" || true
  done
fi

# ---------------------------------------------------------------- stitch
XFADE_FRAMES=12
CLIPS=()
for SHOT in $SHOTS; do
  DIR="$OUT/frames/$SHOT"
  [ -d "$DIR" ] || { echo "no frames for $SHOT in $DIR" >&2; exit 1; }
  # frames may be strided (preview); concatenate through a list so numbering does not matter
  ls "$DIR"/frame_*.png | sort | sed "s|^|file '$PWD/|; s|$|'|" > "$OUT/${SHOT}_frames.txt"
  ffmpeg -y -loglevel error -r "$OUT_FPS" -f concat -safe 0 -i "$OUT/${SHOT}_frames.txt" \
      -c:v libx264 -pix_fmt yuv420p -crf 18 -r "$OUT_FPS" "$OUT/${SHOT}${TAG}.mp4"
  CLIPS+=("$OUT/${SHOT}${TAG}.mp4")
  echo "== $SHOT: $(ls "$DIR"/frame_*.png | wc -l | tr -d ' ') frames -> $OUT/${SHOT}${TAG}.mp4"
done

FINAL="$OUT/walkthrough${TAG}.mp4"
if [ "${#CLIPS[@]}" -ge 2 ]; then
  # cross-dissolve: XFADE_FRAMES of the animation, scaled to the output fps
  DUR1=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "${CLIPS[0]}")
  XD=$(python3 -c "print(min(0.5, $XFADE_FRAMES/24.0))")
  OFF=$(python3 -c "print(max(0.0, $DUR1 - $XD))")
  ffmpeg -y -loglevel error -i "${CLIPS[0]}" -i "${CLIPS[1]}" \
      -filter_complex "[0:v][1:v]xfade=transition=fade:duration=${XD}:offset=${OFF},format=yuv420p" \
      -c:v libx264 -crf 18 -r "$OUT_FPS" "$FINAL"
else
  cp "${CLIPS[0]}" "$FINAL"
fi
echo "== stitched: $FINAL ($(ffprobe -v error -show_entries format=duration -of csv=p=0 "$FINAL") s)"

# ---------------------------------------------------------------- stills + contact sheet
STILLS_DIR="$OUT/stills${TAG}"
BLENDER="$BLENDER" DEVICE="$DEVICE" python3 tools/stills.py --res "$RES" --samples "$STILL_SAMPLES" \
    --stage "$STAGE" --out "$STILLS_DIR"
python3 tools/contact_sheet.py "$STILLS_DIR" "$OUT/contact_sheet${TAG}.png"

T1=$(date +%s)
echo "== done in $(( (T1 - T0) / 60 )) min. video: $FINAL  sheet: $OUT/contact_sheet${TAG}.png"
