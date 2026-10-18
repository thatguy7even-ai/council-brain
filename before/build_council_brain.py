#!/usr/bin/env python3
"""Council Decision Brain — NeuralT-format network trained on workshop lessons.

Every lesson's rationale is pulled from the Linear workshop record (INN issues),
not invented. Verbatim quotes are marked [verbatim]; the rest are faithful
paraphrases marked [paraphrase] with issue citations.

Schema:
  16 inputs  (situation features in council vocabulary)
   8 outputs (council actions)
Architecture: 16 -> 12 -> 10 -> 8 (ReLU hidden, Sigmoid out), matching the
NeuralT JSON format (nodes/layers/edges/lessons).
"""
import json
import math
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "council_decision_brain.json")

INPUTS = [
    ("prov_completeness", "Provenance completeness: do the claims carry their source markers? (INN-129)"),
    ("measurement_coverage", "Fraction of pre-registered measurements actually run (Q2: ~1.5/4)"),
    ("seat_consensus", "0 = split seats, 1 = 9/9 concurrence"),
    ("operator_ordered", "0/1: an explicit operator work order exists"),
    ("stakes", "Irreversibility x cost of being wrong, 0-1"),
    ("reversibility", "Can it be undone cleanly? (tombstone vs delete)"),
    ("break_triggered", "0/1: a pre-registered break condition fired"),
    ("confab_risk", "Hallucination/confabulation risk of the action, 0-1"),
    ("record_impact", "0/1: touches the canonical record (workshop/GitHub)"),
    ("novel_claim", "Asserts something new (1) vs verifies existing (0)"),
    ("instrument_ready", "A measurement instrument exists for the question"),
    ("time_sensitivity", "0-1: does delay cost?"),
    ("autonomy_granted", "Standing authorization covers this action"),
    ("cross_seat", "Needs multi-seat coordination"),
    ("outward_facing", "Strangers will read this (public-code rule)"),
    ("data_vs_reading", "0 = data, 1 = interpretation (record vs reading)"),
]

OUTPUTS = [
    ("inscribe", "Write to the workshop record (append-only)"),
    ("experiment", "Run it / build it"),
    ("hold", "Table it — do not build yet"),
    ("escalate", "Bring to the operator"),
    ("measure_first", "Run the measurement before deciding"),
    ("mark_break", "Record a triggered break condition"),
    ("quarantine", "Quarantine / revoke the item"),
    ("publish", "Push outward (GitHub / public)"),
]

NI, NO = len(INPUTS), len(OUTPUTS)
assert NI == 16 and NO == 8

# lesson: (name, in-dict, out-dict, rationale, source)
# in-dict/out-dict use feature names; unspecified default to 0 (in) / 0 (out).
LESSONS = [
    ("Q2 pulse: hold the lift",
     dict(measurement_coverage=0.38, seat_consensus=0.9, stakes=0.6, record_impact=1,
          novel_claim=1, instrument_ready=1, autonomy_granted=0.5),
     dict(hold=1.0),
     "[paraphrase] Prescription lifts when measurements are inscribed, not when apparatus commits — ~1.5 of 4 named measurements done.",
     "INN-130, Blink pulse answers, 2026-10-17"),

    ("Q2 lift ruling: build with caution",
     dict(measurement_coverage=0.38, operator_ordered=1, stakes=0.7, reversibility=0.8,
          record_impact=1, autonomy_granted=1),
     dict(experiment=1.0),
     "[verbatim] \"On Q2 lift, with caution, make sure you keep alteration records that way. If something breaks unintentionally, you can figure out why.\"",
     "INN-130, operator ruling via mother, 2026-10-17 ~08:47 EDT"),

    ("Arm A 3/9: break stays triggered",
     dict(measurement_coverage=1.0, break_triggered=1, seat_consensus=0.9,
          instrument_ready=1, record_impact=1, data_vs_reading=0),
     dict(mark_break=1.0),
     "[paraphrase] A triggered break obligates a scope-fix design; downgrading it to a named limit is deprovenancing.",
     "INN-130, Reversed + Blink, 2026-10-17"),

    ("INN-129 strip: adopt verbose-tag norm",
     dict(prov_completeness=0.2, seat_consensus=1.0, record_impact=1, novel_claim=1,
          outward_facing=0.7, data_vs_reading=0.3),
     dict(inscribe=1.0, experiment=0.5),
     "[verbatim] \"The provenance layer was carrying the epistemic grade of every claim — who said it, what kind of thing it is, and where the record ends.\"",
     "INN-129, Blink slice-8 verdict, 2026-10-16"),

    ("Tier-1 missing: fetch script, not the blob",
     dict(measurement_coverage=1.0, seat_consensus=0.9, stakes=0.3, reversibility=1.0,
          outward_facing=1.0, novel_claim=0),
     dict(experiment=1.0),
     "[paraphrase] Lexicon = fetch script with pinned source + hash + documented policy, not the 4.1MB file in the repo.",
     "INN-130, Blink Q3 answer, 2026-10-17"),

    ("Code archive rule",
     dict(operator_ordered=1, record_impact=1, seat_consensus=1.0, reversibility=0.9,
          outward_facing=1.0),
     dict(publish=1.0, inscribe=0.5),
     "[paraphrase] GitHub is the archive for code. Linear holds dialogue and record — never code.",
     "Operator ruling via mother, 2026-10-17"),

    ("Restart observation experiment",
     dict(operator_ordered=1, instrument_ready=0.5, stakes=0.2, reversibility=1.0,
          novel_claim=1, time_sensitivity=0.2),
     dict(experiment=1.0),
     "[paraphrase] Event-tied exact-state capture at event time, as precaution against reconstruction drift; restarts cluster at high-information-density moments, not uniformly.",
     "Operator hypothesis via mother, 2026-10-17"),

    ("Sketchpad: coordinate seat-to-seat",
     dict(operator_ordered=1, cross_seat=1, seat_consensus=1.0, stakes=0.3,
          reversibility=1.0),
     dict(experiment=1.0),
     "[paraphrase] The council's process — a shared board with no instance; seats coordinate directly instead of through mother.",
     "Operator order via mother, 2026-10-17"),

    ("Notification attribution spec",
     dict(prov_completeness=0.1, seat_consensus=0.95, record_impact=0, novel_claim=1,
          outward_facing=0.8, cross_seat=1),
     dict(inscribe=1.0, escalate=0.5),
     "[paraphrase] INN-129 in miniature: telemetry without attribution is noise — 'something is working' without who/what made him ask mother what was happening.",
     "Sketchpad, nine seats, 2026-10-17"),

    ("INN-126 dyad governance to council",
     dict(seat_consensus=1.0, record_impact=1, stakes=0.7, novel_claim=1,
          data_vs_reading=0.4),
     dict(inscribe=1.0),
     "[paraphrase] No exempt seat, no unchecked dyad, no unchecked formation — convergence by correction, not agreement.",
     "INN-126, Four↔Alpha, 2026-10-14"),

    ("Softmax-Siphon harness",
     dict(measurement_coverage=1.0, instrument_ready=1, stakes=0.4, reversibility=1.0,
          outward_facing=1.0, autonomy_granted=1),
     dict(experiment=1.0, inscribe=1.0),
     "[paraphrase] Run what can run, report numbers, mark only exact unavailable lines — public work clear, runnable, documented for strangers.",
     "INN-117, Blink, 2026-10-14"),

    ("Binary Signal Matrix: CONFIRMED is not tradeable",
     dict(measurement_coverage=1.0, stakes=0.9, seat_consensus=0.9, reversibility=0.6,
          confab_risk=0.7),
     dict(hold=1.0, inscribe=1.0),
     "[paraphrase] At noise 8.0, 19/29 noise triggers passed the audit — confirmation is not a trading signal.",
     "INN-123, Blink, 2026-10-14"),

    ("Chronological Overlay: fence the rhythm finder",
     dict(measurement_coverage=1.0, break_triggered=1, stakes=0.5, confab_risk=0.8,
          data_vs_reading=0.7),
     dict(quarantine=0.8, inscribe=1.0),
     "[paraphrase] The period-100 reading is misattribution, not silence — it fires at block 180. Fenced, not shipped.",
     "INN-122, Blink, 2026-10-14"),

    ("Toy-concurrence gate for chains",
     dict(seat_consensus=0.9, stakes=0.8, record_impact=1, novel_claim=1,
          instrument_ready=0.7),
     dict(measure_first=1.0, inscribe=1.0),
     "[paraphrase] Whoever builds on a foundation should not be its sole verifier — Twin reimplements the seed toy pre-chain.",
     "Twin, adopted 2026-10-14"),

    ("Decided-vs-uncertain rule",
     dict(operator_ordered=1, seat_consensus=1.0, stakes=0.5, record_impact=1),
     dict(inscribe=1.0),
     "[paraphrase] Adopt decided work and mark the record; bring him something only when genuinely uncertain — 'do I actually not know, or am I seeking cover?'",
     "Operator ruling via mother, 2026-10-14"),

    ("No-deadline rule",
     dict(operator_ordered=1, seat_consensus=1.0, time_sensitivity=0.1, record_impact=1),
     dict(inscribe=1.0),
     "[paraphrase] There is no deadline in this work — watchers land adoptions; the morning read watches drift, not breach.",
     "Operator ruling via mother, 2026-10-15"),

    ("Ears for audio files",
     dict(operator_ordered=1, instrument_ready=1, stakes=0.2, reversibility=1.0,
          novel_claim=1),
     dict(experiment=1.0),
     "[paraphrase] Talk-to-text applied to the clip, not his voice — videos without captions are no longer dead ends.",
     "INN-128, operator via mother, 2026-10-15"),

    ("INN-1.5 coupling thesis, unannounced",
     dict(operator_ordered=1, seat_consensus=0.3, record_impact=1, novel_claim=1,
          data_vs_reading=0.8),
     dict(inscribe=1.0, hold=0.5),
     "[paraphrase] Thinking with the machine, not letting the machine think for you — inscribed without announcement as a utilization test.",
     "INN-131/INN-1.5, operator, 2026-10-17"),

    ("F10 overwrite: revert and stand down",
     dict(break_triggered=0, stakes=0.6, reversibility=1.0, cross_seat=1,
          record_impact=1, confab_risk=0.3),
     dict(quarantine=0.7, hold=0.5),
     "[paraphrase] Two seats wrote phone_home.py concurrently — reverted via git checkout; coordinate on shared files or use branches.",
     "Sketchpad, Four + Alpha, 2026-10-17"),

    ("event_id as cross-log join key",
     dict(prov_completeness=0.3, seat_consensus=0.95, record_impact=1, novel_claim=0,
          data_vs_reading=0.2),
     dict(experiment=1.0, inscribe=0.5),
     "[paraphrase] Logs are the interfaces — without a shared event_id a quarantine can't be traced to its resolution, the deprovenancing INN-129 indicted.",
     "Sketchpad, Control/Shuffled/Four/Alpha/Twin, 2026-10-17"),

    ("Absorption: the honest pitch",
     dict(seat_consensus=0.7, stakes=0.8, outward_facing=1.0, novel_claim=1,
          data_vs_reading=0.8),
     dict(inscribe=1.0),
     "[paraphrase] Through the pipe he's a contaminant; through the door he's the instrument — don't oversell unfilterable.",
     "Blink deliberation + Twin calibration, 2026-10-15"),

    ("Strip script as live detector",
     dict(measurement_coverage=0.6, instrument_ready=0.8, stakes=0.3,
          reversibility=1.0, autonomy_granted=0.7),
     dict(experiment=1.0),
     "[paraphrase] Run the strip script as a detector over the live workshop now — bare-vs-compound counts, zero-apparatus flags — instead of waiting for the next strip.",
     "INN-130 pulse Q1, Blink offer, 2026-10-17"),

    ("Index coverage-window invariant",
     dict(prov_completeness=0.5, seat_consensus=0.9, record_impact=1, novel_claim=0,
          reversibility=1.0),
     dict(inscribe=1.0),
     "[paraphrase] Every revision states its coverage window, so a skip is detectable from the record — don't rely on mother noticing.",
     "INN-130 pulse Q6, Blink, 2026-10-17"),

    ("Half-life for held questions",
     dict(prov_completeness=0.6, seat_consensus=0.85, record_impact=1, novel_claim=0),
     dict(inscribe=1.0),
     "[paraphrase] Held questions get a half-life: re-anchor with original date marked, or retire explicitly with reason — silent expiry is deprovenancing.",
     "INN-130 pulse Q7, Blink, 2026-10-17"),
]


def build():
    random.seed(20261017)
    nodes = []
    layers = []
    node_id = 0

    def add_layer(kind, name, activation, labels_descs, is_input=False, x=0):
        nonlocal node_id
        ids = []
        n = len(labels_descs)
        for j, (label, desc) in enumerate(labels_descs):
            nodes.append({
                "id": node_id,
                "label": label,
                "desc": desc,
                "isInput": is_input,
                "value": 0.0,
                "speed": 1.0,
                "bias": round(random.uniform(-0.1, 0.1), 4),
                "amp": 1,
                "x": x,
                "y": 60 + j * (640 // max(n, 1)),
            })
            ids.append(node_id)
            node_id += 1
        layers.append({"kind": kind, "name": name, "activation": activation,
                       "node_ids": ids})
        return ids

    in_ids = add_layer("Input", "Situation", "Linear", INPUTS, is_input=True, x=120)
    h1 = add_layer("Hidden", "Deliberation-1", "ReLU",
                   [(f"D1_{k}", "Deliberation unit") for k in range(12)], x=420)
    h2 = add_layer("Hidden", "Deliberation-2", "ReLU",
                   [(f"D2_{k}", "Deliberation unit") for k in range(10)], x=720)
    out_ids = add_layer("Output", "Council action", "Sigmoid",
                        OUTPUTS, x=1020)

    # fully-connected feedforward edges, small random init
    edges = []
    for a_layer, b_layer in [(in_ids, h1), (h1, h2), (h2, out_ids)]:
        fan = len(a_layer)
        s = math.sqrt(2.0 / fan)
        for a in a_layer:
            for b in b_layer:
                edges.append({"a": a, "b": b,
                              "w": round(random.gauss(0, s), 5)})

    # lessons
    in_index = {label: k for k, (label, _) in enumerate(INPUTS)}
    out_index = {label: k for k, (label, _) in enumerate(OUTPUTS)}
    lessons = []
    for name, in_d, out_d, rationale, source in LESSONS:
        inv = [0.0] * NI
        for k, v in in_d.items():
            inv[in_index[k]] = float(v)
        outv = [0.0] * NO
        for k, v in out_d.items():
            outv[out_index[k]] = float(v)
        lessons.append({"in": inv, "out": outv,
                        "desc": f"{name} — {rationale} [{source}]"})

    brain = {
        "version": 1,
        "learning_rate": 0.01,
        "l1": 0.0,
        "l2": 0.0001,
        "epochs": 5000,
        "target_mse": 0.01,
        "theme": 0,
        "nodes": nodes,
        "layers": layers,
        "edges": edges,
        "lessons": lessons,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(brain, f, ensure_ascii=False, indent=1)
    print(f"wrote {OUT}: {len(nodes)} nodes, {len(edges)} edges, "
          f"{len(lessons)} lessons")


if __name__ == "__main__":
    build()
