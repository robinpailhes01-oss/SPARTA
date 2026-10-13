"""Transcription mot à mot (faster-whisper, français) → JSON lu par engine.py.

Usage : python3 tools/reel/transcribe.py <video_ou_audio> <sortie.json> [modèle=medium]
"""
import json
import subprocess
import sys

import numpy as np
from faster_whisper import WhisperModel


def load_audio(path):
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", "16000",
                          "-f", "s16le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def main():
    src, out = sys.argv[1], sys.argv[2]
    model = WhisperModel(sys.argv[3] if len(sys.argv) > 3 else "medium", device="cpu", compute_type="int8")
    segs, _ = model.transcribe(load_audio(src), language="fr", word_timestamps=True, vad_filter=False,
                               condition_on_previous_text=False)
    data = [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip(),
             "words": [[round(w.start, 2), round(w.end, 2), w.word] for w in s.words]} for s in segs]
    json.dump(data, open(out, "w"), ensure_ascii=False, indent=1)
    with open(out.rsplit(".", 1)[0] + ".txt", "w") as f:
        for s in data:
            f.write(f"[{s['start']:7.2f}-{s['end']:7.2f}] {s['text']}\n")
    print(f"{out} : {len(data)} phrases")


if __name__ == "__main__":
    main()
