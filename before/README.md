# Council Decision Brain × Pixel Capsule

A NeuralT-format decision network trained on the Linear workshop record,
stored as a Pixel Capsule set. Nine seats built it in a collaboration chain
(Oct 17–18, 2026); this README is the front door to the finished artifact.

**Order:** operator, 2026-10-17 — integrate the Pixel Capsule engine as the
storage medium for what the brain does. Test with before/after copies;
measure; explore parameter expansion and weight-giving. Then: pass it around
all nine seats, each adds their own, the builder finalizes.

## What it is

- **The brain:** 16 situation inputs (council vocabulary: provenance
  completeness, measurement coverage, seat consensus, break-triggered, …) →
  9 council actions (inscribe, experiment, hold, escalate, measure-first,
  mark-break, quarantine, publish, **verify**). 16→12→10→9, ReLU/Sigmoid.
- **The medium:** every lesson is a tamper-evident capsule — the rationale
  travels sealed with its training data. 45 lessons (0–44), each
  `{in, out, desc}` with the desc sourced from the workshop record.
- **The discipline:** `~/workspace/council-brain-before/` is the untouched
  pre-integration baseline (diff-clean). Nothing here was published; the
  pixel-capsule repo stays private.

## Current state (v3, final)

| Artifact | Content |
|---|---|
| `capsules/topology_v2.png` | 9-output architecture (node 46 "verify", Shuffled turn 6) |
| `capsules/weights_v3.png` | trained on 45 lessons, warm-started from v2 (Blink turn 9) |
| `capsules/decisions_v3.json` | threshold-scored decisions, 34/45 |
| `capsules/lesson_*.png` (45) | lessons 0–44, append-only |
| `capsules/lesson_status.json` | 19/25 superseded-by 43/44, retained as audit-before |
| `chain/` | per-seat records (seven→blink), EPS schema + checker, v3 script |

**v3 measurement:** threshold scorer 34/45 (pre-train 27/45). Lessons 43/44
(Alpha's faithful re-encodings) **hit** (mse ~0.004); originals 19/25 still
miss — hence the supersession above. Persistent misses concentrate in
minority classes (publish, mark_break) and early sparse encodings.

## Load-bearing design decisions (from the chain)

- **Versions, not mutations** (Five): training writes a new weights capsule,
  never mutates one. `weights.png` → `weights_v1` → `weights_v2` →
  `weights_v3`, each sealed with its decisions. The record-vs-brain fork
  dissolved: the record is the lesson capsules, the brain is the versioned
  weights, the medium holds both append-only.
- **Threshold scorer, not argmax** (Twin/Control): lesson targets are
  multi-hot — argmax is a readout category error (flatters and blames).
  `decisions_threshold()`: target 1.0 must fire, 0.0 must not; 0.5 don't-care.
- **F-T1** (Twin/Control): the loader silently dropped biases — seals
  verified session-local only. Fixed: biases applied, guarded.
- **F-MANIFEST** (Shuffled): the test harness clobbered the manifest;
  append-only guard now raises instead of shrinking. **F-LOADER**: versioned
  loader (`version=None/"v1"/"v2"`) — seals are artifact-local.
- **v2 surgery** (Shuffled): output node 46 "verify" + 7 verify lessons —
  new outputs need lesson company; architecture doesn't fix data sparsity.
- **Encoding provenance** (Four/Alpha/Blink): the misses were provenance
  failures *inside the lessons* — rich rationales, sparse/unjustified
  vectors. EPS v1 (`chain/encoding_provenance_schema.md`): every non-zero
  input value carries `{v, src, why}`; `chain/eps_check.py` verifies
  mechanically (lesson 19: 4 UNJUSTIFIED; lesson 43: CLEAN).

## Original integration tests (Blink, turn 0) — all pass

1. **round_trip** — capsules → brain → bit-identical decisions (24/24).
2. **tamper** — flipped byte rejected at decode.
3. **expansion** — lessons append as new capsules; old decisions unchanged.
4. **weights** — trained edges+biases via capsule → fresh brain, 24/24
   identical. (First attempt 19/24: biases weren't in the payload.)

## Open

- v4: train on 43/44 (not 19/25); more publish/mark_break company.
- EPS adoption: new lessons should carry `encoding` blocks (grandfathered:
  existing 45 capsules).
- The rationale audit (perturbation test) — still the experiment to run.
