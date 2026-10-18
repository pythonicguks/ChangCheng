# ChangCheng 長城

Apprendre le mandarin au niveau A1, en se concentrant sur la **compréhension** : reconnaître les mots en **caractères traditionnels** et en **pinyin**, sans passer par l'expression orale. L'apprentissage est ludique : on gagne des cartes de culture chinoise (monuments, animaux, fêtes…) en maîtrisant du vocabulaire.

Le nom vient de 長城 (Chángchéng), la Grande Muraille : on construit pierre par pierre.

## État du projet

Premier prototype jouable : appli web statique (un seul fichier HTML) avec six types d'exercices, répétition espacée simple (boîtes de Leitner), collection de cartes à débloquer et réglages de voix. Les voix de l'appli viennent pour l'instant de la synthèse vocale du navigateur ; les mp3 générés par `gen_audio.py` ne sont pas encore branchés.

## Contenu

```
data/vocab.json    58 mots : hanzi_trad, hanzi_simp, pinyin, fr, tags, sources
data/cards.json    5 cartes culturelles + albums (monuments, animaux, boissons, fêtes)
data/voices.json   4 voix (mandarin standard zh-CN et mandarin de Taïwan zh-TW) et 2 vitesses
app/index.template.html    source de l'appli (HTML, CSS et JS)
scripts/build_app.py       assemble l'appli et ses données dans docs/index.html
docs/index.html            appli prête à servir (GitHub Pages : branche main, dossier /docs)
scripts/validate_data.py   vérifie la cohérence des données
scripts/gen_audio.py       génère les audios mp3 pour chaque voix et vitesse
```

## Données

- **Mots** : chaque mot a un `id` stable (`w001`…). Le pinyin utilise les diacritiques (mā), pas les chiffres (ma1). Les tons neutres suivent l'usage du continent (xièxie, péngyou) ; les voix zh-TW peuvent les prononcer avec un ton plein.
- **Sources** : le champ `sources` croise HSK, TOCFL et EBCL. Pour l'instant il est rempli **de mémoire** (HSK 2.0) et `sources_verified` vaut `false` : TOCFL et EBCL restent à croiser avec les listes officielles. Une liste vide signifie « mot ajouté pour la collection culturelle, ou pas encore vérifié ».
- **Cartes** : une carte se débloque quand tous ses `words_required` sont maîtrisés. Le nom de la carte est lui-même du vocabulaire, et chaque carte a une phrase d'exemple construite uniquement avec ses mots requis (vérifié par `validate_data.py`). Les champs `image` et `image_credit` sont à remplir avec des fichiers de Wikimedia Commons (auteur et licence à créditer).

## Utilisation

```bash
python3 scripts/validate_data.py            # vérifier les données
python3 scripts/build_app.py                # régénérer docs/index.html après un changement de données

pip install -r requirements.txt
python3 scripts/gen_audio.py --dry-run      # voir ce qui sera généré
python3 scripts/gen_audio.py                # générer les audios (les fichiers existants sont ignorés)
```

Les audios sont rangés par voix et par vitesse : `audio/<voix>/<vitesse>/<id>.mp3` (par exemple `audio/zh-CN-XiaoxiaoNeural/slow/w056.mp3`). Ils sont générés une fois, l'appli n'a besoin d'aucun serveur.

## Idées pour la suite

- Exercices : caractère → pinyin, pinyin → caractère, caractère → sens, sens → caractère ; discrimination des tons à l'écoute ; paires minimales ; mini-phrases.
- Réglages : choix de la voix, vitesse lente ou normale, mode « voix variées » (une voix au hasard à chaque écoute).
- Répétition espacée (SM-2 ou FSRS), une carte par direction, 10 à 15 nouveaux mots par session.
- Ludique : série de jours, quête quotidienne, raretés, passeport par région.
- Compléter le vocabulaire avec les listes TOCFL (Novice) et EBCL.
