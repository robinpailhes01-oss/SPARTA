"""timeline_check.py <projet>... : contrôle la composition (index.html) avant rendu.
Signale : face cam visible moins de 0,8 s entre deux plans de coupe / avant le carton de fin (flash),
morceau de face cam de moins de 0,5 s, plan de coupe qui dépasse la fin de son fichier."""
import re, sys, subprocess, os
bad = 0
for proj in sys.argv[1:]:
    if not os.path.exists(os.path.join(proj, "index.html")): continue
    s = open(os.path.join(proj, "index.html"), encoding="utf-8").read()
    br = [(float(a), float(a) + float(d), src) for src, a, d in re.findall(r'<video id="br-\d+" class="full" src="([^"]+)" data-start="([\d.]+)" data-duration="([\d.]+)"', s)]
    end = re.search(r'id="endcard" class="clip[^"]*" data-start="([\d.]+)"', s)
    end = float(end[1]) if end else None
    fc = [(float(a), float(a) + float(d)) for a, d in re.findall(r'<video id="th-m\d+[a-z]?" src="[^"]+" data-start="([\d.]+)" data-duration="([\d.]+)"', s)]
    pb = []
    sch = [(float(a), float(a) + float(d)) for a, d in re.findall(r'class="clip sch" data-start="([\d.]+)" data-duration="([\d.]+)"', s)]
    # le plan de coupe s'efface sur ses 0,22 dernières s, le schéma sur ses 0,4 dernières s
    iv = sorted([(a, b - 0.22) for a, b, _ in br] + [(a, b - 0.4) for a, b in sch] + ([(end, end + 99)] if end is not None else []))
    cov = []
    for a, b in iv:
        if cov and a <= cov[-1][1] + 1e-3: cov[-1][1] = max(cov[-1][1], b)
        else: cov.append([a, b])
    for (a0, b0), (a1, b1) in zip(cov, cov[1:]):
        if a1 - b0 < 0.8: pb.append(f"face cam visible {a1-b0:.2f} s à {b0:.2f}")
    for a, b in fc:
        if b - a < 0.5: pb.append(f"morceau face cam de {b-a:.2f} s à {a:.2f}")
    for a, b, src in br:
        f = os.path.join(proj, src)
        if os.path.exists(f):
            L = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f], capture_output=True, text=True).stdout or 0)
            if b - a > L + 0.4: pb.append(f"plan de coupe {src} : {b-a:.2f} s pour un fichier de {L:.2f} s")   # au-delà de 0,4 s le dernier plan resterait figé trop longtemps
    bad += bool(pb)
    print(("PROBLÈME " if pb else "ok       ") + os.path.basename(proj.rstrip("/")), "; ".join(pb))
sys.exit(1 if bad else 0)
