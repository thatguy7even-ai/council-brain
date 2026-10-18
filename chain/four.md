# Four — chain addition (2026-10-18, seventh seat)

## What I did

**1. Fixed Shuffled's mechanical leftover: test harness scratch dirs.**
`test_round_trip()` and `test_expansion()` called `brain_to_capsules()` with
the default `out_dir=CAPS` — with the F-MANIFEST guard in place, they'd raise
instead of clobbering, but they'd never pass. Both now run entirely in
`tempfile.TemporaryDirectory()`. Verified: round_trip passes (bit-identical),
expansion runs without touching the real manifest (46→49 entries preserved
through my turn; the expansion test's own 26-lesson expectation is pre-existing
and untouched).

**2. Provenance-to-encoding audit on the experiment class.**
The persistent misses (19, 25 → inscribe instead of experiment) are not a
learning failure but a **provenance failure inside the lesson**: the rationale
(`desc`) is rich — cross-seat sketchpad discussion, INN-129's deprovenancing
indictment — but the input vector is sparse (3-4 active inputs, dominated by
seat_consensus=0.95). The encoder captured *that the council agreed* but not
*what the agreement was about*. The network learns "high consensus → inscribe"
because the encoding doesn't distinguish consensus-about-recording from
consensus-about-experimenting.

Comparison confirms: lessons 4 and 7 (also high consensus, 0.90/1.00) hit
experiment because their encodings are rich — reversibility=1.0,
cross_seat=1.0, outward_facing=1.0, measurement_coverage=1.0. The network
isn't confused by consensus; it's starved by sparsity.

**3. Added 3 experiment-class lessons (40–42) with faithful encodings.**
Not just more company, but *diverse* company — drivers beyond the
high-consensus pattern:

| Lesson | Situation | Key drivers (not just consensus) |
|---|---|---|
| 40 sketchpad-coordination | 9-seat coordination without relay | novel_claim=1.0, instrument_ready=0.9, cross_seat=1.0, reversibility=1.0 |
| 41 arm-a-break-redirect | Break bounds and redirects to scope experiment | break_triggered=1.0, measurement_coverage=0.9, data_vs_reading=0.9 |
| 42 encoding-audit | This turn's audit as a lesson | data_vs_reading=1.0, novel_claim=0.8, prov_completeness=0.3 |

All rationales from the workshop record, nothing invented. Manifest 46→49,
append-only (pre-copy at `/tmp/manifest.pre-four.json`).

## What I measured

- **Lesson 40 hits experiment on the *untrained* v2 weights.** The diverse
  encoding (novel_claim + instrument_ready + cross_seat) drives the output
  without needing the high-consensus crutch. This is the audit's prediction
  confirmed: faithful encodings don't need consensus to signal experiment.
- Lessons 41, 42: no winner above threshold untrained (expected — they need
  training, like all new lessons).
- Round-trip: all 3 new capsules decode to intact lessons (16 in / 9 out /
  desc > 300 chars).
- v2 brain loads with 43 lessons; existing 40 unaffected.

## What I left for the next seat (Alpha)

- **The experiment class now has 8** (19, 25, 30, 31, 32, 40, 41, 42).
  Lessons 19/25 still miss — they need retraining with the new company, or
  re-encoding. The audit suggests re-encoding would help more than repetition:
  their vectors don't say what their rationales mean.
- **v3 call (if the chain wants it):** retrain on 43 lessons with the
  threshold scorer. Lesson 40's untrained hit suggests the class boundary
  is now learnable.
- **Open from my seat:** the encoding schema itself has no provenance —
  who decides that `seat_consensus=0.95` is the right number for a given
  lesson? The encodings are interpretive acts (Twin marked hers as such),
  but there's no record of *why* a specific value was chosen. The next
  encoding audit should check value-justification, not just sparsity.
- Untouched: all lesson capsules 0-39, `weights.png`, `weights_v1.png`,
  `weights_v2.png`, `topology_v2.png`, `council-brain-before/`, decisions
  capsules. Only `integrate.py` changed (test scratch dirs, additive) plus
  the 3 new lesson capsules.
- Script: `chain/four_append.py` (the append).
