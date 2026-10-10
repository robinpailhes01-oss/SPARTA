"""Génère index.html (composition HyperFrames) à partir de la liste de montage ci-dessous.

Usage : python3 montage.py   (depuis le dossier du projet)

Toutes les valeurs de style viennent de ../../STYLE.md (charte v0.1).
Les temps « src » sont ceux du témoignage brut (assets/temoignage.mp4).
"""

import html
import json

W, H, FPS = 1080, 1920, 30

# --- 1. Segments du témoignage, dans l'ordre du montage -----------------------
# (id, src_in, src_out, [instants src où le cadrage alterne large/serré])
SEGMENTS = [
    ("hook",      20.72, 26.35, []),            # « J'avais envie de me reprendre en main… »
    ("intro",      2.08,  5.15, []),            # « Moi c'est Nicolas, 43 ans, Castelnau »
    ("debut",      5.92,  9.40, []),            # « J'ai commencé le coaching en fin avril »
    ("duree",     12.02, 14.80, []),            # « 7, 8 mois, 9 mois, je ne compte plus »
    ("pourquoi",  27.05, 34.40, [29.88]),       # « plutôt que de rester sans rien faire… »
    ("sparta",    35.25, 38.45, []),            # « j'ai trouvé coach Sparta… »
    ("coachs",    39.92, 43.08, []),            # « Marco, Akli et tous les coachs »
    ("feeling",   43.48, 45.95, []),            # « le feeling est bien passé »
    ("diete",     46.55, 58.02, [49.40]),       # « tenir 3 mois… la diète… prise de masse »
]

# Cadrage : large = 100 %, serré = 128 % centré sur le visage (STYLE § 3).
PUNCH_SCALE = 1.28
PUNCH_ORIGIN = "47% 21%"
FIRST_TIGHT = True  # l'accroche démarre en plan serré

# --- 2. Sous-titres : (texte, src_début, src_fin). **x** = ExtraBold (chiffres)
CAPTIONS = [
    ("J'avais envie", 20.80, 21.32),
    ("de me reprendre", 21.32, 22.16),
    ("un peu en main,", 22.16, 22.78),
    ("je sortais d'une période", 22.86, 23.50),
    ("difficile,", 23.50, 24.04),
    ("personnellement,", 24.04, 24.72),
    ("professionnellement.", 24.90, 26.20),
    ("Moi c'est Nicolas,", 2.16, 3.02),
    ("j'ai **43 ans**,", 3.20, 4.20),
    ("je vis à Castelnau.", 4.22, 5.06),
    ("J'ai commencé", 6.00, 6.72),
    ("le coaching", 6.72, 7.80),
    ("en fin avril.", 7.80, 9.32),
    ("Peut-être **7, 8 mois**,", 12.10, 13.02),
    ("**9 mois**, je sais pas,", 13.04, 13.68),
    ("je ne compte plus.", 13.74, 14.70),
    ("Plutôt que de rester", 27.12, 29.10),
    ("sans rien faire", 29.10, 29.88),
    ("l'été arrivant,", 29.88, 30.72),
    ("je me suis dit", 30.94, 31.32),
    ("pourquoi pas essayer", 31.32, 33.12),
    ("de se mettre", 33.12, 33.46),
    ("au sport à fond.", 33.46, 34.28),
    ("Du coup j'ai trouvé", 35.32, 36.22),
    ("coach Sparta,", 36.22, 36.98),
    ("qui était juste à côté", 36.98, 37.94),
    ("de chez moi.", 37.94, 38.36),
    ("J'ai fait", 39.98, 40.32),
    ("la connaissance", 40.32, 40.84),
    ("de Marco, Akli", 40.84, 42.22),
    ("et tous les coachs,", 42.22, 42.96),
    ("ça s'est", 43.54, 43.92),
    ("super bien passé,", 43.92, 44.64),
    ("le feeling", 44.78, 45.12),
    ("est bien passé.", 45.12, 45.84),
    ("J'ai pu me motiver", 46.60, 48.06),
    ("et être motivé", 48.06, 48.90),
    ("comme il fallait", 48.90, 49.44),
    ("pour tenir d'abord", 49.44, 51.24),
    ("les **3 premiers mois**,", 51.24, 52.18),
    ("avec un premier mois", 52.18, 53.80),
    ("super difficile", 53.80, 54.70),
    ("avec la diète,", 54.70, 55.90),
    ("et puis après", 56.04, 56.72),
    ("un peu de", 56.72, 57.32),
    ("prise de masse.", 57.32, 57.98),
]

# --- 3. Plans de coupe, en temps du MONTAGE : (fichier, début, fin, src_offset)
#        (rempli après le calcul des segments, voir BROLL_AT plus bas)
#        ancre = (segment, instant src) : le plan démarre à cet instant du témoignage.
BROLL_AT = [
    # fichier                       segment     src_début  durée  offset
    ("assets/archive_salle.mp4",    "hook",     22.86,     2.06,  0.2),  # « je sortais d'une période difficile »
    ("assets/broll/mesure.mp4",     "debut",    6.60,      2.10,  0.3),  # « j'ai commencé le coaching »
    ("assets/broll/souleve_terre.mp4", "pourquoi", 31.20,  1.60,  0.4),  # « pourquoi pas essayer »
    ("assets/broll/disque.mp4",     "pourquoi", 32.80,     1.60,  0.6),  # « au sport à fond »
    ("assets/broll/enseigne_sparta.mp4", "sparta", 36.10,  2.35,  0.2),  # « coach Sparta »
    ("assets/broll/coachs_accueil.mp4", "coachs", 40.30,   1.75,  0.3),  # « la connaissance de Marco, Akli »
    ("assets/broll/coach_enseigne.mp4", "coachs", 42.05,   1.03,  0.5),  # « et tous les coachs »
    ("assets/archive_rire.mp4",     "feeling",  43.48,     2.47,  0.3),  # « super bien passé » (Nicolas)
    ("assets/broll/developpe_couche.mp4", "diete", 49.30,  1.90,  0.4),  # « pour tenir d'abord »
    ("assets/broll/rowing_coach.mp4", "diete",  51.20,     1.70,  0.5),  # « les 3 premiers mois »
    ("assets/broll/shaker.mp4",     "diete",    54.60,     1.60,  0.9),  # « avec la diète »
]

# Preuve (STYLE § 6) : avant/après de face puis de profil, ancré sur « et puis après ».
PROOF_ANCHOR = ("diete", 55.95)
PROOF = [("assets/photos/8e2b3bca.jpg", 2.0), ("assets/photos/934393f3.jpg", 1.9)]
PROOF_BG = "assets/broll/disque_10kg.mp4"    # sous la carte, assombri (la voix continue)

END_CARD = 2.0  # 1,5 s de logo + 0,5 s de fondu au noir (STYLE § 7)
FLASH_ANCHOR = ("hook", 22.86)  # le seul effet autorisé : flash vers l'archive

# Musique (STYLE § 9) : extraite du reel Sparta df1 (voix retirée avec Demucs),
# préparée à -30 LUFS (≈ -18 dB sous la voix à -13 LUFS). Elle entre sur le flash, reste sous la voix et remonte
# sur la carte de fin. MUSIC_END_BOOST = gain sur la carte de fin (max 3.98 = +12 dB).
MUSIC = "assets/musique.wav"
MUSIC_LEN = 43.67
MUSIC_END_BOOST = 3.5
# Creux d'égalisation fixes calculés par le carve HyperFrames (force 0.3) : la musique
# laisse de la place à la voix sur 250 Hz, 630 Hz et 1,6 kHz.
MUSIC_FX = {"version": 1, "nodes": [
    {"type": "peaking", "id": "n1", "params": {"frequency": 250, "gain": -6.8, "q": 1.46}},
    {"type": "peaking", "id": "n2", "params": {"frequency": 630, "gain": -3.4, "q": 1.46}},
    {"type": "peaking", "id": "n3", "params": {"frequency": 1600, "gain": -4.29, "q": 1.46}}]}

# --- Motion design (v3) -------------------------------------------------------
# Caméra vivante (règle multi-phase-camera) : poussée lente continue sur chaque plan.
PUSH_TH = 1.06        # face caméra : +6 % sur la durée du plan
PUSH_BROLL = 1.08     # plans de coupe : +8 %
# Coups de zoom sur les temps forts de la musique (beats/assets/musique.wav.json),
# seulement quand Nicolas est à l'image.
BEATS = "beats/assets/musique.wav.json"
BEAT_MIN_STRENGTH = 0.4
BEAT_MIN_GAP = 2.5    # s entre deux coups
BEAT_PUNCH = 1.045    # amplitude du coup (retour à 1 en 0,35 s)

# Chiffres animés (règle counting-dynamic-scale) : (valeur, unité, libellé, segment, src)
STATS = [
    (43, "ANS", "NICOLAS · CASTELNAU", "intro", 3.20),
    (9, "MOIS", "DE COACHING", "duree", 13.04),
    (3, "MOIS", "PREMIERS MOIS · DIÈTE", "diete", 51.30),
]
STAT_DUR = 2.3

# ---------------------------------------------------------------------------
def build():
    seg_start, t = {}, 0.0
    for sid, a, b, _ in SEGMENTS:
        seg_start[sid] = (t, a, b)
        t = round(t + round(b - a, 3), 3)  # cumul arrondi : aucun chevauchement audio
    speech_end = t

    def to_tl(sid, src):
        t0, a, b = seg_start[sid]
        assert a - 1e-6 <= src <= b + 1e-6, (sid, src)
        return round(t0 + (src - a), 3)

    def seg_of(src):
        for sid, a, b, _ in SEGMENTS:
            if a - 0.05 <= src <= b + 0.05:
                return sid
        raise ValueError(src)

    proof_t = to_tl(*PROOF_ANCHOR)
    proof_end = round(proof_t + sum(d for _, d in PROOF), 3)
    end_start = max(proof_end, speech_end)
    total = round(end_start + END_CARD, 3)

    parts, tweens = [], []
    th_windows, cover = [], []  # fenêtres où Nicolas est à l'image / où il est masqué
    z = 1

    # Témoignage : un <video> par segment, dans un cadre non minuté pour les punch-in.
    tight = FIRST_TIGHT
    for i, (sid, a, b, flips) in enumerate(SEGMENTS):
        t0 = seg_start[sid][0]
        d = round(b - a - 0.002, 3)  # 2 ms de marge : jamais deux voix superposées
        fade = {"version": 1, "lanes": [{"target": "volume", "points": [
            {"t": 0, "v": 0}, {"t": 0.03, "v": 1}, {"t": round(d - 0.04, 3), "v": 1}, {"t": d, "v": 0}]}]}
        parts.append(
            f'<div class="frame" id="thf-{sid}" style="z-index:{z}"><div class="punch" id="thp-{sid}">'
            f'<video id="th-{sid}" src="assets/temoignage.mp4" data-start="{round(t0,3)}" data-duration="{d}" '
            f'data-media-start="{a}" data-track-index="0" playsinline data-has-audio="true" '
            f"data-automation='{json.dumps(fade)}'></video></div></div>")
        # Cadrage large/serré alterné à chaque coupe, avec une poussée lente continue.
        bounds = [round(t0, 3)] + [to_tl(sid, f) for f in flips] + [round(t0 + d, 3)]
        for r0, r1 in zip(bounds, bounds[1:]):
            s0 = PUNCH_SCALE if tight else 1
            tweens.append(f'tl.fromTo("#thf-{sid}", {{scale: {s0}}}, {{scale: {round(s0 * PUSH_TH, 4)}, '
                          f'duration: {round(r1 - r0, 3)}, ease: "none", immediateRender: false}}, {r0});')
            th_windows.append((r0, r1, sid))
            tight = not tight  # chaque coupe (ou changement de cadrage) alterne large/serré
    z += 1

    # Plans de coupe (muets, par-dessus le témoignage).
    for k, (src, sid, s, d, off) in enumerate(BROLL_AT):
        st = to_tl(sid, s)
        parts.append(
            f'<div class="frame-b" id="brf-{k}" style="z-index:{z}">'
            f'<video id="br-{k}" class="full" src="{src}" data-start="{st}" data-duration="{d}" '
            f'data-media-start="{off}" data-track-index="1" muted playsinline></video></div>')
        tweens.append(f'tl.fromTo("#brf-{k}", {{scale: 1}}, {{scale: {PUSH_BROLL}, duration: {d}, '
                      f'ease: "none", immediateRender: false}}, {st});')
        cover.append((st, round(st + d, 3)))
    z += 1

    # Flash (0,3 s) au passage vers l'archive.
    ft = to_tl(*FLASH_ANCHOR)
    parts.append(f'<div id="flash" class="clip" data-start="{round(ft-0.02,3)}" data-duration="0.4" '
                 f'data-track-index="2" style="z-index:{z+3}"><div class="flash-inner"></div></div>')
    tweens.append(f'tl.fromTo("#flash .flash-inner", {{opacity: 0.85}}, {{opacity: 0, duration: 0.32, ease: "power2.out"}}, {round(ft,3)});')

    # Fond sous la carte de preuve, une fois la parole finie.
    if True:
        parts.append(
            f'<video id="proof-bg" class="clip full" src="{PROOF_BG}" data-start="{round(proof_t,3)}" '
            f'data-duration="{round(proof_end - proof_t,3)}" data-media-start="0" data-track-index="1" '
            f'muted playsinline style="z-index:{z}"></video>')

    # Carte de preuve : la moitié « avant » d'abord, puis un balayage révèle « après ».
    cover.append((proof_t, proof_end))
    pt = proof_t
    for k, (img, d) in enumerate(PROOF):
        p = round(pt, 3)
        parts.append(
            f'<div id="proof-{k}" class="clip proof" data-start="{p}" data-duration="{d}" '
            f'data-track-index="3" style="z-index:{z+1}"><div class="proof-card">'
            f'<img class="proof-img" src="{img}" alt="Nicolas avant et après" />'
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

    # Chiffres animés : plaque sombre, chiffre or qui compte en grandissant, unité puis libellé.
    for k, (val, unit, label, sid, src) in enumerate(STATS):
        st = to_tl(sid, src)
        q = f"#stat-{k}"
        parts.append(
            f'<div id="stat-{k}" class="clip stat" data-start="{st}" data-duration="{STAT_DUR}" '
            f'data-track-index="7" style="z-index:{z+2}"><div class="stat-plate">'
            f'<div class="stat-row"><span class="stat-num" id="stat-num-{k}">{val}</span>'
            f'<span class="stat-unit">{unit}</span></div><div class="stat-label">{html.escape(label)}</div></div></div>')
        cd = 0.7 if val > 9 else 0.45
        tweens += [
            f'tl.fromTo("{q} .stat-plate", {{scaleX: 0.2, opacity: 0}}, {{scaleX: 1, opacity: 1, duration: 0.28, ease: "power3.out"}}, {st});',
            f'(() => {{ const el = document.getElementById("stat-num-{k}"); const c{k} = {{ v: 0 }}; '
            f'tl.fromTo(c{k}, {{ v: 0 }}, {{ v: {val}, duration: {cd}, ease: "power2.out", '
            f'{"immediateRender: false, " if k else ""}onUpdate: () => {{ el.textContent = String(Math.round(c{k}.v)); }} }}, {round(st + 0.1, 3)}); }})();',
            f'tl.fromTo("#stat-num-{k}", {{scale: 0.55}}, {{scale: 1, duration: {cd}, ease: "power2.out"}}, {round(st + 0.1, 3)});',
            f'tl.fromTo("{q} .stat-unit", {{x: -24, opacity: 0}}, {{x: 0, opacity: 1, duration: 0.3, ease: "back.out(1.7)"}}, {round(st + 0.1 + cd, 3)});',
            f'tl.fromTo("{q} .stat-label", {{y: 10, opacity: 0}}, {{y: 0, opacity: 1, duration: 0.3, ease: "power2.out"}}, {round(st + 0.25, 3)});',
            f'tl.to("{q} .stat-plate", {{opacity: 0, y: -12, duration: 0.25, ease: "power2.in"}}, {round(st + STAT_DUR - 0.3, 3)});',
        ]

    # Coups de zoom sur les temps forts de la musique, quand Nicolas est à l'image.
    m0 = round(to_tl(*FLASH_ANCHOR), 3)
    beats = sorted((round(m0 + b["time"], 3), b["strength"]) for b in json.load(open(BEATS))["beats"]
                   if b["strength"] >= BEAT_MIN_STRENGTH)
    punches, last = [], -99.0
    for bt, _ in beats:
        win = next((w for w in th_windows if w[0] + 0.3 <= bt <= w[1] - 0.45), None)
        hidden = any(c0 - 0.1 <= bt <= c1 + 0.1 for c0, c1 in cover)
        if win and not hidden and bt - last >= BEAT_MIN_GAP:
            punches.append((bt, win[2]))
            last = bt
    for bt, sid in punches:
        tweens.append(f'tl.fromTo("#thp-{sid}", {{scale: {BEAT_PUNCH}}}, {{scale: 1, duration: 0.35, '
                      f'ease: "power3.out", immediateRender: false}}, {bt});')

    # Sous-titres.
    caps = []
    for text, a, b in CAPTIONS:
        sid = seg_of(a)
        caps.append([to_tl(sid, a), to_tl(sid, min(b, seg_start[sid][2])), sid, text])
    for i, c in enumerate(caps):
        end = c[1] + 0.12
        if i + 1 < len(caps) and caps[i + 1][2] == c[2]:
            end = min(end, caps[i + 1][0]) if caps[i + 1][0] - c[1] < 0.3 else end
            end = min(end, caps[i + 1][0])
        seg_end = seg_start[c[2]][0] + (seg_start[c[2]][2] - seg_start[c[2]][1])
        c[1] = round(min(end, seg_end), 3)
    cap_html = []
    for i, (a, b, _, text) in enumerate(caps):
        esc = html.escape(text).replace("&#x27;", "’").replace("'", "’")
        while "**" in esc:
            esc = esc.replace("**", "<b>", 1).replace("**", "</b>", 1)
        cap_html.append(f'<div id="cap-{i}" class="clip cap" data-start="{a}" data-duration="{round(b-a,3)}" '
                        f'data-track-index="4"><span class="cap-box">{esc}</span></div>')
    parts.append(f'<div id="captions" style="z-index:{z+4}">' + "".join(cap_html) + "</div>")

    # Musique : entre sur le flash, remonte sur la carte de fin.
    m0 = round(ft, 3)
    mdur = round(min(MUSIC_LEN, total - m0), 3)
    sp_end, card = round(speech_end - m0, 3), round(end_start - m0, 3)
    lane = {"version": 1, "lanes": [{"target": "volume", "points": [
        {"t": 0, "v": 0}, {"t": 0.4, "v": 1}, {"t": sp_end, "v": 1},
        {"t": card, "v": MUSIC_END_BOOST}, {"t": round(mdur - 0.6, 3), "v": MUSIC_END_BOOST}, {"t": mdur, "v": 0}]}]}
    parts.append(f'<audio id="music" src="{MUSIC}" data-start="{m0}" data-duration="{mdur}" '
                 f'data-media-start="0" data-track-index="6" data-volume="1" '
                 f"data-fx-chain='{json.dumps(MUSIC_FX)}' data-automation='{json.dumps(lane)}'></audio>")

    # Carte de fin.
    parts.append(
        f'<div id="endcard" class="clip" data-start="{round(end_start,3)}" data-duration="{END_CARD}" '
        f'data-track-index="5" style="z-index:{z+5}"><img id="end-logo" src="assets/brand/logo_or_blanc.png" alt="Sparta, centre de coaching privé" /></div>')
    tweens.append(f'tl.fromTo("#end-logo", {{opacity: 0, scale: 0.97}}, {{opacity: 1, scale: 1, duration: 0.4, ease: "power2.out"}}, {round(end_start,3)});')
    tweens.append(f'tl.to("#end-logo", {{opacity: 0, duration: 0.5, ease: "power1.in"}}, {round(total - 0.55,3)});')

    doc = TEMPLATE.format(W=W, H=H, FPS=FPS, total=total, parts="\n      ".join(parts),
                          tweens="\n      ".join(tweens), origin=PUNCH_ORIGIN)
    open("index.html", "w").write(doc)
    print(f"index.html : {total:.2f} s, parole {speech_end:.2f} s, {len(caps)} sous-titres, "
          f"{len(BROLL_AT)} plans de coupe, preuve à {proof_t:.2f} s, carte de fin à {end_start:.2f} s")


TEMPLATE = """<!doctype html>
<html lang="fr">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <title>Témoignage Nicolas — Sparta</title>
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
      /* Carte de preuve — STYLE § 6 */
      .proof {{ position: absolute; inset: 0; background: rgba(0,0,0,0.4); display: flex; justify-content: center; align-items: flex-start; padding-top: 420px; }}
      .proof-card {{ width: 760px; height: 760px; border: 8px solid #FFFFFF; box-shadow: 0 0 24px rgba(0,0,0,0.4); background: #000000; }}
      .proof-card {{ position: relative; overflow: hidden; }}
      .proof-card img {{ display: block; width: 100%; height: 100%; object-fit: cover; }}
      .proof-divider {{ position: absolute; top: 0; bottom: 0; left: 50%; width: 10px; margin-left: -5px; background: #E3CF8F; box-shadow: 0 0 0 2px rgba(0,0,0,0.55), 0 0 24px rgba(227,207,143,0.9); }}
      .tag {{ position: absolute; top: 18px; font-family: "Montserrat", sans-serif; font-weight: 800; font-size: 30px; letter-spacing: 0.14em;
             padding: 8px 16px; border-radius: 4px; line-height: 1; }}
      .tag-avant {{ left: 18px; color: #FFFFFF; background: rgba(0,0,0,0.65); }}
      .tag-apres {{ right: 18px; color: #000000; background: #C3B486; transform-origin: 100% 0%; }}
      /* Chiffres animés */
      .stat {{ position: absolute; left: 0; width: {W}px; top: 940px; height: 300px; display: flex; align-items: center; justify-content: center; }}
      .stat-plate {{ display: flex; flex-direction: column; align-items: center; padding: 22px 56px 26px; background: rgba(8,8,8,0.8);
                    border-top: 4px solid #C3B486; border-radius: 6px; transform-origin: 50% 50%; }}
      .stat-row {{ display: flex; align-items: baseline; justify-content: center; gap: 18px; width: 460px; }}
      .stat-num {{ display: inline-block; font-family: "Montserrat", sans-serif; font-weight: 800; font-size: 170px; line-height: 0.9;
                  color: #C3B486; font-variant-numeric: tabular-nums; transform-origin: 50% 80%; }}
      .stat-unit {{ display: inline-block; font-family: "Montserrat", sans-serif; font-weight: 800; font-size: 64px; color: #C3B486; letter-spacing: 0.06em; }}
      .stat-label {{ margin-top: 12px; font-family: "Montserrat", sans-serif; font-weight: 600; font-size: 30px; letter-spacing: 0.2em; color: #FFFFFF; }}
      /* Sous-titres — STYLE § 5 */
      #captions {{ position: absolute; inset: 0; pointer-events: none; }}
      .cap {{ position: absolute; left: 0; width: {W}px; top: 1340px; height: 100px; display: flex; align-items: center; justify-content: center; }}
      .cap-box {{ display: inline-block; font-family: "Montserrat", sans-serif; font-weight: 600; font-size: 46px; line-height: 1; color: #FFFFFF;
                 background: rgba(0,0,0,0.5); padding: 10px 14px; border-radius: 6px; white-space: nowrap; }}
      .cap-box b {{ font-weight: 800; }}
      /* Carte de fin — STYLE § 7 */
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
    build()
