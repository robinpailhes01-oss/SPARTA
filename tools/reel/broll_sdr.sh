#!/bin/bash
# Prépare les plans de coupe iPhone (HDR HLG bt2020) en SDR bt709 1080×1920 30 i/s.
# Sans cette conversion, HyperFrames détecte du HDR et exige ~9 Go d'images 16 bits (ou rend un fichier HLG).
# Tone mapping « hable » : garde le contraste et les plafonds lumineux sans les brûler (comparatif hable/mobius/reinhard).
# Usage : tools/reel/broll_sdr.sh <dossier_rushes_MOV> <dossier_sortie>
set -euo pipefail
IN="$1"; OUT="$2"; mkdir -p "$OUT"
for f in "$IN"/*.MOV "$IN"/*.mov; do
  [ -e "$f" ] || continue
  b=$(basename "${f%.*}")
  ffmpeg -nostdin -v error -y -i "$f" -an \
    -vf "zscale=w=1080:h=1920:filter=lanczos,zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,fps=30" \
    -c:v libx264 -crf 16 -preset medium -g 30 -keyint_min 30 -sc_threshold 0 -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
    -movflags +faststart "$OUT/$b.mp4" &
done
wait
