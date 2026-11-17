#!/bin/bash
# Extrait les passages du cours de 44 min (copie Drive), lecture en flux.
D=/home/user/SPARTA/rushes/cours44; P=/tmp/claude-0/-home-user-SPARTA/c4e298a3-8dce-5fb4-b2b3-46338f72f342/scratchpad/rangeproxy.py
cd $D; unset http_proxy
pgrep -f rangeproxy.py >/dev/null || (nohup python3 -I $P > /dev/null 2>&1 &); sleep 2
for seg in "a1 1411 22" "a2 1502 9" "b1 1277 15" "b2 1334 9" "c1 2255 29" "d1 2393 11" "d2 2434 16" "e1 2475 8" "e2 2490 19" "f1 2619 24"; do
  set -- $seg; [ -s $1.mp4 ] && continue
  for essai in 1 2 3 4 5; do
    ffmpeg -nostdin -v error -ss $2 -i http://127.0.0.1:8765/a.mov -t $3 -map 0:v:0 -map 0:a:0 -vf fps=30 -c:v libx264 -crf 17 -preset fast -pix_fmt yuv420p -c:a aac -b:a 192k -y $1.part.mp4 && mv $1.part.mp4 $1.mp4 && break
    sleep 20
  done
done
echo FINI
