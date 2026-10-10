# Analyse des vidéos de référence — Sparta

Vidéos sources dans `references/deja-fait/` (df1–df3) et `references/a-faire/` (af1). Les vidéos ne sont pas commitées (`.gitignore`).
Pour chaque vidéo, on commite les images clés compressées (`keyframes/`) et la transcription (`*.transcript.txt` ; mots horodatés dans `*.transcript.json`).

## Méthode et limites (à lire avant les chiffres)

- **3 vidéos sur 4 sont des enregistrements d'écran iPhone de l'appli Instagram** (1206×2622, HEVC 60 i/s) : af1, df2, df3. Elles contiennent l'interface Instagram (boutons, pseudo, légende, barre du bas) et pas le fichier source. Seule df1 est un vrai export 9:16 (464×832, 60 i/s, 1,6 Mb/s, donc en basse définition).
- Pour convertir en pixels d'une vidéo 1080×1920, on suppose qu'Instagram remplit l'écran en hauteur (facteur 2622/1920 = 1,366, côtés rognés). Les tailles en px de af1, df2 et df3 sont donc des **estimations à ±10 %**.
- **af1 s'arrête net à 75 s, au milieu d'une phrase** (« It's about making sure that you're fit and… »). On ne voit ni la fin, ni la carte de fin, ni l'appel à l'action.
- Les coupes ont été détectées automatiquement (ffmpeg, seuil de changement de scène 0,25, coupes < 0,3 s fusionnées) puis vérifiées image par image. Les recadrages sur un même plan (punch-in) sont parfois sous-comptés.
- La musique a été estimée par mesure du niveau dans les silences de parole. **Je n'ai pas pu l'écouter**, donc la présence et le style de musique sont à confirmer.
- Transcription : Whisper `small` (FR pour df1–df3, EN pour af1). Les noms propres et les chiffres sont approximatifs (ex. df2 « 21 % → 9 % de masse grasse »).

## Tableau de synthèse

| | af1 (cible) | df1 | df2 | df3 |
|---|---|---|---|---|
| Compte | @ultimateperformancelive (UK) | Sparta | @sparta_coaching_montpellier | @sparta_coaching_montpellier |
| Langue | anglais | français | français | français |
| Durée | ≥ 75,0 s (tronquée) | 43,7 s | 45,9 s | 86,3 s |
| Plans | 33 | 16 | 12 | 47 |
| Durée moyenne d'un plan | 2,27 s | 2,73 s | 3,82 s | 1,84 s |
| Durée médiane / max d'un plan | 2,0 s / 7,3 s | 2,7 s / 6,1 s | 2,4 s / **15,7 s** | 1,8 s / 5,4 s |
| Débit de parole | 3,4 mots/s | 4,1 mots/s | 3,8 mots/s | 4,4 mots/s |
| Premier mot prononcé | 0,0 s | 2,0 s | 2,1 s | 0,0 s (en milieu de phrase) |
| Qui parle en premier | l'adhérente (sa douleur) | le coach (présentation) | le coach (présentation) | le coach (présentation) |
| Loudness intégrée | −12,6 LUFS | −15,5 LUFS | −12,5 LUFS | −12,9 LUFS |
| Sous-titres : position (centre, % de la hauteur) | **72 %** | 50 % | 45 % | 57 % |
| Sous-titres : fond | bandeau noir ≈ 50 % | aucun | aucun | aucun |

---

## af1 — cible (Ultimate Performance, « I couldn't even walk »)

Images : `a-faire/keyframes/`.

**Format** : 9:16, ≥ 75 s, 33 plans de 2,0 s (médiane). Seul plan long : 7,3 s (30–37 s, le fou rire « Brazilian bum lift »). Tournage à 2 caméras (plan large à deux et plan serré sur la personne qui parle), avec punch-in fréquents (12 s large → 13 s serré → 14 s large). Optique ciné, faible profondeur de champ, étalonnage sombre et contrasté, accents rouges de la marque (logo UP sur le polo, machines rouges).

**Structure**
| t (s) | Bloc | Contenu |
|---|---|---|
| 0–4 | **Accroche** | L'adhérente, en plan serré : « I had bilateral hip surgery and I was in a wheelchair. » À 2,5 s, flash vers une **photo d'archive** (elle en fauteuil roulant, avec béquilles), plus une lumière parasite orange/verte à 4 s. La douleur et la preuve visuelle arrivent en moins de 4 s. |
| 4–15 | Envie | « I wanted to walk again / to train », puis le coach : « more scared, less confident ». Retour sur elle : « I couldn't even walk. » |
| 15–31 | Méthode et progrès | Le coach raconte la progression (« split squats », « step up », « more range »). **Chaque exercice cité est montré en plan de coupe au moment où il est dit.** |
| 32–40 | Respiration et humour | « I wanted a Brazilian bum lift » / « Just do some split squats. That's it. » Fou rire à deux, plan de 7,3 s laissé en entier. |
| 41–57 | Le « pourquoi » | Le coach, face caméra, explique sa méthode (« the why sets everything up »). Plans de coupe d'exercices intercalés. |
| 57–65 | **Preuve chiffrée** | Elle tient un disque de 20 kg : « I had to carry that around every day. Now I can't even lift it. » Puis « I'm 23kg (50lbs) down. » La métaphore visuelle rend le chiffre concret. |
| 65–75+ | Conclusion | « The focus on health… it's not about image. » La vidéo coupe avant la fin, donc l'appel à l'action est **inconnu**. |

**Sous-titres** (`af1_soustitre_detail.jpg`)
- Une seule ligne, 2 à 5 mots (≤ 24 caractères), segmentée par groupe de sens.
- Police sans-serif géométrique semi-bold (proche Montserrat SemiBold / Proxima Nova Semibold), blanc `#F8F8F7`.
- Taille ≈ 44 px pour une largeur de 1080 (hauteur de capitale ≈ 32 px).
- Bandeau rectangulaire noir derrière le texte, opacité ≈ 50 % (le fond passe de 38 à 18 de luminance), hauteur ≈ 66 px, marge latérale ≈ 12 px, coins à peine arrondis.
- Centré horizontalement. Centre vertical à y ≈ 1390 / 1920 (72 %), juste au-dessus de la zone occupée par l'interface Instagram.
- Aucun mot mis en couleur et aucune animation : apparition et disparition sèches, calées sur la parole.
- Chiffres écrits en chiffres, avec l'unité (« 23kg (50lbs) »).

**Plans de coupe** : environ 45 % du temps à l'écran, toujours **illustratifs du mot prononcé** (split squat, step up, rowing), filmés pendant une vraie séance avec le coach dans le champ. Ils ne sont jamais décoratifs.

**Audio** : −12,6 LUFS. Voix très présente. Dans les silences, le niveau descend à −31 dBFS (p10) contre −16 dBFS pour la parole : s'il y a une musique, elle est au moins 15 dB sous la voix. Aucun rythme net détecté.

**Transitions** : coupes franches, plus **un seul effet** (flash et lumière parasite à 2,5–4,5 s sur la photo d'archive).

**Branding** : pas de bandeau prénom/salle, ni de logo incrusté pendant les 75 s visibles. La marque est **dans l'image** (polo UP du coach, logo sur les disques, mur de logo). Le titre du post reprend la citation d'accroche : « "I couldn't even walk" ».

---

## df1 — Sparta, Xavier (≈ 1 an de coaching, santé/anti-stress)

Images : `deja-fait/keyframes/df1_*`.

- **Format** : export 464×832 (**trop basse définition**), 43,7 s, 16 plans de 2,7 s en moyenne.
- **Structure** : 0–2 s, montage muet de 4 plans d'entraînement de 0,5 s (accroche visuelle, sans parole). À 2 s, le coach : « Alors salut à tous, aujourd'hui je suis avec Xavier… » (présentation). 20–38 s, Xavier : reprise à 60 ans, coach personnel, « bulle de bien-être ». 38 s, lumière parasite. 39–42 s, poignée de main. 42–43,7 s, carte de fin.
- **Sous-titres** : 1 à 3 mots, police système type SF Pro Regular, blanc, légère ombre portée, pas de fond, environ 48 px pour 1080 de large, centrés à 50 % de la hauteur, donc **sur les corps**. Les nombres sont en gras (« **10** ans »). Apparition sèche.
- **Plans de coupe** : environ 50 % du temps, exercices avec le coach (bonne pratique). 14–16 s : une salle vide sans personne (plan de coupe faible).
- **Audio** : −15,5 LUFS, musique discrète au début (−23 dBFS avant la parole).
- **Branding** : logo Sparta (casque doré et « SPARTA ») en haut à droite de 37 à 42 s, environ 110 px de large pour 1080. **Carte de fin** de 1,5 s : fond `#000000`, casque doré (or moyen `#8E7247`, clair `#C3B486`, foncé `#765D33`), mot « SPARTA » blanc `#E0E0E0` et « CENTRE DE COACHING PRIVÉ ». Le logo fait 48 % de la largeur, centré entre 40 et 60 % de la hauteur, avec un fondu de sortie.
- **Décor** : salle claire, gazon vert, mur végétal, roll-up Sparta en fond. Plans larges en pied, filmés à l'iPhone.

## df2 — Sparta Montpellier, Mikaël (43 ans, 4 mois, 21 % → 9 % de masse grasse)

Images : `deja-fait/keyframes/df2_*`.

- **Format** : 45,9 s, 12 plans, moyenne 3,8 s. **Plan fixe de 15,7 s** (10,6–26,3 s) : les deux hommes debout, cadrés en pied, sans changement.
- **Structure** : 0–2 s, montage muet (4 plans). 2 s, « Donc aujourd'hui on est avec Mika… ». **3–6 s, photo avant/après incrustée** (encadré blanc, fond noir, environ 38 % de la largeur) : c'est la meilleure preuve de toutes les vidéos actuelles. Ensuite Mikaël parle, puis le coach conclut : « Félicitations… On continue comme ça. »
- **Sous-titres** : 1 à 3 mots, sans-serif fine (type SF Pro Light), blanc, sans fond, environ 52 px, centrés à 45 % de la hauteur.
- **Audio** : musique **au niveau de la voix ou plus fort**. Niveau médian dans les silences −14 dBFS contre −20 dBFS pour la parole, et −12 dBFS avant le premier mot. Shazam a été lancé pendant l'enregistrement (« Aucun morceau trouvé »).
- **Transitions** : lumière parasite orange à 10 s.
- **Branding** : « SPARTA / CENTRE DE COACHING PRIVÉ » en surimpression qui apparaît en fondu sur le dernier plan (45 s), sans carte de fin séparée. Coachs en survêtement noir avec le logo.

## df3 — Sparta Montpellier, Jean-Marie (2,5 mois, prise de masse, coach Sébastien)

Images : `deja-fait/keyframes/df3_*`.

- **Format** : 86,3 s (trop long), 47 plans, moyenne 1,84 s (**le rythme le plus proche de la cible**).
- **Structure** : **démarre au milieu d'une phrase** (« …de Jean-Marie »), donc l'introduction a été coupée. Le coach parle environ 60 % du temps. Témoignage de Jean-Marie de 20 à 50 s (« chez Sparta on donne tout »). Fin sur un plan de coupe de disque, sans conclusion ni carte de fin.
- **Sous-titres** (`df3_soustitre_detail.jpg`) : **2 lignes**. Ligne 1 en sans-serif regular blanche, ligne 2 en **gras noir/heavy** blanc. Effet karaoké : les mots pas encore prononcés sont en gris (≈ 60 % d'opacité) et passent au blanc quand ils sont dits. Environ 40 px pour 1080, centrés à 57 % de la hauteur. C'est le seul style animé.
- **Plans de coupe** : environ 65 % du temps, **étalonnés en noir et blanc** (ralentis sur les efforts, gros plans de mains et de disques). Rendu le plus « premium » des trois.
- **Audio** : −12,9 LUFS, voix dominante, aucun rythme musical détecté (musique très basse ou absente).
- **Branding** : aucun logo incrusté visible. T-shirts noirs « SPARTA » et d'autres marques (SOCRI) portés par les coachs.

---

## Constats transverses

1. **Accroche** : les 3 vidéos Sparta s'ouvrent sur le coach qui présente (« aujourd'hui je suis avec… »), ou en milieu de phrase. La cible s'ouvre sur **la douleur de l'adhérente, à la première personne, avec une preuve visuelle**, en moins de 4 s.
2. **Sous-titres** : 3 styles différents sur 3 vidéos, aucun avec un fond, tous placés au milieu de l'image sur les visages et les corps. La cible a un style unique, lisible, posé à 72 % de la hauteur.
3. **Preuve** : les chiffres existent chez Sparta (21 → 9 %, +2 kg de muscle, 1 an, 60 ans) mais restent noyés dans le discours. Seule df2 les montre (avant/après). La cible construit un moment dédié à la preuve (disque de 20 kg puis « 23 kg »).
4. **Image** : Sparta filme en plan large, en pied, à l'iPhone, dans une lumière plate. La cible utilise des plans moyens et serrés, deux axes, des punch-in et un étalonnage contrasté. df3 (plans de coupe en noir et blanc) est l'exception déjà proche.
5. **Musique** : de « au niveau de la voix » (df2) à « absente » (df3). La cible la garde inaudible ou presque.
6. **Branding** : la carte de fin noire avec le casque doré (df1) est propre et identifiable, mais elle n'est utilisée que dans une vidéo sur trois.
