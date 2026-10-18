#!/usr/bin/env python3
"""Assemble l'application en un seul fichier HTML autonome (données incluses).

Usage :
    python3 scripts/build_app.py                      # écrit index.html (page complète, pour GitHub Pages)
    python3 scripts/build_app.py --fragment FICHIER   # écrit le fragment sans <html>/<head>/<body>
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

WRAP = """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<style>
:root { color-scheme: light; padding-top: env(safe-area-inset-top, 0px); padding-bottom: env(safe-area-inset-bottom, 0px); }
body { margin: 0; font: 14px system-ui, sans-serif; }
img { max-width: 100%; }
[hidden] { display: none !important; }
</style>
</head>
<body>
{body}
</body>
</html>
"""


def js(obj):
    # Sûr à l'intérieur d'une balise <script>
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


def build_fragment():
    template = (ROOT / "app" / "index.template.html").read_text(encoding="utf-8")
    vocab = json.loads((ROOT / "data" / "vocab.json").read_text(encoding="utf-8"))["words"]
    cards = json.loads((ROOT / "data" / "cards.json").read_text(encoding="utf-8"))
    cards_out = {"albums": cards["albums"], "cards": cards["cards"]}
    return template.replace("__VOCAB__", js(vocab)).replace("__CARDS__", js(cards_out))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--fragment", help="écrire seulement le fragment à ce chemin")
    args = p.parse_args()
    fragment = build_fragment()
    if args.fragment:
        out = Path(args.fragment)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(fragment, encoding="utf-8")
    else:
        out = ROOT / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(WRAP.replace("{body}", fragment), encoding="utf-8")
    print(f"Écrit : {out} ({out.stat().st_size // 1024} Ko)")


if __name__ == "__main__":
    main()
