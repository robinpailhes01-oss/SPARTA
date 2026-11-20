"""Format « reel de Sébastien » (retour client du 20/11) : ouverture de 5 plans de séance de 0,5 s avec leur son réel,
puis l'interview (rendu HyperFrames muet côté séance) où l'on remet le son réel de chaque plan de séance sous la voix.
Pas de musique (ou très basse avec --musique). Noir et blanc sur l'ouverture si edl["noir_blanc"].
Usage : python3 tools/reel/format_seb.py <projet> <image.mp4> <sortie.mp4> [--ambiance -20] [--musique fichier.wav --musique-db -24]"""
import json, os, re, subprocess, sys
proj, image, out = sys.argv[1:4]
opt = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
amb_db = float(opt("--ambiance", -20)); mus = opt("--musique", None); mus_db = float(opt("--musique-db", -24))
edl = json.load(open(os.path.join(proj, "edl.json"))); html = open(os.path.join(proj, "index.html")).read()
tmp = out + ".tmp"; os.makedirs(tmp, exist_ok=True)
run = lambda *a: subprocess.run(a, check=True)
SH = 0.5
pre = edl.get("preroll") or []
nb = ",hue=s=0,eq=contrast=1.06" if edl.get("noir_blanc") else ""
# 1) ouverture
inp, flt = [], []
for i, (f, o) in enumerate(pre):
    inp += ["-ss", str(o), "-t", str(SH), "-i", f]
    flt.append(f"[{i}:v]fps=30,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1{nb},trim=0:{SH},setpts=PTS-STARTPTS[v{i}]")
    flt.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{SH},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st={SH-0.03}:d=0.03[a{i}]")
n = len(pre)
flt.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[pv][pa0]")
flt.append("[pa0]loudnorm=I=-18:TP=-2[pa]")
run("ffmpeg", "-v", "error", *inp, "-filter_complex", ";".join(flt), "-map", "[pv]", "-map", "[pa]", "-c:v", "libx264", "-crf", "16",
    "-preset", "fast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-y", f"{tmp}/pre.mp4")
pre_d = SH * n
# 2) ambiance : son réel de chaque plan de séance, à sa place dans l'interview
brs = re.findall(r'<video id="br-(\d+)" class="full" src="[^"]+" data-start="([\d.]+)" data-duration="([\d.]+)"', html)
ai, af, lab = [], [], []
for j, (k, st, d) in enumerate(brs):
    b = edl["broll"][int(k)]; st, d = float(st), float(d)
    ai += ["-ss", str(b["de"]), "-t", str(d), "-i", b["rush"]]
    af.append(f"[{j + 1}:a]aresample=48000,aformat=channel_layouts=stereo,highpass=f=60,afade=t=in:d=0.08,afade=t=out:st={max(d - 0.15, 0)}:d=0.15,"
              f"adelay={int(st * 1000)}|{int(st * 1000)}[b{j}]")
    lab.append(f"[b{j}]")
# niveau : ambiance normalisée puis placée à amb_db sous la voix (voix ≈ -14 LUFS)
af.append(f"{''.join(lab)}amix=inputs={len(lab)}:normalize=0,loudnorm=I={-14 + amb_db}:TP=-6[amb]" if lab else "anullsrc[amb]")
af.append("[0:a]aresample=48000,aformat=channel_layouts=stereo[voix]")
mix = "[voix][amb]amix=inputs=2:duration=first:normalize=0[mx]"
af.append(mix)
run("ffmpeg", "-v", "error", "-i", image, *ai, "-filter_complex", ";".join(af), "-map", "0:v", "-map", "[mx]", "-c:v", "copy",
    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-y", f"{tmp}/main.mp4")
# 3) ouverture + interview, musique éventuelle, -14 LUFS
with open(f"{tmp}/list.txt", "w") as fh:
    fh.write(f"file '{os.path.abspath(tmp)}/pre.mp4'\nfile '{os.path.abspath(tmp)}/main.mp4'\n")
run("ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", f"{tmp}/list.txt", "-c:v", "libx264", "-crf", "16", "-preset", "fast",
    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-y", f"{tmp}/cat.mp4")
def musique_base(music, end_at, dst):
    """Piste des reels Sparta (séparée de la voix) : début fort, lit bas rallongé par fondus, remontée finale sur le logo."""
    md = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", music], capture_output=True, text=True).stdout)
    A0, A1, B0 = 3.0, md - 4.6, md - 4.4
    need = end_at - 0.2
    seg = [(0, A1)]
    while sum(b - a for a, b in seg) - 1.0 * (len(seg) - 1) < need:
        seg.append((A0 + 6, A1))
    ch = [f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS[s{i}]" for i, (a, b) in enumerate(seg)]
    cur = "s0"
    for i in range(1, len(seg)):
        ch.append(f"[{cur}][s{i}]acrossfade=d=1.0:c1=tri:c2=tri[x{i}]"); cur = f"x{i}"
    ch.append(f"[{cur}]atrim=0:{need},asetpts=PTS-STARTPTS[body]")
    ch.append(f"[0:a]atrim={B0}:{md},asetpts=PTS-STARTPTS,afade=t=out:st={md - B0 - 1.2}:d=1.2[tail]")
    ch.append("[body][tail]acrossfade=d=0.4,aresample=48000,aformat=channel_layouts=stereo[mus]")
    run("ffmpeg", "-v", "error", "-i", music, "-filter_complex", ";".join(ch), "-map", "[mus]", "-y", dst)

mus_base = opt("--musique-base", None)
milieu = opt("--musique-milieu", None)
if mus_base and milieu:
    # Ouverture sur la piste des reels Sparta, puis fondu vers une musique légère sous la voix (retour client du 20/11 :
    # le milieu de la piste séparée n'était qu'un grondement grave).
    m_ = re.search(r'id="endcard" class="clip[^"]*" data-start="([\d.]+)"', html)
    tot = pre_d + float(m_[1]) + 2.0
    rel = float(opt("--milieu-db", -20))
    run("ffmpeg", "-v", "error", "-i", mus_base, "-stream_loop", "-1", "-i", milieu, "-filter_complex",
        f"[0:a]atrim=0:{pre_d + 0.9},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,volume=3dB[a];"
        f"[1:a]atrim=0:{tot},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,loudnorm=I={-14 + rel}:TP=-4[b];"
        f"[a][b]acrossfade=d=0.9:c1=tri:c2=tri,atrim=0:{tot},afade=t=out:st={tot - 1.6}:d=1.6[mus]", "-map", "[mus]", "-y", f"{tmp}/mus.wav")
    run("ffmpeg", "-v", "error", "-i", f"{tmp}/cat.mp4", "-i", f"{tmp}/mus.wav", "-filter_complex",
        "[0:a][1:a]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]",
        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-y", out)
elif mus_base:
    m_ = re.search(r'id="endcard" class="clip[^"]*" data-start="([\d.]+)"', html)
    musique_base(mus_base, pre_d + float(m_[1]), f"{tmp}/mus.wav")
    gain = float(opt("--musique-gain", 3))
    run("ffmpeg", "-v", "error", "-i", f"{tmp}/cat.mp4", "-i", f"{tmp}/mus.wav", "-filter_complex",
        f"[1:a]volume={gain}dB[m];[0:a][m]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]",
        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-y", out)
elif mus:
    run("ffmpeg", "-v", "error", "-i", f"{tmp}/cat.mp4", "-stream_loop", "-1", "-i", mus, "-filter_complex",
        f"[1:a]volume={mus_db + 14}dB,aresample=48000[m];[0:a][m]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]",
        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-y", out)
else:
    run("ffmpeg", "-v", "error", "-i", f"{tmp}/cat.mp4", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-ar", "48000", "-movflags", "+faststart", "-y", out)
print(f"{out} : ouverture {pre_d:.1f} s, {len(brs)} plans de séance avec leur son")
