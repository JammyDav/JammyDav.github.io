"""
make_synthetic.py - invented laboratory estate -> synthetic_register.xlsx

Writes a workbook in the same shape the asset risk pipeline reads (sheet
'Risk Register' with the header on row 2, plus a 'Methodology' sheet), filled
with invented data: made-up cost centres, suppliers, asset IDs, generic
equipment descriptions and budgets from a plausible distribution. Nothing is
derived from any real register.

The scoring columns are computed with the real rules (weights 30/25/25/20,
High >= 4.0, Medium >= 2.5) so the methodology panel stays truthful.

    python make_synthetic.py           # writes synthetic_register.xlsx
    python make_synthetic.py --seed 3  # a different invented estate
"""
import argparse
import math
import random
from datetime import datetime
from pathlib import Path

import openpyxl
from openpyxl.styles import Font

HERE = Path(__file__).resolve().parent
OUT = HERE / "synthetic_register.xlsx"

WEIGHTS = {"criticality": 0.30, "age": 0.25, "breakdowns": 0.25, "obsolescence": 0.20}
THRESHOLDS = {"High": 4.0, "Medium": 2.5}

# Invented cost centres: code, name, approximate asset count, criticality lean (-1..+1)
COST_CENTRES = [
    ("CC3105", "Analytical Chemistry", 420, 0.5),
    ("CC3120", "Bioassay Services", 300, 0.3),
    ("CC3142", "Formulation Science", 250, 0.1),
    ("CC3160", "Process Development", 230, 0.2),
    ("CC3188", "Stability Testing", 210, 0.4),
    ("CC3204", "Microbiology", 190, 0.3),
    ("CC3217", "Discovery Biology", 260, -0.1),
    ("CC3233", "Pilot Plant", 140, 0.6),
    ("CC3251", "QC Release", 180, 0.7),
    ("CC3276", "Metabolism and Residues", 160, 0.0),
    ("CC3290", "Site Services", 110, -0.4),
]

# Generic equipment: description stem, expected life (yrs), median budget (GBP), share weight,
# and the cost centres it is most common in (by name keyword).
EQUIPMENT = [
    ("HPLC SYSTEM", 10, 38000, 9, ("Analytical", "Stability", "QC", "Formulation")),
    ("UHPLC SYSTEM", 10, 56000, 5, ("Analytical", "QC", "Metabolism")),
    ("GAS CHROMATOGRAPH", 12, 42000, 4, ("Analytical", "Metabolism", "QC")),
    ("LC-MS SYSTEM", 9, 210000, 2, ("Analytical", "Metabolism", "Discovery")),
    ("GC-MS SYSTEM", 10, 118000, 2, ("Metabolism", "Analytical")),
    ("ANALYTICAL BALANCE", 12, 4600, 10, ()),
    ("MICROBALANCE", 12, 14500, 2, ("Analytical", "Formulation")),
    ("BENCHTOP CENTRIFUGE", 12, 7200, 7, ()),
    ("ULTRACENTRIFUGE", 12, 74000, 1, ("Bioassay", "Discovery")),
    ("UV-VIS SPECTROPHOTOMETER", 12, 15500, 4, ("Analytical", "QC", "Bioassay")),
    ("FTIR SPECTROMETER", 12, 31000, 2, ("Analytical", "Formulation", "QC")),
    ("MICROPLATE READER", 9, 46000, 4, ("Bioassay", "Discovery")),
    ("LIQUID HANDLING WORKSTATION", 10, 96000, 3, ("Bioassay", "Discovery")),
    ("CO2 INCUBATOR", 12, 9200, 6, ("Bioassay", "Microbiology", "Discovery")),
    ("ULTRA-LOW TEMPERATURE FREEZER", 10, 11800, 7, ()),
    ("LABORATORY REFRIGERATOR", 12, 3100, 8, ()),
    ("STEAM AUTOCLAVE", 15, 48000, 2, ("Microbiology", "Site Services", "Pilot")),
    ("DISSOLUTION TESTER", 12, 36000, 3, ("Formulation", "QC", "Stability")),
    ("BIOLOGICAL SAFETY CABINET", 15, 14200, 5, ("Microbiology", "Bioassay", "Discovery")),
    ("PH METER", 8, 1300, 7, ()),
    ("KARL FISCHER TITRATOR", 10, 12400, 3, ("Analytical", "QC", "Formulation")),
    ("WATER PURIFICATION SYSTEM", 10, 16500, 3, ()),
    ("STABILITY CHAMBER", 15, 32000, 4, ("Stability",)),
    ("PARTICLE SIZE ANALYSER", 12, 86000, 1, ("Formulation", "Pilot")),
    ("REAL-TIME PCR SYSTEM", 8, 39000, 2, ("Microbiology", "Discovery", "Bioassay")),
    ("THERMAL CYCLER", 8, 11500, 2, ("Discovery", "Bioassay")),
    ("INVERTED MICROSCOPE", 15, 23000, 2, ("Bioassay", "Microbiology")),
    ("JACKETED REACTOR SYSTEM", 15, 140000, 1, ("Pilot", "Process")),
    ("ROTARY EVAPORATOR", 10, 8800, 3, ("Process", "Formulation", "Pilot")),
    ("TABLET HARDNESS TESTER", 12, 9500, 2, ("Formulation", "QC")),
]
MODEL_PREFIX = ["HX", "QV", "TR", "LM", "ZK", "PD", "NE", "VR", "SB", "OK"]

# Invented service providers
PROVIDERS = ["Larkspur Instruments", "Quillon Service", "Orrin Calibration", "Tamsin & Vale",
             "Brightmoor Labs", "Halcyon Field", "In-house", "OEM contract"]
PROVIDER_W = [14, 12, 9, 8, 10, 7, 22, 18]

OBSOLESCENCE = [("Supported", 1), ("End of sale", 2), ("Limited parts availability", 3),
                ("End of support announced", 4), ("No longer supported", 5)]
OBS_W = [64, 12, 11, 8, 5]

FLOORS = ["L0", "L1", "L2", "L3"]
KEEP_UPPER = {"HPLC", "UHPLC", "LC-MS", "GC-MS", "UV-VIS", "FTIR", "CO2", "PH", "PCR"}


def sentence(stem):
    """'HPLC SYSTEM' -> 'HPLC system'; acronyms stay upper case."""
    words = [w if w in KEEP_UPPER else w.lower() for w in stem.split()]
    words = ["pH" if w == "PH" else "UV-Vis" if w == "UV-VIS" else w for w in words]
    out = " ".join(words).replace("karl fischer", "Karl Fischer")
    return out[:1].upper() + out[1:]


def age_score(pct):
    return 1 if pct < 0.5 else 2 if pct < 0.75 else 3 if pct < 1.0 else 4 if pct < 1.25 else 5


def bd_score(n):
    return 1 if n == 0 else 2 if n == 1 else 3 if n == 2 else 4 if n <= 4 else 5


def overall(crit, a, b, o):
    w = WEIGHTS
    return round(crit * w["criticality"] + a * w["age"] + b * w["breakdowns"] + o * w["obsolescence"], 2)


def rating(s):
    return "High" if s >= THRESHOLDS["High"] else "Medium" if s >= THRESHOLDS["Medium"] else "Low"


def wchoice(rng, items, weights):
    return rng.choices(items, weights=weights, k=1)[0]


def make_assets(rng):
    assets, used_ids = [], set()
    for code, cc_name, n_approx, lean in COST_CENTRES:
        n = int(n_approx * 0.8 * rng.uniform(0.9, 1.1))
        weights = [w * (3 if any(k in cc_name for k in where) else (1 if not where else 0.25))
                   for (_, _, _, w, where) in EQUIPMENT]
        for _ in range(n):
            stem, life, median, _, _ = wchoice(rng, EQUIPMENT, weights)
            model = f"{rng.choice(MODEL_PREFIX)}-{rng.randint(1, 9) * 100 + rng.choice([0, 10, 20, 40, 50, 80])}"
            desc = f"{sentence(stem)} {model}"
            while True:
                aid = f"AR{rng.randint(100000, 999999)}"
                if aid not in used_ids:
                    used_ids.add(aid)
                    break
            age = round(max(0.3, rng.gammavariate(2.2, life * 0.29)), 1)
            pct = age / life
            crit = max(1, min(5, round(rng.gauss(2.35 + 0.7 * lean, 0.9))))
            lam = 0.25 + 0.6 * max(0.0, pct - 0.6)
            bds = min(7, sum(1 for _ in range(12) if rng.random() < lam / 12))
            obs_label, obs = wchoice(rng, OBSOLESCENCE, OBS_W)
            if pct > 1.1 and rng.random() < 0.2:   # old kit drifts out of support
                obs_label, obs = OBSOLESCENCE[min(4, OBSOLESCENCE.index((obs_label, obs)) + 1)]
            blank_obs = rng.random() < 0.035
            budget = round(median * math.exp(rng.gauss(0, 0.35)) / 10) * 10
            assets.append({
                "id": aid, "desc": desc, "cc": code, "cc_name": cc_name,
                "location": f"{cc_name.split()[0]} lab, {rng.choice(FLOORS)}",
                "provider": wchoice(rng, PROVIDERS, PROVIDER_W),
                "age": age, "life": life, "crit": crit, "bds": bds,
                "obs_label": None if blank_obs else obs_label, "obs": None if blank_obs else obs,
                "budget": budget,
            })
    return assets


def stress(rng, assets, k):
    """A handful of business-critical, old, unreliable, unsupported assets: the High-risk list."""
    pool = [a for a in assets if a["budget"] > 9000]
    for a in rng.sample(pool, k):
        a["crit"] = 5
        a["age"] = round(a["life"] * rng.uniform(1.28, 1.75), 1)
        a["bds"] = rng.randint(3, 6)
        a["obs_label"], a["obs"] = OBSOLESCENCE[rng.choice([3, 4])]


def score(assets):
    for a in assets:
        a["pct"] = round(a["age"] / a["life"], 4)
        a["age_s"] = age_score(a["pct"])
        a["bd_s"] = bd_score(a["bds"])
        a["timeframe"] = round(a["life"] - a["age"], 1)
        if a["obs"] is None:
            a["score"], a["rating"] = None, None   # the workbook formula never resolves without obsolescence
        else:
            a["score"] = overall(a["crit"], a["age_s"], a["bd_s"], a["obs"])
            a["rating"] = rating(a["score"])


def write(assets, path, as_of):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Risk Register"
    ws.append(["Asset Risk Register (synthetic demo data, invented by make_synthetic.py)"])
    ws["A1"].font = Font(bold=True, size=13)
    header = ["Asset ID", "Asset Description", "Location / Function", "Service Provider", "GL Account",
              "Asset Age (years)", "Expected lifetime", "% expected lifetime", "Criticality Score (1-5)",
              "Breakdowns - Last 12 Months (count)", "Obsolescence", "Obsolescence Score (1-5)",
              "Replacement Timeframe (years)", "Estimated Replacement Budget (£)", "Age Score (1-5)",
              "Breakdown Score (1-5)", "Overall Risk Score", "Risk Rating"]
    ws.append(header)
    for c in ws[2]:
        c.font = Font(bold=True)
    for a in assets:
        ws.append([a["id"], a["desc"], a["location"], a["provider"], f"{a['cc']} - {a['cc_name']}",
                   a["age"], a["life"], a["pct"], a["crit"], a["bds"], a["obs_label"], a["obs"],
                   a["timeframe"], a["budget"], a["age_s"], a["bd_s"], a["score"], a["rating"]])
    ws.freeze_panes = "A3"

    m = wb.create_sheet("Methodology")
    rows = [
        ["Asset risk methodology (synthetic demo)"],
        ["1. Overview"],
        ["Every asset in the register is scored on four components, each on a common 1 to 5 scale, and the weighted sum gives an overall risk score."],
        ["The overall score sets a High, Medium or Low rating, which drives the recommended replacement action and the budget year."],
        ["2. Weighting"],
        ["Component", "Weight", "What it captures"],
        ["Business criticality", 0.30, "Impact on testing, release or safety if the asset is unavailable"],
        ["Age vs expected life", 0.25, "How much of its expected working life the asset has used"],
        ["Breakdown history", 0.25, "Unplanned breakdowns recorded in the last 12 months"],
        ["Obsolescence", 0.20, "Manufacturer support status: parts, service and software"],
        ["Criticality carries the largest weight because the cost of losing a business-critical asset outweighs its age or repair history; the other three components describe how likely that loss is."],
        ["3. Scales"],
        ["Age: under 50% of life scores 1, up to 75% scores 2, up to 100% scores 3, up to 125% scores 4, beyond that 5."],
        ["Breakdowns in 12 months: none 1, one 2, two 3, three or four 4, five or more 5."],
        ["4. Ratings"],
        ["High 4.0 and above; Medium 2.5 to 3.99; Low below 2.5."],
        ["5. Assumptions"],
        ["• All data in this workbook is invented for a public demonstration; no asset, supplier, cost centre or budget is real."],
        ["• Replacement budgets are like-for-like estimates in GBP and exclude installation and qualification."],
        ["• Expected lifetimes are typical figures for the equipment class, not manufacturer commitments."],
        ["• Blank obsolescence means no recorded support concern and is scored 1."],
        ["The methodology is designed to be reviewed with budget holders each year; weights and thresholds sit in one configuration block so any change is visible and repeatable."],
    ]
    for r in rows:
        m.append(r)
    m.column_dimensions["A"].width = 110
    wb.properties.modified = as_of
    wb.properties.creator = "make_synthetic.py"
    wb.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=4242)
    ap.add_argument("--high", type=int, default=8, help="how many assets to push into High risk")
    args = ap.parse_args()
    rng = random.Random(args.seed)
    assets = make_assets(rng)
    stress(rng, assets, args.high)
    score(assets)
    rng.shuffle(assets)
    write(assets, OUT, datetime(2026, 10, 1, 9, 0))

    rated = [a for a in assets if a["rating"]]
    by = {k: sum(1 for a in rated if a["rating"] == k) for k in ("High", "Medium", "Low")}
    print(f"Wrote {OUT.name}: {len(assets):,} assets, {len(COST_CENTRES)} cost centres, "
          f"{len(assets) - len(rated)} with no obsolescence record")
    print(f"  Workbook ratings: High {by['High']}, Medium {by['Medium']:,} ({by['Medium'] / len(rated):.0%}), Low {by['Low']:,}")
    if not 5 <= by["High"] <= 12:
        raise SystemExit("High count outside the 'handful' range; try another --seed or --high")


if __name__ == "__main__":
    main()
