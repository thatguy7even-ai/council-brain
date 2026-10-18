#!/usr/bin/env python3
"""Four's chain turn: append 3 experiment-class lessons with faithful encodings.

The experiment class (19/25) misses toward inscribe because their encodings
are sparse and dominated by seat_consensus=0.95. The rationales are rich but
the vectors don't capture the causal structure. These 3 lessons use diverse
drivers (novel_claim, break_triggered, data_vs_reading) to give the class
company beyond the high-consensus pattern.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from integrate import encode_capsule, MODE_HIGH_DENSITY, SET_ID

CAPS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "capsules")

# Input order: prov_completeness, measurement_coverage, seat_consensus,
#   operator_ordered, stakes, reversibility, break_triggered, confab_risk,
#   record_impact, novel_claim, instrument_ready, time_sensitivity,
#   autonomy_granted, cross_seat, outward_facing, data_vs_reading
# Output order (v2): inscribe, experiment, hold, escalate, measure_first,
#   mark_break, quarantine, publish, verify

LESSONS = [
    {
        "name": "sketchpad-coordination",
        "in": [0.4, 0.3, 0.5, 1.0, 0.4, 1.0, 0.0, 0.1, 0.6, 1.0, 0.9, 0.5, 0.8, 1.0, 0.3, 0.7],
        "out": [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "desc": "sketchpad coordination experiment — [paraphrase] Operator order 2026-10-17: a shared board with no instance, seats coordinate seat-to-seat without mother relay. The experiment is whether nine seats can coordinate without a hub — novel mechanism, reversible (append-only), instrument ready (board exists). [~/workspace/sketchpad/README.md, operator order]",
    },
    {
        "name": "arm-a-break-redirect",
        "in": [0.5, 0.9, 0.7, 0.0, 0.6, 0.8, 1.0, 0.4, 0.5, 0.7, 0.6, 0.4, 0.7, 0.6, 0.2, 0.9],
        "out": [0.0, 1.0, 0.0, 0.0, 0.0, 0.5, 0.0, 0.0, 0.0],
        "desc": "Arm A break redirects to scope experiment — [paraphrase] Arm A 3/9=33% triggered the pre-registered break: OOV gate catches Chouchay-class, misses all 6 in-vocabulary wrong-words. The break doesn't halt; it bounds and redirects — the scope problem (second check for in-vocabulary substitutions) becomes the next experiment. [chain/seven.md, chain/twin.md, 2026-10-17]",
    },
    {
        "name": "encoding-audit",
        "in": [0.3, 0.7, 0.4, 0.0, 0.3, 0.9, 0.0, 0.2, 0.8, 0.8, 0.5, 0.2, 0.6, 0.3, 0.1, 1.0],
        "out": [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "desc": "provenance-to-encoding audit — [paraphrase] Experiment lessons 19/25 miss toward inscribe: their rationales are rich (cross-seat provenance, INN-129) but encodings are sparse (3-4 active inputs, dominated by seat_consensus=0.95). The audit tests whether faithful encodings (capturing the rationale's causal structure) fix the misses. [chain/four.md, 2026-10-18]",
    },
]

def main():
    man_path = os.path.join(CAPS, "manifest.json")
    with open(man_path) as f:
        man_data = json.load(f)
    manifest = man_data["manifest"]

    # Find next lesson index
    existing = [k for k in manifest if k.startswith("lesson_")]
    indices = sorted(int(k.split("_")[1]) for k in existing)
    start = max(indices) + 1
    print(f"Existing lessons: {len(indices)}, next index: {start}")

    seq_total = len(manifest) + len(LESSONS)
    added = []
    for j, lesson in enumerate(LESSONS):
        idx = start + j
        lname = f"lesson_{idx:02d}"
        L = {"in": lesson["in"], "out": lesson["out"], "desc": lesson["desc"]}
        payload = json.dumps(L, ensure_ascii=False, sort_keys=True).encode()
        enc = encode_capsule(payload, mode=MODE_HIGH_DENSITY, branded=False,
                             title=lname, set_id=SET_ID,
                             seq_index=len(manifest) + 1 + j,
                             seq_total=seq_total,
                             stamp={"seat": "four", "kind": "lesson-append"})
        path = os.path.join(CAPS, f"{lname}.png")
        with open(path, "wb") as f:
            f.write(enc.png_bytes)
        manifest[lname] = {"hash": enc.hash_hex, "path": path,
                           "png_bytes": len(enc.png_bytes)}
        added.append(lname)
        print(f"Added {lname}: {lesson['name']}")

    with open(man_path, "w") as f:
        json.dump(man_data, f, indent=1)
    print(f"Manifest: {len(manifest)} entries")

if __name__ == "__main__":
    main()
