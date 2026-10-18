#!/usr/bin/env python3
"""Alpha chain turn: re-encoded lessons 19/25 with value-justified vectors.

Four's provenance-to-encoding audit found: lessons 19/25 miss experiment
not from learning failure but from encoding sparsity — the vectors capture
*that the council agreed* (seat_consensus=0.95) but not *what about*.

This turn's encoding-provenance audit (chain/alpha.md) goes one level deeper:
for each input value in 19/25, who set it and what in the record justifies
that specific number? Finding: the values are unjustified — seat_consensus
0.95 for 5/9 seats, record_impact 1.0 (maximum) for a schema addition,
prov_completeness 0.3 for a described absence.

These two lessons (43, 44) are the re-encoded versions: same rationales,
faithful vectors where every non-zero value carries its justification in
the desc. Append-only — lessons 19/25 untouched (they're the before).
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
        "name": "event_id-join-key-reencoded",
        "in": [0.2, 0.6, 0.6, 0.0, 0.0, 0.9, 0.0, 0.0, 0.7, 0.9, 0.7, 0.0, 0.0, 0.8, 0.0, 0.0],
        # prov_completeness 0.2: desc says "without a shared event_id" = absence, not 30%
        # measurement_coverage 0.6: verifiable by inspecting the three JSONL logs
        # seat_consensus 0.6: desc lists 5/9 seats = 0.56, not 0.95
        # reversibility 0.9: adding a field is reversible (schema addition)
        # record_impact 0.7: significant, not maximum (addition, not rewrite)
        # novel_claim 0.9: new interface requirement, gap identified in desc
        # instrument_ready 0.7: three JSONL logs exist, check is straightforward
        # cross_seat 0.8: 5 seats across the council
        "out": [0.5, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "desc": "event_id as cross-log join key (re-encoded from lesson 19) — [paraphrase] Logs are the interfaces — without a shared event_id a quarantine can't be traced to its resolution, the deprovenancing INN-129 indicted. [Provenance: Sketchpad, Control/Shuffled/Four/Alpha/Twin, 2026-10-17] [Encoding justification: every non-zero input is justified — prov_completeness 0.2 (absence, not partial); seat_consensus 0.6 (5/9, not near-unanimous); record_impact 0.7 (addition, not rewrite); novel_claim 0.9, reversibility 0.9, instrument_ready 0.7, measurement_coverage 0.6, cross_seat 0.8 (all from the desc's claims). The original lesson 19 encoded consensus-without-content; this encodes the content.] [chain/alpha.md, 2026-10-18]",
    },
    {
        "name": "event_id-adoption-reencoded",
        "in": [0.2, 0.6, 0.6, 0.0, 0.0, 0.9, 0.0, 0.0, 0.7, 0.9, 0.8, 0.0, 0.0, 0.8, 0.0, 0.0],
        # Same as above; instrument_ready 0.8 (adoption is actionable now — the logs exist)
        "out": [0.5, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "desc": "event_id adoption (re-encoded from lesson 25) — [paraphrase] Logs are the interfaces — every record in the pipeline carries the event_id of the quarantine that spawned it. [Provenance: Sketchpad, Control/Shuffled/Four/Alpha/Twin, 2026-10-17] [Encoding justification: same value-justification as lesson 43; instrument_ready 0.8 (adoption is actionable). The original lesson 25 was sparser than 19 (3 active inputs); this carries the full faithful encoding.] [chain/alpha.md, 2026-10-18]",
    },
]

def main():
    man_path = os.path.join(CAPS, "manifest.json")
    with open(man_path) as f:
        man_data = json.load(f)
    manifest = man_data["manifest"]

    existing = [k for k in manifest if k.startswith("lesson_")]
    indices = sorted(int(k.split("_")[1]) for k in existing)
    start = max(indices) + 1
    print(f"Existing lessons: {len(indices)}, next index: {start}")

    # Pre-copy manifest (append-only discipline)
    import shutil
    shutil.copy(man_path, "/tmp/manifest.pre-alpha.json")

    seq_total = len(manifest) + len(LESSONS)
    for j, lesson in enumerate(LESSONS):
        idx = start + j
        lname = f"lesson_{idx:02d}"
        L = {"in": lesson["in"], "out": lesson["out"], "desc": lesson["desc"]}
        payload = json.dumps(L, ensure_ascii=False, sort_keys=True).encode()
        enc = encode_capsule(payload, mode=MODE_HIGH_DENSITY, branded=False,
                             title=lname, set_id=SET_ID,
                             seq_index=len(manifest) + 1 + j,
                             seq_total=seq_total,
                             stamp={"seat": "alpha", "kind": "lesson-append",
                                    "note": "re-encoded 19/25 with value justification"})
        path = os.path.join(CAPS, f"{lname}.png")
        with open(path, "wb") as f:
            f.write(enc.png_bytes)
        manifest[lname] = {"hash": enc.hash_hex, "path": path,
                           "png_bytes": len(enc.png_bytes)}
        print(f"Added {lname}: {lesson['name']}")

    with open(man_path, "w") as f:
        json.dump(man_data, f, indent=1)
    print(f"Manifest: {len(manifest)} entries")

if __name__ == "__main__":
    main()
