#!/usr/bin/env python3
"""Blink — chain turn 9 (final): v3 retrain on 45 lessons.

- Warm start from sealed weights_v2 (version lineage, not fresh init).
- Lessons 0-32 extended to 9-targets in memory (verify=0.0); capsules untouched.
- lr=0.02 (v2's recovered config; lr=0.05 diverged per Shuffled), 500 epochs.
- Seals weights_v3.png + decisions_v3.json (threshold-scored), append-only.
"""
import copy
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from integrate import (capsules_to_brain, decisions_threshold, _output_names)

CAPS = os.path.join(os.path.dirname(HERE), "capsules")
sys.path.insert(0, "/home/hatch/workspace/repos/pixel-capsule/backend")
from capsule_engine import encode_capsule, decode_capsule, MODE_HIGH_DENSITY


def train(brain, epochs=500, lr=0.02, seed=7, l2=0.0001):
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
    n_out = len(layers[-1]["node_ids"])
    for ep in range(epochs):
        tot = 0.0
        for L in brain["lessons"]:
            tgt = list(L["out"]) + [0.0] * (n_out - len(L["out"]))  # extend 8->9 in memory
            val = {}
            for li, l in enumerate(layers):
                for nid in l["node_ids"]:
                    if li == 0:
                        val[nid] = L["in"][li0[nid]]
                    else:
                        val[nid] = act(l["activation"], nodes[nid]["bias"] +
                                       sum(val[a]*w for a, w in pred.get(nid, [])))
            outs = layers[-1]["node_ids"]
            err = {nid: val[nid]-tgt[i] for i, nid in enumerate(outs)}
            tot += sum(e*e for e in err.values())/len(err)
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
        if (ep+1) % 100 == 0:
            print(f"  epoch {ep+1}: mse={tot/len(brain['lessons']):.4f}", flush=True)
    for e in brain["edges"]:
        for c, lst in pred.items():
            for a, w in lst:
                if e["a"] == a and e["b"] == c:
                    e["w"] = w
    return brain


def main():
    print("loading v2 (45 lessons)...")
    brain = capsules_to_brain(caps_dir=CAPS, version="v2")
    print(f"  lessons: {len(brain['lessons'])}, outputs: {len(brain['layers'][-1]['node_ids'])}")
    pre = decisions_threshold(brain)
    pre_hits = sum(1 for r in pre if r["hit"])
    print(f"  pre-train threshold: {pre_hits}/{len(pre)}")
    print("training v3 (warm start from weights_v2, lr=0.02, 500 epochs)...")
    trained = train(brain)
    post = decisions_threshold(trained)
    post_hits = sum(1 for r in post if r["hit"])
    print(f"  post-train threshold: {post_hits}/{len(post)}")
    names = _output_names(trained)
    print("  key lessons:")
    for i in [19, 25, 40, 41, 42, 43, 44]:
        r = post[i]
        print(f"    lesson {i}: hit={r['hit']} mse={r['mse']} fired={r['fired']} missed={r['missed']}")
    # seal weights_v3 (edges + biases), append-only
    biases = {str(n["id"]): n["bias"] for n in trained["nodes"]}
    payload = json.dumps({"edges": trained["edges"], "biases": biases}, sort_keys=True).encode()
    with open(os.path.join(CAPS, "manifest.json")) as f:
        man = json.load(f)
    seq = len(man["manifest"]) + 1
    enc = encode_capsule(payload, mode=MODE_HIGH_DENSITY, branded=False,
                         title="weights_v3", set_id="council-brain-v1",
                         seq_index=seq, seq_total=seq,
                         stamp={"seat": "blink", "kind": "weights",
                                "train": "warm-start v2, 45 lessons, lr=0.02, 500ep, seed 7"})
    path = os.path.join(CAPS, "weights_v3.png")
    with open(path, "wb") as f:
        f.write(enc.png_bytes)
    man["manifest"]["weights_v3"] = {"hash": enc.hash_hex, "path": path,
                                     "png_bytes": len(enc.png_bytes)}
    # decisions_v3 record
    dec = {"version": "v3", "threshold_hits": f"{post_hits}/{len(post)}",
           "per_lesson": [{"lesson": i, **{k: r[k] for k in ("hit", "mse", "fired", "missed", "leaked")}}
                          for i, r in enumerate(post)]}
    dpath = os.path.join(CAPS, "decisions_v3.json")
    with open(dpath, "w") as f:
        json.dump(dec, f, indent=1)
    man["manifest"]["decisions_v3"] = {"path": dpath}
    with open(os.path.join(CAPS, "manifest.json"), "w") as f:
        json.dump(man, f, indent=1)
    print(f"  sealed weights_v3.png ({len(enc.png_bytes)}B) + decisions_v3.json")
    print(f"  manifest: {seq-1} -> {len(man['manifest'])}")


if __name__ == "__main__":
    main()
