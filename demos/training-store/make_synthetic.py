"""
make_synthetic.py - invented inputs for the Training Store demo

Writes the three files the Training Store pipeline joins, all invented:

  synthetic_lms.xlsx         LMS catalogue export (titles, types, curricula membership,
                             active flag, descriptions, durations; deep links left blank)
  synthetic_matrix.json      skills-matrix mapping of each course to an equipment path
                             and the maintenance verbs it covers
  synthetic_equipment.xlsx   a small equipment table with invented manufacturers,
                             series and models (the source of model-number synonyms)

Course titles are generic; manufacturers, series and models are made up.

    python make_synthetic.py && python build.py
"""
import argparse
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

import openpyxl

HERE = Path(__file__).resolve().parent
SEP = chr(1)

VERBS = {"pm": "PM", "rep": "Repair", "ins": "Install", "cal": "Calibrate", "oq": "OQ"}

# (skills-matrix equipment Type, sub-types, readable name). Types are the pipeline's generic
# TYPE2CLASS keys, so each lands in one of its equipment classes.
TOPICS = [
    ("LC SYSTEM", ["HPLC", "UHPLC"], "HPLC"),
    ("GC SYSTEM", ["GC-FID", "HEADSPACE SAMPLER"], "Gas chromatography"),
    ("ORGANIC MASS SPECTROMETERS", ["TRIPLE QUADRUPOLE", "Q-TOF"], "LC-MS"),
    ("CENTRIFUGES", ["BENCHTOP CENTRIFUGE", "ULTRACENTRIFUGE"], "Centrifuge"),
    ("ANALYTICAL BALANCES", ["SEMI-MICRO BALANCE"], "Analytical balance"),
    ("PIPETTES", ["SINGLE CHANNEL PIPETTE", "MULTICHANNEL PIPETTE"], "Pipette"),
    ("LIQUID HANDLER", ["8-CHANNEL WORKSTATION"], "Liquid handler"),
    ("PLATE READER", ["MULTIMODE READER"], "Plate reader"),
    ("SPECTROPHOTOMETERS", ["UV-VIS SPECTROPHOTOMETER"], "UV-Vis spectrophotometer"),
    ("FREEZERS", ["ULT FREEZER"], "Ultra-low freezer"),
    ("REFRIGERATORS", [], "Laboratory refrigerator"),
    ("INCUBATORS", ["CO2 INCUBATOR"], "CO2 incubator"),
    ("STERILIZING/AUTOCLAVE", ["STEAM AUTOCLAVE"], "Autoclave"),
    ("DISSOLUTION SYSTEM", ["PADDLE APPARATUS"], "Dissolution tester"),
    ("TITRATORS", ["KARL FISCHER TITRATOR"], "Karl Fischer titrator"),
    ("PCR EQUIPMENT", ["REAL-TIME PCR", "THERMAL CYCLER"], "PCR instrument"),
    ("MICROSCOPE OPTICAL BASIC", [], "Optical microscope"),
    ("VACUUM PUMPS", [], "Vacuum pump"),
    ("WATER TREATMENT/PURIFICATION", ["ULTRAPURE WATER SYSTEM"], "Water purification system"),
    ("ICP-OES", [], "ICP-OES"),
    ("FUME HOODS", [], "Fume cupboard"),
    ("GAS/AIR CONTROL", ["NITROGEN GENERATOR"], "Nitrogen generator"),
    ("ELECTRICAL/POWER", ["UPS"], "UPS and power"),
    ("DATA LOGGER", [], "Data logger"),
    ("PHYSICAL PROPERTIES - LIQUID", ["VISCOMETER"], "Viscometer"),
    ("EVAPORATORS", ["ROTARY EVAPORATOR"], "Rotary evaporator"),
    ("CELL COUNTER/ANALYZER", [], "Cell counter"),
    ("ANALYZERS", ["TOC ANALYSER"], "TOC analyser"),
]

# Invented manufacturers and their invented series; model codes are generated below.
MAKERS = {
    "Torvik": ["Vantor", "Kelda"], "Quenby": ["Arcline", "Stratum"], "Hollin": ["Meridian", "Corra"],
    "Pellucid": ["Lumen", "Opalis"], "Astrel": ["Nexa", "Brio"], "Marrowfield": ["Halden", "Tessa"],
    "Corvana": ["Ostra", "Pivot"], "Lindqvist": ["Fjell", "Varde"],
}

ADMIN = [
    "Good documentation practice refresher", "Data integrity essentials", "Working at client sites: induction",
    "Customer service in the lab", "Time management for field engineers", "Coaching conversations for team leads",
    "Train the trainer: observation sign-off", "Ergonomics for bench work", "Information security awareness",
    "Inclusive teams", "Managing difficult customer conversations", "Expenses and purchasing basics",
    "Code of conduct annual refresher", "Quality management system overview", "Wellbeing at work",
    "Leadership foundations", "Audit readiness for site teams", "Change management basics",
    "CMMS work order closure", "Presentation skills for engineers", "Customer handover conversations",
    "Writing clear service reports", "Feedback that helps", "Planning your week as a field engineer",
    "Email etiquette for client sites", "Mentoring apprentices", "Running a toolbox talk",
]
SAFETY = [
    "Laboratory safety basics", "Chemical handling and COSHH", "Biosafety level 2 working practices",
    "Electrical safety for instrument engineers", "Lockout and isolation", "Compressed gas cylinders",
    "Manual handling", "Cryogen safety", "Working alone", "Spill response", "Radiation safety awareness",
    "Working at height in plant rooms", "Pressure systems awareness", "Fire safety for laboratory staff",
    "Waste segregation in the lab", "Hazardous energy and stored pressure",
]
SOFTWARE = [("Chromatography data system basics", ["Chromlex CDS"]), ("Plate reader software essentials", ["ReadSuite"]),
            ("Liquid handler method editing", ["FlowScript"]), ("Mass spectrometer acquisition software", ["IonDesk"])]

TEMPLATES = [
    # (title pattern, LMS type, verbs, probability)
    ("{n} fundamentals", "Online Course", {"pm": 2}, 0.75),
    ("{n}: preventive maintenance", "Online Course", {"pm": 1}, 0.8),
    ("{n} troubleshooting workshop", "Event", {"rep": 1, "pm": 1}, 0.55),
    ("{n} installation and qualification", "Event", {"ins": 1, "oq": 1}, 0.35),
    ("{n} calibration procedure walkthrough", "Video", {"cal": 1}, 0.3),
    ("{n} knowledge check", "Test", {}, 0.6),
    ("{n} observation checklist", "Material", {}, 0.55),
    ("{n} on-the-job practical", "Material", {}, 0.2),
    ("{n} advanced diagnostics", "Event", {"rep": 1}, 0.45),
    ("{n} daily checks and cleaning", "Video", {"pm": 2}, 0.55),
    ("{n} module replacement", "Online Course", {"rep": 1, "pm": 2}, 0.45),
    ("{n} decontamination and handover", "Online Course", {"pm": 2}, 0.4),
    ("{n} refresher", "Online Course", {"pm": 1}, 0.5),
    ("{n} practical assessment", "Test", {}, 0.45),
    ("{n} performance verification", "Event", {"cal": 1, "oq": 1}, 0.35),
]
CORE = ("fundamentals", "preventive maintenance", "troubleshooting", "knowledge check", "observation checklist")


def desc_for(title, ty, name):
    if ty == "Test":
        return f"A short knowledge check on {name.lower()} principles and safe working. Pass mark 80%."
    if "observation" in title:
        return f"Observed practical sign-off for {name.lower()} work, completed by a qualified trainer."
    if ty == "Event":
        return f"Instructor-led session covering {title.split(name)[-1].strip(' :').lower() or 'core tasks'} on {name.lower()} equipment, with hands-on practice."
    return f"Self-paced module: {title.lower()}. Covers the main components, routine checks and common faults."


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=11)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    base = datetime(2026, 9, 1)

    lms = []           # rows for the LMS export
    matrix = {}        # course title -> {path: {verb: 1|2}}
    software = {}

    def add(title, ty, desc, cur="", active=True, dur=None):
        lms.append({"Training title": title, "Training type": ty, "Training active": "Y" if active else "N",
                    "Curriculum title (training)": cur, "Last modified date": base - timedelta(days=rng.randint(5, 900)),
                    "Training description": desc, "Deeplink (SSO)": "", "Part duration": dur})

    for typ, subs, name in TOPICS:
        made = []
        for pat, ty, verbs, p in TEMPLATES:
            if rng.random() > p:
                continue
            title = pat.format(n=name)
            dur = rng.choice([20, 30, 45, 60, 90]) if ty in ("Online Course", "Video") else None
            add(title, ty, desc_for(title, ty, name), active=rng.random() > 0.07, dur=dur)
            if ty == "Event" and rng.random() < 0.6:     # scheduled instances share the event's title
                for _ in range(rng.randint(1, 3)):
                    add(title, "Session", "", active=True)
            path = SEP.join([typ] + ([rng.choice(subs)] if subs and rng.random() < 0.6 else []))
            if verbs:
                matrix[title] = {path: dict(verbs)}
            elif ty in ("Test", "Material"):
                matrix[title] = {path: {"pm": 2}}
            made.append(title)
        # Curriculum: the pathway that bundles what exists for this equipment
        if len(made) >= 3 and rng.random() < 0.8:
            cur = f"{name} engineer pathway"
            add(cur, "Curriculum", f"The full learning path for {name.lower()} work, from fundamentals to observed sign-off.")
            for t in [t for t in made if any(k in t for k in CORE)]:
                add(t, next(r["Training type"] for r in lms if r["Training title"] == t), "", cur=cur)

    # OEM-specific modules: these carry an invented maker and series in the title
    for maker, series in MAKERS.items():
        for s in series:
            for typ, subs, name in rng.sample(TOPICS[:16], 2):
                title = f"{maker} {s} {name}: module service"
                add(title, "Online Course", f"Service tasks specific to the invented {maker} {s} range.", dur=rng.choice([30, 45]))
                matrix[title] = {SEP.join([typ] + (subs[:1] if subs else [])): {"pm": 1, "rep": 2}}

    for title, sw in SOFTWARE:
        add(title, "Online Course", f"Getting started with {sw[0]}, an invented application used in this demo.", dur=45)
        software[title] = sw
    for t in SAFETY:
        add(t, rng.choice(["Online Course", "Online Course", "Event"]), "Mandatory safety training for laboratory engineers.", dur=30)
    for t in ADMIN:
        add(t, rng.choice(["Online Course", "Online Course", "Event", "Video"]), "Professional skills for field and site teams.",
            active=rng.random() > 0.1, dur=rng.choice([15, 30, 45]))
    # Programmes that are not equipment-specific
    for cur, members in [("New starter programme", ["Laboratory safety basics", "Working at client sites: induction",
                                                     "Good documentation practice refresher", "Information security awareness"]),
                         ("Team lead programme", ["Coaching conversations for team leads", "Leadership foundations",
                                                  "Managing difficult customer conversations", "Time management for field engineers"])]:
        add(cur, "Curriculum", "A structured programme of core courses.")
        for m in members:
            add(m, next(r["Training type"] for r in lms if r["Training title"] == m), "", cur=cur)
    add("Vendor course record: external provider", "External Training", "Placeholder record for training delivered by an outside provider.")

    # ---- LMS export (header is not on the first row, as in a real report export) ----
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Report"
    ws.append(["Synthetic LMS catalogue export (invented by make_synthetic.py)"])
    ws.append([f"Generated {base:%d %b %Y}"])
    cols = list(lms[0])
    ws.append(cols)
    for r in lms:
        ws.append([r[c] for c in cols])
    wb.save(HERE / "synthetic_lms.xlsx")

    # ---- skills-matrix export ----
    (HERE / "synthetic_matrix.json").write_text(json.dumps(
        {"meta": {"verbs": VERBS, "note": "Synthetic"}, "records": matrix, "software": {"records": software}},
        indent=1), encoding="utf-8")

    # ---- equipment table (one row per invented model) ----
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Equipment"
    ws.append(["ID", "Class", "Type", "Type I", "Type II", "Manufacturer", "Series/Family", "Model"])
    n = 0
    examples = []
    for maker, series in MAKERS.items():
        for typ, subs, name in rng.sample(TOPICS, 9):
            s = rng.choice(series)
            prefix = (maker[:1] + s[:1]).upper()
            for _ in range(rng.randint(2, 4)):
                n += 1
                model = f"{prefix}{rng.randint(2, 9)}{rng.choice(['00', '20', '40', '60', '80'])}"
                sub = rng.choice(subs) if subs else None
                ws.append([f"EQ{n:05d}", "", typ, sub, None, maker, s, model])
                if typ == "LC SYSTEM":
                    examples.append(f"{maker} {model}")
    wb.save(HERE / "synthetic_equipment.xlsx")

    titles = {r["Training title"] for r in lms}
    print(f"Wrote synthetic_lms.xlsx ({len(lms)} rows, {len(titles)} distinct titles), "
          f"synthetic_matrix.json ({len(matrix)} mapped), synthetic_equipment.xlsx ({n} models)")
    print("  Model numbers that should find HPLC training:", ", ".join(examples[:4]))


if __name__ == "__main__":
    main()
