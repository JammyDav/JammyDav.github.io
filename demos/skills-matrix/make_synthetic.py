"""
make_synthetic.py - seeded generator for the skills matrix demo -> data.json

Everything here is invented: 60 engineers with obviously fictional names, five
made-up sites and twelve generic equipment classes. Re-running with the same
seed produces the same file byte for byte.

    python make_synthetic.py            # writes data.json next to this file
    python make_synthetic.py --seed 7   # a different, equally fictional team
"""
import argparse
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent

LEVELS = [
    {"n": 0, "label": "Not assessed"},
    {"n": 1, "label": "Aware", "desc": "Knows what it is and the safety rules; does not work on it."},
    {"n": 2, "label": "Supervised", "desc": "Carries out routine tasks with a competent engineer present."},
    {"n": 3, "label": "Competent", "desc": "Maintains and repairs it unsupervised; signed off by observation."},
    {"n": 4, "label": "Can train", "desc": "Competent, and qualified to train and assess others on it."},
]
COMPETENT_MIN = 3
TRAINER_LEVEL = 4

# Invented sites. Each leans towards some classes so the gaps differ by site.
SITES = [
    {"id": "alder", "name": "Alder Park", "lean": ["hplc", "gc", "ms", "balance"]},
    {"id": "brook", "name": "Brookvale", "lean": ["plate", "liquid", "incubator", "freezer"]},
    {"id": "cinder", "name": "Cinder Hill", "lean": ["autoclave", "centrifuge", "incubator", "balance"]},
    {"id": "dunmore", "name": "Dunmore Quay", "lean": ["dissolution", "uvvis", "hplc", "balance"]},
    {"id": "elm", "name": "Elmstead", "lean": ["centrifuge", "freezer", "plate", "uvvis"]},
]
SITE_SIZES = [14, 12, 11, 12, 11]  # 60 engineers

# Generic classes only: no real inventory, models or hierarchy.
CLASSES = [
    {"id": "balance", "name": "Analytical balance", "short": "Balance"},
    {"id": "centrifuge", "name": "Centrifuge", "short": "Centrifuge"},
    {"id": "hplc", "name": "HPLC system", "short": "HPLC"},
    {"id": "gc", "name": "Gas chromatograph", "short": "GC"},
    {"id": "ms", "name": "Mass spectrometer", "short": "Mass spec"},
    {"id": "uvvis", "name": "UV-Vis spectrophotometer", "short": "UV-Vis"},
    {"id": "plate", "name": "Plate reader", "short": "Plate reader"},
    {"id": "liquid", "name": "Liquid handler", "short": "Liquid handler"},
    {"id": "incubator", "name": "Incubator", "short": "Incubator"},
    {"id": "freezer", "name": "Ultra-low freezer", "short": "ULT freezer"},
    {"id": "autoclave", "name": "Autoclave", "short": "Autoclave"},
    {"id": "dissolution", "name": "Dissolution tester", "short": "Dissolution"},
]
# Harder classes: fewer people reach Competent anywhere.
HARD = {"ms": 0.66, "dissolution": 0.72, "liquid": 0.82, "gc": 0.9}

FIRST = ["Alex", "Bailey", "Casey", "Dana", "Eden", "Frankie", "Gale", "Harper", "Indy", "Jordan", "Kai", "Lane",
         "Morgan", "Noel", "Oakley", "Parker", "Quinn", "Reese", "Sage", "Taylor", "Umi", "Val", "Wren", "Yael",
         "Zion", "Ari", "Blair", "Cam", "Drew", "Ellis", "Finley", "Gray", "Hollis", "Jesse", "Kendall", "Logan",
         "Marlo", "Nico", "Ollie", "Peyton", "Remy", "Shay", "Tatum", "Rory", "Avery", "Brook", "Charlie", "Dallas",
         "Emery", "Flynn", "Hayden", "Jules", "Kit", "Lennon", "Milan", "Nova", "Perry", "Robin", "Sam", "Toby"]
LAST = ["Alder", "Birch", "Cedar", "Dunlin", "Elder", "Fern", "Gorse", "Hazel", "Ivy", "Juniper", "Kestrel", "Linden",
        "Maple", "Nettle", "Osprey", "Plover", "Quill", "Rowan", "Sorrel", "Teal", "Umber", "Vetch", "Willow", "Yarrow",
        "Aspen", "Bracken", "Curlew", "Dove", "Egret", "Finch", "Heron", "Larch", "Merlin", "Oriole", "Pippin", "Reed",
        "Sedge", "Thistle", "Wren", "Starling"]
ROLES = [("Apprentice", 0.12), ("Field engineer", 0.58), ("Senior engineer", 0.22), ("Site lead", 0.08)]
ROLE_BOOST = {"Apprentice": -1.1, "Field engineer": 0.0, "Senior engineer": 0.7, "Site lead": 0.9}


def pick_role(rng):
    r, acc = rng.random(), 0.0
    for name, p in ROLES:
        acc += p
        if r < acc:
            return name
    return ROLES[-1][0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20261017)
    args = ap.parse_args()
    rng = random.Random(args.seed)

    names = [(f, l) for f in FIRST for l in LAST]
    rng.shuffle(names)
    used = set()
    engineers = []
    k = 0
    for site, size in zip(SITES, SITE_SIZES):
        for _ in range(size):
            while names[k][0] in used:
                k += 1
            first, last = names[k]
            used.add(first)
            role = pick_role(rng)
            skills = {}
            # Each engineer covers a handful of classes, weighted to the site's lean.
            weights = {c["id"]: (3.0 if c["id"] in site["lean"] else 1.0) for c in CLASSES}
            n_classes = rng.randint(3, 8) if role != "Apprentice" else rng.randint(2, 4)
            pool = list(weights)
            chosen = set()
            while len(chosen) < n_classes:
                total = sum(weights[c] for c in pool if c not in chosen)
                r, acc = rng.random() * total, 0.0
                for c in pool:
                    if c in chosen:
                        continue
                    acc += weights[c]
                    if r <= acc:
                        chosen.add(c)
                        break
            for cid in sorted(chosen, key=lambda c: [x["id"] for x in CLASSES].index(c)):
                base = rng.gauss(2.4, 0.9) + ROLE_BOOST[role] + (0.4 if cid in site["lean"] else -0.2)
                base *= HARD.get(cid, 1.0)
                level = max(1, min(4, round(base)))
                # Most levels are manager-validated; a few self-assessments are still pending.
                validated = 1 if rng.random() < 0.86 else 0
                skills[cid] = [level, validated]
            engineers.append({
                "id": f"E{len(engineers) + 1:03d}",
                "name": f"{first} {last}",
                "site": site["id"],
                "role": role,
                "skills": skills,
            })

    data = {
        "meta": {
            "seed": args.seed,
            "note": "Synthetic data. Every engineer, site and level is invented by make_synthetic.py.",
            "levels": LEVELS,
            "competent_min": COMPETENT_MIN,
            "trainer_level": TRAINER_LEVEL,
            "gap_threshold": 2,
        },
        "sites": [{"id": s["id"], "name": s["name"]} for s in SITES],
        "classes": CLASSES,
        "engineers": engineers,
    }
    out = HERE / "data.json"
    out.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    # Report: the gap view is only interesting if there are some gaps to find.
    print(f"Wrote {out.name}: {len(engineers)} engineers, {len(SITES)} sites, {len(CLASSES)} classes (seed {args.seed})")
    for s in [None] + SITES:
        team = [e for e in engineers if s is None or e["site"] == s["id"]]
        gaps = []
        for c in CLASSES:
            n = sum(1 for e in team if e["skills"].get(c["id"], [0, 0])[0] >= COMPETENT_MIN and e["skills"][c["id"]][1])
            if n < 2:
                gaps.append(f"{c['short']} ({n})")
        print(f"  {s['name'] if s else 'All sites':<13} gaps: {', '.join(gaps) or 'none'}")


if __name__ == "__main__":
    main()
