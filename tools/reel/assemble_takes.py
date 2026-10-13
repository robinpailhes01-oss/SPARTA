"""Assemble un reel multi-prises : liste de montage (prises + B-roll) → projet HyperFrames prêt pour engine.py.

Usage : python3 tools/reel/assemble_takes.py <plan.json> <dossier_projet>

plan.json :
{
  "title": "...", "fps": 25,
  "takes_dir": "work/takes",                 # <takes_dir>/<prise>/assets/facecam.mp4 (préparé)
  "words_dir": ".../fc",                     # <words_dir>/dji<prise>.json (transcription du rush brut)
  "broll_dir": "broll/examen",               # <broll_dir>/<clip>.mp4
  "faces": {"0555": {"origin": "52% 28%", "tight_scale": 1.6, "wide_scale": 1.0}, ...},
  "edl": { "kicker": "...", "morceaux": [{"prise","in","out","texte","cadrage"}],
           "broll": [{"prise","at","clip","offset","dur"}], "flash": "...", "corrections": [[a, b]] },
  "emphasis": ["coach"],                     # mots à mettre en or dans les sous-titres (en plus des chiffres)
  "music": "assets/musique.wav", "end_card": {...}
}
Le dossier projet doit déjà exister (npx hyperframes init) ; les polices et le logo y sont copiés.
"""
import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run(*cmd):
    subprocess.run(cmd, check=True)


def dur(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                                capture_output=True, text=True, check=True).stdout)


def main():
    plan = json.load(open(sys.argv[1]))
    proj = sys.argv[2]
    edl = plan["edl"]
    A = os.path.join(proj, "assets")
    os.makedirs(os.path.join(A, "broll"), exist_ok=True)
    os.makedirs(os.path.join(A, "fonts"), exist_ok=True)
    os.makedirs(os.path.join(A, "brand"), exist_ok=True)
    nico = os.path.join(ROOT, "videos/temoignage-nicolas/assets")
    for f in os.listdir(os.path.join(nico, "fonts")):
        shutil.copy(os.path.join(nico, "fonts", f), os.path.join(A, "fonts", f))
    shutil.copy(os.path.join(nico, "brand/logo_or_blanc.png"), os.path.join(A, "brand/logo_or_blanc.png"))

    # 1. Prises utilisées, mises bout à bout (une seule fois chacune) → facecam.mp4
    takes = []
    for m in edl["morceaux"]:
        if m["prise"] not in takes:
            takes.append(m["prise"])
    offsets, t, lst = {}, 0.0, os.path.join(A, ".concat.txt")
    with open(lst, "w") as f:
        for p in takes:
            src = os.path.abspath(os.path.join(ROOT, plan["takes_dir"], p, "assets/facecam.mp4"))
            offsets[p] = round(t, 3)
            t += dur(src)
            f.write(f"file '{src}'\n")
    run("ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
        "-movflags", "+faststart", os.path.join(A, "facecam.mp4"))
    os.remove(lst)
    real = dur(os.path.join(A, "facecam.mp4"))
    print(f"facecam.mp4 : {len(takes)} prises, {real:.2f} s (attendu {t:.2f} s)")

    # 2. Mots recalés sur la timeline commune
    merged = []
    for p in takes:
        for seg in json.load(open(os.path.join(plan["words_dir"], f"dji{p}.json"))):
            merged.append({"start": seg["start"] + offsets[p], "end": seg["end"] + offsets[p], "text": seg["text"],
                           "words": [[round(w[0] + offsets[p], 3), round(w[1] + offsets[p], 3), w[2]] for w in seg["words"]]})
    json.dump(merged, open(os.path.join(A, "facecam.words.json"), "w"), ensure_ascii=False, indent=1)

    # 3. B-roll : copie des clips utilisés
    for b in edl["broll"]:
        dst = os.path.join(A, "broll", b["clip"] + ".mp4")
        if not os.path.exists(dst):
            shutil.copy(os.path.join(ROOT, plan["broll_dir"], b["clip"] + ".mp4"), dst)

    # 4. Musique : bouclée en fondu enchaîné jusqu'à la durée nécessaire
    total_needed = sum(m["out"] - m["in"] for m in edl["morceaux"]) + 4.0
    music_src = os.path.join(ROOT, plan["music"])
    mlen = dur(music_src)
    loops = max(1, int(total_needed // (mlen - 3)) + 1)
    if loops > 1:
        inputs = []
        for _ in range(loops):
            inputs += ["-i", music_src]
        chain, last = [], "[0:a]"
        for k in range(1, loops):
            chain.append(f"{last}[{k}:a]acrossfade=d=3:c1=tri:c2=tri[x{k}]")
            last = f"[x{k}]"
        run("ffmpeg", "-nostdin", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(chain), "-map", last,
            "-c:a", "pcm_s16le", os.path.join(A, "musique.wav"))
    else:
        shutil.copy(music_src, os.path.join(A, "musique.wav"))
    music_len = dur(os.path.join(A, "musique.wav"))

    # 4 bis. Un petit fichier par morceau (0,3 s de marge) : beaucoup plus léger à lire que la face cam entière
    os.makedirs(os.path.join(A, "fc"), exist_ok=True)
    cuts = {}
    for i, m in enumerate(edl["morceaux"]):
        src = os.path.abspath(os.path.join(ROOT, plan["takes_dir"], m["prise"], "assets/facecam.mp4"))
        start = max(0.0, m["in"] - 0.3)
        out_f = os.path.join(A, "fc", f"m{i:02d}.mp4")
        run("ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", f"{start:.3f}", "-i", src, "-t", f"{m['out'] - start + 0.3:.3f}",
            "-c:v", "libx264", "-crf", "15", "-preset", "fast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k",
            "-movflags", "+faststart", out_f)
        cuts[i] = (f"assets/fc/m{i:02d}.mp4", round(start + offsets[m["prise"]], 3))

    # 5. edl.json pour engine.py
    faces = plan.get("faces", {})
    segments = []
    for i, m in enumerate(edl["morceaux"]):
        p, off = m["prise"], offsets[m["prise"]]
        s = {"id": f"m{i:02d}", "in": round(m["in"] + off, 3), "out": round(m["out"] + off, 3),
             "src": cuts[i][0], "src_offset": cuts[i][1]}
        if m.get("cadrage") in ("serre", "large"):
            s["cadrage"] = m["cadrage"]
        if m.get("flips"):                                  # changements de cadrage, en temps du rush
            s["flips"] = [round(f + off, 3) for f in m["flips"]]
        s.update({k: v for k, v in faces.get(p, {}).items()})
        s.update({k: m[k] for k in ("origin", "tight_scale", "wide_scale") if k in m})   # réglage propre au morceau
        segments.append(s)
    seg_of = lambda tt: next(s["id"] for s in segments if s["in"] - 0.06 <= tt <= s["out"] + 0.06)
    broll = []
    for b in edl["broll"]:
        at = round(b["at"] + offsets[b["prise"]], 3)
        try:
            sid = seg_of(at)
        except StopIteration:
            print(f"B-roll ignoré (hors montage) : {b}")
            continue
        broll.append({"src": f"assets/broll/{b['clip']}.mp4", "seg": sid, "at": at, "dur": b["dur"],
                      "offset": b["offset"]})
    out = {
        "title": plan["title"], "fps": plan.get("fps", 25), "source": "assets/facecam.mp4",
        "words": "assets/facecam.words.json", "segments": segments,      # "source" : non lue (src par morceau)
        "punch": {"scale": 1.3, "origin": "50% 28%", "first_tight": True},
        "corrections": {a: b for a, b in edl.get("corrections", [])},
        "emphasis": plan.get("emphasis", []),
        "broll": broll,
        "music": {"src": "assets/musique.wav", "len": round(music_len, 3), "end_boost": 3.5,
                  "start": {"seg": segments[0]["id"], "at": segments[0]["in"]}, "beats": "beats/assets/musique.wav.json"},
        "end_card": plan.get("end_card", {"logo": "assets/brand/logo_or_blanc.png", "dur": 2.0}),
    }
    if edl.get("kicker"):
        out["kicker"] = {"text": edl["kicker"], "dur": edl.get("kicker_dur", 2.0)}
    if plan.get("flash"):
        out["flash"] = plan["flash"]
    if plan.get("grade"):
        out["grade"] = plan["grade"]
    json.dump(out, open(os.path.join(proj, "edl.json"), "w"), ensure_ascii=False, indent=1)
    os.remove(os.path.join(A, "facecam.mp4"))          # chaque morceau a son fichier ; la concaténation ne sert plus
    print(f"edl.json : {len(segments)} morceaux, {len(broll)} plans de coupe, musique {music_len:.1f} s, offsets {offsets}")


if __name__ == "__main__":
    main()
