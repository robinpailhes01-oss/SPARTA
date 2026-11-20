# Analyse Ultimate Performance (@ultimateperformancelive) — novembre 2026

Modèle demandé par le client le 20/11/2026, en priorité pour les témoignages. Ce document complète `ANALYSES.md`, où se trouve l'analyse de af1.
Images clés : `up-2026-11/keyframes/`. Les vidéos ne sont pas commitées.

## Corpus et limites

- **8 vidéos analysées**, plus af1, déjà analysée dans `ANALYSES.md`. La plus longue des 3 vidéos Instagram est en fait la version complète d'af1.
  - **3 reels Instagram récents** : `DdUTezAFSJP` (af1 complète, « I couldn't even walk »), `DfuQ16Cmfgd` (« 165 hours », message d'un dirigeant) et `DfpAY7vCndy` (témoignage d'Alex, dentiste). Les deux premiers ont été envoyés par le client.
  - **5 TikTok de 2024** du même compte : Jen (−33 kg), Jamie Lomas, Gemma Atkinson, Mark Owen et Lamorne Morris.
- **Pourquoi pas plus de reels Instagram** :
  - Sans connexion, Instagram n'expose que les 6 dernières publications, dont 2 vidéos.
  - YouTube bloque le téléchargement (« confirm you're not a bot »).
  - Le quota Apify est épuisé.
  - Les TikTok, plus anciens (2024), complètent le corpus. Ils ont un ton « célébrité » plus appuyé.
- **Méthode** :
  - Coupes : ffmpeg, scène > 0,25, coupes de moins de 0,3 s fusionnées.
  - Transcription : faster-whisper medium.
  - Musique : niveau mesuré dans les trous de parole, pas écoutée.
  - Tailles : en pixels sur une base 1080 × 1920. Les fichiers Instagram sont en 720 × 1280, donc les tailles sont à ±10 %.

## Tableau

| | af1 / DdUTezAFSJP | DfpAY7vCndy (Alex) | DfuQ16Cmfgd (165 h) | tt Jen | tt Lamorne | tt Gemma | tt Jamie | tt Mark Owen |
|---|---|---|---|---|---|---|---|---|
| Type | témoignage cliente + coach | témoignage client | message de la marque | coach + cliente | célébrité | célébrité | célébrité | célébrité |
| Durée | 78,2 s | 38,2 s | 66,1 s | 48,6 s | 29,4 s | 57,4 s | 56,2 s | 61,8 s |
| Plans / durée moyenne | 32 / 2,4 s | 24 / 1,6 s | 38 / 1,7 s | 21 / 2,3 s | 15 / 2,0 s | 43 / 1,3 s | 37 / 1,5 s | 44 / 1,4 s |
| 1er mot | 0,0 s | 0,0 s | 0,0 s | 0,0 s | 0,2 s | 0,0 s | 9,4 s | 3,8 s |
| Accroche | la douleur (« I was in a wheelchair ») + photo d'archive à 2,5 s | le bénéfice (« a better gift ») | l'idée choc (« 165 hours ») | le chiffre (« 100 kg → 67 kg ») | une réplique drôle | une séance (rire) | le physique final | une séance |
| Texte à l'écran en ouverture | aucun | aucun | aucun | aucun | nom en surimpression, titre « U.P. JOURNEY » | aucun | aucun | logo |
| Part de plans de coupe | ≈ 45 % | ≈ 47 % | ≈ 46 % | ≈ 59 % | ≈ 55 % | ≈ 50 % | ≈ 60 % | ≈ 60 % |
| Sous-titres | oui | oui | oui | oui | non | non | non | non |
| Musique (écart parole / trous) | fond continu (−7 dB) | fond continu (−3 dB) | fond continu, parole sans trou | fond continu | musique + parole | ambiance | ambiance | ambiance |
| Loudness | −14,1 LUFS | −14,2 | −14,3 | −12,9 | −14,4 | −31 (sans normalisation) | −23,7 | −23,3 |
| Fin | carte noire, petit logo « UP » blanc, ≈ 2,5 s | carte noire, petit logo « UP » blanc, ≈ 4 s | carte noire, petit logo « UP » blanc, ≈ 2,5 s | logo UP rouge + bouton « ENQUIRE NOW » | logo + « Watch the full video on YouTube » | logo UP rouge | (non vue) | logo UP rouge |

Les 4 vidéos sans sous-titres sont des TikTok : l'appli ajoutait les sous-titres automatiques.

## Ce qui revient (points communs), par impact

1. **On ouvre sur une phrase forte, sans titre.**
   - Dans 6 vidéos sur 8, le premier mot tombe à moins de 0,3 s.
   - C'est la personne elle-même qui pose la douleur, le chiffre ou l'idée.
   - Aucune des 3 vidéos Instagram n'a de titre ni d'accroche écrite en haut de l'image : **la phrase dite est l'accroche**.
2. **Le visage est toujours entier et dégagé.**
   - En plan serré, le haut du crâne est à 8–15 % de la hauteur et les yeux à 25–33 %.
   - En plan large, la tête est dans le tiers haut avec de l'air au-dessus.
   - Aucun texte, logo ou graphique ne passe sur la tête ou le visage : les seuls textes sont les sous-titres, sur le buste.
3. **Les sous-titres sont discrets et neutres.**
   - Une ligne de 2 à 4 mots, en sans-serif moyen (proche Inter ou SF Pro Medium).
   - Corps ≈ 38–40 px pour 1080 de large, en blanc pur.
   - Sans bandeau, sans couleur de mot-clé, sans animation.
   - Centrés à **y ≈ 71 % de la hauteur** (≈ 1365 px sur 1920), sur le buste.
   - Seule l'ancienne vidéo af1 avait un léger bandeau ; les reels de 2025-2026 n'en ont plus.
4. **Le montage est rapide et vivant.**
   - Plans de 1,3 à 2,4 s (médiane ≈ 1,7 s), parole presque sans trou (respirations coupées).
   - On alterne en coupe sèche large et serré, de face et de trois-quarts. Chaque interview est tournée à deux angles, ou recadrée de façon nette.
5. **Environ 50 % de plans de coupe, toujours illustratifs.**
   - L'exercice ou le geste dont on parle est montré au moment où il est dit (split squat, poignée de main, coach qui corrige).
   - Ce sont des plans de séance réels avec le coach dans le champ, jamais des plans d'ambiance vides.
6. **La preuve est concrète.**
   - Un chiffre dit à l'oral : « 23 kg down », « 100 kg → 67 kg », « 41 sessions », « 55 years old ».
   - Quand c'est possible, un objet le rend visible : un disque de 20 kg porté dans les bras, une photo d'archive.
   - Le chiffre n'est pas mis en graphique.
7. **La relation coach-client est visible.**
   - On voit le coach et l'adhérent ensemble : plan à deux debout, main sur l'épaule, rires.
   - Le coach parle aussi, environ 30 à 50 % du temps.
8. **Fond musical continu, sous la voix.**
   - Cinématique, sans temps forts audibles, environ 3 à 7 dB sous la parole.
   - −14 LUFS intégrés sur les vidéos Instagram.
9. **Fin sobre.**
   - Carte noire de 2,5 à 4 s avec un petit logo blanc centré, sans appel à l'action, sur les vidéos Instagram récentes.
   - Les TikTok ajoutaient « ENQUIRE NOW » ou un renvoi vers YouTube.
10. **Image de cinéma.**
    - Faible profondeur de champ, étalonnage sombre et contrasté.
    - La couleur de la marque (rouge) est présente dans le décor et sur les tenues, pas en graphisme.
    - Transitions : coupe franche. De temps en temps, un filé (flou de bougé) ou un flash de lumière, au plus une fois par vidéo.

Ce qu'on ne voit pas chez eux : schémas, pictogrammes, compteurs, titres en haut d'écran, mots-clés colorés, zooms animés. Seules exceptions, les surimpressions de nom et de titre de la série célébrité (TikTok Lamorne).

## À appliquer à nos témoignages Sparta (par rapport à aujourd'hui)

| Sujet | Sparta aujourd'hui | Ce qu'on retient d'UP | Changement proposé |
|---|---|---|---|
| Accroche | Titre écrit en haut sur 7 témoignages sur 11, 64 px, sur voile sombre, pendant 4 à 6,5 s (ex. « Eline, 21 ans · −14 kg en 3 mois »). **Sur les plans serrés, il recouvre le haut de la tête** (voir `sparta_eline_1.5s_titre_sur_la_tete.jpg`). | Pas de titre : la première phrase forte de l'adhérent·e suffit. | Supprimer le titre du haut, ou le réduire à une ligne courte placée **sous le menton ou sur le buste, jamais sur la tête**, 2 s max. Commencer sur la phrase la plus forte (douleur ou chiffre). |
| Cadrage | Recadrages serrés qui collent parfois le haut du crâne au bord de l'image. | Tête entière, haut du crâne à 8–15 % de la hauteur, yeux au tiers haut. | Régler l'origine du cadre et le zoom pour garder au moins 8 % d'air au-dessus de la tête. Vérifier sur une capture par plan avant chaque rendu. |
| Sous-titres | Montserrat 700, 52 px, mots-clés or, halo ; centrés à y ≈ 1250–1340 px (65–70 %). | Blanc simple, ≈ 40 px, sans couleur, à y ≈ 1365 px (71 %). | Garder Montserrat (charte), mais passer en 600–700, 44–46 px, blanc. Or seulement sur le chiffre clé, pas sur 3 ou 4 mots-clés. Placer à y ≈ 1360 px. |
| Rythme | Plans de 2,4 à 2,7 s ; une seule caméra, alternance large et serré par recadrage. | 1,3 à 2,4 s, parole sans trou. | Couper les respirations et les hésitations, alterner large et serré toutes les 1,5 à 2,5 s (coupe nette, sans zoom animé : déjà fait). |
| Plans de coupe | **Aucun** dans 5 témoignages sur 11 (Eline, Manon, Lisa, Anaïs, Daisy : face caméra seule). Julien a 7 plans de coupe, Jennifer 5, soit environ 25–35 % du temps. | ≈ 50 %, illustratifs, coach et adhérent en séance. | Intercaler des plans de séance du même adhérent avec Lucas (rushes « séances » sur le Drive) sur les phrases qui parlent d'entraînement. À tourner si on ne les a pas : c'est l'écart le plus visible. |
| Coach à l'image | Témoignage seul face caméra. | Coach et client ensemble, échange et rire. | Pour les prochains tournages : un plan à deux, et une ou deux phrases du coach. |
| Preuve | Chiffre dit à l'oral et écrit dans le titre. | Chiffre dit à l'oral + objet ou photo qui le montre. | Garder le chiffre à l'oral et en sous-titre (en or). Si possible, photo avant/après ou objet (disque du poids perdu). |
| Musique | Fond léger (spec C, −20 dB sous la voix), −14 LUFS. | Fond continu, plus présent (−3 à −7 dB). | Garder le fond léger que le client a validé ; on peut monter de 3–4 dB si le témoignage est très calme. |
| Fin | Carte noire avec logo Sparta. | Carte noire, petit logo blanc, 2,5–4 s. | Rien à changer : déjà dans l'esprit. |
| Graphismes | Accroche, schémas (sur les reels de formation). | Aucun sur les témoignages. | Aucun schéma sur les témoignages. Les schémas restent réservés aux reels de formation, jamais sur la tête. |

## Ordre conseillé pour l'essai sur nos vidéos

1. Sur un témoignage déjà monté (ex. Eline), sans retourner :
   - retirer le titre du haut ;
   - remonter la phrase la plus forte en ouverture ;
   - sous-titres plus discrets à 71 % ;
   - zoom réglé pour garder la tête entière ;
   - respirations coupées.
2. Comparer côte à côte avec la version actuelle avant de généraliser.
3. Les plans de coupe illustratifs et le coach à l'image demandent des rushes de séance avec l'adhérent : à vérifier sur le Drive, sinon à prévoir au prochain tournage.
