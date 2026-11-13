"""Tri d'un dossier de rushes : fiche par clip (durée, format, niveau sonore), planche-contact et transcription.

Usage : python3 tools/reel/tri_rushes.py <dossier_rushes> <dossier_sortie> [modèle=medium]
Écrit <sortie>/<clip>.jpg (8 images réparties), <sortie>/<clip>.words.json (si de la parole) et <sortie>/index.json.
Relançable : les clips déjà traités sont sautés.
"""
import json
import os
import subprocess
import sys

import numpy as np


def probe(path):
    j = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                   "format=duration:stream=codec_type,width,height,r_frame_rate,color_transfer:stream_side_data=rotation",
                                   "-of", "json", path], capture_output=True, text=True).stdout)
    v = next((s for s in j["streams"] if s["codec_type"] == "video"), {})
    n, d = (v.get("r_frame_rate", "0/1").split("/") + ["1"])[:2]
    return {"duree": round(float(j["format"]["duration"]), 2), "w": v.get("width"), "h": v.get("height"),
            "fps": round(float(n) / float(d or 1), 2), "trc": v.get("color_transfer"),
            "audio": any(s["codec_type"] == "audio" for s in j["streams"])}


def audio(path):
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", path, "-vn", "-map", "0:a:0", "-ac", "1", "-ar", "16000",
                          "-f", "s16le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def main():
    src, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    idx_path = os.path.join(out, "index.json")
    idx = json.load(open(idx_path)) if os.path.exists(idx_path) else {}
    model = None
    for name in sorted(os.listdir(src)):
        if not name.lower().endswith((".mp4", ".mov")) or name in idx:
            continue
        path, base = os.path.join(src, name), name.rsplit(".", 1)[0]
        try:
            p = probe(path)
        except Exception as e:                      # fichier incomplet ou illisible : on le reprendra au prochain passage
            print(name, "illisible", e); continue
        n = 8
        step = max(p["duree"] / n, 0.04)
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", path, "-vf",
                        f"fps=1/{step:.3f},scale=-2:384,tile={n}x1", "-frames:v", "1", "-update", "1",
                        os.path.join(out, base + ".jpg")])
        p["texte"], p["mots"] = "", 0
        if p["audio"]:
            a = audio(path)
            p["rms_db"] = round(float(20 * np.log10(max(np.sqrt((a ** 2).mean()), 1e-6))), 1) if len(a) else None
            if len(a) > 16000:
                if model is None:
                    from faster_whisper import WhisperModel
                    model = WhisperModel(sys.argv[3] if len(sys.argv) > 3 else "medium", device="cpu", compute_type="int8")
                segs, _ = model.transcribe(a, language="fr", word_timestamps=True, vad_filter=True,
                                           condition_on_previous_text=False)
                data = [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip(),
                         "words": [[round(w.start, 2), round(w.end, 2), w.word] for w in s.words]} for s in segs]
                if data:
                    json.dump(data, open(os.path.join(out, base + ".words.json"), "w"), ensure_ascii=False, indent=1)
                p["texte"] = " ".join(s["text"] for s in data)
                p["mots"] = sum(len(s["words"]) for s in data)
        idx[name] = p
        json.dump(idx, open(idx_path, "w"), ensure_ascii=False, indent=1)
        print(f"{name} {p['duree']} s {p['w']}x{p['h']} {p['mots']} mots", flush=True)


if __name__ == "__main__":
    main()
