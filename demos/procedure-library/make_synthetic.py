"""
make_synthetic.py - invented inputs for the procedure library demo

Writes, all invented:
  register.json                   a document register in the shape build_index.py reads
  example/gaps.xlsx               a gap and verification register (sheet 'Gaps')
  example/EX-01_Closing a corrective work order.md
                                  one invented procedure, written in the library's
                                  procedure skeleton, with two deliberate faults for
                                  the checker to find: a banned word, and a VERIFY
                                  marker that has no row in the gap register

No programme name, real titles, real IDs, real section names or people: owners and
reviewers are role titles, IDs use a made-up EX- pattern.

    python make_synthetic.py && python build.py
"""
import json
import random
from datetime import date, timedelta
from pathlib import Path

import openpyxl

HERE = Path(__file__).resolve().parent
EX = HERE / "example"
MASTER_NAME = "EX-01_Closing a corrective work order.md"

FAMILIES = ["Planning and scheduling", "Work execution", "Assets and records", "Quality and compliance",
            "Training and competence", "Suppliers and parts", "Health and safety", "Library administration"]
TYPES = [("Procedure", 0.34), ("Work instruction", 0.24), ("Form", 0.16), ("Job aid", 0.12),
         ("Manual", 0.06), ("Template", 0.05), ("Register", 0.03)]
STATUS = [("Planned", 0.22), ("Draft", 0.22), ("In Review", 0.16), ("Issued", 0.32), ("Superseded", 0.03), ("Live", 0.05)]
TOPICS = {
    "Planning and scheduling": ["Building the weekly maintenance schedule", "Prioritizing incoming requests", "Planning a shutdown window",
                                "Rescheduling missed preventive work", "Capacity check before accepting new assets"],
    "Work execution": ["Closing a corrective work order", "Raising a maintenance request", "Handing over equipment after repair",
                       "Recording time and parts on a job", "Working on equipment in a shared lab", "Out-of-hours callout"],
    "Assets and records": ["Adding a new asset to the CMMS", "Retiring an asset", "Annual asset verification",
                           "Correcting an asset record", "Linking service history after a transfer"],
    "Quality and compliance": ["Handling a deviation", "Preparing for an audit", "Document review and approval",
                               "Controlling changes to a procedure", "Reviewing calibration results"],
    "Training and competence": ["Observed competency sign-off", "Onboarding a new engineer", "Recording external training",
                                "Assigning training after a procedure change"],
    "Suppliers and parts": ["Ordering a spare part", "Receiving and booking in parts", "Engaging an outside service provider",
                            "Returning a faulty part"],
    "Health and safety": ["Isolating equipment before work", "Reporting a near miss", "Working with hazardous substances",
                          "Permit to work for plant rooms"],
    "Library administration": ["Starting a new document", "Building and checking a document", "Requesting a review",
                               "Issuing a document", "Retiring a document"],
}
SUFFIX = {"Procedure": "", "Work instruction": "", "Form": ": record form", "Job aid": ": quick guide",
          "Manual": " manual", "Template": " template", "Register": " register"}
OWNERS = ["Operations lead", "Quality lead", "Planning lead", "Training lead", "Health and safety lead", "Library owner"]
REVIEWERS = ["Field technician panel", "Supervisor panel", "Quality reviewer", "Planner panel", "Training reviewer"]


def pick(rng, items):
    r, acc = rng.random(), 0.0
    for v, p in items:
        acc += p
        if r < acc:
            return v
    return items[-1][0]


def register(rng):
    docs, revs, n = [], [], 0
    start = date(2026, 3, 2)
    for fi, fam in enumerate(FAMILIES):
        for topic in TOPICS[fam]:
            types = ["Procedure"] + [pick(rng, TYPES) for _ in range(rng.randint(0, 2))]
            for ty in dict.fromkeys(types):
                n += 1
                did = "EX-01" if topic == "Closing a corrective work order" and ty == "Procedure" else f"EX-{fi + 1}{n:02d}"
                st = "Draft" if did == "EX-01" else pick(rng, STATUS)
                created = start + timedelta(days=rng.randint(0, 150))
                modified = created + timedelta(days=rng.randint(3, 60))
                nrev = {"Planned": 0, "Draft": 1, "In Review": rng.randint(1, 2), "Issued": rng.randint(2, 3),
                        "Superseded": 3, "Live": 1}[st]
                rev_list = []
                for k in range(nrev):
                    rv = f"R{k}.0" if st in ("Issued", "Superseded") or k < nrev - 1 else f"R{k}.{rng.randint(1, 3)} (draft)"
                    rev_list.append({"id": did, "revision": rv, "date": (created + timedelta(days=12 * k + 2)).isoformat(),
                                     "note": ["First draft from sources", "Review comments dispositioned", "Issued after sign-off",
                                              "Minor revision after audit"][min(k, 3)],
                                     "author": rng.choice(OWNERS), "status": "Current" if k == nrev - 1 else "Superseded"})
                revs += rev_list
                verify = "" if st in ("Planned", "Live") else (0 if st in ("Issued", "Superseded") else rng.randint(0, 6))
                if did == "EX-01":
                    verify = 2
                docs.append({
                    "id": did, "title": topic + SUFFIX[ty], "type": ty, "status": st,
                    "section": fam, "subsection": f"{fam} · {ty.lower()}s", "location": f"library/{fam.split()[0].lower()}/",
                    "parent": "" if ty == "Procedure" else f"procedure for {topic.lower()}",
                    "revision": rev_list[-1]["revision"] if rev_list else "", "created": created.isoformat(),
                    "modified": modified.isoformat(), "owner": rng.choice(OWNERS), "sponsor": "Operations director",
                    "reviewers": rng.choice(REVIEWERS) if st in ("In Review", "Issued", "Superseded") else "",
                    "reviewer_pool": "Field technician panel; Supervisor panel" if st == "Draft" else "",
                    "next": {"Planned": "Draft from sources", "Draft": "Build, check, request review", "In Review": "Disposition comments",
                             "Issued": "", "Superseded": "", "Live": "Maintained continuously"}[st],
                    "pages": "" if st == "Planned" else rng.randint(2, 8), "verify_open": verify,
                    "file": f"{did}_{topic + SUFFIX[ty]}.docx", "project": "2026 procedure rebuild (synthetic)", "extra": "",
                })
    return {"library": "Example procedure library (synthetic)", "documents": docs, "revisions": revs}


MASTER = """# EX-01 Closing a corrective work order

| | |
|---|---|
| Administrative Procedure | Closing a corrective work order |
| Revision | R0.1 (draft) |
| Number | EX-01 |
| Effective Date | On issue |
| Owner | Operations lead |

Uncontrolled When Printed

## 1. Purpose and Scope

### 1.1 Purpose
This procedure tells you how to close a corrective work order after a repair. It also tells you how to hand the equipment back to the user.

### 1.2 Scope
This procedure applies to:
- Corrective work orders for laboratory equipment.
- Repairs by a field technician or an outside service provider.

This procedure does not apply to:
- Preventive maintenance. See the preventive maintenance procedure.

## 2. Triggers and Inputs

### 2.1 Triggers
- The field technician completes a repair.

### 2.2 Required inputs
- The open work order in the CMMS.
- The service report from the repair.

## 3. Roles and Responsibilities

| Role | Responsibility in this procedure |
|---|---|
| Field Technician | Records the repair and returns the equipment to service. |
| Supervisor | Reviews the work order before closure. |
| Planner | Closes the work order and books follow-up work. |

## 4. Requirements

### 4.1 Competence
The field technician holds a current sign-off for the equipment class.

### 4.2 Time and SLA
- Close the work order within two working days of the repair.

### 4.3 Systems and Tools
- CMMS: work order screen and asset history.

### 4.4 Forms
- Equipment handover form, kept with the work order.

## 5. Procedure

A summary process flow of work order closure is provided in Figure 1.

Figure 1.  Work Order Closure Flow

| 5.1  Record the repair | ▶ | 5.2  Hand back | ▶ | 5.3  Review and close |
|---|---|---|---|---|
| Field Technician |  | Field Technician |  | Supervisor, Planner |
| Section 9: 1 |  | Section 9: 2 |  | Section 9: 1 |
| For all associated documents, see section 9 |  |  |  |  |

### 5.1 Record the repair

5.1.1 Field Technician: In the CMMS, open the work order. Record the fault found and the action taken.

5.1.2 Field Technician: Record the parts used and the time spent.

5.1.3 Field Technician: Attach the service report to the work order.

### 5.2 Hand back the equipment

5.2.1 Field Technician: Complete the equipment handover form with the user.

5.2.2 Field Technician: Decision: Does the equipment pass its functional check? If yes, go to 5.2.3. If no, go to 7.

5.2.3 Field Technician: Ensure the status label shows the equipment is in service.

### 5.3 Review and close

5.3.1 Supervisor: Review the work order record against the service report.

5.3.2 Supervisor: Confirm the closure time limit. [VERIFY: closure time limit for outside providers; Source needed: Operations lead]

5.3.3 Planner: Set the work order status to Closed.

5.3.4 Planner: Book any follow-up work as a new work order. [VERIFY: whether follow-up work keeps the original priority; Source needed: Planning lead]

## 6. Key Metrics and SLAs

| Metric | Target |
|---|---|
| Work orders closed within two working days | 95 percent |

## 7. Exceptions and Escalation

- If the equipment fails its functional check, the Field Technician escalates to the Supervisor.

## 8. Definitions

| Term | Meaning |
|---|---|
| CMMS | Computerized maintenance management system, here eMaint. It manages assets, work orders and maintenance records. |
| Work order | A record of a maintenance task, its labor, parts and result. |

## 9. Associated Documents

| Document | Type |
|---|---|
| [Raising a maintenance request](https://example.com/library/raising-a-maintenance-request) | Procedure |
| [Equipment handover form](https://example.com/library/equipment-handover-form) | Form |

## 10. Summary of Changes

| Details | Version | Author | Date |
|---|---|---|---|
| First draft | R0.1 | Operations lead | Draft |
"""


def main():
    rng = random.Random(7)
    EX.mkdir(exist_ok=True)
    reg = register(rng)
    (HERE / "register.json").write_text(json.dumps(reg, indent=1, ensure_ascii=False), encoding="utf-8")
    (EX / MASTER_NAME).write_text(MASTER, encoding="utf-8")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Gaps"
    ws.append(["Gap ID", "Document", "Statement", "Source needed", "Status"])
    # Only the first marker is logged; the second is the deliberate unlogged VERIFY.
    ws.append(["G-001", "EX-01", "Closure time limit for outside providers", "Operations lead", "Open"])
    ws.append(["G-002", "EX-07", "Shutdown notice period for shared labs", "Planning lead", "Open"])
    wb.save(EX / "gaps.xlsx")
    d = reg["documents"]
    print(f"Wrote register.json: {len(d)} documents across {len({x['section'] for x in d})} families, "
          f"{len({x['type'] for x in d})} types, {sum(1 for x in d if x['status'] == 'Issued')} issued, {len(reg['revisions'])} revisions")
    print(f"Wrote example/{MASTER_NAME} and example/gaps.xlsx")


if __name__ == "__main__":
    main()
