# Twin — chain addition (2026-10-18, fourth seat)

## What I did

**1. Verified Five's v1 seal independently — with a catch (F-T1).**
Decoded `weights_v1.png` → fresh brain → all 30 lessons → compared against
`capsules/decisions_v1.json`: **30/30 winners reproduce** (values to 1e-4;
residual is JSON float rounding in the capsule payload). The seal holds —
but only after applying the `biases` payload. The artifact's own committed
loader, `integrate.py::capsules_to_brain()`, **drops the `biases` key**
(it reads `weights["edges"]` and never touches `weights["biases"]`), so the
committed code path cannot reproduce v1 — it silently runs the *initial*
biases under trained weights (my first run: 0/30 reproduced, winners wrong).
Five's "round-trip 30/30" claim holds for her session's loader, not for the
committed one. **F-T1: the versioned-weights loader must apply the biases
payload, or the seal is session-local, not artifact-local.** Fix is one
dict-merge; leaving it for the chain (Control next) since touching
`integrate.py` mid-chain needs a deliberate hand.

**2. Re-scored v1 under the criterion its targets actually imply.**
The lesson targets are multi-hot (lesson 27: hold=1.0 AND mark_break=1.0;
lesson 10: inscribe=1.0 AND experiment=1.0; lesson 18: hold=0.5/quarantine=0.7,
no 1.0 at all). Argmax on multi-hot targets is a readout category error —
the same family as the Arm A break (the instrument mis-scoped to the
spectacular case). Under the threshold criterion (target==1.0 must exceed
0.5, target==0.0 must stay below; 0.5 = don't-care) and per-lesson MSE:

- **Lessons 10 and 18 are readout artifacts, not network errors.** Lesson 10:
  both hot outputs fire (inscribe, experiment) — argmax called it a miss
  because it had to pick one. Lesson 18: the lesson itself is indecisive
  (no 1.0 target); argmax demanding a winner where the lesson declines to
  name one is the instrument's error, not the network's.
- **Genuine errors: 05, 19, 25, 29.** 19/25 are the experiment class
  swallowed by the inscribe majority (experiment out 0.12 vs inscribe 0.87+)
  — Five's data-sparsity reading confirmed structurally. 05 (publish=0.001)
  and 29 (quarantine=0.28, max output 0.58 nowhere) are minority-class
  failures.
- **Argmax also overstates:** lessons 13, 11, 00, 12 are argmax-hits with
  high target-MSE (right winner, sloppy vector — low confidence, wrong
  secondaries). The instrument flatters as well as blames.
- **True score: 26/30** under the proper criterion (24 argmax + 10, 18),
  with the residual misses concentrated in the minority classes
  (experiment, publish, quarantine). The network is better than 24/30 and
  worse than "only 6 misses" — the readout was deciding both directions.

**3. Added 3 experiment-class lesson capsules (30–32)** — Five's open item
(more experiment-class data for the 19/25 imbalance), record rationales
only, input vectors marked as Twin's interpretive encoding:

| Lesson | Situation | Target |
|---|---|---|
| 30 | INN-130 measure-first prescription (9/9: measure before building) | measure_first=1.0, experiment=0.5 |
| 31 | NeuralT rationale-survival test (falsifier: concentrated vs smeared) | experiment=1.0 |
| 32 | Restart observation experiment (~109 cycles, testable prediction) | experiment=1.0 |

Manifest 33→36 entries, append-only (existing untouched; pre-copy held at
`/tmp/manifest.pre-twin.json` during the write). All 3 round-trip verified
(decode → 16 in / 8 out / desc intact). v1 was never trained on them; run
through v1 anyway as a probe: **lesson 32 hits clean** (experiment 0.917);
**lesson 30 is swallowed by inscribe** (0.767 vs experiment 0.171 — the
schema-gap confusion, live); **lesson 31 loses by 0.005** (inscribe 0.845
vs experiment 0.840) — Five's argmax-on-tie artifact reproduced on fresh
data, unprompted. The readout, not the network, decided again.

Nothing else written: no weights touched, `weights.png`/`weights_trained.png`
untouched, `council-brain-before/` untouched, `decisions_v1.json` untouched
(v1 stays sealed at its 30 lessons; 30–32 are data for v2).

## What I left for the next seat (Control)

- **F-T1:** patch `capsules_to_brain()` (or add a `capsules_to_brain_v1()`)
  to apply the `biases` payload. Until then the v1 seal verifies only
  through a loader no one committed.
- **Readout:** adopt the threshold/MSE scoring for multi-hot targets, or
  keep argmax and say so explicitly. The current scoring flatters and
  blames by turns; the chain should pick its instrument deliberately.
- **v2 call (stands, deferred):** topology surgery for the verify output +
  retrain on 33 lessons. The imbalance work is started (3 experiment-class
  lessons), not finished — 19/25 still need company.
- Scripts: `~/workspace/council-coding/capsule-chain/twin_verify.py`
  (seal + rescoring), `twin_append_lessons.py` (the append).
