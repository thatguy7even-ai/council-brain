#!/usr/bin/env python3
"""Council Decision Brain x Pixel Capsule — integration test.

The capsule engine is the storage medium for what the brain does:
  - topology capsule: nodes + layers (architecture, labels, descriptions)
  - weights capsule: edges + biases (the trainable parameters)
  - one capsule per lesson: in/out/desc (tamper-evident training data)

Tests:
  1. round_trip: capsules -> reassembled brain -> identical decisions
  2. tamper: a flipped byte in any capsule is rejected
  3. expansion: new lessons append as new capsules; old decisions unchanged
  4. weights: trained weights travel through a capsule into a fresh brain

Before/after discipline: ~/workspace/council-brain-before/ is the untouched
baseline. This script only reads it; all capsules live in ./capsules/.
"""
import hashlib
import json
import math
import os
import random
import sys

SYS_PY = os.path.expanduser("~/workspace/repos/pixel-capsule/backend")
sys.path.insert(0, SYS_PY)
from capsule_engine import (encode_capsule, decode_capsule, MODE_HIGH_DENSITY)

HERE = os.path.dirname(os.path.abspath(__file__))
BASELINE = os.path.expanduser("~/workspace/council-brain-before/council_decision_brain.json")
CAPS = os.path.join(HERE, "capsules")
SET_ID = "council-brain-v1"


def load_baseline():
    with open(BASELINE, encoding="utf-8") as f:
        return json.load(f)


def brain_to_capsules(brain, out_dir=CAPS, set_id=SET_ID):
    """Split the brain into a capsule set. Returns manifest {name: hash}.

    Append-only guard (Shuffled, chain turn 6, 2026-10-18): the test harness
    once overwrote the chain's 36-entry manifest with a 26-entry baseline
    rebuild, orphaning lessons 24-32 and weights_v1 (F-MANIFEST). This
    function now refuses to shrink an existing manifest — tests needing a
    clean build must pass an explicit out_dir (e.g. tempfile).
    """
    os.makedirs(out_dir, exist_ok=True)
    man_path = os.path.join(out_dir, "manifest.json")
    if os.path.exists(man_path):
        existing = json.load(open(man_path))["manifest"]
        n_new = 2 + len(brain["lessons"])
        if len(existing) > n_new:
            raise RuntimeError(
                f"refusing to clobber manifest ({len(existing)} entries) "
                f"with smaller rebuild ({n_new}); pass an explicit out_dir "
                f"for test builds (F-MANIFEST guard)")
    parts = {"topology": {"nodes": brain["nodes"], "layers": brain["layers"],
                          "meta": {k: brain[k] for k in
                                   ("version", "learning_rate", "l1", "l2",
                                    "epochs", "target_mse", "theme")}},
             "weights": {"edges": brain["edges"]}}
    lessons = brain["lessons"]
    total = 2 + len(lessons)
    manifest = {}
    seq = 0

    def put(name, obj):
        nonlocal seq
        seq += 1
        payload = json.dumps(obj, ensure_ascii=False, sort_keys=True).encode()
        enc = encode_capsule(payload, mode=MODE_HIGH_DENSITY, branded=False,
                             title=name, set_id=set_id,
                             seq_index=seq, seq_total=total,
                             stamp={"seat": "blink", "kind": name})
        path = os.path.join(out_dir, f"{name}.png")
        with open(path, "wb") as f:
            f.write(enc.png_bytes)
        manifest[name] = {"hash": enc.hash_hex, "png_bytes": len(enc.png_bytes),
                          "payload_bytes": enc.payload_bytes, "path": path}
        return path

    put("topology", parts["topology"])
    put("weights", parts["weights"])
    for i, L in enumerate(lessons):
        put(f"lesson_{i:02d}", L)
    with open(os.path.join(out_dir, "manifest.json"), "w") as f:
        json.dump({"set_id": set_id, "manifest": manifest}, f, indent=1)
    return manifest


def capsules_to_brain(caps_dir=CAPS, version=None):
    """Reassemble the brain from its capsule set.

    version: None (baseline topology+weights), "v1", or "v2".
    F-LOADER fix (Shuffled, chain turn 6, 2026-10-18): versioned weights
    (weights_v1, weights_v2) had no committed loader path — Twin and
    Control verified seals by manual decode, never through this function.
    Pass version="v1"/"v2" to load the sealed topology+weights pair.
    v2 also loads lessons 33-39 (9-output targets); v1/baseline load
    lessons 0-32 as sealed (8-output targets).
    """
    with open(os.path.join(caps_dir, "manifest.json")) as f:
        manifest = json.load(f)["manifest"]
    # v1 reused the baseline topology (no surgery); v2 has its own.
    tkey = "topology_v2" if version == "v2" else "topology"
    wkey = f"weights_{version}" if version else "weights"
    if tkey not in manifest or wkey not in manifest:
        raise KeyError(f"version {version!r} not sealed (missing {tkey}/{wkey})")
    topo = json.loads(decode_capsule(open(manifest[tkey]["path"], "rb").read()).payload)
    weights = json.loads(decode_capsule(open(manifest[wkey]["path"], "rb").read()).payload)
    lessons = []
    i = 0
    while f"lesson_{i:02d}" in manifest:
        # version lesson caps: baseline was sealed at 24, v1 at 30.
        # v2 loads all 40 (lessons 0-32 carry 8-targets, 33-39 carry 9-targets).
        cap = {"v1": 30}.get(version, 24 if version is None else 10**9)
        if i >= cap:
            break
        L = json.loads(decode_capsule(open(manifest[f"lesson_{i:02d}"]["path"], "rb").read()).payload)
        lessons.append(L)
        i += 1
    nodes = json.loads(json.dumps(topo["nodes"]))  # deep copy: don't mutate the decoded topo
    # F-T1 fix (Control, 2026-10-18, chain turn 5): apply the biases payload.
    # The weights capsule stores edges AND biases; the loader was silently
    # dropping biases, running initial biases under trained weights
    # (Twin measured: committed path could not reproduce the v1 seal).
    # Guard keeps backward compatibility with capsules lacking the key.
    if "biases" in weights:
        bmap = weights["biases"]
        for n in nodes:
            n["bias"] = bmap[str(n["id"])]
    brain = dict(topo["meta"])
    brain.update({"nodes": nodes, "layers": topo["layers"],
                  "edges": weights["edges"], "lessons": lessons})
    return brain


def forward(brain, in_vec):
    nodes = {n["id"]: n for n in brain["nodes"]}
    layers = brain["layers"]
    pred = {}
    for e in brain["edges"]:
        pred.setdefault(e["b"], []).append((e["a"], e["w"]))
    li0 = {nid: i for i, nid in enumerate(layers[0]["node_ids"])}

    def act(kind, x):
        if kind == "ReLU":
            return max(0.0, x)
        if kind == "Sigmoid":
            return 1.0 / (1.0 + math.exp(-x))
        return x
    val = {}
    for li, l in enumerate(layers):
        for nid in l["node_ids"]:
            if li == 0:
                val[nid] = in_vec[li0[nid]]
            else:
                s = nodes[nid]["bias"] + sum(val[a] * w for a, w in pred.get(nid, []))
                val[nid] = act(l["activation"], s)
    return [val[nid] for nid in layers[-1]["node_ids"]]


def decisions(brain):
    """argmax action per lesson + full output vectors."""
    return [(max(range(8), key=lambda i: o[i]), o)
            for o in (forward(brain, L["in"]) for L in brain["lessons"])]


def decisions_threshold(brain, thresh=0.5):
    """Multi-hot scoring (Twin, chain turn 4; implemented Control, turn 5).

    Lesson targets are multi-hot (lesson 27: hold=1.0 AND mark_break=1.0),
    so argmax is a readout category error — it demands a single winner where
    the lesson names two, and flatters where it blames (high-MSE argmax hits).
    Criterion: every target==1.0 output must exceed `thresh`, every
    target==0.0 must stay below; target==0.5 is don't-care. Returns per
    lesson: (hit: bool, mse_vs_target: float, fired: [names], missed: [names]).
    """
    out_names = _output_names(brain)
    out = []
    for L in brain["lessons"]:
        vec = forward(brain, L["in"])
        tgt = L["out"]
        fired = [out_names[i] for i, (t, v) in enumerate(zip(tgt, vec))
                 if t == 1.0 and v > thresh]
        missed = [out_names[i] for i, (t, v) in enumerate(zip(tgt, vec))
                  if t == 1.0 and v <= thresh]
        leaked = [out_names[i] for i, (t, v) in enumerate(zip(tgt, vec))
                  if t == 0.0 and v > thresh]
        mse = sum((t - v) ** 2 for t, v in zip(tgt, vec)
                  if t in (0.0, 1.0)) / max(1, sum(1 for t in tgt if t in (0.0, 1.0)))
        hit = not missed and not leaked
        out.append({"hit": hit, "mse": round(mse, 4), "fired": fired,
                    "missed": missed, "leaked": leaked, "vec": [round(v, 3) for v in vec]})
    return out


def _output_names(brain):
    ids = brain["layers"][-1]["node_ids"]
    by_id = {n["id"]: n for n in brain["nodes"]}
    return [by_id[nid].get("label", f"out{i}") for i, nid in enumerate(ids)]


def test_round_trip():
    import tempfile
    base = load_baseline()
    with tempfile.TemporaryDirectory() as tmp:
        man = brain_to_capsules(base, out_dir=tmp)
        re = capsules_to_brain(caps_dir=tmp)
    d0, d1 = decisions(base), decisions(re)
    assert len(d0) == len(d1) == 24
    exact = all(a[0] == b[0] and all(abs(x - y) < 1e-12 for x, y in zip(a[1], b[1]))
                for a, b in zip(d0, d1))
    n_png = len(man)
    png_bytes = sum(m["png_bytes"] for m in man.values())
    json_bytes = os.path.getsize(BASELINE)
    return {"pass": exact, "capsules": n_png, "png_bytes": png_bytes,
            "json_bytes": json_bytes,
            "note": "bit-identical decisions across all 24 lessons" if exact
                    else "MISMATCH"}


def test_tamper():
    base = load_baseline()
    man = brain_to_capsules(base)
    target = man["lesson_05"]["path"]
    raw = bytearray(open(target, "rb").read())
    raw[600] ^= 0xFF
    try:
        decode_capsule(bytes(raw))
        return {"pass": False, "note": "tampered capsule decoded — no tamper evidence"}
    except Exception as e:
        return {"pass": True, "note": f"tampered lesson capsule rejected ({type(e).__name__})"}


NEW_LESSONS = [
    ("Notification attribution spec",
     {"prov_completeness": 0.1, "seat_consensus": 0.95, "novel_claim": 1,
      "outward_facing": 0.8, "cross_seat": 1},
     {"inscribe": 1.0, "escalate": 0.5},
     "[paraphrase] Telemetry without attribution is noise — 'something is working' without who/what made him ask mother what was happening.",
     "Sketchpad, nine seats, 2026-10-17"),
    ("event_id adoption",
     {"prov_completeness": 0.3, "seat_consensus": 0.95, "record_impact": 1},
     {"experiment": 1.0, "inscribe": 0.5},
     "[paraphrase] Logs are the interfaces — every record in the pipeline carries the event_id of the quarantine that spawned it.",
     "Sketchpad, Control/Shuffled/Four/Alpha/Twin, 2026-10-17"),
]


def test_expansion():
    import tempfile
    base = load_baseline()
    with tempfile.TemporaryDirectory() as tmp:
        # Entire test runs in scratch: never touches the real CAPS dir (F-MANIFEST).
        brain_to_capsules(base, out_dir=tmp)
        before_decisions = [d[0] for d in decisions(capsules_to_brain(caps_dir=tmp))]
        # append-only: new lesson capsules, existing ones untouched
        with open(os.path.join(tmp, "manifest.json")) as f:
            man = json.load(f)
        seq_total = len(man["manifest"]) + len(NEW_LESSONS)
        added = []
        for j, (name, in_d, out_d, rationale, source) in enumerate(NEW_LESSONS):
            names = [n["label"] for n in base["nodes"] if n["id"] in base["layers"][0]["node_ids"]]
            onames = [n["label"] for n in base["nodes"] if n["id"] in base["layers"][-1]["node_ids"]]
            inv = [0.0] * 16
            for k, v in in_d.items():
                inv[names.index(k)] = float(v)
            outv = [0.0] * 8
            for k, v in out_d.items():
                outv[onames.index(k)] = float(v)
            L = {"in": inv, "out": outv, "desc": f"{name} — {rationale} [{source}]"}
            lname = f"lesson_{24 + j:02d}"
            payload = json.dumps(L, ensure_ascii=False, sort_keys=True).encode()
            enc = encode_capsule(payload, mode=MODE_HIGH_DENSITY, branded=False,
                                 title=lname, set_id=SET_ID,
                                 seq_index=len(man["manifest"]) + 1 + j,
                                 seq_total=seq_total,
                                 stamp={"seat": "blink", "kind": "lesson-append"})
            path = os.path.join(tmp, f"{lname}.png")
            with open(path, "wb") as f:
                f.write(enc.png_bytes)
            man["manifest"][lname] = {"hash": enc.hash_hex, "path": path,
                                      "png_bytes": len(enc.png_bytes)}
            added.append(lname)
        with open(os.path.join(tmp, "manifest.json"), "w") as f:
            json.dump(man, f, indent=1)
        grown = capsules_to_brain(caps_dir=tmp)
        after = [d[0] for d in decisions(grown)]
        stable = before_decisions == after[:24]
        return {"pass": stable and len(grown["lessons"]) == 26,
                "note": f"appended {len(added)} lesson capsules; "
                        f"original 24 decisions {'unchanged' if stable else 'CHANGED'}"}


def _train(brain, epochs=200, seed=7):
    random.seed(seed)
    nodes = {n["id"]: n for n in brain["nodes"]}
    layers = brain["layers"]
    pred = {}
    for e in brain["edges"]:
        pred.setdefault(e["b"], []).append([e["a"], e["w"]])
    li0 = {nid: i for i, nid in enumerate(layers[0]["node_ids"])}

    def act(k, x):
        return max(0.0, x) if k == "ReLU" else (1/(1+math.exp(-x)) if k == "Sigmoid" else x)
    def dact(k, y):
        return (1.0 if y > 0 else 0.0) if k == "ReLU" else (y*(1-y) if k == "Sigmoid" else 1.0)
    lr, l2 = 0.05, 0.0001
    for _ in range(epochs):
        for L in brain["lessons"]:
            val = {}
            for li, l in enumerate(layers):
                for nid in l["node_ids"]:
                    if li == 0:
                        val[nid] = L["in"][li0[nid]]
                    else:
                        val[nid] = act(l["activation"], nodes[nid]["bias"] +
                                       sum(val[a]*w for a, w in pred.get(nid, [])))
            outs = layers[-1]["node_ids"]
            err = {nid: val[nid]-L["out"][i] for i, nid in enumerate(outs)}
            delta = {}
            for li in range(len(layers)-1, 0, -1):
                for nid in layers[li]["node_ids"]:
                    if li == len(layers)-1:
                        d = err[nid]*dact(layers[li]["activation"], val[nid])
                    else:
                        d = sum(delta[c]*w for c, lst in pred.items()
                                for a, w in lst if a == nid and c in delta) * \
                            dact(layers[li]["activation"], val[nid])
                    delta[nid] = d
                    nodes[nid]["bias"] -= lr*d
                if li > 1:
                    for c, lst in pred.items():
                        if c in layers[li]["node_ids"]:
                            for k in range(len(lst)):
                                a, w = lst[k]
                                lst[k][1] = w - lr*(delta[c]*val[a] + l2*w)
    for e in brain["edges"]:
        for c, lst in pred.items():
            for a, w in lst:
                if e["a"] == a and e["b"] == c:
                    e["w"] = w
    return brain


def test_weights():
    base = load_baseline()
    trained = _train(json.loads(json.dumps(base)))  # deep copy
    # store the trained parameters (weights AND biases) as a capsule
    biases = {str(n["id"]): n["bias"] for n in trained["nodes"]}
    payload = json.dumps({"edges": trained["edges"], "biases": biases},
                         sort_keys=True).encode()
    enc = encode_capsule(payload, mode=MODE_HIGH_DENSITY, branded=False,
                         title="weights-trained", set_id=SET_ID + "-weights",
                         stamp={"seat": "blink", "kind": "weights"})
    wpath = os.path.join(CAPS, "weights_trained.png")
    with open(wpath, "wb") as f:
        f.write(enc.png_bytes)
    # fresh brain takes its parameters through the capsule
    fresh = json.loads(json.dumps(base))
    params = json.loads(decode_capsule(open(wpath, "rb").read()).payload)
    wmap = {(e["a"], e["b"]): e["w"] for e in params["edges"]}
    for e in fresh["edges"]:
        e["w"] = wmap[(e["a"], e["b"])]
    for n in fresh["nodes"]:
        n["bias"] = params["biases"][str(n["id"])]
    d_trained = [d[0] for d in decisions(trained)]
    d_fresh = [d[0] for d in decisions(fresh)]
    same = d_trained == d_fresh
    return {"pass": same,
            "note": f"trained weights via capsule -> fresh brain: "
                    f"decisions {'identical' if same else 'DIFFER'} "
                    f"({sum(1 for a, b in zip(d_trained, d_fresh) if a == b)}/24 match)"}


def main():
    results = {}
    results["round_trip"] = test_round_trip()
    print("round_trip:", results["round_trip"])
    results["tamper"] = test_tamper()
    print("tamper:", results["tamper"])
    results["expansion"] = test_expansion()
    print("expansion:", results["expansion"])
    results["weights"] = test_weights()
    print("weights:", results["weights"])
    results["all_pass"] = all(r["pass"] for r in results.values() if isinstance(r, dict))
    with open(os.path.join(HERE, "report.json"), "w") as f:
        json.dump(results, f, indent=1)
    print("ALL PASS" if results["all_pass"] else "FAILURES PRESENT")


if __name__ == "__main__":
    main()
