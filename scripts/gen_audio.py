#!/usr/bin/env python3
"""Génère les audios (mots et phrases des cartes) pour chaque voix et chaque vitesse.

Les fichiers sont rangés ainsi : audio/<voix>/<vitesse>/<id>.mp3
Exemple : audio/zh-CN-XiaoxiaoNeural/slow/w056.mp3

Usage :
    pip install -r requirements.txt
    python3 scripts/gen_audio.py                      # tout générer (les fichiers existants sont ignorés)
    python3 scripts/gen_audio.py --dry-run            # lister ce qui serait généré
    python3 scripts/gen_audio.py --voices zh-CN-XiaoxiaoNeural --speeds slow
    python3 scripts/gen_audio.py --only w001 w002 c001
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
AUDIO = ROOT / "audio"


def load(name):
    with open(DATA / name, encoding="utf-8") as f:
        return json.load(f)


def build_items():
    """Retourne {id: (traditionnel, simplifié)} : mots (wXXX) et phrases de cartes (cXXX)."""
    items = {}
    for w in load("vocab.json")["words"]:
        items[w["id"]] = (w["hanzi_trad"], w.get("hanzi_simp", w["hanzi_trad"]))
    for c in load("cards.json")["cards"]:
        ph = c["phrase"]
        items[c["id"]] = (ph["hanzi_trad"], ph.get("hanzi_simp", ph["hanzi_trad"]))
    return items


async def synth(sem, text, voice, rate, out, retries=3):
    import edge_tts

    async with sem:
        for attempt in range(1, retries + 1):
            try:
                out.parent.mkdir(parents=True, exist_ok=True)
                await edge_tts.Communicate(text, voice, rate=rate).save(str(out))
                return None
            except Exception as exc:  # réseau, quota...
                out.unlink(missing_ok=True)  # ne jamais laisser un fichier vide ou partiel
                if attempt == retries:
                    return f"{out.relative_to(ROOT)}: {exc}"
                await asyncio.sleep(2 * attempt)


async def run(args):
    cfg = load("voices.json")
    voices = args.voices or [v["id"] for v in cfg["voices"]]
    speeds = args.speeds or list(cfg["speeds"])
    unknown = [v for v in voices if v not in {x["id"] for x in cfg["voices"]}]
    unknown += [s for s in speeds if s not in cfg["speeds"]]
    if unknown:
        print(f"Voix ou vitesses inconnues : {unknown}", file=sys.stderr)
        return 1

    items = build_items()
    if args.only:
        missing = [i for i in args.only if i not in items]
        if missing:
            print(f"Identifiants inconnus : {missing}", file=sys.stderr)
            return 1
        items = {i: items[i] for i in args.only}

    jobs = []
    for voice in voices:
        for speed in speeds:
            for item_id, (trad, simp) in items.items():
                # Les voix de Chine continentale lisent le texte simplifié, celles de Taïwan le traditionnel
                text = trad if voice.startswith("zh-TW") else simp
                out = AUDIO / voice / speed / f"{item_id}.mp3"
                if not out.exists() or args.force:
                    jobs.append((text, voice, cfg["speeds"][speed], out))

    print(f"{len(jobs)} fichier(s) à générer ({len(items)} textes x {len(voices)} voix x {len(speeds)} vitesses, hors existants)")
    if args.dry_run:
        for text, voice, rate, out in jobs[:10]:
            print(f"  {out.relative_to(ROOT)}  <-  {text} ({rate})")
        if len(jobs) > 10:
            print(f"  ... et {len(jobs) - 10} autres")
        return 0

    sem = asyncio.Semaphore(args.concurrency)
    results = await asyncio.gather(*(synth(sem, *job) for job in jobs))
    failures = [r for r in results if r]
    print(f"{len(jobs) - len(failures)} généré(s), {len(failures)} échec(s)")
    for f in failures:
        print(f"  - {f}", file=sys.stderr)
    return 1 if failures else 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--voices", nargs="+", help="identifiants de voix (défaut : toutes)")
    p.add_argument("--speeds", nargs="+", help="vitesses (défaut : toutes)")
    p.add_argument("--only", nargs="+", help="limiter à ces identifiants (ex. w001 c001)")
    p.add_argument("--force", action="store_true", help="régénérer même si le fichier existe")
    p.add_argument("--dry-run", action="store_true", help="afficher sans générer")
    p.add_argument("--concurrency", type=int, default=4)
    sys.exit(asyncio.run(run(p.parse_args())))


if __name__ == "__main__":
    main()
