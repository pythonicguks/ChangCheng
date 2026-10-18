#!/usr/bin/env python3
"""Aide pour les images Wikimedia Commons (nécessite un accès réseau à commons.wikimedia.org).

Chercher des photos candidates, avec auteur et licence :
    python3 scripts/commons.py search "Temple of Heaven Beijing" --limit 8

Remplir automatiquement le crédit des cartes qui ont un `image_file` :
    python3 scripts/commons.py fill

Le champ `image_file` est le nom du fichier Commons, avec des _ (par exemple
Badaling_China_Great-Wall-of-China-01.jpg). `fill` lit l'auteur et la licence sur
Commons, écrit `image_credit` et passe `image_verified` à true.
Seules les licences libres sont acceptées (CC BY, CC BY-SA, CC0, domaine public).
"""
import argparse
import html
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://commons.wikimedia.org/w/api.php"
CARDS = Path(__file__).resolve().parent.parent / "data" / "cards.json"
UA = "ChangCheng/0.1 (https://github.com/pythonicguks/ChangCheng; projet pédagogique)"
FREE = re.compile(r"^(CC BY(-SA)? [0-9.]+|CC0.*|Public domain.*|PD.*|GFDL.*)$", re.I)


def api(**params):
    params.update(format="json", formatversion="2")
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def clean(text):
    """Retire le HTML des métadonnées Commons."""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", text or ""))).strip()


def parse_pages(data):
    """Transforme la réponse de l'API en liste de dicts (titre, auteur, licence, taille, page)."""
    out = []
    for p in data.get("query", {}).get("pages", []):
        info = (p.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata", {})
        title = p["title"].removeprefix("File:")
        out.append({
            "file": title.replace(" ", "_"),
            "artist": clean(meta.get("Artist", {}).get("value")) or "Auteur inconnu",
            "license": clean(meta.get("LicenseShortName", {}).get("value")) or "licence inconnue",
            "size": f"{info.get('width', '?')}x{info.get('height', '?')}",
            "page": info.get("descriptionurl", ""),
        })
    return out


def lookup(titles):
    return parse_pages(api(action="query", titles="|".join("File:" + t for t in titles),
                           prop="imageinfo", iiprop="url|size|extmetadata"))


def search(query, limit):
    return parse_pages(api(action="query", generator="search", gsrsearch=query, gsrnamespace=6,
                           gsrlimit=limit, prop="imageinfo", iiprop="url|size|extmetadata"))


def cmd_search(args):
    for r in search(args.query, args.limit):
        ok = "libre" if FREE.match(r["license"]) else "À VÉRIFIER"
        print(f"{r['file']}\n   {r['artist']} | {r['license']} ({ok}) | {r['size']}\n   {r['page']}")


def cmd_fill(_args):
    data = json.loads(CARDS.read_text(encoding="utf-8"))
    cards = [c for c in data["cards"] if c.get("image_file")]
    found = {r["file"]: r for r in lookup([c["image_file"] for c in cards])}
    problems = 0
    for c in cards:
        r = found.get(c["image_file"])
        if not r or r["license"] == "licence inconnue":
            print(f"{c['id']}: fichier introuvable ou licence illisible ({c['image_file']})", file=sys.stderr)
            problems += 1
            continue
        if not FREE.match(r["license"]):
            print(f"{c['id']}: licence non reconnue comme libre ({r['license']}), à vérifier à la main", file=sys.stderr)
            problems += 1
            continue
        c["image_credit"] = f"{r['artist']}, {r['license']}"
        c["image_verified"] = True
        print(f"{c['id']}: {c['image_credit']}")
    CARDS.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 1 if problems else 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search", help="chercher des fichiers sur Commons")
    s.add_argument("query")
    s.add_argument("--limit", type=int, default=8)
    s.set_defaults(func=cmd_search)
    f = sub.add_parser("fill", help="remplir image_credit depuis Commons")
    f.set_defaults(func=cmd_fill)
    args = p.parse_args()
    sys.exit(args.func(args) or 0)


if __name__ == "__main__":
    main()
