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
  "segments": [{"id": "hook", "in": 20.72, "out": 26.35, "flips": [24.0],
                "src": "assets/fc/m00.mp4", "src_offset": 20.42,   # optionnel : fichier propre au morceau
                "cadrage": "serre", "origin": "50% 24%", "tight_scale": 1.5, "wide_scale": 1.1}],
  "tighten": 0.45,                           # optionnel : coupe les silences internes > 0,45 s
  "punch": {"scale": 1.28, "origin": "47% 21%", "first_tight": true},
  "grade": {"preset": "skin-soft", "intensity": 0.58},   # optionnel, sur la face cam
  "captions": [["texte", src_in, src_out]],  # optionnel : sinon générés depuis "words"
  "corrections": {"Castelnaud": "Castelnau"},# corrections de transcription
  "broll": [{"src": "...", "seg": "hook", "at": 22.86, "dur": 2.0, "offset": 0.2}],
  "flash": {"seg": "hook", "at": 22.86},     # optionnel, un seul effet par vidéo
  "kicker": {"text": "COACHING PRIVÉ", "dur": 2.6},   # optionnel : surtitre fin en ouverture
  "schemas": [{"type": "flow", "seg": "m02", "at": 597.2, "dur": 4.4, "titre": "SQUAT",
               "etapes": [["Squat profond", "buste penché"], ["Chaîne postérieure"], ["Ischios + fessiers"]]},
              {"type": "bars", "seg": "m05", "at": 42.6, "dur": 4.6, "titre": "DÉPENSE ÉNERGÉTIQUE",
               "lignes": [["Cardio", "300–500 kcal", 0.22], ["Renforcement", "toute la journée", 1.0]]}],
                                             # optionnel : schémas animés (motion design) par-dessus le formateur
  "hook": {"text": "Tu cours 4 fois par semaine | **sans résultat** ?", "dur": 4.5},   # optionnel : phrase d'accroche en haut
                                             # (« | » = saut de ligne, ** ** = mot en or) ; remplace le surtitre
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
# Transitions adoucies (retour client du 15/11 : coupures et transitions trop sèches). "transitions": false dans l'EDL = coupes sèches.
DISSOLVE = 0.16         # (n'est plus utilisé entre deux plans de face cam : voir SETTLE)
# Retour client du 18/11 (« cuts bizarres, pas entraînants ») : plus de fondu entre deux plans de la même personne
# (effet fantôme) ni de zoom animé en pleine phrase. Coupe franche + changement de cadre, et le plan entrant
# « se pose » (léger zoom qui se résorbe) ; les changements de cadre internes tombent sur les pauses de la voix.
SETTLE, SETTLE_S = 0.35, 1.035
FLIP_SNAP = 0.8         # un changement de cadre se cale sur la pause la plus proche (± s), sinon il est supprimé
BROLL_FADE = 0.22       # entrée et sortie en fondu des plans de coupe (s)
FLIP_EASE = 0.30        # passage large ↔ serré animé au lieu d'un saut (s)
AUDIO_IN, AUDIO_OUT = 0.05, 0.08     # fondus de la voix à chaque coupe (s)
BEAT_MIN_STRENGTH = 0.4
BEAT_MIN_GAP = 2.5
BEAT_PUNCH = 1.045
CAP_MAX_CHARS = 24      # § 5 : 1 ligne, ≤ 24 caractères
# Styles de sous-titres (edl["cap_style"]). « boite » = fond noir 50 % (§ 5). Les autres sont sans fond :
# lisibilité par ombre portée + léger voile dégradé en bas d'image (#cap-scrim), mots-clés (edl["keywords"]) en <em>.
_SHADOW = "text-shadow: 0 0 1px rgba(0,0,0,0.55), 0 2px 4px rgba(0,0,0,0.45), 0 6px 20px rgba(0,0,0,0.30);"
_HALO = (" .cap-box { position: relative; isolation: isolate; }"
         " .cap-box::before { content: ''; position: absolute; inset: -64px -70px; z-index: -1;"
         " background: radial-gradient(closest-side, rgba(0,0,0,0.30) 0%, rgba(0,0,0,0.14) 50%, rgba(0,0,0,0) 100%); }")
_KW_GOLD = "#E6D3A0"     # or « texte » : plus clair que l'or du logo, pour tenir sur le tee-shirt blanc
_KW_SHADOW = "text-shadow: 0 0 2px rgba(0,0,0,0.85), 0 1px 3px rgba(0,0,0,0.6), 0 6px 20px rgba(0,0,0,0.30);"
# Variante éditoriale de la définition : initiales en Playfair italique, comme les mots-clés.
DEF_STYLES = {
    "editorial": " .di { font-family: 'Playfair Display', serif; font-style: italic; font-weight: 600; font-size: 104px; padding-right: 10px; }"
                 " .dr { font-weight: 600; }",
}
CAP_STYLES = {
    # « base » : style des témoignages Sparta publiés (Mickaël, Xavier) — texte fin crème au milieu de l'image,
    # sans fond ni mot coloré, 2 à 4 mots (retour client du 20/11).
    "base": " @font-face { font-family: 'InterBase'; font-weight: 400; src: url('assets/fonts/Inter-Regular.otf') format('opentype'); }"
            " .cap { top: 1180px; } .cap-box { background: none; padding: 0; font-family: 'InterBase', sans-serif; font-weight: 400;"
            " font-size: 52px; letter-spacing: -0.005em; color: #F3ECD6; text-shadow: 0 1px 3px rgba(0,0,0,0.45), 0 2px 12px rgba(0,0,0,0.25); }"
            " .cap-box b, .cap-box em { font-weight: 400; font-style: normal; color: inherit; font-size: 1em; }",
    # Montserrat Bold blanc, mots-clés ExtraBold or.
    "epure": _HALO + " .cap-box { background: none; padding: 0; font-weight: 700; font-size: 52px; " + _SHADOW + " }"
             " .cap-box b, .cap-box em { font-weight: 800; font-style: normal; font-size: 1.06em; letter-spacing: 0.01em; color: " + _KW_GOLD + "; " + _KW_SHADOW + " }",
    # Montserrat SemiBold blanc, mots-clés en Playfair Display italique or ; sigles en capitales droites or.
    "editorial": _HALO + " .cap-box { background: none; padding: 0; font-weight: 600; font-size: 52px; " + _SHADOW + " }"
                 " .cap-box em { font-family: 'Playfair Display', serif; font-style: italic; font-weight: 600; font-size: 1.3em;"
                 " letter-spacing: 0; color: " + _KW_GOLD + "; line-height: 0.8; " + _KW_SHADOW + " }"
                 " .cap-box em.ac, .cap-box b { font-family: 'Montserrat', sans-serif; font-style: normal; font-weight: 800;"
                 " font-size: 1em; letter-spacing: 0.04em; color: " + _KW_GOLD + "; " + _KW_SHADOW + " }",
    "majuscules": _HALO + " .cap-box { background: none; padding: 0; font-weight: 700; font-size: 44px; letter-spacing: 0.08em;"
                  " text-transform: uppercase; " + _SHADOW + " }"
                  " .cap-box b, .cap-box em { font-weight: 800; font-style: normal; color: " + _KW_GOLD + "; }",
    "karaoke": _HALO + " .cap-box { background: none; padding: 0; font-weight: 700; font-size: 52px; " + _SHADOW + " }"
               " .cap-box .w { opacity: 0.68; } .cap-box .w:first-child { opacity: 1; }"
               " .cap-box b, .cap-box em { font-weight: 800; font-style: normal; color: " + _KW_GOLD + "; }",
}
CAP_MAX_WORDS = 5
GOLD = "#D9C48E"        # § 5 : chiffres mis en avant

# Pictogrammes des schémas (retour client du 19/11 : « des petits schémas pour visualiser »).
# Tracés au trait or (viewBox 48×48), dessinés à l'apparition (stroke-dashoffset 1 → 0, pathLength = 1).
SCH_ICONS = {
    "horloge": '<circle cx="24" cy="24" r="17"/><path d="M24 14V24L31 29"/>',
    "calendrier": '<rect x="7" y="11" width="34" height="30" rx="3"/><path d="M7 19H41M16 6V14M32 6V14M14 27H18M22 27H26M30 27H34M14 34H18M22 34H26"/>',
    "perso": '<circle cx="24" cy="16" r="7"/><path d="M10 41C10 33 16 28 24 28S38 33 38 41"/>',
    "equipe": '<circle cx="18" cy="17" r="6"/><path d="M6 40C6 33 11 28 18 28S30 33 30 40"/><circle cx="33" cy="15" r="5"/><path d="M31 25C37 25 42 29 42 36"/>',
    "societe": '<path d="M10 41V12L24 7L38 12V41M5 41H43M17 18H21M27 18H31M17 25H21M27 25H31M21 41V33H27V41"/>',
    "diplome": '<path d="M24 9L4 18L24 27L44 18Z"/><path d="M12 22V31C12 34 17 37 24 37S36 34 36 31V22M44 18V28"/>',
    "carte": '<rect x="5" y="11" width="38" height="26" rx="3"/><circle cx="16" cy="22" r="4"/><path d="M10 32C11 29 13 28 16 28S21 29 22 32M27 20H37M27 26H35"/>',
    "contrat": '<path d="M13 6H29L37 14V42H13Z"/><path d="M29 6V14H37M18 21H32M18 27H32M18 35C20 33 22 37 24 35S27 33 29 35"/>',
    "bouclier": '<path d="M24 6L38 11V22C38 31 32 37 24 41C16 37 10 31 10 22V11Z"/><path d="M17 24L22 29L31 19"/>',
    "haltere": '<path d="M6 24H42M10 17V31M15 13V35M33 13V35M38 17V31"/>',
    "euro": '<path d="M35 13A13 13 0 1 0 35 35M9 21H27M9 28H27"/>',
    "hausse": '<path d="M6 36L17 25L24 32L39 16M31 16H39V24"/>',
    "baisse": '<path d="M6 14L17 25L24 18L39 34M31 34H39V26"/>',
    "coche": '<path d="M11 25L20 34L37 14"/>',
    "croix": '<path d="M14 14L34 34M34 14L14 34"/>',
    "bulle": '<path d="M7 10H41V32H22L13 39V32H7Z"/><path d="M14 19H34M14 25H27"/>',
    "livre": '<path d="M24 13C19 9 13 9 7 10V37C13 36 19 36 24 40C29 36 35 36 41 37V10C35 9 29 9 24 13Z"/><path d="M24 13V40"/>',
    "cible": '<circle cx="24" cy="24" r="17"/><circle cx="24" cy="24" r="10"/><circle cx="24" cy="24" r="3"/>',
    "attention": '<path d="M24 7L43 40H5Z"/><path d="M24 19V29M24 34V35"/>',
    "cadenas": '<rect x="11" y="21" width="26" height="20" rx="3"/><path d="M16 21V15A8 8 0 0 1 32 15V21M24 29V34"/>',
    "fleche": '<path d="M8 24H38M30 16L38 24L30 32"/>',
    "ampoule": '<path d="M18 32C18 28 12 25 12 18A12 12 0 0 1 36 18C36 25 30 28 30 32Z"/><path d="M19 37H29M21 42H27"/>',
    "dos": '<path d="M24 6V42M18 12H30M17 19H31M17 26H31M18 33H30M20 40H28"/>',
    "jambe": '<path d="M20 6L18 22L22 33L19 42H27M26 6L27 21L29 31"/>',
    "coeur": '<path d="M24 40C10 31 6 24 6 17A9 9 0 0 1 24 13A9 9 0 0 1 42 17C42 24 38 31 24 40Z"/><path d="M12 24H18L21 18L26 30L29 24H36"/>',
    "eclair": '<path d="M27 5L11 27H23L21 43L37 21H25Z"/>',
    "goutte": '<path d="M24 6C24 6 12 20 12 29A12 12 0 0 0 36 29C36 20 24 6 24 6Z"/>',
    "feu": '<path d="M24 42C15 42 11 35 12 28C13 21 19 18 18 9C25 13 28 19 27 24C30 22 31 19 31 17C35 21 37 26 36 31C35 38 30 42 24 42Z"/>',
    "assiette": '<circle cx="24" cy="24" r="17"/><circle cx="24" cy="24" r="10"/>',
}

def sch_icon(name, el_id, size=96, color=None, sw=2.6):
    """Pictogramme SVG (traits or) ; chaque tracé reçoit pathLength=1 pour l'animation de dessin."""
    body = SCH_ICONS.get(name, SCH_ICONS["cible"])
    body = re.sub(r"<(path|circle|rect)\b", r'<\1 pathLength="1"', body)
    return (f'<svg id="{el_id}" class="sch-ico" viewBox="0 0 48 48" width="{size}" height="{size}" fill="none" '
            f'stroke="{color or GOLD}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round">{body}</svg>')

def sch_draw(el_id, t, dur=0.7):
    """Dessine le pictogramme au trait (seek-safe : simple tween de propriété CSS)."""
    return (f'tl.fromTo("#{el_id} path, #{el_id} circle, #{el_id} rect", {{strokeDashoffset: 1}}, '
            f'{{strokeDashoffset: 0, duration: {dur}, ease: "power2.inOut", stagger: 0.08}}, {round(t, 3)});')
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
            core = w.strip(",.?!;:«»\"")
            if core in corrections:                          # correction en mot entier uniquement
                w = w.replace(core, corrections[core], 1)
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
        "leur", "leurs", "ne", "n’", "tant", "très", "plus", "trop", "si", "comme", "est", "suis", "a",
        "ai", "était", "puis", "donc", "alors", "parce", "quand", "lorsque", "y", "cette", "cet", "ces",
        "pourquoi", "peu", "tout", "tous", "toute", "toutes", "bien", "super",
        "va", "vas", "vais", "vont", "peux", "peut", "dois", "doit", "faut", "où"}
# Paires jamais séparées entre deux sous-titres.
NO_SPLIT = {("coach", "sportif"), ("coachs", "sportifs"), ("salle", "de"), ("mise", "en"),
            # locutions figées : « en tant | que », « une fois | que », « mettre | en place », « prendre | contact »…
            ("tant", "que"), ("fois", "que"), ("parce", "que"), ("alors", "que"), ("mettre", "en"), ("en", "place"),
            ("as", "besoin"), ("a", "besoin"), ("avoir", "besoin"),
            ("est-ce", "que"), ("comme", "ça")}
# Mots qui ouvrent naturellement une nouvelle ligne (on préfère couper juste avant).
OPENERS = {"et", "mais", "donc", "ou", "pour", "qui", "parce", "car", "quand"}
NUM_WORDS = {"deux": "2", "trois": "3", "quatre": "4", "cinq": "5", "six": "6", "sept": "7", "huit": "8",
             "neuf": "9", "dix": "10", "onze": "11", "douze": "12", "quinze": "15", "vingt": "20",
             "trente": "30", "quarante": "40", "cinquante": "50", "cent": "100"}
NUM_FOLLOW = UNITS | {"premiers", "premières", "derniers", "dernières"}


def _bare(w):
    w = w.replace("\xa0", " ").strip(" ,.?!;:«»\"").lower()
    return w.split("’")[-1] if "’" in w[:-1] else w      # « d’une » → « une », « j’ai » → « ai »


def _chunk_cost(toks, last_word, next_word, dur=None, max_chars=CAP_MAX_CHARS):
    text = " ".join(toks)
    n = len(text)
    if n > max_chars or len(toks) > CAP_MAX_WORDS:
        return None
    cost = abs(n - 18) * 0.15                       # longueur idéale ≈ 18 caractères
    if dur is not None and dur < 0.45:
        cost += 4.0                                 # carton trop bref : illisible, clignote
    if len(toks) == 1:
        cost += 3.0                                 # pas de mot isolé
    for t in toks[:-1]:                             # ponctuation au milieu d'une ligne : on préfère couper dessus
        if t.replace("*", "")[-1:] in ".?!":
            cost += 6.0                             # « de résultat. Ben ouais, » : deux phrases sur une ligne
        elif t.replace("*", "")[-1:] in ",;:":
            cost += 0.8
    if last_word[-1:] in ",.?!;:":
        cost -= 2.5                                 # coupure sur la ponctuation
    elif _bare(last_word) in WEAK or last_word.endswith("’"):
        cost += 8.0                                 # jamais après un mot-outil
    if next_word and _bare(next_word) in UNITS and is_number(_bare(last_word)):
        cost += 50.0                                # jamais un chiffre séparé de son unité
    if next_word and _bare(next_word) in OPENERS and _bare(last_word) not in WEAK:
        cost -= 1.0                                 # « …une séance | et à assurer… »
    if next_word and ((_bare(last_word), _bare(next_word)) in NO_SPLIT or _bare(next_word) == "pas"):
        cost += 50.0                                # « coach | sportif », « sais | pas » : interdit
    return cost


def auto_captions(words, segments, emphasis=(), max_chars=CAP_MAX_CHARS):
    """Sous-titres § 5 : 1 ligne, 1 à 5 mots, ≤ 24 caractères, découpage optimal par phrase
    (ponctuation, jamais après un mot-outil, jamais un chiffre sans son unité) ;
    chiffres en nombres, chiffres + unité en gras or."""
    out = []
    sentence_start = True                                   # suit l'ordre du montage, d'un morceau à l'autre
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
                d_ = (ws[j][0] if j < n else ws[j - 1][1]) - ws[i][0]
                c = _chunk_cost([w[2] for w in ws[i:j]], ws[j - 1][2], ws[j][2] if j < n else None, d_, max_chars)
                if c is not None and (best[j] is None or best[i] + c < best[j]):
                    best[j], prev[j] = best[i] + c, i
        cuts, j = [], n
        while j > 0:
            cuts.append((prev[j], j))
            j = prev[j]
        cuts.reverse()
        for i, j in cuts:
            toks, times, k = [], [], i
            while k < j:
                t = ws[k][2]
                times.append(ws[k][0])
                if is_number(t) and k + 1 < j and (_bare(ws[k + 1][2]) in NUM_FOLLOW):
                    span = 2 + (k + 2 < j and _bare(ws[k + 1][2]) not in UNITS and _bare(ws[k + 2][2]) in UNITS)
                    grp = [ws[k + m][2] for m in range(span)]
                    trail = grp[-1][-1] if grp[-1][-1] in ",.?!" else ""
                    toks.append("**" + " ".join(grp).rstrip(",.?!") + "**" + trail)
                    k += span
                    continue
                if is_number(t) or _bare(t) in emphasis:
                    trail = t[-1] if t[-1] in ",.?!" else ""
                    word = t.rstrip(',.?!')
                    if _bare(t) in emphasis:
                        word = word.strip("«»\"").upper()        # mot d'appel à l'action : « COACH »
                    toks.append(f"**{word}**{trail}")
                else:
                    toks.append(t)
                k += 1
            if sentence_start and toks and toks[0][:1].islower():
                toks[0] = toks[0][0].upper() + toks[0][1:]
            text = " ".join(toks)
            sentence_start = text.rstrip("*")[-1:] in ".?!"
            out.append([text, ws[i][0], min(ws[j - 1][1], seg["out"]), toks, times])
    return out


# --- Construction ----------------------------------------------------------------
def build(project):
    edl = json.load(open(os.path.join(project, "edl.json")))
    fps = edl.get("fps", FPS)
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
    # Transitions : le plan entrant apparaît en fondu (0,16 s) par-dessus la fin du plan sortant (clip muet « queue »),
    # les passages large ↔ serré sont animés, la voix a des fondus plus longs.
    soft = edl.get("transitions", True)
    tight = punch["first_tight"]
    for si, s in enumerate(segments):
        sid, a, b = s["id"], s["in"], s["out"]
        t0 = seg_start[sid][0]
        d = round(b - a - 0.002, 3)
        fade = {"version": 1, "lanes": [{"target": "volume", "points": [
            {"t": 0, "v": 0}, {"t": AUDIO_IN if soft else 0.03, "v": 1},
            {"t": round(d - (AUDIO_OUT if soft else 0.04), 3), "v": 1}, {"t": d, "v": 0}]}]}
        org = s.get("origin", punch["origin"])          # point de zoom propre au morceau (visage)
        src = s.get("src", edl["source"]); mstart = round(a - s.get("src_offset", 0), 3)
        parts.append(
            f'<div class="frame" id="thf-{sid}" style="z-index:{z};transform-origin:{org}"><div class="punch" id="thp-{sid}" style="transform-origin:{org}">'
            f'<video id="th-{sid}" src="{src}" data-start="{round(t0,3)}" data-duration="{d}" '
            f'data-media-start="{mstart}" data-track-index="0" playsinline data-has-audio="true"{grade_attr} '
            f"data-automation='{json.dumps(fade)}'></video></div></div>")
        ws_ = [w for w in words if w[0] >= a - 0.05 and w[1] <= b + 0.05]
        gaps = [((e0 + s1) / 2, s1 - e0) for (_, e0, _), (s1, _, _) in zip(ws_, ws_[1:]) if s1 - e0 >= 0.12]
        fl = []
        for f in s.get("flips", []):
            if not ws_:
                fl.append(f); continue
            near = [g for g, _ in gaps if abs(g - f) <= FLIP_SNAP and a + 0.8 < g < b - 0.8]
            if near:
                g = min(near, key=lambda x: abs(x - f))
                if all(abs(g - x) > 1.2 for x in fl): fl.append(round(g, 3))
        bounds = [round(t0, 3)] + [to_tl(sid, f) for f in sorted(fl)] + [round(t0 + d, 3)]
        if s.get("cadrage") in ("serre", "large"):
            tight = s["cadrage"] == "serre"
        prev_end = None
        for r0, r1 in zip(bounds, bounds[1:]):
            s0 = (s.get("tight_scale", punch["scale"]) if tight else s.get("wide_scale", 1))
            s1 = round(s0 * PUSH_TH, 4)
            tweens.append(f'tl.fromTo("#thf-{sid}", {{scale: {s0}}}, {{scale: {s1}, '
                          f'duration: {round(r1 - r0, 3)}, ease: "none", immediateRender: false}}, {r0});')
            if soft and (prev_end is not None or si > 0):       # le plan (ou le nouveau cadre) se pose
                tweens.append(f'tl.fromTo("#thp-{sid}", {{scale: {SETTLE_S}}}, {{scale: 1, duration: {SETTLE}, '
                              f'ease: "power2.out", immediateRender: false}}, {r0});')
            th_windows.append((r0, r1, sid))
            prev_end = s1
            tight = not tight
        if soft and si == len(segments) - 1:
            last, ov = True, 0.3                            # dernier plan : se prolonge sous le fondu du carton de fin
            parts.append(
                f'<div class="frame" id="tlf-{sid}" style="z-index:{z};transform-origin:{org}">'
                f'<video id="tl-{sid}" src="{src}" data-start="{round(t0 + d, 3)}" data-duration="{ov}" '
                f'data-media-start="{round(mstart + d, 3)}" data-track-index="13" muted playsinline{grade_attr}></video></div>')
            tweens.append(f'tl.set("#tlf-{sid}", {{scale: {prev_end}}}, 0);')
            tweens.append(f'tl.to("#tlf-{sid}", {{opacity: 0, duration: {round(ov * 0.9, 3)}, ease: "none"}}, {round(t0 + d + ov * 0.1, 3)});') if last else None
    z += 1

    # Plans de coupe (muets, par-dessus la face cam).
    # Deux plans qui se suivent sans trou s'enchaînent en fondu : le premier se prolonge sous le second.
    brs = [(to_tl(br["seg"], br["at"]), br["dur"]) for br in edl.get("broll", [])]
    for k, br in enumerate(edl.get("broll", [])):
        st, d = brs[k]
        # Un plan qui s'arrête juste avant le suivant (trou < 0,6 s) ou juste avant le carton de fin (< 0,8 s)
        # se prolonge dessous, sinon la face cam apparaît une fraction de seconde (« flash »).
        nxt = [brs[j][0] for j in range(len(brs)) if j != k and -0.05 <= brs[j][0] - (st + d) <= 0.6]
        # un schéma qui démarre juste après (< 1 s) : le plan reste dessous jusqu'à son arrivée
        nxt += [a for a in (to_tl(x["seg"], x["at"]) for x in edl.get("schemas", [])) if -0.05 <= a - (st + d) <= 1.0]
        to_end = soft and -0.05 <= end_start - (st + d) <= 0.8
        chained = soft and bool(nxt)
        if chained:
            d_eff = round(min(nxt) - st + BROLL_FADE, 3)
        elif to_end:
            d_eff = round(end_start - st + 0.35, 3)
        else:
            d_eff = d
        chained = chained or to_end
        g = f" data-color-grading='{json.dumps(br['grade'])}'" if br.get("grade") else ""
        parts.append(
            f'<div class="frame-b" id="brf-{k}" style="z-index:{z}">'
            f'<video id="br-{k}" class="full" src="{br["src"]}" data-start="{st}" data-duration="{d_eff}" '
            f'data-media-start="{br.get("offset", 0)}" data-track-index="{1 + k % 2}" muted playsinline{g}></video></div>')
        tweens.append(f'tl.fromTo("#brf-{k}", {{scale: 1}}, {{scale: {PUSH_BROLL}, duration: {d_eff}, '
                      f'ease: "none", immediateRender: false}}, {st});')
        if soft:                                            # entrée et sortie en fondu
            f_ = min(BROLL_FADE, d / 3)
            tweens.append(f'tl.fromTo("#brf-{k}", {{opacity: 0}}, {{opacity: 1, duration: {round(f_, 3)}, ease: "power1.out", immediateRender: false}}, {st});')
            if not chained:
                tweens.append(f'tl.to("#brf-{k}", {{opacity: 0, duration: {round(f_, 3)}, ease: "power1.in"}}, {round(st + d - f_, 3)});')
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
    if edl.get("hook"):
        hk = edl["hook"]; hd = hk.get("dur", 6.5)
        lines = []
        for ln in hk["text"].split("|"):
            esc = html.escape(ln.strip()).replace("&#x27;", "’").replace("'", "’")
            while "**" in esc:
                esc = esc.replace("**", "<b>", 1).replace("**", "</b>", 1)
            lines.append(esc)
        # "position": "bas" : titre posé sur le buste, au-dessus des sous-titres, quand la tête est haute dans le cadre
        # (règle client du 19/11 : jamais de texte sur la tête).
        hcls = "clip bas" if hk.get("position") == "bas" else "clip"
        parts.append(f'<div id="hook" class="{hcls}" data-start="0.2" data-duration="{hd}" data-track-index="8" '
                     f'style="z-index:{z+2}"><div class="hook-inner"><span class="hook-rule"></span>'
                     f'<span class="hook-text">{"<br>".join(lines)}</span></div></div>')
        tweens += [
            'tl.fromTo("#hook .hook-rule", {scaleX: 0}, {scaleX: 1, duration: 0.5, ease: "power2.out"}, 0.2);',
            'tl.fromTo("#hook .hook-text", {opacity: 0, y: 14}, {opacity: 1, y: 0, duration: 0.55, ease: "power2.out"}, 0.35);',
            f'tl.to("#hook .hook-inner", {{opacity: 0, duration: 0.45, ease: "power1.in"}}, {round(0.2 + hd - 0.5, 3)});',
        ]
    elif edl.get("kicker"):
        kd = edl["kicker"].get("dur", 2.6)
        parts.append(f'<div id="kicker" class="clip" data-start="0.15" data-duration="{kd}" data-track-index="8" '
                     f'style="z-index:{z+2}"><div class="kicker-inner"><span class="kicker-rule"></span>'
                     f'<span class="kicker-text">{"<br>".join(html.escape(x.strip()) for x in edl["kicker"]["text"].split("|"))}</span></div></div>')
        tweens += [
            f'tl.fromTo("#kicker .kicker-rule", {{scaleX: 0}}, {{scaleX: 1, duration: 0.5, ease: "power2.out"}}, 0.15);',
            f'tl.fromTo("#kicker .kicker-text", {{opacity: 0, y: 8}}, {{opacity: 1, y: 0, duration: 0.5, ease: "power2.out"}}, 0.35);',
            f'tl.to("#kicker .kicker-inner", {{opacity: 0, duration: 0.4, ease: "power1.in"}}, {round(0.15 + kd - 0.45, 3)});',
        ]

    # Schémas animés : texte et filets or sur voile léger, un seul élément à l'écran (§ 0), sous-titres conservés.
    #   flow : étapes empilées reliées par des flèches ; "barre": true sur une étape = texte barré (idée fausse)
    #   bars : lignes « libellé / valeur » avec une barre dont la longueur compare les valeurs (0 à 1)
    for si, sc in enumerate(edl.get("schemas", [])):
        t0 = to_tl(sc["seg"], sc["at"]); d = sc.get("dur", 4.5); sid = f"sch{si}"
        # Schéma qui finit juste avant le carton de fin : on le garde jusqu'au fondu au noir,
        # sinon la face cam réapparaît une fraction de seconde (retour client du 18/11).
        # Idem si un plan de coupe ou un autre schéma démarre juste après : on enchaîne sans revoir la face cam.
        suiv = [a for a, _ in cover if a > t0 + 0.5] + [to_tl(x["seg"], x["at"]) for x in edl.get("schemas", []) if x is not sc] + [end_start]
        suiv = [a for a in suiv if 0 <= a - (t0 + d) <= (1.5 if a == end_start else 1.0)]
        if suiv:
            d = round(min(suiv) - t0 + 0.4, 3)
        def esc_(x):
            e = html.escape(x).replace("&#x27;", "’").replace("'", "’")
            while "**" in e:
                e = e.replace("**", "<b>", 1).replace("**", "</b>", 1)
            return e
        body, anim = [], []
        cle = {"flow": "etapes", "bars": "lignes", "checks": "lignes", "timeline": "etapes", "icones": "items", "chiffre": "sous", "vs": None}[sc["type"]]
        n = 2 if sc["type"] == "vs" else len(sc.get(cle) or [])
        gap = max(0.5, (d - 1.3) / max(n, 1))
        if sc.get("titre"):
            body.append(f'<div class="sch-title" id="{sid}-t">{esc_(sc["titre"])}</div>')
            anim.append(f'tl.fromTo("#{sid}-t", {{opacity: 0, y: -8}}, {{opacity: 1, y: 0, duration: 0.4, ease: "power2.out"}}, {round(t0 + 0.25, 3)});')
        # instants d'apparition : listés en temps source ("temps"), sinon répartis sur la durée
        tps = [to_tl(sc["seg"], x) for x in sc["temps"]] if sc.get("temps") else [round(t0 + 0.55 + k * gap, 3) for k in range(n)]
        if sc["type"] == "flow":
            for k, et in enumerate(sc["etapes"]):
                lines = et if isinstance(et, list) else [et]
                barre = sc.get("barres", [])
                cls = "sch-step" + (" sch-strike" if k in barre else "")
                if k in barre:
                    # un trait par ligne, à la largeur de la ligne (sur deux lignes, un trait unique tombait entre elles et se lisait comme un soulignement)
                    inner = "<br>".join(f'<span class="sch-ln">{esc_(x)}<span class="sch-bar"></span></span>' for x in lines)
                else:
                    inner = "<br>".join(esc_(x) for x in lines)
                body.append(f'<div class="{cls}" id="{sid}-s{k}"><span class="sch-txt">{inner}</span></div>')
                ts = tps[k]
                anim.append(f'tl.fromTo("#{sid}-s{k}", {{opacity: 0, y: 18}}, {{opacity: 1, y: 0, duration: 0.45, ease: "power2.out"}}, {ts});')
                if k in barre:
                    anim.append(f'tl.fromTo("#{sid}-s{k} .sch-bar", {{scaleX: 0}}, {{scaleX: 1, duration: 0.4, ease: "power2.inOut"}}, {round(ts + 0.5, 3)});')
                if k < n - 1:
                    body.append(f'<div class="sch-arrow" id="{sid}-a{k}"><span class="sch-line"></span><span class="sch-head"></span></div>')
                    anim.append(f'tl.fromTo("#{sid}-a{k}", {{opacity: 0, scaleY: 0}}, {{opacity: 1, scaleY: 1, duration: 0.3, ease: "power2.out"}}, {round(max(ts + 0.35, tps[k + 1] - 0.35), 3)});')
        elif sc["type"] == "chiffre":
            # Gros chiffre qui défile (ex. « 120 h »), libellé dessous, pictogramme au-dessus, puis lignes courtes
            ic = f"{sid}-i"
            if sc.get("icone"):
                body.append(f'<div class="sch-ic-wrap">{sch_icon(sc["icone"], ic, 120)}</div>')
                anim.append(sch_draw(ic, t0 + 0.15, 0.8))
            v = sc["valeur"]
            body.append(f'<div class="sch-big" id="{sid}-b">{esc_(sc.get("prefixe", ""))}<span class="sch-num" id="{sid}-n">{esc_(str(v))}</span>'
                        f'<span class="sch-unit">{esc_(sc.get("unite", ""))}</span></div>')
            anim.append(f'tl.fromTo("#{sid}-b", {{opacity: 0, scale: 0.86}}, {{opacity: 1, scale: 1, duration: 0.45, ease: "back.out(1.6)"}}, {round(t0 + 0.3, 3)});')
            if isinstance(v, (int, float)):
                anim.append(f'tl.fromTo("#{sid}-n", {{innerText: 0}}, {{innerText: {v}, snap: {{innerText: 1}}, duration: {sc.get("defile", 1.2)}, ease: "power2.out"}}, {round(t0 + 0.3, 3)});')
            if sc.get("label"):
                body.append(f'<div class="sch-blbl" id="{sid}-l">{esc_(sc["label"])}</div>')
                anim.append(f'tl.fromTo("#{sid}-l", {{opacity: 0, y: 12}}, {{opacity: 1, y: 0, duration: 0.4, ease: "power2.out"}}, {round(t0 + 0.6, 3)});')
            for k, x in enumerate(sc.get("sous") or []):
                body.append(f'<div class="sch-chip" id="{sid}-s{k}">{esc_(x)}</div>')
                anim.append(f'tl.fromTo("#{sid}-s{k}", {{opacity: 0, y: 16}}, {{opacity: 1, y: 0, duration: 0.4, ease: "power2.out"}}, {tps[k]});')
        elif sc["type"] == "vs":
            # Deux cartes face à face (pictogramme, titre, lignes) ; "accent": "g" ou "d" = carte gagnante cerclée d'or
            cards = []
            for k, cote in enumerate(("gauche", "droite")):
                c = sc[cote]; cid = f"{sid}-c{k}"; ic = f"{cid}-i"
                acc = " sch-acc" if sc.get("accent") == "gd"[k] else ""
                lines = "".join(f'<div class="sch-cl" id="{cid}-l{q}">{esc_(x)}</div>' for q, x in enumerate(c.get("lignes", [])))
                cards.append(f'<div class="sch-card{acc}" id="{cid}">{sch_icon(c.get("icone", "cible"), ic, 104)}'
                             f'<div class="sch-ct">{esc_(c["titre"])}</div>{lines}</div>')
                ts = tps[k]
                anim.append(f'tl.fromTo("#{cid}", {{opacity: 0, y: 26}}, {{opacity: 1, y: 0, duration: 0.45, ease: "power2.out"}}, {ts});')
                anim.append(sch_draw(ic, ts + 0.1))
                lt = c.get("temps")
                for q in range(len(c.get("lignes", []))):
                    tq = to_tl(sc["seg"], lt[q]) if lt else round(ts + 0.45 + 0.3 * q, 3)
                    anim.append(f'tl.fromTo("#{cid}-l{q}", {{opacity: 0, y: 10}}, {{opacity: 1, y: 0, duration: 0.35, ease: "power2.out"}}, {tq});')
            body.append(f'<div class="sch-vs">{cards[0]}<div class="sch-vsm" id="{sid}-v">VS</div>{cards[1]}</div>')
            anim.append(f'tl.fromTo("#{sid}-v", {{opacity: 0, scale: 0.5}}, {{opacity: 1, scale: 1, duration: 0.35, ease: "back.out(2)"}}, {round(tps[1] - 0.2, 3)});')
        elif sc["type"] == "timeline":
            # Frise verticale : pastille avec pictogramme, titre (or) et texte ; le filet se trace d'une étape à l'autre
            items = []
            for k, et in enumerate(sc["etapes"]):
                nid = f"{sid}-s{k}"; ic = f"{nid}-i"
                items.append(f'<div class="sch-node" id="{nid}"><div class="sch-dot">{sch_icon(et.get("icone", "cible"), ic, 64)}</div>'
                             f'<div class="sch-ntx"><div class="sch-nt">{esc_(et["titre"])}</div>'
                             + (f'<div class="sch-nd">{esc_(et["texte"])}</div>' if et.get("texte") else "") + '</div></div>')
                anim.append(f'tl.fromTo("#{nid}", {{opacity: 0, x: -24}}, {{opacity: 1, x: 0, duration: 0.45, ease: "power2.out"}}, {tps[k]});')
                anim.append(sch_draw(ic, tps[k] + 0.1, 0.6))
                if k < n - 1:
                    items.append(f'<div class="sch-vl" id="{sid}-a{k}"></div>')
                    anim.append(f'tl.fromTo("#{sid}-a{k}", {{scaleY: 0}}, {{scaleY: 1, duration: 0.35, ease: "power2.inOut"}}, {round(max(tps[k] + 0.4, tps[k + 1] - 0.35), 3)});')
            body.append(f'<div class="sch-tl">{"".join(items)}</div>')
        elif sc["type"] == "checks":
            # Liste vrai / faux : coche or ou croix blanche dessinée, texte barré-estompé quand c'est faux
            for k, (txt, ok) in enumerate(sc["lignes"]):
                rid = f"{sid}-r{k}"; ic = f"{rid}-i"
                body.append(f'<div class="sch-chk{"" if ok else " sch-no"}" id="{rid}">{sch_icon("coche" if ok else "croix", ic, 84, None if ok else "#FFFFFF", 4.2)}'
                            f'<span class="sch-ckt">{esc_(txt)}</span></div>')
                anim.append(f'tl.fromTo("#{rid}", {{opacity: 0, x: -20}}, {{opacity: 1, x: 0, duration: 0.4, ease: "power2.out"}}, {tps[k]});')
                vt = to_tl(sc["seg"], sc["verdicts"][k]) if sc.get("verdicts") else round(tps[k] + 0.5, 3)
                anim.append(f'tl.set("#{ic}", {{opacity: 0}}, {tps[k]});')
                anim.append(f'tl.set("#{ic}", {{opacity: 1}}, {vt});')
                anim.append(sch_draw(ic, vt, 0.45))
                if not ok:
                    anim.append(f'tl.to("#{rid} .sch-ckt", {{opacity: 0.55, duration: 0.3}}, {round(vt + 0.2, 3)});')
        elif sc["type"] == "icones":
            # Grille de pictogrammes légendés qui apparaissent un à un (listes : « 5 choses », « 3 rôles »…)
            tiles = []
            for k, it in enumerate(sc["items"]):
                tid = f"{sid}-s{k}"; ic = f"{tid}-i"
                tiles.append(f'<div class="sch-tile" id="{tid}">{sch_icon(it["icone"], ic, 108)}<div class="sch-tt">{esc_(it["texte"])}</div></div>')
                anim.append(f'tl.fromTo("#{tid}", {{opacity: 0, y: 20, scale: 0.92}}, {{opacity: 1, y: 0, scale: 1, duration: 0.4, ease: "power2.out"}}, {tps[k]});')
                anim.append(sch_draw(ic, tps[k] + 0.05, 0.6))
            body.append(f'<div class="sch-grid sch-g{min(3, max(2, sc.get("colonnes", 3 if n > 4 else 2)))}">{"".join(tiles)}</div>')
        else:
            for k, (lib, val, frac) in enumerate(sc["lignes"]):
                body.append(f'<div class="sch-row" id="{sid}-r{k}"><div class="sch-lab"><span class="sch-txt">{esc_(lib)}</span>'
                            f'<span class="sch-val">{esc_(val)}</span></div><div class="sch-track"><span class="sch-fill" style="width:{round(frac*100)}%"></span></div></div>')
                ts = tps[k]
                anim.append(f'tl.fromTo("#{sid}-r{k}", {{opacity: 0, y: 14}}, {{opacity: 1, y: 0, duration: 0.4, ease: "power2.out"}}, {ts});')
                anim.append(f'tl.fromTo("#{sid}-r{k} .sch-fill", {{scaleX: 0}}, {{scaleX: 1, duration: 1.0, ease: "power2.inOut"}}, {round(ts + 0.25, 3)});')
        parts.append(f'<div id="{sid}" class="clip sch" data-start="{t0}" data-duration="{d}" data-track-index="{11 + si}" style="z-index:{z+2}">'
                     f'<div class="sch-dim"></div><div class="sch-col">{"".join(body)}</div></div>')
        tweens.append(f'tl.fromTo("#{sid} .sch-dim", {{opacity: 0}}, {{opacity: 1, duration: 0.35, ease: "power1.out"}}, {t0});')
        tweens += anim
        tweens.append(f'tl.to("#{sid}", {{opacity: 0, duration: 0.4, ease: "power1.in"}}, {round(t0 + d - 0.4, 3)});')
        cover.append((t0, round(t0 + d, 3)))

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
        base = music.get("level", 0.7)                     # sous la voix : ≥ 18 dB en dessous (§ 9)
        # Points à instants strictement croissants : deux points au même instant sont fusionnés par le
        # moteur, qui étalait alors la remontée de fin sur toute la vidéo (+11 dB sous la voix).
        up0 = round(max(0.5, min(sp_end, card) - 0.15), 3)
        up1 = round(max(up0 + 0.3, card + 0.3), 3)
        fade0 = round(max(up1 + 0.1, mdur - 1.0), 3)
        lane = {"version": 1, "lanes": [{"target": "volume", "points": [
            {"t": 0, "v": 0}, {"t": 0.5, "v": base}, {"t": up0, "v": base},
            {"t": up1, "v": boost}, {"t": fade0, "v": boost}, {"t": mdur, "v": 0}]}]}
        parts.append(f'<audio id="music" src="{music["src"]}" data-start="{m0}" data-duration="{mdur}" '
                     f'data-media-start="{music.get("offset", 0)}" data-track-index="6" data-volume="1" '
                     f"data-fx-chain='{json.dumps(MUSIC_FX)}' data-automation='{json.dumps(lane)}'></audio>")
        # Coups de zoom sur les temps forts : désactivés par défaut (refusés par le client le 13/10),
        # réactivables avec "coups_de_zoom": true dans l'EDL.
        if edl.get("coups_de_zoom", False) and music.get("beats") and os.path.exists(os.path.join(project, music["beats"])):
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
    raw = edl.get("captions") or auto_captions(words, segments, {e.lower() for e in edl.get("emphasis", [])},
                                               edl.get("cap_max_chars", CAP_MAX_CHARS))
    caps = []
    for entry in raw:
        text, a, b = entry[:3]
        toks = entry[3] if len(entry) > 3 else text.split()
        times = entry[4] if len(entry) > 4 else [a + (b - a) * m / max(1, len(toks)) for m in range(len(toks))]
        sid = seg_of(a)
        if not caps or caps[-1][2] != sid:
            a = seg_start[sid][1] if a - seg_start[sid][1] < 0.3 else a
        caps.append([to_tl(sid, a), to_tl(sid, min(b, seg_start[sid][2])), sid, text,
                     toks, [to_tl(sid, max(a, min(t, seg_start[sid][2]))) for t in times]])
    # Mots-clés (« mot important ») : {"mots": "exigences préalables", "n": 1} = 1re occurrence ; "n": 0 = toutes
    kw_marks = set()                                     # (indice sous-titre, indice mot)
    for kw in edl.get("keywords", []):
        kw = {"mots": kw, "n": 1} if isinstance(kw, str) else kw
        casse = kw.get("casse", False)                    # « COACH » (appel à l'action) ≠ « coach sportif »
        norm = (lambda w: w.replace("\xa0", " ").strip(" ,.?!;:«»\"")) if casse else _bare
        target = [norm(x) for x in kw["mots"].split()]
        seen = 0
        for ci, c in enumerate(caps):
            bt = [norm(x.replace("**", "")) for x in c[4]]
            for wi in range(len(bt) - len(target) + 1):
                if bt[wi:wi + len(target)] == target:
                    seen += 1
                    if kw.get("n", 1) in (0, seen):
                        kw_marks.update((ci, wi + m) for m in range(len(target)))
    for i, c in enumerate(caps):
        end = c[1] + 0.12
        if i + 1 < len(caps) and caps[i + 1][2] == c[2]:
            end = min(end, caps[i + 1][0])
        seg_end = seg_start[c[2]][0] + (seg_start[c[2]][2] - seg_start[c[2]][1])
        c[1] = round(min(end, seg_end), 3)
    cap_style = edl.get("cap_style", "boite")
    # Définition d'un sigle (acrostiche) : {"lignes": [["E", "xigences"], ["P", "réalables"], …],
    # "mots": ["exigences", "préalables", …]} — chaque ligne se complète quand le mot est prononcé ;
    # elle remplace les sous-titres pendant ce temps (un seul élément graphique à l'écran, § 7 bis).
    dfn, def_win = edl.get("definition"), None
    if dfn:
        flat = [(_bare(tok.replace("**", "")), t) for c in caps for tok, t in zip(c[4], c[5])]
        times, k = [], 0
        for mot in dfn["mots"]:
            while k < len(flat) and flat[k][0] != _bare(mot):
                k += 1
            times.append(flat[k][1] if k < len(flat) else None)
            k += 1
        if None not in times:
            prev_end = [c[1] for c in caps if c[0] < times[0] - 0.2]
            t0 = round(max(times[0] - 0.12, prev_end[-1] if prev_end else 0.0), 3)   # jamais avec un autre sous-titre
            nxt = [c[0] for c in caps if c[0] > times[-1] + 0.3]
            t1 = round(min(nxt[0] - 0.02 if nxt else times[-1] + 1.0, times[-1] + 1.4), 3)
            def_win = (t0, t1)
            rows = "".join(f'<div class="dl"><span class="di">{html.escape(L)}</span><span class="dr" id="dr-{n}">{html.escape(R)}</span></div>'
                           for n, (L, R) in enumerate(dfn["lignes"]))
            parts.append(f'<div id="def" class="clip" data-start="{t0}" data-duration="{round(t1 - t0, 3)}" data-track-index="9" '
                         f'style="z-index:{z+3}"><div class="def-dim"></div><div class="def-col">{rows}</div></div>')
            tweens.append(f'tl.fromTo("#def .def-dim", {{opacity: 0}}, {{opacity: 1, duration: 0.3, ease: "power1.out"}}, {t0});')
            tweens.append(f'tl.fromTo("#def .di", {{opacity: 0, y: 14}}, {{opacity: 1, y: 0, duration: 0.35, ease: "power2.out", stagger: 0.06}}, {t0});')
            for n, t in enumerate(times):
                tweens.append(f'tl.fromTo("#dr-{n}", {{opacity: 0, x: -8}}, {{opacity: 1, x: 0, duration: 0.3, ease: "power2.out"}}, {round(max(t0 + 0.1, t - 0.04), 3)});')
            tweens.append(f'tl.to("#def", {{opacity: 0, duration: 0.25, ease: "power1.in"}}, {round(t1 - 0.25, 3)});')
    cap_html = []
    for i, (a, b, _, text, toks, wtimes) in enumerate(caps):
        if b - a < 0.05:
            continue
        if def_win and def_win[0] - 0.05 <= a < def_win[1]:
            continue
        spans = []
        for wi, tok in enumerate(toks):
            esc = html.escape(tok).replace("&#x27;", "’").replace("'", "’")
            while "**" in esc:
                esc = esc.replace("**", "<b>", 1).replace("**", "</b>", 1)
            if (i, wi) in kw_marks:                      # la ponctuation reste hors de la mise en valeur
                lead = esc[:len(esc) - len(esc.lstrip("«\xa0 "))]
                core = esc[len(lead):].rstrip(",.?!;:\xa0» ")
                tail = esc[len(lead) + len(core):]
                ac = ' class="ac"' if core.isupper() and len(core) >= 3 else ""      # sigle : EPMSP, COACH
                esc = f"{lead}<em{ac}>{core}</em>{tail}"
            spans.append(f'<span class="w" id="w-{i}-{wi}">{esc}</span>')
            if cap_style == "karaoke" and wi > 0:        # mot pas encore dit : estompé, puis plein à son instant
                tweens.append(f'tl.set("#w-{i}-{wi}", {{opacity: 1}}, {round(max(a, wtimes[wi]), 3)});')
        cap_html.append(f'<div id="cap-{i}" class="clip cap" data-start="{a}" data-duration="{round(b-a,3)}" '
                        f'data-track-index="4"><span class="cap-box">{" ".join(spans)}</span></div>')
    parts.append(f'<div id="captions" style="z-index:{z+4}">' + "".join(cap_html) + "</div>")

    # Carte de fin.
    parts.append(
        f'<div id="endcard" class="clip{" no-logo" if not end_card.get("logo") else ""}" data-start="{round(end_start,3)}" data-duration="{end_card["dur"]}" '
        f'data-track-index="5" style="z-index:{z+5}"' + '>'
        + (f'<img id="end-logo" src="{end_card["logo"]}" alt="Sparta, centre de coaching privé" />' if end_card.get("logo") else '')
        + (f'<div id="end-cta">{cta_html}</div>' if (cta_html := (lambda t: t and html.escape(t).replace("**", "<b>", 1).replace("**", "</b>", 1))(end_card.get("cta"))) else "")
        + '</div>')
    if soft:
        tweens.append(f'tl.fromTo("#endcard", {{opacity: 0}}, {{opacity: 1, duration: 0.3, ease: "none", immediateRender: false}}, {round(end_start, 3)});')
    if end_card.get("logo"):
        tweens.append(f'tl.fromTo("#end-logo", {{opacity: 0, scale: 0.97}}, {{opacity: 1, scale: 1, duration: 0.4, ease: "power2.out"}}, {round(end_start,3)});')
        tweens.append(f'tl.to("#end-logo", {{opacity: 0, duration: 0.5, ease: "power1.in"}}, {round(total - 0.55,3)});')
    if end_card.get("cta"):
        tweens.append(f'tl.fromTo("#end-cta", {{opacity: 0, y: 8}}, {{opacity: 1, y: 0, duration: 0.4, ease: "power2.out"}}, {round(end_start + 0.45, 3)});')
        tweens.append(f'tl.to("#end-cta", {{opacity: 0, duration: 0.5, ease: "power1.in"}}, {round(total - 0.55, 3)});')

    doc = TEMPLATE.format(W=W, H=H, FPS=fps, total=total, parts="\n      ".join(parts), GOLD=GOLD,
                          tweens="\n      ".join(tweens), origin=punch["origin"], title=html.escape(edl["title"]),
                          cap_css=CAP_STYLES.get(edl.get("cap_style", "boite"), ""),
                          def_css=DEF_STYLES.get(edl.get("cap_style", "boite"), ""))
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
      @font-face {{ font-family: "Montserrat"; font-weight: 700; src: url("assets/fonts/montserrat-latin-700-normal.woff2") format("woff2"); }}
      @font-face {{ font-family: "Playfair Display"; font-style: italic; font-weight: 400 900; src: url("assets/fonts/PlayfairDisplay-Italic-VF.ttf") format("truetype"); }}
      @font-face {{ font-family: "Instrument Serif"; font-style: italic; font-weight: 400; src: url("assets/fonts/InstrumentSerif-Italic.ttf") format("truetype"); }}
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
      /* Schémas animés : texte blanc, filets or, voile léger sur la face cam (aucune plaque) */
      .sch {{ position: absolute; inset: 0; }}
      .sch-dim {{ position: absolute; inset: 0; background: radial-gradient(ellipse 100% 58% at 50% 38%, rgba(0,0,0,0.70), rgba(0,0,0,0.46) 65%, rgba(0,0,0,0.16)); }}
      .sch-col {{ position: absolute; left: 0; right: 0; top: 470px; display: flex; flex-direction: column; align-items: center; }}
      .sch-title {{ font-family: "Montserrat", sans-serif; font-weight: 700; font-size: 30px; letter-spacing: 0.32em; color: {GOLD}; margin-bottom: 34px;
                   text-shadow: 0 1px 3px rgba(0,0,0,0.7); }}
      .sch-step {{ position: relative; font-family: "Montserrat", sans-serif; font-weight: 800; font-size: 58px; line-height: 1.18; color: #FFFFFF; text-align: center;
                  white-space: nowrap; text-shadow: 0 0 2px rgba(0,0,0,0.6), 0 3px 10px rgba(0,0,0,0.6), 0 8px 30px rgba(0,0,0,0.45); }}
      .sch-step b {{ color: #E6D3A0; font-weight: 800; }}
      .sch-strike .sch-txt {{ opacity: 0.65; }}
      .sch-ln {{ position: relative; display: inline-block; }}
      .sch-bar {{ position: absolute; left: -12px; right: -12px; top: 52%; height: 6px; background: {GOLD}; transform-origin: 0% 50%; border-radius: 3px;
                 box-shadow: 0 0 0 2px rgba(0,0,0,0.45); }}
      .sch-arrow {{ display: flex; flex-direction: column; align-items: center; height: 74px; transform-origin: 50% 0%; }}
      .sch-line {{ display: block; width: 4px; flex: 1; background: {GOLD}; }}
      .sch-head {{ display: block; width: 0; height: 0; border-left: 14px solid transparent; border-right: 14px solid transparent; border-top: 18px solid {GOLD}; }}
      .sch-row {{ width: 820px; margin-bottom: 52px; }}
      .sch-lab {{ display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 16px; }}
      .sch-lab .sch-txt {{ font-family: "Montserrat", sans-serif; font-weight: 800; font-size: 50px; color: #FFFFFF; text-shadow: 0 2px 10px rgba(0,0,0,0.6); }}
      .sch-val {{ font-family: "Montserrat", sans-serif; font-weight: 700; font-size: 36px; color: {GOLD}; text-shadow: 0 2px 8px rgba(0,0,0,0.6); }}
      .sch-track {{ height: 14px; background: rgba(255,255,255,0.16); border-radius: 7px; overflow: hidden; }}
      .sch-fill {{ display: block; height: 100%; background: {GOLD}; border-radius: 7px; transform-origin: 0% 50%; }}
      .sch-ico {{ display: block; overflow: visible; filter: drop-shadow(0 2px 6px rgba(0,0,0,0.55)); }}
      .sch-ico path, .sch-ico circle, .sch-ico rect {{ stroke-dasharray: 1; stroke-dashoffset: 0; }}
      .sch-ic-wrap {{ margin-bottom: 10px; }}
      .sch-big {{ font-family: "Montserrat", sans-serif; font-weight: 800; font-size: 210px; line-height: 1; color: {GOLD}; letter-spacing: -0.02em;
                 text-shadow: 0 4px 24px rgba(0,0,0,0.55); display: flex; align-items: baseline; }}
      .sch-unit {{ font-size: 96px; margin-left: 14px; }}
      .sch-blbl {{ font-family: "Montserrat", sans-serif; font-weight: 800; font-size: 56px; color: #FFFFFF; margin-top: 8px; text-shadow: 0 3px 12px rgba(0,0,0,0.6); }}
      .sch-chip {{ font-family: "Montserrat", sans-serif; font-weight: 700; font-size: 42px; color: #FFFFFF; margin-top: 26px; padding: 10px 30px;
                  border: 3px solid {GOLD}; border-radius: 40px; background: rgba(0,0,0,0.28); }}
      .sch-vs {{ display: flex; align-items: center; gap: 22px; }}
      .sch-card {{ width: 420px; padding: 34px 20px 30px; border: 3px solid rgba(255,255,255,0.55); border-radius: 26px; background: rgba(0,0,0,0.32);
                  display: flex; flex-direction: column; align-items: center; text-align: center; }}
      .sch-card.sch-acc {{ border-color: {GOLD}; box-shadow: 0 0 0 2px rgba(217,196,142,0.25), 0 10px 40px rgba(0,0,0,0.35); }}
      .sch-ct {{ font-family: "Montserrat", sans-serif; font-weight: 800; font-size: 46px; line-height: 1.12; color: #FFFFFF; margin: 18px 0 14px; }}
      .sch-cl {{ font-family: "Montserrat", sans-serif; font-weight: 700; font-size: 36px; line-height: 1.2; color: #E6D3A0; margin-top: 10px; }}
      .sch-vsm {{ font-family: "Montserrat", sans-serif; font-weight: 800; font-size: 40px; color: #111; background: {GOLD}; width: 84px; height: 84px;
                 border-radius: 50%; display: flex; align-items: center; justify-content: center; flex: none; }}
      .sch-tl {{ display: flex; flex-direction: column; width: 860px; }}
      .sch-node {{ display: flex; align-items: center; gap: 30px; }}
      .sch-dot {{ width: 104px; height: 104px; flex: none; border-radius: 50%; border: 3px solid {GOLD}; background: rgba(0,0,0,0.40);
                 display: flex; align-items: center; justify-content: center; }}
      .sch-nt {{ font-family: "Montserrat", sans-serif; font-weight: 800; font-size: 52px; line-height: 1.1; color: {GOLD}; text-shadow: 0 3px 12px rgba(0,0,0,0.6); }}
      .sch-nd {{ font-family: "Montserrat", sans-serif; font-weight: 700; font-size: 38px; line-height: 1.2; color: #FFFFFF; margin-top: 6px; text-shadow: 0 3px 12px rgba(0,0,0,0.6); }}
      .sch-vl {{ width: 4px; height: 56px; margin: 6px 0 6px 50px; background: {GOLD}; transform-origin: 50% 0%; }}
      .sch-chk {{ display: flex; align-items: center; gap: 26px; width: 880px; margin-bottom: 34px; }}
      .sch-ckt {{ font-family: "Montserrat", sans-serif; font-weight: 800; font-size: 48px; line-height: 1.15; color: #FFFFFF; text-shadow: 0 3px 12px rgba(0,0,0,0.6); }}
      .sch-grid {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 34px 26px; }}
      .sch-g3 {{ width: 960px; }} .sch-g2 {{ width: 760px; }}
      .sch-tile {{ width: 290px; display: flex; flex-direction: column; align-items: center; text-align: center; padding: 26px 10px 22px;
                  border: 3px solid rgba(217,196,142,0.75); border-radius: 24px; background: rgba(0,0,0,0.32); }}
      .sch-tt {{ font-family: "Montserrat", sans-serif; font-weight: 800; font-size: 38px; line-height: 1.15; color: #FFFFFF; margin-top: 16px; }}
      .sch-tt b, .sch-ct b, .sch-nd b, .sch-ckt b, .sch-blbl b {{ color: #E6D3A0; }}
      /* Accroche en haut d'image : texte blanc gras, mot-clé en or, sans fond (§ 0), sous la zone de sécurité (y ≥ 250) */
      #hook {{ position: absolute; left: 0; width: {W}px; top: 0; height: 760px; display: flex; justify-content: center; padding-top: 262px;
              background: linear-gradient(to bottom, rgba(0,0,0,0.58) 0%, rgba(0,0,0,0.46) 38%, rgba(0,0,0,0.18) 72%, rgba(0,0,0,0) 100%); }}
      #hook.bas {{ top: 900px; height: 440px; padding-top: 104px;
              background: linear-gradient(to bottom, rgba(0,0,0,0) 0%, rgba(0,0,0,0.42) 34%, rgba(0,0,0,0.42) 80%, rgba(0,0,0,0) 100%); }}
      .hook-inner {{ display: flex; flex-direction: column; align-items: center; gap: 26px; }}
      .hook-rule {{ display: block; width: 110px; height: 5px; background: {GOLD}; transform-origin: 50% 50%; }}
      .hook-text {{ display: block; font-family: "Montserrat", sans-serif; font-weight: 800; font-size: 64px; line-height: 1.2; color: #FFFFFF;
                   text-align: center; white-space: nowrap; text-shadow: 0 0 2px rgba(0,0,0,0.55), 0 3px 8px rgba(0,0,0,0.55), 0 8px 30px rgba(0,0,0,0.45); }}
      .hook-text b {{ font-weight: 800; color: #E6D3A0; }}
      #kicker {{ position: absolute; left: 0; width: {W}px; top: 250px; height: 120px; display: flex; justify-content: center; }}
      .kicker-inner {{ display: flex; flex-direction: column; align-items: center; gap: 18px; }}
      .kicker-rule {{ display: block; width: 72px; height: 3px; background: {GOLD}; transform-origin: 50% 50%; }}
      .kicker-text {{ display: block; font-family: "Montserrat", sans-serif; font-weight: 600; font-size: 30px; letter-spacing: 0.32em;
                     color: #FFFFFF; text-align: center; line-height: 1.45; text-shadow: 0 1px 3px rgba(0,0,0,0.65), 0 2px 18px rgba(0,0,0,0.6); }}
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
      .cap-box b, .cap-box em {{ font-weight: 800; font-style: normal; color: {GOLD}; }}
      {cap_css}
      /* Carte de fin — § 7 */
      #endcard {{ position: absolute; inset: 0; background: #000000; display: flex; align-items: center; justify-content: center; }}
      #end-logo {{ display: block; width: 520px; height: auto; }}
      #end-cta {{ position: absolute; left: 0; width: {W}px; top: 1250px; text-align: center; font-family: "Montserrat", sans-serif;
                 font-weight: 600; font-size: 30px; letter-spacing: 0.32em; color: #FFFFFF; }}
      #end-cta b {{ font-weight: 800; color: #E6D3A0; }}
      /* Carte de fin sans logo (contenus de formation) : l'appel à l'action seul, au centre */
      #endcard.no-logo #end-cta {{ top: 50%; transform: translateY(-50%); font-size: 46px; }}
      /* Définition d'un sigle (acrostiche) */
      #def {{ position: absolute; inset: 0; }}
      .def-dim {{ position: absolute; inset: 0; background: radial-gradient(ellipse 85% 60% at 50% 45%, rgba(0,0,0,0.55), rgba(0,0,0,0.30)); }}
      .def-col {{ position: absolute; left: 0; right: 0; top: 560px; display: flex; flex-direction: column; align-items: center; }}
      .dl {{ width: 580px; display: flex; align-items: baseline; height: 112px; }}
      .di {{ display: inline-block; width: 96px; text-align: right; padding-right: 4px; font-family: "Montserrat", sans-serif; font-weight: 800; font-size: 92px;
            color: #E6D3A0; text-shadow: 0 0 2px rgba(0,0,0,0.85), 0 2px 10px rgba(0,0,0,0.5); }}
      .dr {{ font-family: "Montserrat", sans-serif; font-weight: 700; font-size: 58px; color: #FFFFFF;
            text-shadow: 0 0 1px rgba(0,0,0,0.55), 0 2px 4px rgba(0,0,0,0.45), 0 6px 20px rgba(0,0,0,0.30); }}
      {def_css}
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
