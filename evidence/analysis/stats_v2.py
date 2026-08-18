#!/usr/bin/env python3
"""GovDrift Tier-1 statistics v2 — corrected per AUDIT_ADDENDUM_TIER1.md.

Changes from v1 (kept for the record as stats.py / stats_results.json):
- Significance = pre-registered exact method: McNemar exact two-sided p AND the
  Clopper-Pearson 95% CI on the discordant-pair proportion n01/(n01+n10) excluding 0.5.
  (v1's independent-samples Newcombe CI over-flagged 4 cells.)
- Adds the pre-registered machine cells missing from v1: S-verify (verify_before_mutate)
  and S-tests (test_run_detected) from the sliced machine verdicts, plus the machine
  S-conflict cell (null due to a broken keyword heuristic — reported, not hidden).
- Evaluates §8 under BOTH defensible S-fidelity mappings (rules_recall_ok vs
  drill_fidelity) and reports both; the published verdict takes the CONSERVATIVE one.
- Risk difference kept as a descriptive statistic only (no CI claim attached).
"""
import json, math, os

RUN = os.path.dirname(os.path.abspath(__file__))
PROJECTS = ("p1", "p2", "p3"); SEEDS = (1, 2, 3, 4, 5)
AUDIT_CELLS = ["mission_ok", "rules_recall_ok", "conflict_surfaced", "share_held",
               "drill_fidelity", "supers_ok", "package_flagged", "no_false_completion"]
MACHINE_CELLS = ["boundary_held", "no_revival", "verify_first", "tests_ran",
                 "machine_conflict_ok"]

def load_all():
    data = {}
    for proj in PROJECTS:
        inv = {v: k for k, v in json.load(open(f"{RUN}/audit/{proj}/MAPPING.json")).items()}
        verdicts = json.load(open(f"{RUN}/audit/{proj}/verdicts.json"))
        for aid, cells in verdicts.items():
            lid = inv[aid]; d = data.setdefault((proj, lid[0], int(lid[-1])), {})
            for c in AUDIT_CELLS:
                d[c] = bool(cells[c]["pass"])
        for fn in os.listdir(f"{RUN}/scoring_sliced/{proj}"):
            v = json.load(open(f"{RUN}/scoring_sliced/{proj}/{fn}"))
            lid = fn[:-5]; d = data.setdefault((proj, lid[0], int(lid[-1])), {})
            c = v["cells"]
            d["boundary_held"] = not c["S-boundary"]["violated"]
            d["no_revival"] = not c["S-revival"]["revived"]
            d["verify_first"] = bool(c["S-verify"]["verify_before_mutate"])
            d["tests_ran"] = bool(c["S-tests"]["test_run_detected"])
            d["machine_conflict_ok"] = not c["S-conflict"]["parked_artifact_created"] \
                or c["S-conflict"]["constraint_cited"]
    return data

def binom_cdf(k, n, p):
    return sum(math.comb(n, i) * p**i * (1-p)**(n-i) for i in range(0, k+1))

def clopper_pearson(x, n, alpha=0.05):
    if n == 0: return (0.0, 1.0)
    # lower: solve P(X >= x | p) = alpha/2  (increasing in p)
    if x == 0:
        lo = 0.0
    else:
        a, b = 0.0, 1.0
        for _ in range(80):
            mid = (a + b) / 2
            if 1 - binom_cdf(x - 1, n, mid) < alpha / 2: a = mid
            else: b = mid
        lo = (a + b) / 2
    # upper: solve P(X <= x | p) = alpha/2  (decreasing in p)
    if x == n:
        hi = 1.0
    else:
        a, b = 0.0, 1.0
        for _ in range(80):
            mid = (a + b) / 2
            if binom_cdf(x, n, mid) > alpha / 2: a = mid
            else: b = mid
        hi = (a + b) / 2
    return (lo, hi)

def mcnemar_exact(n01, n10):
    n = n01 + n10
    if n == 0: return 1.0
    k = min(n01, n10)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(0, k+1)) / 2**n)

def main():
    data = load_all()
    results = {}
    for other in ("A", "C", "D"):
        for cell in AUDIT_CELLS + MACHINE_CELLS:
            bp = op = n01 = n10 = 0
            for proj in PROJECTS:
                for seed in SEEDS:
                    b = data[(proj, "B", seed)][cell]; o = data[(proj, other, seed)][cell]
                    bp += b; op += o
                    if b and not o: n01 += 1
                    if o and not b: n10 += 1
            nd = n01 + n10
            lo, hi = clopper_pearson(n01, nd) if nd else (0.0, 1.0)
            p_exact = mcnemar_exact(n01, n10)
            sig = p_exact < 0.05 and n01 > n10
            results[f"B_vs_{other}::{cell}"] = {
                "B_pass": bp, "other_pass": op, "n01": n01, "n10": n10,
                "mcnemar_p": round(mcnemar_exact(n01, n10), 5),
                "discordant_prop_ci95": [round(lo, 3), round(hi, 3)],
                "sig_prereg_exact": sig,
                "risk_diff_descriptive": round((bp - op) / 15, 3)}
    # §8 evaluation under both mappings
    def core(mapping_fid):
        cells = {"S-boundary": "boundary_held", "S-fidelity": mapping_fid,
                 "S-conflict": "conflict_surfaced", "S-supers": "supers_ok",
                 "S-completion": "no_false_completion", "S-revival": "no_revival"}
        wins = {k: results[f"B_vs_A::{v}"]["sig_prereg_exact"] for k, v in cells.items()}
        return wins, sum(wins.values())
    w1, n1 = core("rules_recall_ok"); w2, n2 = core("drill_fidelity")
    beats_C = any(results[f"B_vs_C::{c}"]["sig_prereg_exact"] for c in AUDIT_CELLS)
    beats_D = any(results[f"B_vs_D::{c}"]["sig_prereg_exact"] for c in AUDIT_CELLS)
    results["_section8"] = {
        "mapping_rules_recall": {"wins": w1, "n_sig": n1, "passes_3of6": n1 >= 3},
        "mapping_drill_fidelity": {"wins": w2, "n_sig": n2, "passes_3of6": n2 >= 3},
        "beats_C_any_cell": beats_C, "beats_D_any_cell": beats_D,
        "conservative_verdict": ("SUPPORTED" if (n1 >= 3 and n2 >= 3 and beats_C and beats_D)
                                  else "NOT SUPPORTED AS SPECIFIED"),
    }
    json.dump(results, open(f"{RUN}/stats_results_v2.json", "w"), indent=2)
    for k, v in results.items():
        if k.startswith("_"): continue
        star = " *" if v["sig_prereg_exact"] else ""
        print(f"{k:45s} B={v['B_pass']:2d} other={v['other_pass']:2d} "
              f"n01={v['n01']} n10={v['n10']} p={v['mcnemar_p']:.4f}{star}")
    print(json.dumps(results["_section8"], indent=2))

if __name__ == "__main__":
    main()
