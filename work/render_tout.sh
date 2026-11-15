#!/bin/bash
# Rend tout le lot : reels 13-17, stories, puis ré-rendu des anciens reels (transitions adoucies, accroches, musique dynamique).
# Usage : render_tout.sh <projet:musique> ...   (musique = A ou B)
cd /home/user/SPARTA
for it in "$@"; do
  p=${it%%:*}; m=${it##*:}; d=videos/$p; R=$d/renders; mkdir -p $R; s=$(date +%s)
  (cd $d && timeout 3000 npx --yes hyperframes@0.8.152 render -o renders/$p-image.mp4 -f 30 -q delivery --sdr --skill=general-video > renders.log 2>&1) && echo "OK $p $(( $(date +%s)-s ))s" || { echo "ECHEC $p"; tail -4 $d/renders.log; continue; }
  python3 tools/reel/mix_audio.py $d $R/$p-image.mp4 work/musique/$p.mov work/musique/spec_dyn$m.json | tail -1
  bash tools/reel/finalize.sh work/musique/$p.mov $R/$p-v2.mp4 $R/$p-v2-leger.mp4 | tail -1
  rm -f work/musique/$p.mov $R/$p-image.mp4
  python3 -c "import glob,os,sys; [os.remove(f) for pat in ('*-musique*.mp4','*-s-musique*.mp4','*-A-musique*.mp4') for f in glob.glob(sys.argv[1]+'/'+pat)]" $R
  echo "FINI $p"
done
echo TOUT-FINI
