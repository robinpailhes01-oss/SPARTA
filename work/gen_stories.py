"""Génère les stories (1080 × 1920, 6 à 9 s) : un temps fort de témoignage, citation en haut, un plan de leur séance."""
import json, os
SD = 'rushes/seances/'
def f(n): return SD + [x for x in os.listdir(SD) if f'_{n}_D' in x][0]
P = {"0347": "rushes/interview/DJI_20261026180353_0347_D.MP4", "0349": "rushes/interview/DJI_20261026180503_0349_D.MP4",
     "0350": "rushes/interview/DJI_20261026180635_0350_D.MP4", "0298": "rushes/interview/DJI_20261026170411_0298_D.MP4"}
def story(name, titre, hook, morceaux, brolls, nom):
    mor = [{"prise": p, "in": a, "out": b, "qui": "J", "cadrage": "serre", **({"texte": t} if t else {})} for p, a, b, t in morceaux]
    total = sum(b - a for _, a, b, _ in morceaux)
    cadres = {"0347": {"J": {"origin": "0% 34%", "tight_scale": 1.9, "wide_scale": 1.0}},
              "0349": {"J": {"origin": "0% 32%", "tight_scale": 1.9, "wide_scale": 1.0}},
              "0350": {"J": {"origin": "0% 34%", "tight_scale": 1.9, "wide_scale": 1.0}},
              "0298": {"J": {"origin": "0% 24%", "tight_scale": 1.9, "wide_scale": 1.0}}}
    broll, t0 = [], 0.0
    # plan de coupe : un par morceau (le dernier tiers du passage), 2,2 s
    for i, (clip, de) in enumerate(brolls):
        p, a, b, _ = morceaux[i]
        d = round(min(2.2, (b - a) - 1.6), 2)
        broll.append({"src": f(clip), "de": de, "morceau": i, "at": round(b - d - 0.15, 2), "dur": d})
    d = {"title": titre, "fps": 30, "modele": "large-v3", "prises": {p: P[p] for p in {m[0] for m in morceaux}},
         "cadres": cadres, "morceaux": mor, "broll": broll,
         "edl": {"cap_style": "epure", "cap_max_chars": 26,
                 "hook": {"text": hook + f" | ∙ {nom}", "dur": round(total + 1.2, 2)},
                 "end_card": {"logo": "assets/brand/logo_or_blanc.png", "dur": 1.5}, "keywords": []}}
    os.makedirs(f'videos/{name}', exist_ok=True)
    json.dump(d, open(f'videos/{name}/plan.json', 'w'), ensure_ascii=False, indent=1)
    print(name, round(total, 1), 's')

story('story-julien-1', 'Story Julien 1', "« Plus de bien | que le **kiné** »",
      [("0298", 44.40, 48.66, "Non, je l'ai senti dès les premières semaines, j'ai plus mal au dos quasiment."),
       ("0298", 53.80, 58.24, "Et dans la bonne humeur. Et ça m'a fait plus de bien que le kiné.")], [("0282", 6.0), ("0297", 2.0)], "Julien, 44 ans")
story('story-julien-2', 'Story Julien 2', "« La **santé** | n'a pas de prix »",
      [("0298", 80.52, 86.70, None), ("0298", 86.84, 89.59, "Et la santé, elle n'a pas de prix.")], [("0281", 4.0), ("0289", 6.0)], "Julien, 44 ans")
story('story-julien-3', 'Story Julien 3', "« **Investir** dans | une salle comme ça »",
      [("0298", 72.84, 80.50, "Moi, je dirais qu'il vaut mieux investir dans une salle comme ça, ici, plutôt que dans les salles grand public moins chères,")],
      [("0297", 10.0)], "Julien, 44 ans")
story('story-jennifer-1', 'Story Jennifer 1', "« Des exercices **précis**, | en **sécurité**, | bien **encadrés** »",
      [("0347", 19.19, 26.66, None)], [("0331", 4.0)], "Jennifer, 40 ans")
story('story-jennifer-2', 'Story Jennifer 2', "« **Plus à l'aise** | à la salle »",
      [("0349", 10.46, 15.28, None), ("0349", 15.38, 18.65, "Et puis, je suis plus à l'aise maintenant à la salle quand j'y vais.")],
      [("0316", 8.0), ("0321", 4.0)], "Jennifer, 40 ans")
story('story-jennifer-3', 'Story Jennifer 3', "« **Plus confortable** | dans ma pratique | sportive »",
      [("0349", 18.75, 25.12, "Les exercices que je ne savais pas faire, je suis beaucoup plus confortable dans ma pratique sportive quotidienne.")],
      [("0305", 14.0)], "Jennifer, 40 ans")
story('story-jennifer-4', 'Story Jennifer 4', "Si tu hésites : | **reprends** tes rênes",
      [("0349", 61.17, 65.24, "Si tu décides de reprendre tes rênes en main, c'est comme ça que tu peux débloquer les choses."),
       ("0350", 17.26, 19.95, None)], [("0343", 2.0), ("0340", 6.0)], "Jennifer, 40 ans")
