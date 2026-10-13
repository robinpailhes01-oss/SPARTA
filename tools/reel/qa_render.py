"""Contrôle qualité d'un rendu : planches d'images + mesures techniques, pour relecture avant livraison.

Usage : python3 tools/reel/qa_render.py <dossier_projet> <rendu.mp4> <dossier_sortie> [--whisper]

Produit dans <dossier_sortie> :
  hook_01.png         les 3 premières secondes (accroche + kicker)
  caps_NN.png         chaque sous-titre à mi-durée, bande 1080 px pleine définition (lisibilité, orthographe)
  capsctx_NN.png      les mêmes instants en image entière réduite (placement, visage, plan de coupe)
  cuts_NN.png         chaque raccord face cam : dernière image avant / première image après
  broll_NN.png        chaque plan de coupe : entrée, milieu, sortie
  end_01.png          carton de fin
  report.json         durées, loudness, gels d'image, noirs, silences, sous-titres attendus, raccords, plans de coupe
                      (+ mots reconnus sur le son du rendu avec --whisper, pour vérifier la synchro des sous-titres)
"""
import html
import json
import os
import re
import subprocess
import sys

FPS = 25          # remplacé par la cadence réelle du rendu dans main()


def sh(*cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def parse(index_html):
    s = open(index_html, encoding="utf-8").read()
    caps = [{"id": int(m[0]), "start": float(m[1]), "dur": float(m[2]), "text": html.unescape(re.sub(r"<[^>]+>", "", m[3]))}
            for m in re.findall(r'id="cap-(\d+)" class="clip cap" data-start="([\d.]+)" data-duration="([\d.]+)"[^>]*>'
                                r'<span class="cap-box">(.*?)</span>', s)]
    segs = [{"id": m[0], "start": float(m[1]), "dur": float(m[2])}
            for m in re.findall(r'<video id="th-(m\d+)" src="[^"]+" data-start="([\d.]+)" data-duration="([\d.]+)"', s)]
    brolls = [{"id": m[0], "src": m[1], "start": float(m[2]), "dur": float(m[3]), "media_start": float(m[4])}
              for m in re.findall(r'<video id="(br-\d+)" class="full" src="([^"]+)" data-start="([\d.]+)" '
                                  r'data-duration="([\d.]+)" data-media-start="([\d.]+)"', s)]
    end = re.search(r'id="endcard" class="clip" data-start="([\d.]+)" data-duration="([\d.]+)"', s)
    return caps, segs, brolls, (float(end[1]), float(end[2])) if end else None


def sheet(render, times, out_pattern, font, cols=4, rows=2, w=360, h=640, crop=None):
    """Extrait les images aux instants donnés (numéros d'image exacts) et les monte en planches cols×rows."""
    if not times:
        return []
    frames = sorted({max(0, round(t * FPS)) for t in times})
    sel = "+".join(f"eq(n\\,{n})" for n in frames)
    label = (f"drawtext=fontfile={font}:text='%{{eif\\:n\\:d}}  t=%{{pts\\:flt}}':x=12:y=12:fontsize=34:"
             "fontcolor=yellow:box=1:boxcolor=black@0.7:boxborderw=6")
    if crop:                                  # bande pleine définition (sous-titres)
        vf = f"select='{sel}',{crop},{label},tile=1x{rows}:padding=4:color=0x303030"
    else:
        vf = f"select='{sel}',{label},scale={w}:{h},tile={cols}x{rows}:padding=4:color=0x303030"
    sh("ffmpeg", "-nostdin", "-v", "error", "-y", "-i", render, "-vf", vf, "-fps_mode", "passthrough", "-start_number", "1", out_pattern)
    d = os.path.dirname(out_pattern)
    pre = os.path.basename(out_pattern).split("%")[0]
    return sorted(f for f in os.listdir(d) if f.startswith(pre))


def measures(render):
    r = {}
    p = sh("ffprobe", "-v", "error", "-show_entries", "stream=codec_type,duration,width,height,r_frame_rate,color_transfer,pix_fmt",
           "-show_entries", "format=duration,size,bit_rate", "-of", "json", render)
    r["probe"] = json.loads(p.stdout)
    e = sh("ffmpeg", "-nostdin", "-i", render, "-af", "ebur128=peak=true", "-f", "null", "-").stderr
    summ = e[e.rfind("Summary:"):]
    for k, pat in (("I_LUFS", r"I:\s+(-?[\d.]+) LUFS"), ("LRA_LU", r"LRA:\s+([\d.]+) LU"), ("truepeak_dBFS", r"Peak:\s+(-?[\d.]+) dBFS")):
        m = re.search(pat, summ)
        r[k] = float(m[1]) if m else None
    f = sh("ffmpeg", "-nostdin", "-i", render, "-vf", "freezedetect=n=0.0008:d=0.4", "-map", "0:v", "-f", "null", "-").stderr
    r["freezes"] = [(float(a), float(b)) for a, b in zip(re.findall(r"freeze_start: ([\d.]+)", f), re.findall(r"freeze_end: ([\d.]+)", f))]
    b = sh("ffmpeg", "-nostdin", "-i", render, "-vf", "blackdetect=d=0.08:pix_th=0.10", "-map", "0:v", "-f", "null", "-").stderr
    r["blacks"] = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", b)
    s = sh("ffmpeg", "-nostdin", "-i", render, "-af", "silencedetect=n=-45dB:d=0.3", "-map", "0:a", "-f", "null", "-").stderr
    r["silences"] = list(zip(re.findall(r"silence_start: (-?[\d.]+)", s), re.findall(r"silence_end: ([\d.]+)", s)))
    # Niveau par fenêtre de 0,5 s (repère la musique trop forte sous la voix ou les trous)
    a = sh("ffmpeg", "-nostdin", "-i", render, "-af", "asetnsamples=24000,astats=metadata=1:reset=1,"
           "ametadata=print:key=lavfi.astats.Overall.RMS_level", "-map", "0:a", "-f", "null", "-").stderr
    r["rms_per_0.5s"] = [round(float(x), 1) if x not in ("-inf", "inf") else -99.0
                         for x in re.findall(r"lavfi.astats.Overall.RMS_level=(-?[\w.]+)", a)]
    return r


def main():
    global FPS
    proj, render, out = sys.argv[1], sys.argv[2], sys.argv[3]
    n, d = sh("ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
              "-of", "csv=p=0", render).stdout.strip().split("/")
    FPS = float(n) / float(d)
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        if f.endswith(".png"):
            os.remove(os.path.join(out, f))
    font = os.path.abspath(os.path.join(proj, "assets/fonts", sorted(os.listdir(os.path.join(proj, "assets/fonts")))[0]))
    caps, segs, brolls, end = parse(os.path.join(proj, "index.html"))

    mids = [c["start"] + c["dur"] / 2 for c in caps]
    rep = {"render": render, "captions": caps, "segments": segs, "broll": brolls, "end_card": end, "sheets": {}}
    rep["sheets"]["hook"] = sheet(render, [0.0, 0.4, 0.8, 1.2, 1.6, 2.0, 2.5, 3.0], f"{out}/hook_%02d.png", font)
    rep["sheets"]["caps"] = sheet(render, mids, f"{out}/caps_%02d.png", font, rows=6, crop="crop=1080:260:0:1260")
    rep["sheets"]["capsctx"] = sheet(render, mids, f"{out}/capsctx_%02d.png", font, cols=6, rows=2, w=300, h=533)
    cut_t = []
    for s in segs[1:]:
        cut_t += [s["start"] - 1 / FPS, s["start"] + 1 / FPS]
    rep["sheets"]["cuts"] = sheet(render, cut_t, f"{out}/cuts_%02d.png", font, cols=4, rows=2)
    br_t = []
    for b in brolls:
        br_t += [b["start"] + 0.04, b["start"] + b["dur"] / 2, b["start"] + b["dur"] - 0.08]
    rep["sheets"]["broll"] = sheet(render, br_t, f"{out}/broll_%02d.png", font, cols=6, rows=2, w=300, h=533)
    if end:
        rep["sheets"]["end"] = sheet(render, [end[0] - 0.2, end[0] + 0.3, end[0] + 1.0, end[0] + end[1] - 0.1],
                                     f"{out}/end_%02d.png", font)
    rep["measures"] = measures(render)

    if "--whisper" in sys.argv:
        wav = os.path.join(out, "voice.wav")
        sh("ffmpeg", "-nostdin", "-v", "error", "-y", "-i", render, "-ac", "1", "-ar", "16000", wav)
        tools = os.path.dirname(os.path.abspath(__file__))
        sh("python3", os.path.join(tools, "transcribe.py"), wav, os.path.join(out, "render.words.json"), "medium")
        words = []
        if os.path.exists(os.path.join(out, "render.words.json")):
            for seg in json.load(open(os.path.join(out, "render.words.json"))):
                words += seg["words"]
        rep["render_words"] = words
        # Décalage sous-titre ↔ voix : pour chaque sous-titre, premier mot reconnu dont le texte correspond
        def norm(x):
            return re.sub(r"[^\wà-ÿ]", "", x.lower())
        sync, j = [], 0
        for c in caps:
            first = norm(c["text"].split()[0]) if c["text"].split() else ""
            for k in range(j, min(j + 25, len(words))):
                if norm(words[k][2]).startswith(first[:4]) and abs(words[k][0] - c["start"]) < 1.5:
                    sync.append({"cap": c["id"], "text": c["text"], "cap_start": c["start"], "voice_start": round(words[k][0], 2),
                                 "delta": round(c["start"] - words[k][0], 2)})
                    j = k + 1
                    break
            else:
                sync.append({"cap": c["id"], "text": c["text"], "cap_start": c["start"], "voice_start": None, "delta": None})
        rep["caption_sync"] = sync
        os.remove(wav)
    json.dump(rep, open(os.path.join(out, "report.json"), "w"), ensure_ascii=False, indent=1)
    m = rep["measures"]
    print(json.dumps({k: m[k] for k in ("I_LUFS", "LRA_LU", "truepeak_dBFS", "freezes", "blacks")}, ensure_ascii=False))
    print({k: len(v) for k, v in rep["sheets"].items()})


if __name__ == "__main__":
    main()
