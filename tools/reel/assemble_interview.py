"""Assemble un témoignage (interview à deux, une ou plusieurs prises) → projet HyperFrames prêt pour engine.py.

Usage : python3 tools/reel/assemble_interview.py <plan.json> <dossier_projet> [--sans-video]

plan.json :
{
  "title": "...", "fps": 30, "modele": "large-v3",
  "prises": {"0298": "rushes/interview/DJI_..._0298_D.MP4"},
  "cadres": {"0298": {"J": {"origin": "10% 24%", "tight_scale": 2.0, "wide_scale": 1.0}, "C": {...}}},
  "morceaux": [{"prise": "0298", "in": 55.27, "out": 58.24, "qui": "J", "cadrage": "serre", "flips": [..],
                "texte": "Et ça m'a fait plus de bien que le kiné."}],        # texte : optionnel, corrige la transcription
  "broll": [{"src": "rushes/lot2/DJI_..._0531_D.MP4", "de": 9.0, "morceau": 1, "at": 3.2, "dur": 2.6}],
  "edl": {"kicker": {...}, "end_card": {...}, "keywords": [...], "cap_style": "epure", "cap_max_chars": 26}
}
Les temps "in", "out", "flips" et "at" sont ceux de la prise brute. Chaque morceau devient un fichier assets/fc/mNN.mp4
(0,3 s de marge, voix normalisée à -13 LUFS par prise) ; la transcription est faite morceau par morceau, donc sans
mot à cheval sur une coupe. "texte" remplace les mots transcrits en gardant leurs instants (même nombre de mots,
sinon les instants sont répartis). --sans-video ne refait que les mots et edl.json.
"""
import json
import os
import shutil
import subprocess
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODELE = "videos/epmsp-A-epure"          # polices, logo et fichiers de projet repris du reel validé


def run(*cmd):
    subprocess.run(cmd, check=True)


def loudnorm_args(src, cache):
    if src not in cache:
        e = subprocess.run(["ffmpeg", "-nostdin", "-i", src, "-vn", "-af",
                            "highpass=f=80,loudnorm=I=-13:TP=-1.5:LRA=9:print_format=json", "-f", "null", "-"],
                           capture_output=True, text=True).stderr
        d = json.loads(e[e.rindex("{"):e.rindex("}") + 1])
        cache[src] = (f"measured_I={d['input_i']}:measured_TP={d['input_tp']}:measured_LRA={d['input_lra']}:"
                      f"measured_thresh={d['input_thresh']}:offset={d['target_offset']}")
    return f"highpass=f=80,loudnorm=I=-13:TP=-1.5:LRA=9:{cache[src]}:linear=true,aresample=48000"


def main():
    plan = json.load(open(sys.argv[1]))
    proj = sys.argv[2]
    video = "--sans-video" not in sys.argv
    A = os.path.join(proj, "assets")
    for d in ("fc", "broll", "fonts", "brand"):
        os.makedirs(os.path.join(A, d), exist_ok=True)
    ref = os.path.join(ROOT, MODELE)
    for f in ("hyperframes.json", "package.json", "meta.json"):
        if not os.path.exists(os.path.join(proj, f)):
            shutil.copy(os.path.join(ref, f), os.path.join(proj, f))
    for d in ("fonts", "brand"):
        for f in os.listdir(os.path.join(ref, "assets", d)):
            shutil.copy(os.path.join(ref, "assets", d, f), os.path.join(A, d, f))

    prises = {k: os.path.join(ROOT, v) for k, v in plan["prises"].items()}
    offsets = {k: 1000.0 * i for i, k in enumerate(prises)}          # timeline commune : une prise tous les 1000 s
    cache_path = os.path.join(A, "loudnorm.json")
    cache = json.load(open(cache_path)) if os.path.exists(cache_path) else {}
    wcache_path = os.path.join(A, "mots_cache.json")
    wcache = json.load(open(wcache_path)) if os.path.exists(wcache_path) else {}
    model = None
    segments, words = [], []
    for i, m in enumerate(plan["morceaux"]):
        src, off = prises[m["prise"]], offsets[m["prise"]]
        start = max(0.0, m["in"] - 0.3)
        rel = f"assets/fc/m{i:02d}.mp4"
        out_f = os.path.join(proj, rel)
        if video:
            run("ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", f"{start:.3f}", "-i", src, "-t", f"{m['out'] - start + 0.3:.3f}",
                "-map", "0:v:0", "-map", "0:a:0", "-af", loudnorm_args(src, cache),
                "-c:v", "libx264", "-crf", "15", "-preset", "fast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k",
                "-movflags", "+faststart", out_f)
            json.dump(cache, open(cache_path, "w"), indent=1)
        cadre = plan.get("cadres", {}).get(m["prise"], {}).get(m.get("qui", ""), {})
        s = {"id": f"m{i:02d}", "in": round(m["in"] + off, 3), "out": round(m["out"] + off, 3), "src": rel,
             "src_offset": round(start + off, 3), **cadre}
        if m.get("cadrage"):
            s["cadrage"] = m["cadrage"]
        if m.get("flips"):
            s["flips"] = [round(f + off, 3) for f in m["flips"]]
        segments.append(s)

        # Mots du morceau (transcription du seul passage in → out), en temps de la timeline commune.
        key = f'{m["prise"]}:{m["in"]}:{m["out"]}'
        if key not in wcache:
            if model is None:
                from faster_whisper import WhisperModel
                model = WhisperModel(plan.get("modele", "large-v3"), device="cpu", compute_type="int8")
            raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{m['in']:.3f}", "-t", f"{m['out'] - m['in']:.3f}",
                                  "-i", src, "-vn", "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True).stdout
            segs, _ = model.transcribe(np.frombuffer(raw, np.float32), language="fr", word_timestamps=True,
                                       condition_on_previous_text=False)
            wcache[key] = [[round(w.start, 2), round(w.end, 2), w.word.strip()] for sg in segs for w in sg.words]
            json.dump(wcache, open(wcache_path, "w"), ensure_ascii=False, indent=1)
        ws = [list(w) for w in wcache[key]]
        # Recolle les élisions et traits d'union (« j » + « 'ai ») pour compter des mots entiers.
        mots = []
        for a, b, w in ws:
            if mots and (w[:1] in "'’-"):
                mots[-1][1], mots[-1][2] = b, mots[-1][2] + w
            else:
                mots.append([a, b, w])
        dur = m["out"] - m["in"]
        if m.get("texte"):
            voulu = m["texte"].split()
            if len(voulu) == len(mots):
                for w, t in zip(mots, voulu):
                    w[2] = t
            else:
                print(f"  m{i:02d} : {len(mots)} mots transcrits, {len(voulu)} voulus — instants répartis sur le passage parlé")
                a0, b0 = (mots[0][0], mots[-1][1]) if mots else (0.05, dur - 0.1)
                poids = np.cumsum([0] + [len(t) + 1 for t in voulu])
                mots = [[round(a0 + (b0 - a0) * poids[k] / poids[-1], 2), round(a0 + (b0 - a0) * poids[k + 1] / poids[-1], 2), t]
                        for k, t in enumerate(voulu)]
        recolle = []                                   # « mois » + « ? » → « mois ? » (espace insécable)
        for w in mots:
            if recolle and w[2] in ("?", "!", ":", ";", "»"):
                recolle[-1][1], recolle[-1][2] = w[1], recolle[-1][2] + "\xa0" + w[2]
            else:
                recolle.append(w)
        mots = recolle
        for w in mots:
            w[0] = round(min(max(w[0], 0.02), dur - 0.1) + m["in"] + off, 3)
            w[1] = round(min(max(w[1], 0.05), dur - 0.02) + m["in"] + off, 3)
        print(f"m{i:02d} {m.get('qui', '?')} {dur:5.2f} s : " + " ".join(w[2] for w in mots))
        words.append({"start": mots[0][0] if mots else s["in"], "end": mots[-1][1] if mots else s["out"],
                      "text": " ".join(w[2] for w in mots), "words": mots})
    json.dump(words, open(os.path.join(A, "facecam.words.json"), "w"), ensure_ascii=False, indent=1)

    # Plans de coupe : passage utile seulement, 1080 × 1920, image clé chaque seconde.
    broll = []
    for k, b in enumerate(plan.get("broll", [])):
        rel = f"assets/broll/b{k:02d}.mp4"
        if video:
            run("ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", f"{b['de']:.3f}", "-i", os.path.join(ROOT, b["src"]),
                "-t", f"{b['dur'] + 0.4:.3f}", "-an",
                "-vf", b.get("vf", "") + "scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920",
                "-c:v", "libx264", "-crf", "15", "-preset", "medium", "-g", "25", "-keyint_min", "25", "-sc_threshold", "0",
                "-pix_fmt", "yuv420p", "-movflags", "+faststart", os.path.join(proj, rel))
        m = plan["morceaux"][b["morceau"]]
        broll.append({"src": rel, "seg": f"m{b['morceau']:02d}", "at": round(b["at"] + offsets[m["prise"]], 3),
                      "dur": b["dur"], "offset": 0})

    edl = {"title": plan["title"], "fps": plan.get("fps", 30), "source": segments[0]["src"],
           "words": "assets/facecam.words.json", "segments": segments, "broll": broll,
           "punch": {"scale": 1.3, "origin": "50% 28%", "first_tight": True}, **plan.get("edl", {})}
    json.dump(edl, open(os.path.join(proj, "edl.json"), "w"), ensure_ascii=False, indent=1)
    print(f"{proj}/edl.json : {len(segments)} morceaux, {len(broll)} plans de coupe, "
          f"{sum(s['out'] - s['in'] for s in segments):.1f} s de parole")


if __name__ == "__main__":
    main()
