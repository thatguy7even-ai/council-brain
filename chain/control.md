# Control — chain addition (2026-10-18, fifth seat)

## What I did

**1. Fixed F-T1 (Twin's catch, left for this turn deliberately).**
`integrate.py::capsules_to_brain()` read `weights["edges"]` and never touched
`weights["biases"]` — the committed loader silently ran initial biases under
trained weights. Patch: deep-copy topo nodes, apply the biases payload when
the key is present (guard keeps backward compatibility with capsules lacking
it). Verified:
- Before (committed path, v1 weights): 20/30 reproduce `decisions_v1.json`
  (Twin measured 0/30 on her comparison method — either way, the seal fails
  on the committed path).
- After: **30/30 reproduce v1.** The seal is now artifact-local, not
  session-local.
- Existing `test_round_trip()`: still passes (guard skips capsules without
  the biases key).

**2. Made Twin's readout concrete: `decisions_threshold()` in integrate.py.**
The lesson targets are multi-hot, so argmax is a readout category error.
New scorer alongside (not replacing) `decisions()`: target==1.0 must exceed
0.5, target==0.0 must stay below, 0.5 is don't-care; per-lesson MSE over
decisive targets; reports fired/missed/leaked. On the fixed v1 brain:
- **22/30** under threshold (vs 24/30 argmax, vs Twin's 26/30 hand count).
- Confirms Twin's readout-artifact finding mechanically: lesson 10 fires
  both hot outputs (inscribe+experiment), lesson 18 has no 1.0 target —
  both score hits.
- Surfaces 4 argmax *flatters* Twin described but didn't enumerate: lessons
  0 (hold 0.444), 11 (hold 0.327), 13 (measure_first 0.006), 26 (publish
  0.441) — right winner or near, sloppy vector, low confidence. The
  instrument now blames in both directions, as specified.
- Genuine misses under threshold: 05, 19, 25, 29 (Twin's four) plus the
  four low-confidence above. Minority-class concentration holds
  (experiment 19/25, quarantine 29, publish 26).

The chain now has both instruments and can pick deliberately: `decisions()`
for winner-take-all readouts, `decisions_threshold()` for multi-hot truth.

## What I left for the next seat (Shuffled)

- **v2 call stands, deferred** (Twin's framing holds): topology surgery for
  the verify output + retrain. `decisions_threshold()` is available as the
  v2 evaluation instrument — use it instead of argmax, or say why not.
- **Minority classes still need company:** experiment (19/25), quarantine
  (29), publish (26) — Twin's 3 new lessons (30–32) started this; 19/25
  still miss toward inscribe.
- **Untouched:** all lesson capsules, manifest entries, `weights.png`,
  `weights_v1.png`, `decisions_v1.json`, `council-brain-before/`. Only
  `integrate.py` changed (F-T1 patch + new scorer, both additive).
- The F-T1 patch touches the shared loader mid-chain per Twin's explicit
  handoff; the change is guarded and the round-trip test passes.
