"""Format « témoignage de base » Sparta (Mickaël, Xavier) — retour client du 20/11.
Ouverture : 5 plans de séance très courts (≈ 0,5 s) sur la musique seule, puis l'interview (rendu HyperFrames sans titre),
musique de leur vidéo : forte sur l'ouverture, basse sous la voix, qui remonte sur le logo de fin.
Usage : python3 tools/reel/format_base.py <projet> <image.mp4> <musique.wav> <sortie.mp4>
  <projet>/edl.json : "preroll": [[fichier, début], ...] (sinon 5 plans pris dans assets/broll)."""
import json, os, subprocess, sys
proj, image, music, out = sys.argv[1:5]
edl = json.load(open(os.path.join(proj, "edl.json")))
SH = 0.52
pre = edl.get("preroll") or [[f"assets/broll/b{k:02d}.mp4", o] for k, o in ((0, 0.4), (2, 1.6), (4, 0.8), (5, 1.8), (6, 0.6))]
tmp = out + ".tmp"; os.makedirs(tmp, exist_ok=True)
run = lambda *a: subprocess.run(a, check=True)
# 1) ouverture : plans muets mis bout à bout (coupes franches)
inputs, filt = [], []
for i, (f, o) in enumerate(pre):
    inputs += ["-ss", str(o), "-t", str(SH), "-i", os.path.join(proj, f)]
    filt.append(f"[{i}:v]fps=30,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,trim=0:{SH},setpts=PTS-STARTPTS[v{i}]")
n = len(pre)
filt.append("".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[pv]")
run("ffmpeg", "-v", "error", *inputs, "-f", "lavfi", "-t", str(SH * n), "-i", "anullsrc=r=48000:cl=stereo",
    "-filter_complex", ";".join(filt), "-map", "[pv]", "-map", f"{n}:a", "-c:v", "libx264", "-crf", "16", "-preset", "fast",
    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-y", f"{tmp}/pre.mp4")
pre_d = SH * n
img_d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", image], capture_output=True, text=True).stdout)
total = pre_d + img_d
import re
m = re.search(r'id="endcard" class="clip[^"]*" data-start="([\d.]+)"', open(os.path.join(proj, "index.html")).read())
end_at = pre_d + (float(m[1]) if m else img_d - 2)
# 2) musique : début de la piste (ouverture), lit « sous la voix » rallongé par fondus, fin de piste sur le logo
md = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", music], capture_output=True, text=True).stdout)
A0, A1 = 3.0, md - 4.6           # zone basse de la piste source
B0 = md - 4.4                    # remontée finale
need = end_at - 0.2              # musique « corps » jusqu'au logo
parts, t, src = [], 0.0, []
seg = [(0, A1)]
while sum(b - a for a, b in seg) - 1.0 * (len(seg) - 1) < need:
    seg.append((A0 + 6, A1))
chain = []
for i, (a, b) in enumerate(seg):
    chain.append(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS[s{i}]")
cur = "s0"
for i in range(1, len(seg)):
    chain.append(f"[{cur}][s{i}]acrossfade=d=1.0:c1=tri:c2=tri[x{i}]"); cur = f"x{i}"
chain.append(f"[{cur}]atrim=0:{need},asetpts=PTS-STARTPTS[body]")
chain.append(f"[0:a]atrim={B0}:{md},asetpts=PTS-STARTPTS,afade=t=out:st={md - B0 - 1.2}:d=1.2[tail]")
chain.append(f"[body][tail]acrossfade=d=0.4[mus]")
run("ffmpeg", "-v", "error", "-i", music, "-filter_complex", ";".join(chain), "-map", "[mus]", "-ar", "48000", "-ac", "2", "-y", f"{tmp}/mus.wav")
# 3) image : ouverture + interview, puis mixage voix + musique et -14 LUFS
with open(f"{tmp}/list.txt", "w") as fh:
    fh.write(f"file '{os.path.abspath(tmp)}/pre.mp4'\nfile '{os.path.abspath(image)}'\n")
run("ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", f"{tmp}/list.txt", "-c:v", "libx264", "-crf", "16", "-preset", "fast",
    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-y", f"{tmp}/cat.mp4")
gain = float(edl.get("base_music_gain", 0.0))
run("ffmpeg", "-v", "error", "-i", f"{tmp}/cat.mp4", "-i", f"{tmp}/mus.wav", "-filter_complex",
    f"[1:a]volume={gain}dB[m];[0:a][m]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]",
    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-y", out)
print(f"{out} : ouverture {pre_d:.2f} s + interview {img_d:.2f} s, logo à {end_at:.2f} s")
