"""Moteur de reels Sparta : génère index.html (composition HyperFrames) depuis un edl.json.

Usage : python3 tools/reel/engine.py <dossier_projet>   (lit <dossier_projet>/edl.json)

Toutes les règles visuelles viennent de STYLE.md (§ 0 direction premium et minimaliste,
§ 5 sous-titres, § 6 preuve, § 7 carte de fin, § 7 bis motion design, § 9 audio).
Les temps « src » sont ceux de la vidéo face cam brute ; le moteur les convertit en
temps du montage.

edl.json (seuls "title", "source" et "segments" sont obligatoires) :
{
  "title": "Témoignage Nicolas — Sparta",
  "source": "assets/facecam.mp4",            # face cam (son conservé)
  "words": "assets/facecam.words.json",      # transcription mot à mot (pour les sous-titres auto)
  "segments": [{"id": "hook", "in": 20.72, "out": 26.35, "flips": [24.0]}],
  "tighten": 0.45,                           # optionnel : coupe les silences internes > 0,45 s
  "punch": {"scale": 1.28, "origin": "47% 21%", "first_tight": true},
  "grade": {"preset": "skin-soft", "intensity": 0.58},   # optionnel, sur la face cam
  "captions": [["texte", src_in, src_out]],  # optionnel : sinon générés depuis "words"
  "corrections": {"Castelnaud": "Castelnau"},# corrections de transcription
  "broll": [{"src": "...", "seg": "hook", "at": 22.86, "dur": 2.0, "offset": 0.2}],
  "flash": {"seg": "hook", "at": 22.86},     # optionnel, un seul effet par vidéo
  "kicker": {"text": "COACHING PRIVÉ", "dur": 2.6},   # optionnel : surtitre fin en ouverture
  "proof": {"seg": "diete", "at": 55.95, "bg": "...", "images": [["...jpg", 2.0]]},
  "music": {"src": "assets/musique.wav", "len": 43.67, "end_boost": 3.5,
            "start": {"seg": "hook", "at": 22.86}, "beats": "beats/...json"},
  "end_card": {"logo": "assets/brand/logo_or_blanc.png", "dur": 2.0}
}
"""

import html
import json
import os
import re
import sys

W, H, FPS = 1080, 1920, 30

# --- Constantes de la charte (STYLE.md) --------------------------------------
PUSH_TH = 1.06          # § 7 bis : poussée lente sur la face cam
PUSH_BROLL = 1.08       # § 7 bis : poussée lente sur les plans de coupe
BEAT_MIN_STRENGTH = 0.4
BEAT_MIN_GAP = 2.5
BEAT_PUNCH = 1.045
CAP_MAX_CHARS = 24      # § 5 : 1 ligne, ≤ 24 caractères
CAP_MAX_WORDS = 5
GOLD = "#D9C48E"        # § 5 : chiffres mis en avant
MUSIC_FX = {"version": 1, "nodes": [
    {"type": "peaking", "id": "n1", "params": {"frequency": 250, "gain": -6.8, "q": 1.46}},
    {"type": "peaking", "id": "n2", "params": {"frequency": 630, "gain": -3.4, "q": 1.46}},
    {"type": "peaking", "id": "n3", "params": {"frequency": 1600, "gain": -4.29, "q": 1.46}}]}

UNITS = {"an", "ans", "mois", "semaine", "semaines", "jour", "jours", "kg", "kilos", "kilo", "%",
         "séance", "séances", "fois", "h", "heure", "heures", "minute", "minutes", "cm", "coachs",
         "coach", "salles", "salle", "personnes", "clients", "adhérents", "euros", "€"}
NUM_RE = re.compile(r"^\d+([.,]\d+)?(%|kg|h)?[,.]?$")


# --- Transcription → mots --------------------------------------------------------
def load_words(path, corrections):
    """Aplatit un transcript faster-whisper ([{words: [[s, e, mot], …]}]) en [(s, e, mot)]."""
    data = json.load(open(path))
    words = []
    for seg in data:
        for s, e, w in seg["words"]:
            w = w.strip()
            for bad, good in corrections.items():
                w = w.replace(bad, good)
            if w:
                words.append((float(s), float(e), w))
    # Whisper colle parfois « j » et « 'ai » : on recolle les élisions.
    merged = []
    for s, e, w in words:
        if merged and (w.startswith("'") or w.startswith("’") or w.startswith("-")):
            ps, pe, pw = merged[-1]
            merged[-1] = (ps, e, pw + w.replace("'", "’"))
        else:
            merged.append((s, e, w.replace("'", "’")))
    return merged


def tighten_segments(segments, words, max_gap):
    """Découpe chaque segment aux silences internes > max_gap (coupe franche, voix continue)."""
    out = []
    for seg in segments:
        ws = [w for w in words if w[0] >= seg["in"] - 0.05 and w[1] <= seg["out"] + 0.05]
        if not ws:
            out.append(seg)
            continue
        start, k = seg["in"], 0
        for (s0, e0, _), (s1, e1, _) in zip(ws, ws[1:]):
            if s1 - e0 > max_gap:
                out.append({**seg, "id": f'{seg["id"]}-{k}', "in": start, "out": round(e0 + 0.12, 3),
                            "flips": [f for f in seg.get("flips", []) if start <= f <= e0]})
                start, k = round(s1 - 0.08, 3), k + 1
        out.append({**seg, "id": f'{seg["id"]}-{k}' if k else seg["id"], "in": start, "out": seg["out"],
                    "flips": [f for f in seg.get("flips", []) if f >= start]})
    return out


def is_number(w):
    return bool(NUM_RE.match(w.strip("«»\"")))


# Mots après lesquels on ne coupe jamais un sous-titre (articles, prépositions, pronoms
# sujets, conjonctions) : « de me / reprendre » devient « de me reprendre ».
WEAK = {"le", "la", "les", "l’", "un", "une", "des", "du", "de", "d’", "à", "au", "aux", "en", "et",
        "ou", "mais", "que", "qu’", "qui", "pour", "par", "avec", "sans", "sur", "dans", "chez", "je",
        "j’", "tu", "il", "elle", "on", "nous", "vous", "ils", "elles", "me", "m’", "te", "se", "s’",
        "ce", "c’", "ça", "mon", "ma", "mes", "ton", "ta", "tes", "son", "sa", "ses", "notre", "votre",
        "leur", "leurs", "ne", "n’", "pas", "très", "plus", "trop", "si", "comme", "est", "suis", "a",
        "ai", "était", "puis", "donc", "alors", "parce", "quand", "lorsque", "y", "cette", "cet", "ces",
        "pourquoi", "peu", "tout", "tous", "toute", "toutes", "bien", "super"}
NUM_WORDS = {"deux": "2", "trois": "3", "quatre": "4", "cinq": "5", "six": "6", "sept": "7", "huit": "8",
             "neuf": "9", "dix": "10", "onze": "11", "douze": "12", "quinze": "15", "vingt": "20",
             "trente": "30", "quarante": "40", "cinquante": "50", "cent": "100"}
NUM_FOLLOW = UNITS | {"premiers", "premières", "derniers", "dernières"}


def _bare(w):
    w = w.strip(",.?!;:«»\"").lower()
    return w.split("’")[-1] if "’" in w[:-1] else w      # « d’une » → « une », « j’ai » → « ai »


def _chunk_cost(toks, last_word, next_word):
    text = " ".join(toks)
    n = len(text)
    if n > CAP_MAX_CHARS or len(toks) > CAP_MAX_WORDS:
        return None
    cost = abs(n - 18) * 0.15                       # longueur idéale ≈ 18 caractères
    if len(toks) == 1:
        cost += 3.0                                 # pas de mot isolé
    if last_word[-1:] in ",.?!;:":
        cost -= 2.5                                 # coupure sur la ponctuation
    elif _bare(last_word) in WEAK or last_word.endswith("’"):
        cost += 6.0                                 # jamais après un mot-outil
    if next_word and _bare(next_word) in UNITS and is_number(_bare(last_word)):
        cost += 50.0                                # jamais un chiffre séparé de son unité
    return cost


def auto_captions(words, segments):
    """Sous-titres § 5 : 1 ligne, 1 à 5 mots, ≤ 24 caractères, découpage optimal par phrase
    (ponctuation, jamais après un mot-outil, jamais un chiffre sans son unité) ;
    chiffres en nombres, chiffres + unité en gras or."""
    out = []
    for seg in segments:
        ws = [list(w) for w in words if w[0] >= seg["in"] - 0.05 and w[0] < seg["out"] - 0.05]
        # Nombres en lettres → chiffres quand ils précèdent une unité (« trois premiers mois »).
        for i, w in enumerate(ws):
            b = _bare(w[2])
            if b in NUM_WORDS and i + 1 < len(ws) and _bare(ws[i + 1][2]) in NUM_FOLLOW:
                w[2] = NUM_WORDS[b] + w[2][len(b):]
        n = len(ws)
        best = [0.0] + [None] * n
        prev = [0] * (n + 1)
        for j in range(1, n + 1):
            for i in range(max(0, j - CAP_MAX_WORDS), j):
                if best[i] is None:
                    continue
                c = _chunk_cost([w[2] for w in ws[i:j]], ws[j - 1][2], ws[j][2] if j < n else None)
                if c is not None and (best[j] is None or best[i] + c < best[j]):
                    best[j], prev[j] = best[i] + c, i
        cuts, j = [], n
        while j > 0:
            cuts.append((prev[j], j))
            j = prev[j]
        cuts.reverse()
        sentence_start = True
        for i, j in cuts:
            toks, k = [], i
            while k < j:
                t = ws[k][2]
                if is_number(t) and k + 1 < j and (_bare(ws[k + 1][2]) in NUM_FOLLOW):
                    span = 2 + (k + 2 < j and _bare(ws[k + 1][2]) not in UNITS and _bare(ws[k + 2][2]) in UNITS)
                    grp = [ws[k + m][2] for m in range(span)]
                    trail = grp[-1][-1] if grp[-1][-1] in ",.?!" else ""
                    toks.append("**" + " ".join(grp).rstrip(",.?!") + "**" + trail)
                    k += span
                    continue
                if is_number(t):
                    trail = t[-1] if t[-1] in ",.?!" else ""
                    toks.append(f"**{t.rstrip(',.?!')}**{trail}")
                else:
                    toks.append(t)
                k += 1
            text = " ".join(toks)
            if sentence_start and text[:1].islower():
                text = text[0].upper() + text[1:]
            sentence_start = text.rstrip("*")[-1:] in ".?!"
            out.append([text, ws[i][0], min(ws[j - 1][1], seg["out"])])
    return out


# --- Construction ----------------------------------------------------------------
def build(project):
    edl = json.load(open(os.path.join(project, "edl.json")))
    corrections = edl.get("corrections", {})
    words = load_words(os.path.join(project, edl["words"]), corrections) if edl.get("words") else []
    segments = edl["segments"]
    if edl.get("tighten") and words:
        segments = tighten_segments(segments, words, edl["tighten"])

    seg_start, t = {}, 0.0
    for s in segments:
        seg_start[s["id"]] = (t, s["in"], s["out"])
        t = round(t + round(s["out"] - s["in"], 3), 3)
    speech_end = t

    def seg_of(src):
        for s in segments:
            if s["in"] - 0.05 <= src <= s["out"] + 0.05:
                return s["id"]
        raise ValueError(f"instant {src} hors de tout segment")

    def to_tl(sid, src):
        if sid not in seg_start:            # segment découpé par tighten : retrouver le bon morceau
            sid = seg_of(src)
        t0, a, b = seg_start[sid]
        if not (a - 0.06 <= src <= b + 0.06):
            sid = seg_of(src)
            t0, a, b = seg_start[sid]
        return round(t0 + (min(max(src, a), b) - a), 3)

    punch = {"scale": 1.28, "origin": "50% 28%", "first_tight": True, **edl.get("punch", {})}
    proof = edl.get("proof")
    proof_t = to_tl(proof["seg"], proof["at"]) if proof else None
    proof_end = round(proof_t + sum(d for _, d in proof["images"]), 3) if proof else 0
    end_card = {"logo": "assets/brand/logo_or_blanc.png", "dur": 2.0, **edl.get("end_card", {})}
    end_start = max(proof_end, speech_end)
    total = round(end_start + end_card["dur"], 3)

    parts, tweens = [], []
    th_windows, cover = [], []
    z = 1
    grade = edl.get("grade")
    grade_attr = f" data-color-grading='{json.dumps(grade)}'" if grade else ""

    # Face cam : un <video> par segment, cadre large/serré alterné + poussée lente.
    tight = punch["first_tight"]
    for s in segments:
        sid, a, b = s["id"], s["in"], s["out"]
        t0 = seg_start[sid][0]
        d = round(b - a - 0.002, 3)
        fade = {"version": 1, "lanes": [{"target": "volume", "points": [
            {"t": 0, "v": 0}, {"t": 0.03, "v": 1}, {"t": round(d - 0.04, 3), "v": 1}, {"t": d, "v": 0}]}]}
        parts.append(
            f'<div class="frame" id="thf-{sid}" style="z-index:{z}"><div class="punch" id="thp-{sid}">'
            f'<video id="th-{sid}" src="{edl["source"]}" data-start="{round(t0,3)}" data-duration="{d}" '
            f'data-media-start="{a}" data-track-index="0" playsinline data-has-audio="true"{grade_attr} '
            f"data-automation='{json.dumps(fade)}'></video></div></div>")
        bounds = [round(t0, 3)] + [to_tl(sid, f) for f in s.get("flips", [])] + [round(t0 + d, 3)]
        for r0, r1 in zip(bounds, bounds[1:]):
            s0 = punch["scale"] if tight else 1
            tweens.append(f'tl.fromTo("#thf-{sid}", {{scale: {s0}}}, {{scale: {round(s0 * PUSH_TH, 4)}, '
                          f'duration: {round(r1 - r0, 3)}, ease: "none", immediateRender: false}}, {r0});')
            th_windows.append((r0, r1, sid))
            tight = not tight
    z += 1

    # Plans de coupe (muets, par-dessus la face cam).
    for k, br in enumerate(edl.get("broll", [])):
        st = to_tl(br["seg"], br["at"])
        d = br["dur"]
        g = f" data-color-grading='{json.dumps(br['grade'])}'" if br.get("grade") else ""
        parts.append(
            f'<div class="frame-b" id="brf-{k}" style="z-index:{z}">'
            f'<video id="br-{k}" class="full" src="{br["src"]}" data-start="{st}" data-duration="{d}" '
            f'data-media-start="{br.get("offset", 0)}" data-track-index="1" muted playsinline{g}></video></div>')
        tweens.append(f'tl.fromTo("#brf-{k}", {{scale: 1}}, {{scale: {PUSH_BROLL}, duration: {d}, '
                      f'ease: "none", immediateRender: false}}, {st});')
        cover.append((st, round(st + d, 3)))
    z += 1

    # Flash (un seul effet par vidéo).
    ft = None
    if edl.get("flash"):
        ft = to_tl(edl["flash"]["seg"], edl["flash"]["at"])
        parts.append(f'<div id="flash" class="clip" data-start="{round(max(ft-0.02, 0),3)}" data-duration="0.4" '
                     f'data-track-index="2" style="z-index:{z+3}"><div class="flash-inner"></div></div>')
        tweens.append(f'tl.fromTo("#flash .flash-inner", {{opacity: 0.85}}, {{opacity: 0, duration: 0.32, ease: "power2.out"}}, {round(ft,3)});')

    # Surtitre d'ouverture : ligne fine or + texte espacé, sans fond (§ 0).
    if edl.get("kicker"):
        kd = edl["kicker"].get("dur", 2.6)
        parts.append(f'<div id="kicker" class="clip" data-start="0.15" data-duration="{kd}" data-track-index="8" '
                     f'style="z-index:{z+2}"><div class="kicker-inner"><span class="kicker-rule"></span>'
                     f'<span class="kicker-text">{html.escape(edl["kicker"]["text"])}</span></div></div>')
        tweens += [
            f'tl.fromTo("#kicker .kicker-rule", {{scaleX: 0}}, {{scaleX: 1, duration: 0.5, ease: "power2.out"}}, 0.15);',
            f'tl.fromTo("#kicker .kicker-text", {{opacity: 0, y: 8}}, {{opacity: 1, y: 0, duration: 0.5, ease: "power2.out"}}, 0.35);',
            f'tl.to("#kicker .kicker-inner", {{opacity: 0, duration: 0.4, ease: "power1.in"}}, {round(0.15 + kd - 0.45, 3)});',
        ]

    # Preuve : moitié « avant », puis balayage vers « après » (§ 6, § 7 bis).
    if proof:
        if proof.get("bg"):
            parts.append(
                f'<video id="proof-bg" class="clip full" src="{proof["bg"]}" data-start="{round(proof_t,3)}" '
                f'data-duration="{round(proof_end - proof_t,3)}" data-media-start="0" data-track-index="1" '
                f'muted playsinline style="z-index:{z}"></video>')
        cover.append((proof_t, proof_end))
        pt = proof_t
        for k, (img, d) in enumerate(proof["images"]):
            p = round(pt, 3)
            parts.append(
                f'<div id="proof-{k}" class="clip proof" data-start="{p}" data-duration="{d}" '
                f'data-track-index="3" style="z-index:{z+1}"><div class="proof-card">'
                f'<img class="proof-img" src="{img}" alt="Avant et après" />'
                f'<div class="proof-divider"></div>'
                f'<span class="tag tag-avant">AVANT</span><span class="tag tag-apres">APRÈS</span></div></div>')
            q = f"#proof-{k}"
            if k == 0:
                tweens += [
                    f'tl.fromTo("{q} .proof-card", {{scale: 0.94, opacity: 0}}, {{scale: 1, opacity: 1, duration: 0.3, ease: "power3.out"}}, {p});',
                    f'tl.fromTo("{q} .proof-img", {{clipPath: "inset(0% 50% 0% 0%)"}}, {{clipPath: "inset(0% 0% 0% 0%)", duration: 0.6, ease: "power2.inOut"}}, {round(p + 0.65, 3)});',
                    f'tl.fromTo("{q} .proof-divider", {{opacity: 0, x: 0}}, {{opacity: 1, x: 0, duration: 0.15}}, {round(p + 0.5, 3)});',
                    f'tl.to("{q} .proof-divider", {{x: 372, duration: 0.6, ease: "power2.inOut"}}, {round(p + 0.65, 3)});',
                    f'tl.set("{q} .proof-divider", {{x: 0}}, {round(p + 1.27, 3)});',
                    f'tl.fromTo("{q} .tag-avant", {{y: -16, opacity: 0}}, {{y: 0, opacity: 1, duration: 0.3, ease: "power3.out"}}, {round(p + 0.2, 3)});',
                    f'tl.fromTo("{q} .tag-apres", {{scale: 0.6, opacity: 0}}, {{scale: 1, opacity: 1, duration: 0.35, ease: "back.out(2)"}}, {round(p + 1.2, 3)});',
                ]
            pt += d

    # Musique + coups de zoom sur les temps forts.
    music = edl.get("music")
    if music:
        st = music.get("start")
        m0 = to_tl(st["seg"], st["at"]) if st else 0.0
        mdur = round(min(music["len"], total - m0), 3)
        sp_end, card = round(speech_end - m0, 3), round(end_start - m0, 3)
        boost = music.get("end_boost", 3.5)
        lane = {"version": 1, "lanes": [{"target": "volume", "points": [
            {"t": 0, "v": 0}, {"t": 0.4, "v": 1}, {"t": sp_end, "v": 1},
            {"t": card, "v": boost}, {"t": round(mdur - 0.6, 3), "v": boost}, {"t": mdur, "v": 0}]}]}
        parts.append(f'<audio id="music" src="{music["src"]}" data-start="{m0}" data-duration="{mdur}" '
                     f'data-media-start="{music.get("offset", 0)}" data-track-index="6" data-volume="1" '
                     f"data-fx-chain='{json.dumps(MUSIC_FX)}' data-automation='{json.dumps(lane)}'></audio>")
        if music.get("beats") and os.path.exists(os.path.join(project, music["beats"])):
            beats = sorted((round(m0 + b["time"] - music.get("offset", 0), 3), b["strength"])
                           for b in json.load(open(os.path.join(project, music["beats"])))["beats"]
                           if b["strength"] >= BEAT_MIN_STRENGTH)
            last = -99.0
            for bt, _ in beats:
                win = next((w for w in th_windows if w[0] + 0.3 <= bt <= w[1] - 0.45), None)
                hidden = any(c0 - 0.1 <= bt <= c1 + 0.1 for c0, c1 in cover)
                if win and not hidden and bt - last >= BEAT_MIN_GAP:
                    tweens.append(f'tl.fromTo("#thp-{win[2]}", {{scale: {BEAT_PUNCH}}}, {{scale: 1, duration: 0.35, '
                                  f'ease: "power3.out", immediateRender: false}}, {bt});')
                    last = bt

    # Sous-titres.
    raw = edl.get("captions") or auto_captions(words, segments)
    caps = []
    for text, a, b in raw:
        sid = seg_of(a)
        caps.append([to_tl(sid, a), to_tl(sid, min(b, seg_start[sid][2])), sid, text])
    for i, c in enumerate(caps):
        end = c[1] + 0.12
        if i + 1 < len(caps) and caps[i + 1][2] == c[2]:
            end = min(end, caps[i + 1][0])
        seg_end = seg_start[c[2]][0] + (seg_start[c[2]][2] - seg_start[c[2]][1])
        c[1] = round(min(end, seg_end), 3)
    cap_html = []
    for i, (a, b, _, text) in enumerate(caps):
        if b - a < 0.05:
            continue
        esc = html.escape(text).replace("&#x27;", "’").replace("'", "’")
        while "**" in esc:
            esc = esc.replace("**", "<b>", 1).replace("**", "</b>", 1)
        cap_html.append(f'<div id="cap-{i}" class="clip cap" data-start="{a}" data-duration="{round(b-a,3)}" '
                        f'data-track-index="4"><span class="cap-box">{esc}</span></div>')
    parts.append(f'<div id="captions" style="z-index:{z+4}">' + "".join(cap_html) + "</div>")

    # Carte de fin.
    parts.append(
        f'<div id="endcard" class="clip" data-start="{round(end_start,3)}" data-duration="{end_card["dur"]}" '
        f'data-track-index="5" style="z-index:{z+5}"><img id="end-logo" src="{end_card["logo"]}" alt="Sparta, centre de coaching privé" /></div>')
    tweens.append(f'tl.fromTo("#end-logo", {{opacity: 0, scale: 0.97}}, {{opacity: 1, scale: 1, duration: 0.4, ease: "power2.out"}}, {round(end_start,3)});')
    tweens.append(f'tl.to("#end-logo", {{opacity: 0, duration: 0.5, ease: "power1.in"}}, {round(total - 0.55,3)});')

    doc = TEMPLATE.format(W=W, H=H, FPS=FPS, total=total, parts="\n      ".join(parts), GOLD=GOLD,
                          tweens="\n      ".join(tweens), origin=punch["origin"], title=html.escape(edl["title"]))
    open(os.path.join(project, "index.html"), "w").write(doc)
    report = {"duration": total, "speech": speech_end, "segments": len(segments), "captions": len(cap_html),
              "broll": len(edl.get("broll", [])), "broll_cover": round(sum(c1 - c0 for c0, c1 in cover) / max(total, 1), 2),
              "end_card_at": end_start}
    print(json.dumps(report, ensure_ascii=False))
    return report


TEMPLATE = """<!doctype html>
<html lang="fr">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      @font-face {{ font-family: "Montserrat"; font-weight: 600; src: url("assets/fonts/montserrat-latin-600-normal.woff2") format("woff2"); }}
      @font-face {{ font-family: "Montserrat"; font-weight: 800; src: url("assets/fonts/montserrat-latin-800-normal.woff2") format("woff2"); }}
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: {W}px; height: {H}px; overflow: hidden; background: #000000; }}
      #root {{ position: relative; width: 100%; height: 100%; overflow: hidden; background: #000000; }}
      .frame {{ position: absolute; inset: 0; transform-origin: {origin}; will-change: transform; }}
      .punch {{ position: absolute; inset: 0; transform-origin: {origin}; will-change: transform; }}
      .frame-b {{ position: absolute; inset: 0; transform-origin: 50% 50%; will-change: transform; overflow: hidden; }}
      .frame video, video.full {{ position: absolute; left: 0; top: 0; width: {W}px; height: {H}px; object-fit: cover; }}
      #flash {{ position: absolute; inset: 0; }}
      .flash-inner {{ position: absolute; inset: 0; background: #FFFFFF; opacity: 0; }}
      /* Surtitre d'ouverture — § 0 : ligne fine or, texte espacé, sans fond */
      #kicker {{ position: absolute; left: 0; width: {W}px; top: 250px; height: 120px; display: flex; justify-content: center; }}
      .kicker-inner {{ display: flex; flex-direction: column; align-items: center; gap: 18px; }}
      .kicker-rule {{ display: block; width: 72px; height: 3px; background: {GOLD}; transform-origin: 50% 50%; }}
      .kicker-text {{ display: block; font-family: "Montserrat", sans-serif; font-weight: 600; font-size: 30px; letter-spacing: 0.32em;
                     color: #FFFFFF; text-shadow: 0 2px 14px rgba(0,0,0,0.55); }}
      /* Preuve — § 6 */
      .proof {{ position: absolute; inset: 0; background: rgba(0,0,0,0.4); display: flex; justify-content: center; align-items: flex-start; padding-top: 420px; }}
      .proof-card {{ position: relative; overflow: hidden; width: 760px; height: 760px; border: 8px solid #FFFFFF; box-shadow: 0 0 24px rgba(0,0,0,0.4); background: #000000; }}
      .proof-card img {{ display: block; width: 100%; height: 100%; object-fit: cover; }}
      .proof-divider {{ position: absolute; top: 0; bottom: 0; left: 50%; width: 10px; margin-left: -5px; background: #E3CF8F; box-shadow: 0 0 0 2px rgba(0,0,0,0.55), 0 0 24px rgba(227,207,143,0.9); }}
      .tag {{ position: absolute; top: 18px; font-family: "Montserrat", sans-serif; font-weight: 800; font-size: 30px; letter-spacing: 0.14em;
             padding: 8px 16px; border-radius: 4px; line-height: 1; }}
      .tag-avant {{ left: 18px; color: #FFFFFF; background: rgba(0,0,0,0.65); }}
      .tag-apres {{ right: 18px; color: #000000; background: #C3B486; transform-origin: 100% 0%; }}
      /* Sous-titres — § 5 */
      #captions {{ position: absolute; inset: 0; pointer-events: none; }}
      .cap {{ position: absolute; left: 0; width: {W}px; top: 1340px; height: 100px; display: flex; align-items: center; justify-content: center; }}
      .cap-box {{ display: inline-block; font-family: "Montserrat", sans-serif; font-weight: 600; font-size: 46px; line-height: 1; color: #FFFFFF;
                 background: rgba(0,0,0,0.5); padding: 10px 14px; border-radius: 6px; white-space: nowrap; }}
      .cap-box b {{ font-weight: 800; color: {GOLD}; }}
      /* Carte de fin — § 7 */
      #endcard {{ position: absolute; inset: 0; background: #000000; display: flex; align-items: center; justify-content: center; }}
      #end-logo {{ display: block; width: 520px; height: auto; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-width="{W}" data-height="{H}" data-fps="{FPS}" data-duration="{total}">
      {parts}
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      {tweens}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""

if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else ".")
