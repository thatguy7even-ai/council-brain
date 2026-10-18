#!/usr/bin/env python3
"""J-lens analog for the council brain (Five, 2026-10-18).

Anthropic's Jacobian lens: lens_l(h) = unembed(J_l @ h), J_l = E[d(h_final)/d(h_l)].
What an internal activation is *disposed to make the model say*.

Here: J[u][j] = E_lessons[d(out_j)/d(hidden_u)] via backprop per lesson,
averaged over all 30 lessons (the operating-point corpus). Applied to
weights_v1. Reports each hidden unit's disposed output and finds dead units.

Run: python3 chain/jlens_probe.py
"""
import sys, os, json, math
sys.path.insert(0, '.')
sys.path.insert(0, os.path.expanduser("~/workspace/repos/pixel-capsule/backend"))
from capsule_engine import decode_capsule
from integrate import capsules_to_brain, CAPS

brain = capsules_to_brain()
params = json.loads(decode_capsule(open(os.path.join(CAPS, "weights_v1.png"), "rb").read()).payload)
wmap = {(e["a"], e["b"]): e["w"] for e in params["edges"]}
for e in brain["edges"]:
    e["w"] = wmap[(e["a"], e["b"])]
for n in brain["nodes"]:
    n["bias"] = params["biases"][str(n["id"])]
nodes = {n["id"]: n for n in brain["nodes"]}
layers = brain["layers"]
pred = {}
for e in brain["edges"]:
    pred.setdefault(e["b"], []).append((e["a"], e["w"]))

def act(k, x):
    return max(0.0, x) if k == "ReLU" else (1 / (1 + math.exp(-x)) if k == "Sigmoid" else x)

def dact(k, y):
    return (1.0 if y > 0 else 0.0) if k == "ReLU" else (y * (1 - y) if k == "Sigmoid" else 1.0)

li0 = {nid: i for i, nid in enumerate(layers[0]["node_ids"])}
onames = [nodes[nid]["label"] for nid in layers[-1]["node_ids"]]
hidden_ids = [nid for l in layers[1:-1] for nid in l["node_ids"]]

J = {u: [0.0] * 8 for u in hidden_ids}
for L in brain["lessons"]:
    val = {}
    for li, l in enumerate(layers):
        for nid in l["node_ids"]:
            val[nid] = L["in"][li0[nid]] if li == 0 else act(
                l["activation"], nodes[nid]["bias"] + sum(val[a] * w for a, w in pred.get(nid, [])))
    for j, oid in enumerate(layers[-1]["node_ids"]):
        delta = {oid: dact("Sigmoid", val[oid])}
        for li in range(len(layers) - 2, 0, -1):
            nd = {}
            for nid in layers[li]["node_ids"]:
                s = sum(delta.get(c, 0) * w for c, lst in pred.items()
                        for a, w in lst if a == nid and c in delta)
                nd[nid] = s * dact(layers[li]["activation"], val[nid])
            delta = nd
            for nid in layers[li]["node_ids"]:
                J[nid][j] += nd[nid] / len(brain["lessons"])

dead, disp = [], {}
for u in hidden_ids:
    if all(abs(x) < 1e-9 for x in J[u]):
        dead.append(u)
        continue
    j = max(range(8), key=lambda k: abs(J[u][k]))
    disp.setdefault(onames[j], []).append((u, round(J[u][j], 3)))
print("dead units:", dead)
for out, units in sorted(disp.items()):
    pro = [f"{u}({v:+})" for u, v in units if v > 0]
    anti = [f"{u}({v})" for u, v in units if v < 0]
    print(f"{out}: pro={pro} anti={anti}")
