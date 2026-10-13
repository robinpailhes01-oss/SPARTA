#!/bin/bash
# Effet make-up léger : lissage bilatéral + matification des hautes lumières, appliqué
# uniquement sur les tons chair clairs (masque Cb/Cr + luminance > 105, calculé en basse définition
# puis flouté) : barbe, cheveux, sourcils et tatouages, plus sombres, restent nets.
# $1 entrée, $2 sortie, $3 force 0-1 (défaut 0.6)
IN="$1"; OUT="$2"; K="${3:-0.6}"
read W H < <(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 "$IN" | tr ',' ' ')
A=$(python3 -c "print(int(255*$K))")
ffmpeg -nostdin -v error -y -i "$IN" -filter_complex "
[0:v]split=3[a][b][c];
[b]format=yuv444p,bilateral=sigmaS=8:sigmaR=0.06:planes=1,curves=all='0/0 0.55/0.55 0.85/0.80 1/0.92'[s];
[c]scale=iw/4:ih/4,format=yuv444p,geq=lum='if(between(cb(X\,Y)\,77\,127)*between(cr(X\,Y)\,135\,175)*gt(lum(X\,Y)\,105)\,$A\,0)':cb=128:cr=128,format=gray,gblur=sigma=2,scale=${W}:${H}:flags=bicubic[m];
[s][m]alphamerge[sa];
[a]format=yuv444p[a4];
[a4][sa]overlay=format=yuv444,format=yuv420p[out]" -map "[out]" -map 0:a? -c:v libx264 -crf 16 -preset medium -c:a copy "$OUT"
