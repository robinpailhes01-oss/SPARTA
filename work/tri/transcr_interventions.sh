#!/bin/bash
# Audio seul puis transcription (medium) des interventions de Lucas déposées sur le Drive Sparta Académie.
cd /home/user/SPARTA; unset http_proxy
run() { # nom id moov_off moov_size
  d=rushes/$1; mkdir -p $d; [ -s work/tri/$1.jsonl ] && return
  [ -s $d/a.wav ] || { python3 -I /tmp/claude-0/-home-user-SPARTA/c4e298a3-8dce-5fb4-b2b3-46338f72f342/scratchpad/audio_only.py $2 $3 $4 0 99999 $d/a.aac > work/logs/audio_$1.log 2>&1 && ffmpeg -nostdin -v error -i $d/a.aac -ac 1 -ar 16000 -y $d/a.wav; } || { echo "ECHEC audio $1"; return; }
  python3 /tmp/claude-0/-home-user-SPARTA/c4e298a3-8dce-5fb4-b2b3-46338f72f342/scratchpad/transcr2.py $d/a.wav work/tri/$1.jsonl 0 0 > work/logs/tr_$1.log 2>&1; echo "FINI $1"
}
run img5333 1JFr_MaiQVH-FUKqCP2tS3eyQ1ZO4_3kU 11454843924 4218167
run mindset 1SQ0VeNxVaGgs_ssmV0IpMw_wexkYaqjW 5097893195 1908246
run polo 1aKktJ1HpzLfAxvBugHRR_xK-eiSCMIva 20628473052 3787618
echo TOUT-FINI
