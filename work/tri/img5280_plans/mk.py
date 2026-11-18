"""mk.py <spec.json> : écrit videos/<proj>/plan.json et pré-remplit assets/mots_cache.json depuis work/tri/img5280.jsonl.
spec : {"proj", "title", "prises": {k: [fichier, debut_source]}, "vf": {...}, "cadres": {...},
        "morceaux": [{"prise", "a", "b" (temps source), "cadrage", "flips" (source), "fix": [[ancien..],[nouveau..]]...}],
        "schemas": [{... "morceau": i, "at": source, "temps": [source...] }], "edl": {...}}
Les temps source sont convertis en temps de prise (source - debut). Les "temps" de schéma sont convertis en temps
de timeline relatif au morceau du schéma (calcul à travers les coupes)."""
import json, os, sys
R = "/home/user/SPARTA"
sp = json.load(open(sys.argv[1]))
L = [json.loads(l) for l in open(f"{R}/work/tri/img5280.jsonl")]
W = [w for r in L for w in r["words"]]
P = f"{R}/videos/{sp['proj']}"; os.makedirs(f"{P}/assets", exist_ok=True)
keys = list(sp["prises"]); off = {k: 1000.0 * i for i, k in enumerate(keys)}
import subprocess, numpy as np
MASK = {}
def mask(k):
    if k not in MASK:
        f = f"{R}/" + sp["prises"][k][0]
        raw = subprocess.run(["ffmpeg","-nostdin","-v","error","-i",f,"-vn","-af","highpass=f=120","-ac","1","-ar","16000","-f","f32le","-"],capture_output=True).stdout
        a = np.frombuffer(raw, np.float32); n = len(a)//160
        e = 20*np.log10(np.maximum(np.sqrt((a[:n*160].reshape(n,160)**2).mean(1)),1e-6))
        MASK[k] = e > -45
    return MASK[k]
def best_shift(k, ws, f0):
    mk_ = mask(k); best = (0, -1)
    for sh in np.arange(-1.0, 0.41, 0.02):
        sc = 0
        for w in ws:
            i0, i1 = int((w[0] - f0 + sh) * 100), int((w[1] - f0 + sh) * 100)
            if i1 > i0 and i0 >= 0 and i1 < len(mk_): sc += mk_[i0:i1].mean() * (i1 - i0) ** 0.5
        if sc > best[1] + 1e-9: best = (round(float(sh), 2), sc)
    return best[0]
morc, cache, tl, t = [], {}, [], 0.0
for m in sp["morceaux"]:
    f0 = sp["prises"][m["prise"]][1]
    a, b = round(m["a"] - f0, 2), round(m["b"] - f0, 2)
    mm = {"prise": m["prise"], "in": a, "out": b, "qui": "L", "cadrage": m.get("cadrage", "large")}
    if m.get("flips"): mm["flips"] = [round(x - f0, 2) for x in m["flips"]]
    morc.append(mm); tl.append((t, m["a"], m["b"])); t += m["b"] - m["a"]
    if m.get("mots"):          # mots posés à la main : [[début, fin, "texte"]...] en temps source
        ws = [[x[0], x[1], t_] for x in m["mots"] for t_ in [None]]
        ws = []
        for a0, b0, txt in m["mots"]:
            toks = txt.split(); poids = np.cumsum([0] + [len(x) + 1 for x in toks])
            ws += [[round(a0 + (b0 - a0) * poids[j] / poids[-1], 2), round(a0 + (b0 - a0) * poids[j + 1] / poids[-1], 2), x] for j, x in enumerate(toks)]
        sh = 0
    else:
        cand = [list(w) for w in W if w[0] >= m["a"] - 1.2 and w[1] <= m["b"] + 1.2]
        sh = m.get("shift", best_shift(m["prise"], cand, f0))
        ws = [[round(w[0] + sh, 2), round(w[1] + sh, 2), w[2]] for w in cand]
        ws = [w for w in ws if w[0] >= m["a"] - 0.15 and w[0] < m["b"] - 0.1]
    for old, new in m.get("fix", []):
        toks = [w[2] for w in ws]
        for i in range(len(toks) - len(old) + 1):
            if toks[i:i + len(old)] == old:
                s0, e0 = ws[i][0], ws[i + len(old) - 1][1]; n = max(len(new), 1)
                rep = [[round(s0 + (e0 - s0) * k / n, 2), round(s0 + (e0 - s0) * (k + 1) / n, 2), new[k]] for k in range(len(new))]
                ws[i:i + len(old)] = rep; break
        else:
            print("FIX INTROUVABLE", old, "dans", " ".join(toks)); sys.exit(1)
    cache[f'{m["prise"]}:{a}:{b}'] = [[round(max(0, w[0] - m["a"]), 2), round(min(w[1], m["b"]) - m["a"], 2), w[2]] for w in ws]
    print(f"{len(morc)-1}: {b-a:5.2f}s décalage {sh:+.2f}  " + " ".join(w[2] for w in ws))
def src_to_common(x):
    for m in sp["morceaux"]:
        if m["a"] - 0.01 <= x <= m["b"] + 0.01: return round(x - sp["prises"][m["prise"]][1] + off[m["prise"]], 3)
    raise SystemExit(f"temps {x} hors morceaux")
sch = []
for s in sp.get("schemas", []):
    i = s["morceau"]; m = sp["morceaux"][i]; f0 = sp["prises"][m["prise"]][1]
    s = dict(s); s["temps"] = [src_to_common(x) for x in s["temps"]]
    s["at"] = round(s["at"] - f0, 3)
    sch.append(s)
plan = {"title": sp["title"], "fps": 30, "modele": "medium", "prises": {k: v[0] for k, v in sp["prises"].items()},
        "vf": sp["vf"], "cadres": sp["cadres"], "morceaux": morc, "schemas": sch, "edl": sp["edl"]}
json.dump(plan, open(f"{P}/plan.json", "w"), ensure_ascii=False, indent=1)
cp = f"{P}/assets/mots_cache.json"
old = json.load(open(cp)) if os.path.exists(cp) else {}
old.update(cache); json.dump(old, open(cp, "w"), ensure_ascii=False, indent=1)
print(f"total {t:.1f} s")
