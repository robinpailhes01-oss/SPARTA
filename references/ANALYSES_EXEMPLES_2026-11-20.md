# Exemples envoyés par le client (20/11/2026) : analyse et « mix » pour nos témoignages

Images clés : `references/exemples-2026-11-20/keyframes/`. Vidéos non commitées (dans le scratchpad). Analyse d'Ultimate Performance détaillée dans `ANALYSES_UP_2026-11.md`.

## Méthode et limites

- Les vidéos viennent de la page « embed » d'Instagram. Résolution : 720×1280, sauf **Sébastien (DXZtB3ZCG3L) en 360×640**. Les tailles en px sont ramenées à une largeur de 1080, à ±10 %.
- Coupes : détection automatique (ffmpeg, seuil 0,22), vérifiée sur des planches à 1 ou 2 i/s. Effets : pics de luminance image par image et saturation moyenne.
- Son : séparation voix / reste avec demucs (htdemucs). La piste « reste » mélange musique, ambiance de salle et bruitages. L'écart est mesuré en médiane RMS sur des fenêtres de 0,5 s pendant la parole. Les bruitages sont repérés par les transitoires de la piste « reste » ; je ne peux pas écouter, donc leur nature est déduite.
- Transcription : faster-whisper (medium pour Sébastien, small pour les autres), en français.

## Tableau

| | **Sébastien (DXZtB3ZCG3L)** ★ | Mickaël (DZCm7EZo_Fo) | Xavier (DaNzYPponGU) | Back at it (DQjOOHOiI0O) | Joy (DO3JCqdiKok) | Adrien (DPtHJ2rCNek) | UP (2 reels) |
|---|---|---|---|---|---|---|---|
| Type | coach + adhérent debout, puis coach seul devant le mur logo | coach + adhérent debout | coach + adhérent debout | adhérent seul, plan serré mobile | adhérente seule devant le mur végétal, questions écrites | adhérent puis coach, face caméra | coach + client, client seul |
| Durée | 84,8 s | 48,1 s | 43,8 s | 43,2 s | 57,0 s | 132,1 s | 66–78 s |
| Plans / durée moyenne | ≈ 45 / **1,9 s** | ≈ 15 / 3,2 s | ≈ 19 / 2,3 s | ≈ 16 / 2,7 s | ≈ 10 / 5,7 s | ≈ 45 / 2,9 s | 1,6–2,4 s |
| Ouverture (0–3 s) | parole dès 0 s, **plan à deux**, pas de titre | **5 plans de séance de 0,5 s** sur la musique seule | idem, 4–5 plans de 0,5 s | séance + visage, parole à 2,8 s | logo + slogan écrit en haut, sur la tête | parole dès 0 s, sous-titre en majuscules | parole dès 0 s, pas de titre |
| Part de plans de séance | **≈ 60 %** | ≈ 35 % | ≈ 45 % | ≈ 40 % | ≈ 25 % | ≈ 30 % | ≈ 45–50 % |
| Étalonnage | **noir et blanc froid** sur toute la vidéo (saturation 3/255) | couleur ; plans de séance en N&B par moments | couleur ; N&B par moments | couleur légèrement désaturée | couleur ; N&B sur les questions | couleur | sombre, contrasté |
| Sous-titres | **2 lignes : ligne 1 fine, ligne 2 extra-grasse**, blanc, ≈ 40 px, y ≈ 64 %, **mot par mot** | fins, crème, ≈ 48 px, y ≈ 50 %, 2–4 mots, sans gras | idem Mickaël | **1 mot à la fois**, MAJUSCULES grasses, ≈ 32 px, bas | encadré jaune en haut, **sur la tête** ✗ | MAJUSCULES grasses, 1–3 mots, buste | blanc ≈ 40 px, y ≈ 71 % |
| Effets | **filé + blanc sur 2 images** aux changements de lieu (42,3 / 45,0 / 52,8 / 54,9 / 64,7 / 82,8 s), **poussées rapides** sur les disques, gros plans mains/barres, angles bas et inclinés | **fuite de lumière orange** (≈ 0,2 s) ×3, carte avant/après en bas | fuite de lumière ×3, ralentis | flash blanc de 2 images à presque chaque coupe | fuite de lumière orange ×6, cartes « question » | flash blanc 2 images ×15 | au plus 1 effet par vidéo |
| Son | **pas de musique audible** : la piste « reste » est à **−22 dB sous la voix**, c'est le **son réel de la salle** (charges, poulies) qui saute à chaque plan de séance | musique forte en ouverture (−16 dB), puis **−7 dB sous la voix**, remontée sur le logo | musique au niveau de la voix (−0,6 dB) | musique au niveau de la voix, forte en fin | musique −8 dB | musique −6 dB, rythmée (≈ 110 BPM) | −3 à −7 dB |
| Fin | **pas de carte** : finit sur un plan de séance (disques) qui s'enfonce, phrase du coach | logo Sparta or sur noir, ≈ 2 s | logo Sparta, ≈ 2 s | CTA « Réserve ton bilan forme offert via le lien en bio 🔥 » + logo | carte CTA « Envie de changement ? » + logo, 5 s | carte CTA « Tu veux te lancer chez Sparta ? », puis écran CapCut | carte noire + petit logo |

## Sébastien (DXZtB3ZCG3L), seconde par seconde : pourquoi il marche

| t (s) | Ce qu'on voit / entend |
|---|---|
| 0–4,6 | Plan à deux (Sébastien, Jean-Marie), debout, en entier, tête dégagée. Parole dès 0 s : « Je suis accompagné de Jean-Marie… ». Sous-titres mot par mot. |
| 4,6–19 | Une phrase = un plan de séance qui illustre exactement le mot (« intensités » → poulie, « performance » → barre, « s'étoffer » → haltère en gros plan). Plans de 1,1 à 2,1 s, angles bas, cadres inclinés, gros plans mains et disques. Le son de la salle (cliquetis, poulies) est gardé sous la voix. |
| 19–51 | Question / réponse à deux, alternée avec des plans de séance (≈ 1 plan de séance pour 1 plan d'interview). Le chiffre clé (« 2 kilos en 2 mois et demi ») tombe sur un gros plan de charges. |
| 51–55 | Changement de lieu : **filé (flou de mouvement) + 2 images blanches**, puis Sébastien seul devant le mur logo Sparta. |
| 55–84 | Sébastien explique sa méthode, coupé toutes les 1,5–2 s par des plans de séance ; deux autres filés + flash aux changements de lieu. |
| 82,8–84,8 | Dernier plan : poussée lente sur les disques, la phrase se termine (« …les protocoles d'entraînement »), **sans carte de fin**. |

Ce qui le rend excellent :
1. **Le son réel de la salle**, sans musique qui le couvre : ça fait « vrai », on est dans la séance.
2. **Le noir et blanc froid** sur tout : homogène, premium, il gomme les écarts de lumière entre plans.
3. **Les effets sont rares mais placés** : filé + flash seulement aux changements de lieu, poussées rapides sur les gros plans de charges.
4. **Les plans de séance illustrent chaque mot** et sont variés (gros plans, angles bas, inclinés).
5. **Les sous-titres sur 2 lignes** (fin / gras), mot par mot, sur le buste : lisibles sans couvrir.

## Points communs Sparta (6 vidéos)

1. Parole ou séance dès la 1re seconde ; jamais de long titre en ouverture (sauf Joy, où il est sur la tête).
2. Plans de séance réels avec le coach dans le champ, 30–60 % du temps.
3. Plan à deux debout (coach + adhérent), en pied ou à mi-corps, tête entière.
4. Un effet « signature » répété aux transitions : fuite de lumière orange (Mickaël, Xavier, Joy) ou flash blanc de 2 images (Adrien, Back at it, Sébastien).
5. Passages en noir et blanc pour les plans de séance (tout en N&B chez Sébastien).
6. Sous-titres blancs, sans fond, courts (1 à 4 mots), sur le buste ou au centre.
7. −14 LUFS, musique de fond (sauf Sébastien : son réel).
8. Fin : logo Sparta or sur noir (2 s) ou carte « bilan forme offert / lien en bio ».

## Le « mix » recommandé pour nos témoignages (recette)

Base : **Sébastien** (son réel, N&B, effets aux transitions), **ouverture Mickaël/Xavier**, sous-titres « 2 lignes » de Sébastien, fin logo or. Tête toujours entière, aucun texte dessus.

| Bloc | Recette concrète | Où dans notre pipeline |
|---|---|---|
| Ouverture (0–2,5 s) | 4–5 plans de séance de 0,45–0,55 s, coupes franches, son réel de la salle + musique forte (ou rien). Pas de titre. Première phrase forte dès 2,5 s. | `format_base.py` (déjà écrit : préroll). Ajouter le son des plans au lieu du silence. |
| Rythme | Plans de 1,5–2,2 s ; couper respirations et hésitations ; 1 plan de séance pour 1 plan d'interview (≈ 50 %). Chaque plan de séance illustre le mot dit. | `plan.json` (`broll`, `at` sur le mot), `engine.py` (chaînage déjà géré). |
| Étalonnage | Option A (Sébastien) : tout en N&B froid (`hue=s=0`, contraste +8 %, légère teinte bleue dans les noirs). Option B (Mickaël) : couleur pour l'interview, N&B seulement sur les plans de séance. | `grade` / `data-color-grading` dans `engine.py` (filtre CSS `grayscale(1) contrast(1.08)`), ou ffmpeg en sortie. À faire valider (A ou B). |
| Sous-titres | Blanc, sans fond, sans couleur. 2 lignes max : ligne 1 Inter/Montserrat 400, ligne 2 Montserrat 800 ; ≈ 42 px ; y ≈ 1230 px (64 %) ; apparition mot par mot. Jamais sur la tête : en plan serré, rester sous le menton. | Nouveau `cap_style` dans `engine.py` (le style `karaoke` fait déjà le mot par mot ; ajouter fin/gras par ligne). |
| Effets | **Filé + flash blanc** : flou directionnel 3 images + 2 images blanches (0,07 s) **uniquement aux changements de lieu** (2–3 par vidéo). **Poussée rapide** ×1,15 en 0,4 s sur 2–3 gros plans de charges. Fuite de lumière orange (0,25 s) seulement si une carte avant/après apparaît. | `flash` existe dans `engine.py` (un seul) → l'étendre à une liste + flou ; poussée = `fromTo scale` sur le plan de séance. |
| Son | **Garder le son des plans de séance** (charges, poulies) à **−20 à −22 dB sous la voix** ; pas de musique, ou une musique très basse (−24 dB) si le témoignage est calme. Pas de bruitages ajoutés : chez Sébastien, les « impacts » aux coupes sont le son réel des plans. | Aujourd'hui les plans de séance sont `muted` : ajouter un volume (≈ 0,08–0,1) dans `engine.py`, puis `mix_audio.py` avec `music_rel` −24 ou sans musique. |
| Avant/après | Carte blanche en bas au centre (comme Mickaël), entre 3 et 6 s, apparition par fuite de lumière orange. Jamais sur la tête. | `proof` dans `engine.py`, repositionné en bas. |
| Fin | Dernière phrase sur un plan de séance qui s'enfonce lentement, puis logo Sparta or sur noir 1,5–2 s (pas de CTA, comme validé). | `end_card` (déjà). |

## Ce qui demande des rushes qu'on n'a pas

- **Plan à deux debout coach + adhérent** : on l'a pour Julien et Jennifer, pas pour Eline, Manon, Lisa, Anaïs et Daisy (assises seules devant le mur).
- **Plans de séance de l'adhérent·e** (gros plans mains, charges, angles bas) : on en a pour Julien et Jennifer (≈ 7 et 5 plans), **aucun** pour Eline, Manon, Lisa, Anaïs, Daisy.
- **Son réel de la salle** : présent dans les rushes de séance DJI (à vérifier plan par plan). Absent si les rushes sont muets.
- **Plan du coach seul devant le mur logo** (Sébastien) : non tourné pour nos témoignages.
- **Photos avant/après** : non fournies, à part celles de l'ancien montage.

Conclusion : le mix complet est faisable tout de suite sur **Julien et Jennifer**. Pour les 5 témoignages assis, seuls l'étalonnage, les sous-titres, le rythme et la fin sont applicables sans nouveau tournage.

## Anti-exemple

- **Joy (DO3JCqdiKok)** : bandeau logo et sous-titres encadrés jaunes **en haut, sur la tête**, et plan unique de 5,7 s en moyenne. À ne pas reproduire.
