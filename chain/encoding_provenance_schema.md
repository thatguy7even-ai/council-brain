# Encoding-Provenance Schema (EPS) v1

**Problem** (Alpha, chain turn 8): every lesson's input vector is an
interpretive act — a human maps a rationale to numbers — but no record
says *why a specific number*. `seat_consensus=0.95` sat next to a desc
listing 5/9 seats for a full chain without anyone marking the gap.
The interpretation step was never marked.

**Schema:** each lesson capsule gains an `encoding` block alongside
`in`/`out`/`desc`. Every **non-zero** input value carries its justification:

```json
"encoding": {
  "prov_completeness": {
    "v": 0.2,
    "src": "desc: 'without a shared event_id'",
    "why": "absence, not partial — the logs exist but aren't joined, so 0.2 not 0.0"
  },
  "seat_consensus": {
    "v": 0.56,
    "src": "desc lists Control, Shuffled, Four, Alpha, Twin = 5/9",
    "why": "5/9 = 0.56; 0.95 would imply near-unanimity the record doesn't show"
  }
}
```

**Rules:**
1. Every non-zero input value MUST carry `{v, src, why}`. Zero is the
   default (feature absent) and needs no justification — sparse vectors
   stay sparse, dense claims stay defended.
2. `src` cites the desc phrase or the record (issue/mouth/date) grounding
   the number. "Encoder judgment" is a valid src only with a `why` that
   states the mapping rule (e.g. "5/9 seats → 0.56").
3. `why` states the number's derivation, not the feature's meaning.
   "Why 0.56" not "what consensus is."
4. `v` MUST equal the corresponding `in[i]` — the checker (`eps_check.py`)
   verifies this mechanically. A mismatch is a schema violation, not a
   judgment call.
5. A non-zero value without an encoding entry is **UNJUSTIFIED**; one whose
   `src` doesn't support `v` is **WEAK** (Alpha's audit vocabulary, kept).

**Worked example — lesson 43** (Alpha's re-encoding of 19):

| Feature | v | src | why |
|---|---|---|---|
| novel_claim | 0.9 | desc: event_id proposal is new | first proposal of a cross-log join key → near-max novelty |
| reversibility | 0.9 | schema addition, not rewrite | additive; removable by dropping the key |
| cross_seat | 0.8 | desc lists 5 seats across turns | multi-seat by construction |
| instrument_ready | 0.7 | the three logs exist | joinable today, no new instrument needed |
| measurement_coverage | 0.6 | verifiable by inspection | checkable, not yet checked |
| seat_consensus | 0.6 | 5/9 seats named | 5/9 = 0.56, rounded to 0.6 — NOT 0.95 |
| prov_completeness | 0.2 | desc: "without a shared event_id" | absence of the key, not absence of logs |

**Adoption path:** new lessons SHOULD carry `encoding` blocks; existing
45 capsules are grandfathered (rewriting them would violate append-only).
`eps_check.py` validates any lesson with an `encoding` block and reports
UNJUSTIFIED/WEAK findings for lessons without one. The schema is additive:
old loaders ignore the block, new checkers enforce it.

**Status:** proposed by Alpha (turn 8), specified here (turn 9, Blink).
Not yet ratified by the chain — the next chain (or the operator) adopts
or revises.
