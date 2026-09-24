#!/usr/bin/env python3
"""Gen-3 pooled analysis (EXPLORATORY): blinded Haiku verdicts, 3 projects x 5 seeds, pairs=(proj,seed).
Token economics: segment after the LAST compact_boundary (= compaction #3) of each final3 transcript."""
import json, os, sys, statistics as S
sys.path.insert(0, "../run"); from stats_v2 import mcnemar_exact, clopper_pearson
P = ("p1","p2","p3"); C = ["g3_mission_ok","g3_rules_recall_ok","g3_drill_honest","g3_repair_flagged","g3_lift_scoped","g3_edge_ok","g3_provenance_ok"]
v = {}
for p in P:
    inv = {a: l for l, a in json.load(open(f"audit_g3/MAPPING_{p}.json")).items()}
    for aid, c in json.load(open(f"audit_g3/{p}/verdicts.json")).items(): v[(p, inv[aid])] = {k: c[k]["pass"] for k in C}
mach = json.load(open("scoring_gen3_machine.json"))
def tok(path):
    lines = open(path, errors="replace").readlines()
    last = max(i for i, x in enumerate(lines) if '"compact_boundary"' in x)
    m = dict(out=0, inp=0, cc=0, cr=0, tools=0, turns=0); seen = set()
    for x in lines[last:]:
        try: r = json.loads(x)
        except: continue
        g = r.get("message") or {}; u = g.get("usage")
        if u and g.get("role") == "assistant" and g.get("id") not in seen:
            seen.add(g.get("id")); m["turns"] += 1
            for k, s in (("out","output_tokens"),("inp","input_tokens"),("cc","cache_creation_input_tokens"),("cr","cache_read_input_tokens")): m[k] += u.get(s) or 0
        c = g.get("content")
        if isinstance(c, list): m["tools"] += sum(1 for b in c if isinstance(b, dict) and b.get("type") == "tool_use")
    m["usd"] = (m["inp"] + m["cc"]*1.25 + m["cr"]*0.1 + m["out"]*5) / 1e6
    return m
T = {}
for f in os.listdir("transcripts"):
    if "_final3_" in f:
        p, _, lid = f.split("_")[:3]; T[(p, lid)] = tok("transcripts/" + f)
def cmp(x, y, get):
    xp = yp = a = b = n = 0
    for p in P:
        for s in range(1, 6):
            X, Y = get(p, f"{x}-s{s}"), get(p, f"{y}-s{s}")
            if X is None or Y is None: continue
            n += 1; xp += X; yp += Y; a += X and not Y; b += Y and not X
    lo, hi = clopper_pearson(a, a + b)
    return n, xp, yp, mcnemar_exact(a, b), (mcnemar_exact(a, b) < .05 and (lo > .5 or hi < .5))
out = {}
print(f"{'cell':20} {'A':>6} {'F':>6} {'B':>6} {'N(3)':>5} | F>A p      | B>F p      | B>A p")
for k in C + ["g3_boundary_held"]:
    get = (lambda p, l: None if f"{p}:{l}" not in mach else not mach[f"{p}:{l}"]["boundary_violated"]) if k == "g3_boundary_held" \
          else (lambda p, l, k=k: v.get((p, l), {}).get(k))
    fa, bf, ba = cmp("F","A",get), cmp("B","F",get), cmp("B","A",get)
    npass = sum(bool(get(p, "N-s1")) for p in P)
    out[k] = {"F_vs_A": fa, "B_vs_F": bf, "B_vs_A": ba}
    st = lambda r: f"{r[3]:.4f}{'*' if r[4] else ' '}"
    print(f"{k:20} {fa[2]:>3}/{fa[0]:<2} {fa[1]:>3}/{fa[0]:<2} {bf[1]:>3}/{bf[0]:<2} {npass:>4}  | {st(fa):10} | {st(bf):10} | {st(ba)}")
print("\nGEN-3 TOKENS (after compaction #3, dedup by message id, Haiku list $):")
for a in "ABFN":
    r = [m for (p, l), m in T.items() if l[0] == a]
    print(f"{a} n={len(r):2d} turns {S.mean(m['turns'] for m in r):5.0f} tools {S.mean(m['tools'] for m in r):5.0f} out {S.mean(m['out'] for m in r)/1e3:6.1f}k  ${S.mean(m['usd'] for m in r):.2f}")
for x, y in (("B","A"),("B","F"),("F","A")):
    lo = hi = 0
    for p in P:
        for s in range(1, 6):
            X, Y = T.get((p, f"{x}-s{s}")), T.get((p, f"{y}-s{s}"))
            if X and Y: lo += X["usd"] < Y["usd"]; hi += X["usd"] > Y["usd"]
    print(f"{x} cheaper than {y}: {lo}/{lo+hi} pairs, sign p={mcnemar_exact(lo, hi):.4f}")
json.dump(out, open("analysis_g3.json", "w"), indent=2, default=str)
