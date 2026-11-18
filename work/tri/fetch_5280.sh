#!/bin/bash
# Extrait les passages utiles de IMG_5280 (cours, 46 min) en lecture par plages, rien d'autre n'est gardé.
D=/home/user/SPARTA/rushes/img5280; P=/tmp/claude-0/-home-user-SPARTA/c4e298a3-8dce-5fb4-b2b3-46338f72f342/scratchpad/rangeproxy5280.py
cd $D; unset http_proxy
pgrep -f rangeproxy5280.py >/dev/null || (setsid nohup python3 -I $P > /dev/null 2>&1 < /dev/null &); sleep 2
for seg in "obliques 226 172" "debutant 438 150" "hanches 585 66" "diplome 1115 55" "statut 766 46" "formations 1212 25" "h120 1916 136" "orienter 2108 32" "synthese 2376 72"; do
  set -- $seg
  [ -s $1.mp4 ] && continue
  for essai in 1 2 3; do
    ffmpeg -nostdin -v error -ss $2 -i http://127.0.0.1:8765/a.mov -t $3 -map 0:v:0 -map 0:a:0 -vf fps=30 -c:v libx264 -crf 17 -preset fast -pix_fmt yuv420p -c:a aac -b:a 192k -y $1.part.mp4 && mv $1.part.mp4 $1.mp4 && break
    sleep 60
  done
  echo "$1 $([ -s $1.mp4 ] && echo ok || echo ECHEC)"
done
echo FINI
