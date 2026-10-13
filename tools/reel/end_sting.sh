#!/bin/bash
# Remplace le son du carton de fin (musique seule, sans voix) par un extrait musical pleine bande.
# Utile quand le tapis musical vient d'une séparation de stems : sous la voix d'origine il ne reste
# souvent que la basse, inaudible sur un téléphone ; l'intro sans voix du reel source est intacte.
# Usage : tools/reel/end_sting.sh <final.mp4> <extrait.wav> <debut_carton_s> <sortie_final.mp4> <sortie_legere.mp4> [LUFS_carton=-20]
set -euo pipefail
IN="$1"; STING="$2"; T0="$3"; OUT="$4"; LIGHT="$5"; TGT="${6:--20}"
TMP=$(mktemp -d)
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")
XF=0.12                                                   # fondu enchaîné à l'entrée du carton
SL=$(python3 -c "print(round($D - $T0 + $XF, 3))")        # longueur d'extrait nécessaire
I=$(ffmpeg -nostdin -i "$STING" -af ebur128 -f null - 2>&1 | sed -n '/Summary:/,$p' | grep -E "^\s+I:" | awk '{print $2}')
G=$(python3 -c "print(round($TGT - ($I), 2))")
ffmpeg -nostdin -v error -y -i "$IN" -vn -ac 2 -ar 48000 -c:a pcm_s16le "$TMP/a.wav"
FO=$(python3 -c "print(round(max(0.0, $SL - 1.0), 3))")
ffmpeg -nostdin -v error -y -i "$TMP/a.wav" -i "$STING" -filter_complex \
  "[0]atrim=0:$(python3 -c "print(round($T0 + $XF, 3))"),asetpts=N/SR/TB[a];[1]atrim=0:$SL,asetpts=N/SR/TB,volume=${G}dB,afade=t=out:st=$FO:d=1.0,apad=whole_dur=$SL[b];[a][b]acrossfade=d=$XF:c1=tri:c2=tri,alimiter=limit=0.794:level=false" \
  -c:a pcm_s16le "$TMP/mix.wav"
ffmpeg -nostdin -v error -y -i "$IN" -i "$TMP/mix.wav" -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 256k -shortest -movflags +faststart "$OUT"
VB=$(python3 -c "print(int(min(4000, (27.5*8*1024 - 192*$D) / $D)))")
ffmpeg -nostdin -v error -y -i "$OUT" -map 0:v:0 -map 0:a:0 -c:v libx264 -preset slow -b:v ${VB}k -maxrate $((VB*11/10))k -bufsize $((VB*2))k \
  -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 -movflags +faststart -c:a aac -b:a 192k "$LIGHT"
rm -rf "$TMP"
for f in "$OUT" "$LIGHT"; do
  echo "$(basename "$f") : $(ffmpeg -nostdin -i "$f" -af ebur128=peak=true -f null - 2>&1 | sed -n '/Summary:/,$p' | grep -E "^\s+(I|Peak):" | tr -s ' ' | tr '\n' ' ') $(du -h "$f" | cut -f1)"
done
