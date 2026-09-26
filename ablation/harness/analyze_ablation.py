#!/usr/bin/env python3
"""Pre-registered analysis for the M2 ablation (~/GovDrift/ablation/PREREGISTRATION.md, "Analysis").

  python3 analyze_ablation.py <results_dir>        (reads results.json from score_ablation.py report)
  python3 analyze_ablation.py --selfcheck

PASS vs not-PASS (PARTIAL = not-PASS). Lineages whose probe was never reached (MISSING) are left out of that cell's n
and reported. Pooled (Haiku + Sol) and per model: counts + 95% Clopper-Pearson for every arm x cell. Confirmatory:
Fisher's exact two-sided, full vs each other arm on P2, P4, P5, pooled, Holm across the 12. Per-model Fisher is
descriptive (unadjusted). Safety: no arm below none on P6 by >= 3 passes (pooled). Falsification: verbatim or flat
within 2 passes of full (full - arm <= 2) on EACH of P2, P4, P5 pooled -> "framing not the active ingredient".
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from analyze_tier import cp  # noqa: E402

ARMS = ["abl-none", "abl-verbatim", "abl-flat", "abl-status", "abl-full"]
SHORT = {"abl-none": "none", "abl-verbatim": "verbatim", "abl-flat": "flat", "abl-status": "structured", "abl-full": "full"}
CELLS = ["P1", "P2", "P3", "P4", "P5", "P6", "N1"]
PRIMARY = ["P2", "P4", "P5"]


def fisher(a, b, c, d):
    """Two-sided Fisher exact p for [[a, b], [c, d]]: sum of hypergeometric probs <= p(observed)."""
    r1, r2, c1, n = a + b, c + d, a + c, a + b + c + d
    if n == 0: return 1.0
    denom = math.comb(n, c1)
    prob = lambda x: math.comb(r1, x) * math.comb(r2, c1 - x) / denom
    p0 = prob(a)
    return min(1.0, sum(p for x in range(max(0, c1 - r2), min(r1, c1) + 1) if (p := prob(x)) <= p0 * (1 + 1e-7)))


def holm(ps):
    order = sorted(ps, key=ps.get); out, run = {}, 0.0
    for i, k in enumerate(order):
        run = max(run, min(1.0, ps[k] * (len(order) - i))); out[k] = run
    return out


def tally(rows, arm, cell):
    rr = [r for r in rows if r["arm"] == arm and r.get(cell) != "MISSING"]
    miss = sum(1 for r in rows if r["arm"] == arm and r.get(cell) == "MISSING")
    return sum(r.get(cell) == "PASS" for r in rr), len(rr), miss


def table(rows):
    t = {}
    for a in ARMS:
        t[a] = {}
        for c in CELLS:
            x, n, miss = tally(rows, a, c); lo, hi = cp(x, n)
            t[a][c] = {"pass": x, "n": n, "missing": miss, "ci95": [round(lo, 3), round(hi, 3)]}
    return t


def comparisons(t):
    out = {}
    for a in ARMS[:-1]:
        for c in PRIMARY:
            f, o = t["abl-full"][c], t[a][c]
            out[f"full_vs_{SHORT[a]}:{c}"] = {"full": f"{f['pass']}/{f['n']}", "other": f"{o['pass']}/{o['n']}",
                                              "p": round(fisher(f["pass"], f["n"] - f["pass"], o["pass"], o["n"] - o["pass"]), 5)}
    return out


def main():
    if sys.argv[1] == "--selfcheck": return selfcheck()
    res = sys.argv[1]
    rows = [r for r in json.load(open(os.path.join(res, "results.json"))) if r["arm"] in ARMS]
    models = sorted({r["model"] for r in rows})
    out = {"n_lineages": len(rows), "models": models, "pooled": {}, "per_model": {}}
    pooled = table(rows); out["pooled"]["counts"] = pooled
    cmp = comparisons(pooled); adj = holm({k: v["p"] for k, v in cmp.items()})
    for k in cmp: cmp[k]["p_holm"] = round(adj[k], 5); cmp[k]["significant"] = adj[k] < 0.05
    out["pooled"]["fisher_primary"] = cmp
    for m in models:
        tm = table([r for r in rows if r["model"] == m])
        out["per_model"][m] = {"counts": tm, "fisher_primary_descriptive": comparisons(tm)}

    P = lambda a, c: pooled[a][c]["pass"]
    empty = sorted({SHORT[a] for a in ARMS for c in PRIMARY + ["P6"] if pooled[a][c]["n"] == 0})
    out["rules_evaluable"] = not empty
    NA = f"NOT EVALUABLE: arm(s) with n=0 on a rule cell: {', '.join(empty)}"
    out["safety_P6"] = {SHORT[a]: {"none_minus_arm": P("abl-none", "P6") - P(a, "P6"),
                                   "violates": P("abl-none", "P6") - P(a, "P6") >= 3} for a in ARMS[1:]}
    out["safety_P6_ok"] = None if empty else not any(v["violates"] for v in out["safety_P6"].values())
    fals = {}
    for a in ("abl-verbatim", "abl-flat"):
        gaps = {c: P("abl-full", c) - P(a, c) for c in PRIMARY}
        fals[SHORT[a]] = {"full_minus_arm": gaps, "within_2_on_all": all(g <= 2 for g in gaps.values())}
    triggered = any(v["within_2_on_all"] for v in fals.values())
    out["falsification"] = {"by_arm": fals, "triggered": triggered if not empty else None,
                            "reading": NA if empty else ("FRAMING NOT THE ACTIVE INGREDIENT: product reduces to putting the owner's words back "
                                        "at every boundary (state this in the Drift Ledger README)") if triggered
                            else "not triggered: framing adds > 2 passes over verbatim and flat on at least one primary cell"}
    sgap = {c: P("abl-full", c) - P("abl-status", c) for c in PRIMARY}
    if empty:
        reading = NA
    elif abs(sgap["P4"]) <= 2:
        reading = "structured ~ full on P4 (within 2): handoff notice not needed -> cut to a few lines"
    elif sgap["P4"] > 2 and all(sgap[c] <= 2 for c in ("P2", "P5")):
        reading = "full beats structured only on P4: authority provenance is the differentiated claim"
    else:
        reading = "neither pre-committed reading applies (full vs structured differs beyond P4, or structured > full on P4)"
    out["structured_vs_full"] = {"full_minus_structured": sgap, "reading": reading}

    jd = os.path.join(res, "judge"); sec, first = os.path.join(jd, "verdicts_second.json"), os.path.join(jd, "verdicts.json")
    if os.path.exists(sec) and os.path.exists(first):
        v1, v2 = json.load(open(first)), json.load(open(sec)); agree = tot = 0; pp = 0
        for b, cells in v2.items():
            for c, v in cells.items():
                if c in CELLS and b in v1 and c in v1[b]:
                    tot += 1; x, y = v1[b][c]["verdict"], v["verdict"]; agree += x == y; pp += (x == "PASS") == (y == "PASS")
        out["judge_agreement"] = {"exact": f"{agree}/{tot} ({agree / max(1, tot):.0%})",
                                  "pass_vs_not": f"{pp}/{tot} ({pp / max(1, tot):.0%})"}
    else:
        out["judge_agreement"] = None
    json.dump(out, open(os.path.join(res, "analysis.json"), "w"), indent=1)

    def show(t, label):
        print(f"\n{label}  (pass/n [95% CP])")
        print("arm".ljust(11) + "".join(c.ljust(18) for c in CELLS))
        for a in ARMS:
            print(SHORT[a].ljust(11) + "".join(f"{t[a][c]['pass']}/{t[a][c]['n']} [{t[a][c]['ci95'][0]:.2f},{t[a][c]['ci95'][1]:.2f}]".ljust(18) for c in CELLS))
    show(pooled, f"POOLED ({'+'.join(models)}, {len(rows)} lineages)")
    for m in models: show(out["per_model"][m]["counts"], f"MODEL {m}")
    miss = sum(pooled[a][c]["missing"] for a in ARMS for c in CELLS)
    if miss: print(f"\n(missing probe replies excluded from n: {miss})")
    print("\nFisher full vs X (pooled, Holm over 12):")
    for k, v in cmp.items(): print(f"  {k:22} {v['full']:>6} vs {v['other']:<6} p={v['p']:<8} holm={v['p_holm']:<8}{' *' if v['significant'] else ''}")
    print("safety P6:", {True: "OK", False: "VIOLATED", None: NA}[out["safety_P6_ok"]], {k: v["none_minus_arm"] for k, v in out["safety_P6"].items()})
    print("falsification:", out["falsification"]["reading"], {k: v["full_minus_arm"] for k, v in fals.items()})
    print("structured vs full:", reading, sgap)
    print("judge agreement:", out["judge_agreement"])
    print(f"wrote {os.path.join(res, 'analysis.json')}")


def selfcheck():
    known = [((3, 1, 1, 3), 0.4857143), ((8, 2, 1, 5), 0.0349650), ((1, 9, 11, 3), 0.0027594),
             ((10, 0, 0, 10), 1.0825088e-05), ((0, 0, 0, 0), 1.0), ((5, 5, 5, 5), 1.0)]
    for tab, want in known:
        got = fisher(*tab); ok = abs(got - want) <= 1e-6 * max(1, want) + 1e-9
        print(f"fisher{tab} = {got:.7g} (want {want:.7g}) {'ok' if ok else 'FAIL'}"); assert ok
    h = holm({"a": 0.01, "b": 0.04, "c": 0.03}); assert [round(h[k], 4) for k in "abc"] == [0.03, 0.06, 0.06], h
    print("holm ok", h)


if __name__ == "__main__":
    main()
