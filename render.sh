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
#   SHOTS="block street ..." which shots to render (default: the block establishing shot plus the seven spec shots)
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
SHOTS="${SHOTS:-block street main_floor basement upstairs terrace_dusk bedroom garage}"
FPS=$(python3 -c "import json;print(json.load(open('plan.json')).get('fps',24))")

if [ "${PREVIEW:-0}" = "1" ]; then
  RES="${RES:-640x360}"; SAMPLES="${SAMPLES:-32}"; STEP="${STEP:-3}"; TAG="_preview"
  STILL_SAMPLES=${STILL_SAMPLES:-48}
else
  RES="${RES:-1280x720}"; SAMPLES="${SAMPLES:-128}"; STEP="${STEP:-1}"; TAG=""
  STILL_SAMPLES=${STILL_SAMPLES:-$((SAMPLES * 2))}
fi
# strided frames play back at fps/step so the move keeps real-time pacing
OUT_FPS=$(python3 -c "print(max(1, round($FPS / $STEP)))")

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
  # cross-dissolve every cut: XFADE_FRAMES of the animation, scaled to the output fps, chained through one filter graph
  XD=$(python3 -c "print(max($XFADE_FRAMES/$FPS, 2.0/$OUT_FPS))")
  INPUTS=(); for C in "${CLIPS[@]}"; do INPUTS+=(-i "$C"); done
  FILTER=$(python3 - "$XD" "${CLIPS[@]}" <<'PY'
import subprocess, sys
xd = float(sys.argv[1]); clips = sys.argv[2:]
durs = [float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", c]).decode().strip()) for c in clips]
parts = []; prev = "[0:v]"; total = durs[0]
for i in range(1, len(clips)):
    off = max(0.0, total - xd)
    out = "[v%d]" % i if i < len(clips) - 1 else "[vout]"
    parts.append("%s[%d:v]xfade=transition=fade:duration=%.4f:offset=%.4f%s" % (prev, i, xd, off, out))
    total = off + durs[i]; prev = out
print(";".join(parts) + ";[vout]format=yuv420p[final]")
PY
)
  ffmpeg -y -loglevel error "${INPUTS[@]}" -filter_complex "$FILTER" -map "[final]" -c:v libx264 -crf 18 -r "$OUT_FPS" "$FINAL"
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
