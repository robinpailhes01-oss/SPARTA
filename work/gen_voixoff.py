"""Génère les plans des reels « voix de l'interview sur les images de séance » (13, 14, 15)."""
import json, os
SD = 'rushes/seances/'
def f(n): return SD + [x for x in os.listdir(SD) if f'_{n}_D' in x][0]
P = {"0347": "rushes/interview/DJI_20261026180353_0347_D.MP4", "0349": "rushes/interview/DJI_20261026180503_0349_D.MP4",
     "0298": "rushes/interview/DJI_20261026170411_0298_D.MP4"}
def reel(name, titre, hook, morceaux, pool):
    mor, broll, k = [], [], 0
    for i, (pr, a, b, qui, texte) in enumerate(morceaux):
        mor.append({"prise": pr, "in": a, "out": b, "qui": qui, **({"texte": texte} if texte else {})})
        n = max(1, round((b - a) / 2.4)); dur = round((b - a) / n, 3)
        for j in range(n):
            clip, de = pool[k % len(pool)]; k += 1
            broll.append({"src": f(clip), "de": de, "morceau": i, "at": round(a + j * dur, 3), "dur": dur})
    d = {"title": titre, "fps": 30, "modele": "large-v3", "prises": {p: P[p] for p in {m[0] for m in morceaux}},
         "morceaux": mor, "broll": broll,
         "edl": {"cap_style": "epure", "cap_max_chars": 26, "hook": {"text": hook, "dur": 4.5},
                 "end_card": {"logo": "assets/brand/logo_or_blanc.png", "dur": 2.0}, "keywords": []}}
    os.makedirs(f'videos/{name}', exist_ok=True)
    json.dump(d, open(f'videos/{name}/plan.json', 'w'), ensure_ascii=False, indent=1)
    print(name, len(mor), 'morceaux,', len(broll), 'plans de coupe,', round(sum(m[2]-m[1] for m in morceaux), 1), 's')

reel('reel13-jennifer-seance', 'Jennifer en séance — Sparta', "Jennifer, 40 ans | **plus à l'aise** à la salle",
     [("0347", 12.38, 19.17, "J", None),
      ("0349", 10.46, 15.28, "J", None),
      ("0349", 15.38, 18.65, "J", "Et puis, je suis plus à l'aise maintenant à la salle quand j'y vais."),
      ("0349", 18.75, 25.12, "J", "Les exercices que je ne savais pas faire, je suis beaucoup plus confortable dans ma pratique sportive quotidienne."),
      ("0349", 61.17, 65.24, "J", "Si tu décides de reprendre tes rênes en main, c'est comme ça que tu peux débloquer les choses.")],
     [("0301",0.0),("0316",8.0),("0321",2.0),("0305",14.0),("0343",2.0),("0340",6.0),("0307",4.0),("0316",14.0),("0321",8.0),("0305",22.0),("0343",14.0),("0301",8.0),("0304",18.0),("0340",20.0)])
reel('reel14-julien-seance', 'Julien en séance — Sparta', "Julien, 44 ans | **plus mal au dos** | dès les premières semaines",
     [("0298", 18.69, 24.05, "J", None),
      ("0298", 44.40, 48.66, "J", "Non, je l'ai senti dès les premières semaines, j'ai plus mal au dos quasiment."),
      ("0298", 49.00, 53.10, "J", "Et maintenant, on peut commencer à travailler le reste du haut du corps, petit à petit."),
      ("0298", 53.80, 58.24, "J", "Et dans la bonne humeur. Et ça m'a fait plus de bien que le kiné."),
      ("0298", 87.36, 89.59, "J", None)],
     [("0297",2.0),("0282",6.0),("0281",4.0),("0289",6.0),("0297",10.0),("0282",14.0),("0281",8.0),("0289",14.0),("0282",2.0),("0297",14.0),("0281",0.0),("0289",2.0)])
reel('reel15-bien-encadres', 'Bien encadrés — Sparta', "« Des exercices **précis**, | en **sécurité**, | bien **encadrés** »",
     [("0347", 19.19, 26.66, "J", None),
      ("0347", 26.90, 30.20, "J", "Et c'est pour ça que j'ai décidé de rejoindre le coaching privé."),
      ("0298", 80.52, 86.70, "J", None),
      ("0298", 86.84, 89.59, "J", "Et la santé, elle n'a pas de prix.")],
     [("0331",2.0),("0343",6.0),("0340",20.0),("0304",22.0),("0331",10.0),("0289",6.0),("0343",10.0),("0281",4.0),("0340",12.0),("0304",34.0),("0331",14.0)])
