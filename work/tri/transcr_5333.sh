#!/bin/bash
# Audio seul de IMG_5333 (col roulé noir, 61 min) puis transcription medium
cd /home/user/SPARTA/rushes/img5333; unset http_proxy
python3 -I /tmp/claude-0/-home-user-SPARTA/c4e298a3-8dce-5fb4-b2b3-46338f72f342/scratchpad/audio_only.py 1JFr_MaiQVH-FUKqCP2tS3eyQ1ZO4_3kU 11454843924 4218167 0 99999 a.aac > /home/user/SPARTA/work/logs/audio5333.log 2>&1 || { echo ECHEC-AUDIO; exit 1; }
ffmpeg -v error -i a.aac -ac 1 -ar 16000 -y a.wav
python3 /tmp/claude-0/-home-user-SPARTA/c4e298a3-8dce-5fb4-b2b3-46338f72f342/scratchpad/transcr2.py a.wav /home/user/SPARTA/work/tri/img5333.jsonl 0 0 > /home/user/SPARTA/work/logs/tr5333.log 2>&1
echo FINI-5333
