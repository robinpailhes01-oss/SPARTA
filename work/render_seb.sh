#!/bin/bash
# Rend un témoignage au format « Sébastien » : rendu HyperFrames puis format_seb.py (ouverture + son réel de la salle).
cd /home/user/SPARTA; p=$1; d=videos/$p; R=$d/renders; mkdir -p $R; s=$(date +%s)
python3 tools/reel/timeline_check.py $d || { echo "ECHEC $p (timeline)"; exit 1; }
(cd $d && timeout 3000 npx --yes hyperframes@0.8.152 render -o renders/$p-image.mp4 -f 30 -q delivery --sdr --skill=general-video > renders.log 2>&1) || { echo "ECHEC $p"; tail -4 $d/renders.log; exit 1; }
python3 tools/reel/format_seb.py $d $R/$p-image.mp4 $R/$p-v2.mp4 "${@:2}" && ffmpeg -v error -i $R/$p-v2.mp4 -c:v libx264 -crf 23 -preset medium -c:a copy -movflags +faststart -y $R/$p-v2-leger.mp4
rm -rf $R/$p-v2.mp4.tmp /tmp/hyperframes-extract-cache-0
echo "OK $p $(( $(date +%s)-s ))s"; echo FINI-SEB
