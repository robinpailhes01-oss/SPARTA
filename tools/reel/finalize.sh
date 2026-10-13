#!/bin/bash
# Finition d'un rendu HyperFrames pour Instagram :
#   - son ramené à -14 LUFS intégrés (le mixage du rendu sort plus bas que la voix préparée à -13),
#     crêtes tenues par un limiteur à -2 dBFS (≈ -1 dBTP), image copiée sans réencodage
#   - version légère (< 30 Mo pour ~65 s) pour l'envoi
# Usage : tools/reel/finalize.sh <rendu.mp4> <final.mp4> <leger.mp4> [cible_LUFS=-14]
set -euo pipefail
IN="$1"; OUT="$2"; LIGHT="$3"; T="${4:--14}"
I=$(ffmpeg -nostdin -i "$IN" -af ebur128 -f null - 2>&1 | sed -n '/Summary:/,$p' | grep -E "^\s+I:" | awk '{print $2}')
G=$(python3 -c "print(round($T - ($I), 2))")
echo "mesuré $I LUFS → gain $G dB"
ffmpeg -nostdin -v error -y -i "$IN" -map 0:v:0 -map 0:a:0 -c:v copy \
  -af "volume=${G}dB,alimiter=limit=0.794:attack=3:release=80:level=false,aresample=48000" \
  -c:a aac -b:a 256k -movflags +faststart "$OUT"
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")
VB=$(python3 -c "print(int(min(4000, (29.0*8*1024 - 192*$D) / $D)))")     # kb/s vidéo pour tenir sous 29 Mo
ffmpeg -nostdin -v error -y -i "$OUT" -c:v libx264 -preset slow -b:v ${VB}k -maxrate $((VB*11/10))k -bufsize $((VB*2))k \
  -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 -movflags +faststart -c:a aac -b:a 192k "$LIGHT"
for f in "$OUT" "$LIGHT"; do
  echo "$(basename "$f") : $(ffmpeg -nostdin -i "$f" -af ebur128=peak=true -f null - 2>&1 | sed -n '/Summary:/,$p' | grep -E "^\s+(I|Peak):" | tr -s ' ' | tr '\n' ' ') $(du -h "$f" | cut -f1)"
done
