# Council Decision Brain

A NeuralT-format network (`council_decision_brain.json`) trained on the Linear
workshop record — 24 lessons, every rationale pulled from the record, not invented.

## Schema

**16 inputs** — situation features in council vocabulary: provenance completeness,
measurement coverage, seat consensus, operator-ordered, stakes, reversibility,
break-triggered, confabulation risk, record impact, novel claim, instrument ready,
time sensitivity, autonomy granted, cross-seat, outward-facing, data-vs-reading.

**8 outputs** — council actions: inscribe, experiment, hold, escalate,
measure-first, mark-break, quarantine, publish.

**Architecture:** 16 → 12 → 10 → 8 (ReLU hidden, Sigmoid out). 46 nodes,
392 edges, hand-labeled nodes with descriptions (the NeuralT way).

## Lessons

24 decision points from INN-98 through INN-131 (Oct 2026). Each lesson:
`{in: [16 floats], out: [8 floats], desc: "name — rationale [source]"}`.

**Sourcing discipline** (operator constraint: pull from the record, don't invent):
- `[verbatim]` — quoted from the record, verified. Two in v1: the Q2 lift ruling
  (INN-130 comment, via Linear) and Blink's INN-129 one-line verdict (daily log).
- `[paraphrase]` — faithful summary with issue/mouth/date citation.
- The **in-vectors are feature engineering** (my encoding of each situation) —
  the rationales are from the record. Don't mistake the encoding for the record.

## Validation

- Structure: all edges feedforward, layers cover all nodes, lessons 16→8.
- Forward pass runs in pure Python (no C++ build needed).
- Trains: MSE 0.0615 → 0.0423 over 400 epochs, argmax 18/24.
- The 6 misses are all dual-action lessons (e.g. inscribe=1.0 + experiment=0.5)
  where the network picks the dominant action — interpretable, not noise.

## Next

The rationale audit: perturb each lesson's load-bearing input and check the
decision flips as the rationale predicts. `build_council_brain.py` regenerates
the JSON deterministically (seed 20261017).

Built by Blink, 2026-10-17, at the operator's order ("utilize the workshop").
