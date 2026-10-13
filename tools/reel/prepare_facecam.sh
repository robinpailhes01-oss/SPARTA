#!/bin/bash
# Prépare un rush face cam pour engine.py :
#   1. 1080x1920, 30 i/s (recadrage 9:16 si besoin)
#   2. make-up léger (tools/makeup.sh)
#   3. voix : coupe-bas 80 Hz + loudnorm -13 LUFS / -1,5 dBTP (deux passes)
#   4. transcription mot à mot (tools/reel/transcribe.py)
# Usage : tools/reel/prepare_facecam.sh <rush.MOV> <dossier_projet> [force_makeup=0.6]
set -euo pipefail
SRC="$1"; PROJ="$2"; K="${3:-0.6}"
TOOLS="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$PROJ/assets"
TMP="$PROJ/assets/.tmp_conform.mp4"

# 1. Conformation (le son est gardé tel quel à cette étape)
ffmpeg -nostdin -v error -y -i "$SRC" -map 0:v:0 -map 0:a:0 \
  -vf "scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,fps=30" \
  -c:v libx264 -crf 15 -preset fast -pix_fmt yuv420p -c:a aac -b:a 256k "$TMP"

# 2. Make-up
"$TOOLS/makeup.sh" "$TMP" "$PROJ/assets/.tmp_makeup.mp4" "$K"

# 3. Voix : mesure puis normalisation linéaire
M=$(ffmpeg -nostdin -i "$TMP" -af "highpass=f=80,loudnorm=I=-13:TP=-1.5:LRA=9:print_format=json" -f null - 2>&1 \
  | sed -n '/^{/,/^}/p' | python3 -c "import sys,json;d=json.load(sys.stdin);print(f\"measured_I={d['input_i']}:measured_TP={d['input_tp']}:measured_LRA={d['input_lra']}:measured_thresh={d['input_thresh']}:offset={d['target_offset']}\")")
ffmpeg -nostdin -v error -y -i "$PROJ/assets/.tmp_makeup.mp4" -i "$TMP" -map 0:v:0 -map 1:a:0 -c:v copy \
  -af "highpass=f=80,loudnorm=I=-13:TP=-1.5:LRA=9:$M:linear=true,aresample=48000" -c:a aac -b:a 192k \
  -movflags +faststart "$PROJ/assets/facecam.mp4"
rm -f "$TMP" "$PROJ/assets/.tmp_makeup.mp4"

# 4. Transcription
python3 "$TOOLS/reel/transcribe.py" "$PROJ/assets/facecam.mp4" "$PROJ/assets/facecam.words.json" medium
ffmpeg -nostdin -i "$PROJ/assets/facecam.mp4" -af ebur128 -f null - 2>&1 | grep -E "^\s+I:" | tail -1
