#!/usr/bin/env python3
"""Valide la cohérence de data/vocab.json, data/cards.json et data/voices.json.

Usage : python3 scripts/validate_data.py
Code de sortie 0 si tout est correct, 1 sinon.
"""
import json
import re
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
PUNCT = set("。！？，、；：「」『』（）… .!?,;:'\"")
TONE_MARKS = set("āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ")
WORD_FIELDS = ("id", "hanzi_trad", "hanzi_simp", "pinyin", "fr", "tags", "sources")
CARD_FIELDS = (
    "id", "name_hanzi_trad", "pinyin", "name_fr", "album", "rarity",
    "text_fr", "phrase", "words_required",
)


def load(name):
    with open(DATA / name, encoding="utf-8") as f:
        return json.load(f)


def main():
    errors = []
    vocab = load("vocab.json")
    cards = load("cards.json")
    voices = load("voices.json")

    words = vocab["words"]
    by_id = {}
    for w in words:
        wid = w.get("id", "?")
        for field in WORD_FIELDS:
            if field not in w:
                errors.append(f"{wid}: champ manquant '{field}'")
        if wid in by_id:
            errors.append(f"{wid}: id en double")
        by_id[wid] = w
        pinyin = w.get("pinyin", "")
        if re.search(r"\d", pinyin):
            errors.append(f"{wid}: pinyin avec chiffres ({pinyin}), utiliser les diacritiques")
        # Chaque syllabe doit porter un ton, sauf les tons neutres (2e syllabe d'un mot)
        syllables = pinyin.split()
        if len(syllables) == 1 and not any(c in TONE_MARKS for c in pinyin) and len(w.get("hanzi_trad", "")) == 1:
            errors.append(f"{wid}: caractère seul sans marque de ton ({pinyin})")
        if not w.get("hanzi_trad", "").strip():
            errors.append(f"{wid}: hanzi_trad vide")

    albums = {a["id"] for a in cards["albums"]}
    rarities = set(cards["_meta"]["rarities"])
    seen_cards = set()
    for c in cards["cards"]:
        cid = c.get("id", "?")
        for field in CARD_FIELDS:
            if field not in c:
                errors.append(f"{cid}: champ manquant '{field}'")
        if cid in seen_cards:
            errors.append(f"{cid}: id en double")
        seen_cards.add(cid)
        if c.get("album") not in albums:
            errors.append(f"{cid}: album inconnu '{c.get('album')}'")
        if c.get("rarity") not in rarities:
            errors.append(f"{cid}: rareté inconnue '{c.get('rarity')}'")
        required = c.get("words_required", [])
        for wid in required:
            if wid not in by_id:
                errors.append(f"{cid}: mot requis introuvable '{wid}'")
        # Tous les caractères de la phrase doivent venir des mots requis
        covered = set("".join(by_id[w]["hanzi_trad"] for w in required if w in by_id))
        phrase = c.get("phrase", {}).get("hanzi_trad", "")
        for ch in phrase:
            if ch not in PUNCT and ch not in covered:
                errors.append(f"{cid}: le caractère '{ch}' de la phrase n'est couvert par aucun mot requis")

    if not voices.get("voices") or not voices.get("speeds"):
        errors.append("voices.json: 'voices' et 'speeds' sont obligatoires")

    print(f"{len(words)} mots, {len(cards['cards'])} cartes, {len(voices['voices'])} voix")
    if errors:
        print(f"\n{len(errors)} erreur(s) :")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("Données valides.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
