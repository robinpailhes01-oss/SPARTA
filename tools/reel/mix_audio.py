"""Remixe le son d'un rendu sans le refaire : voix reconstruite depuis index.html + musique + effets sonores.

L'image du rendu est recopiée telle quelle ; seule la piste son change. Sert à comparer plusieurs musiques
(ex. générées par ElevenLabs) ou à poser des effets sonores sans relancer HyperFrames (~12 min par rendu).

Usage : python3 tools/reel/mix_audio.py <projet> <rendu.mp4> <sortie.mp4> <spec.json>
spec.json :
  {"music": "musique.mp3", "music_rel": -20,          # musique sous la voix, en LU (intégré)
   "music_eq": true,                                  # creux de 3 dB vers 2,5 kHz pour dégager la parole
   "end_boost": 10, "fade_out": 0.8,                  # remontée sur le carton de fin, fondu final (s)
   "sfx": [{"file": "boom.mp3", "t": 61.09, "rel": -6}, …]}   # rel : niveau en LU par rapport à la voix
Puis tools/reel/finalize.sh <sortie.mp4> <final.mp4> <leger.mp4> pour -14 LUFS et la version légère.
"""
import json
import os
import re
import subprocess
import sys


def lufs(path, af=None):
    cmd = ["ffmpeg", "-nostdin", "-i", path] + (["-af", af + ",ebur128"] if af else ["-af", "ebur128"]) + ["-f", "null", "-"]
    e = subprocess.run(cmd, capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", e[e.rfind("Summary:"):])[0])


def main():
    proj, render, out, spec_path = sys.argv[1:5]
    spec = json.load(open(spec_path))
    s = open(os.path.join(proj, "index.html"), encoding="utf-8").read()
    segs = re.findall(r'<video id="th-m\d+" src="([^"]+)" data-start="([\d.]+)" data-duration="([\d.]+)" '
                      r'data-media-start="([\d.]+)"[^>]*data-has-audio="true"', s)
    end = float(re.search(r'id="endcard" class="clip" data-start="([\d.]+)"', s)[1])
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", render],
                               capture_output=True, text=True).stdout)
    tmp = out + ".voice.wav"

    # 1. Voix : chaque prise face cam à sa place, micro-fondus de 30/40 ms comme dans la composition
    ins, fl = [], []
    for k, (src, a, d, ms) in enumerate(segs):
        a, d, ms = float(a), float(d), float(ms)
        ins += ["-i", os.path.join(proj, src)]
        fl.append(f"[{k}:a]atrim={ms}:{ms + d},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,"
                  f"afade=t=in:d=0.03,afade=t=out:st={d - 0.04}:d=0.04,adelay={int(a * 1000)}:all=1[v{k}]")
    fl.append("".join(f"[v{k}]" for k in range(len(segs))) + f"amix=inputs={len(segs)}:normalize=0,apad,atrim=0:{dur}[vo]")
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[vo]", tmp], check=True)
    v_lufs = lufs(tmp)

    # 2. Musique + effets, niveaux relatifs à la voix (entrée 0 = rendu, 1 = voix)
    ins, fl, labels = ["-i", render, "-i", tmp], [], ["[1:a]"]
    if spec.get("music"):
        m = spec["music"]
        eq = ",equalizer=f=2500:t=q:w=1:g=-3" if spec.get("music_eq", True) else ""
        g = v_lufs + spec.get("music_rel", -20) - lufs(m, af="atrim=0:" + str(end))
        b, fo = spec.get("end_boost", 10), spec.get("fade_out", 0.8)
        vol = (f"volume='{10 ** (g / 20):.5f}*if(lt(t,{end - 0.15}),1,"
               f"if(lt(t,{end + 0.25}),pow(10,{b / 20}*(t-{end - 0.15})/0.4),{10 ** (b / 20):.4f}))':eval=frame")
        fl.append(f"[{len(ins) // 2}:a]aresample=48000,aformat=channel_layouts=stereo{eq},atrim=0:{dur},{vol},"
                  f"afade=t=in:d=0.3,afade=t=out:st={dur - fo}:d={fo}[mu]")
        ins += ["-i", m]
        labels.append("[mu]")
    for j, fx in enumerate(spec.get("sfx", [])):
        g = v_lufs + fx["rel"] - lufs(fx["file"])
        fl.append(f"[{len(ins) // 2}:a]aresample=48000,aformat=channel_layouts=stereo,volume={g:.2f}dB,"
                  f"adelay={int(fx['t'] * 1000)}:all=1[s{j}]")
        ins += ["-i", fx["file"]]
        labels.append(f"[s{j}]")
    fl.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0,atrim=0:{dur}[mix]")
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl),
                    "-map", "0:v:0", "-map", "[mix]", "-c:v", "copy", "-c:a", "pcm_s24le", out], check=True)
    os.remove(tmp)
    print(f"voix {v_lufs} LUFS · {len(segs)} prises · carton de fin {end} s · {len(spec.get('sfx', []))} effets")


if __name__ == "__main__":
    main()
