"""Construit les plan.json des reels tirés de IMG_5280 et pré-remplit mots_cache.json
(mots de la transcription medium, texte corrigé d'après large-v3, instants interpolés pour les mots ajoutés)."""
import json, os, re, difflib, sys
ROOT = "/home/user/SPARTA"
OFF = -0.044            # décalage mesuré entre l'audio extrait et les clips
W = [json.loads(l) for l in open(f"{ROOT}/work/tri/img5280.jsonl")]
WORDS = [w for r in W for w in r["words"]]
norm = lambda s: re.sub(r"[^a-zàâäçéèêëîïôöùûüœ0-9]", "", s.lower())

def mots(clip0, a, b, texte):
    """Mots du passage [a, b] (temps du clip), relatifs à a ; texte = phrase corrigée."""
    src = [[w[0] - clip0 + OFF, w[1] - clip0 + OFF, w[2]] for w in WORDS if a - 0.05 <= w[0] - clip0 + OFF <= b]
    # recolle élisions comme assemble_interview
    ws = []
    for x in src:
        if ws and x[2][:1] in "'’-": ws[-1][1], ws[-1][2] = x[1], ws[-1][2] + x[2]
        else: ws.append(list(x))
    voulu = texte.split()
    sm = difflib.SequenceMatcher(None, [norm(w[2]) for w in ws], [norm(v) for v in voulu], autojunk=False)
    out = [None] * len(voulu)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal" or (tag == "replace" and i2 - i1 == j2 - j1):
            for k in range(j2 - j1): out[j1 + k] = [ws[i1 + k][0], ws[i1 + k][1]]
        elif tag == "replace":
            t0, t1 = ws[i1][0], ws[i2 - 1][1]
            for k in range(j2 - j1):
                out[j1 + k] = [t0 + (t1 - t0) * k / (j2 - j1), t0 + (t1 - t0) * (k + 1) / (j2 - j1)]
    # insertions : interpolées entre voisins
    for j in range(len(out)):
        if out[j] is None:
            k = j
            while k < len(out) and out[k] is None: k += 1
            t0 = out[j - 1][1] if j > 0 else max(0, (out[k][0] if k < len(out) else b - clip0) - 0.3 * (k - j))
            t1 = out[k][0] if k < len(out) else min(b, t0 + 0.3 * (k - j))
            for m in range(j, k): out[m] = [t0 + (t1 - t0) * (m - j) / (k - j), t0 + (t1 - t0) * (m - j + 1) / (k - j)]
    res = []
    for (s, e), v in zip(out, voulu):
        s, e = max(0.0, s - a), max(0.0, e - a)
        res.append([round(s, 2), round(max(e, s + 0.04), 2), v])
    for i in range(1, len(res)):          # monotone
        if res[i][0] < res[i - 1][0]: res[i][0] = res[i - 1][0]
        if res[i][1] < res[i][0]: res[i][1] = res[i][0] + 0.04
    return res

def build(name, cfg):
    proj = f"{ROOT}/videos/{name}"
    os.makedirs(f"{proj}/assets", exist_ok=True)
    prise = cfg["prise"]; clip0 = cfg["clip0"]
    cache_p = f"{proj}/assets/mots_cache.json"
    cache = json.load(open(cache_p)) if os.path.exists(cache_p) else {}
    morceaux = []
    for m in cfg["morceaux"]:
        key = f'{prise}:{m["in"]}:{m["out"]}'
        cache[key] = mots(clip0, m["in"], m["out"], m.pop("texte"))
        morceaux.append({"prise": prise, **m})
    json.dump(cache, open(cache_p, "w"), ensure_ascii=False, indent=1)
    plan = {"title": cfg["title"], "fps": 30, "modele": "medium",
            "prises": {prise: f"rushes/img5280/{prise}.mp4"},
            "vf": {prise: cfg["vf"]}, "cadres": {prise: cfg["cadres"]},
            "morceaux": morceaux, "edl": cfg["edl"], "schemas": cfg.get("schemas", [])}
    json.dump(plan, open(f"{proj}/plan.json", "w"), ensure_ascii=False, indent=1)
    print(name, "ok", sum(m["out"] - m["in"] for m in morceaux))

if __name__ == "__main__":
    cfgs = json.load(open(sys.argv[1]))
    for n, c in cfgs.items():
        if len(sys.argv) < 3 or n in sys.argv[2:]: build(n, c)
