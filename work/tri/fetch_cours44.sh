#!/bin/bash
# Attend que le quota Drive soit levé puis extrait les 4 passages utiles du cours de 44 min (lecture en flux, rien d'autre n'est gardé).
D=/home/user/SPARTA/rushes/cours44; P=/tmp/claude-0/-home-user-SPARTA/c4e298a3-8dce-5fb4-b2b3-46338f72f342/scratchpad/rangeproxy.py
U="https://drive.usercontent.google.com/download?id=1PNEeJjghBbFZFHd_Ewx8AQBwtDJy2ryW&export=download&confirm=t"
cd $D; unset http_proxy
pgrep -f rangeproxy.py >/dev/null || (nohup python3 -I $P > /dev/null 2>&1 &)
for essai in $(seq 1 150); do
  t=$(curl -sSL -m 60 -r 0-1048575 "$U" -o /dev/null -w "%{content_type}")
  if [[ "$t" != text/html* ]]; then
    ok=1
    for seg in "vma 515 250" "sarco 218 82" "krebs 380 72" "cori 776 92"; do
      set -- $seg
      [ -s $1.mp4 ] && continue
      ffmpeg -nostdin -v error -ss $2 -i http://127.0.0.1:8765/a.mov -t $3 -map 0:v:0 -map 0:a:0 -vf fps=30 -c:v libx264 -crf 17 -preset fast -pix_fmt yuv420p -c:a aac -b:a 192k -y $1.part.mp4 && mv $1.part.mp4 $1.mp4 || { ok=0; break; }
    done
    [ $ok = 1 ] && { echo FINI; exit 0; }
  fi
  echo "essai $essai: quota"; sleep 600
done
echo ABANDON; exit 1
