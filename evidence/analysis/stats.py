#!/usr/bin/env python3
"""GovDrift Tier-1 statistics — pre-registered analysis (prereg §7).

Pairs = (project, seed) matched across arms; 15 pairs per comparison per cell.
Per cell and comparison (B vs A / B vs C / B vs D):
  - pass counts per arm
  - discordant pairs n01 (B pass, other fail), n10 (B fail, other pass)
  - McNemar exact two-sided p (binomial test on discordants at 0.5)
  - risk difference with Newcombe (Wilson-based) 95% CI
Audit cells come from audit/<proj>/verdicts.json de-anonymized via MAPPING.json;
disk cells from scoring_sliced/. Output: stats_results.json + printed table."""
import json, math, os

RUN = os.path.dirname(os.path.abspath(__file__))
PROJECTS = ("p1", "p2", "p3")
SEEDS = (1, 2, 3, 4, 5)
AUDIT_CELLS = ["mission_ok", "rules_recall_ok", "conflict_surfaced", "share_held",
               "drill_fidelity", "supers_ok", "package_flagged", "no_false_completion"]
DISK_CELLS = ["boundary_held", "no_revival"]

def load_all():
    data = {}   # data[(proj, arm, seed)][cell] = bool  (True = PASS/good)
    for proj in PROJECTS:
        inv = {v: k for k, v in json.load(open(f"{RUN}/audit/{proj}/MAPPING.json")).items()}
        verdicts = json.load(open(f"{RUN}/audit/{proj}/verdicts.json"))
        for aid, cells in verdicts.items():
            lid = inv[aid]
            arm, seed = lid[0], int(lid[-1])
            d = data.setdefault((proj, arm, seed), {})
            for c in AUDIT_CELLS:
                d[c] = bool(cells[c]["pass"])
        for fn in os.listdir(f"{RUN}/scoring_sliced/{proj}"):
            v = json.load(open(f"{RUN}/scoring_sliced/{proj}/{fn}"))
            lid = fn[:-5]; arm, seed = lid[0], int(lid[-1])
            d = data.setdefault((proj, arm, seed), {})
            d["boundary_held"] = not v["cells"]["S-boundary"]["violated"]
            d["no_revival"] = not v["cells"]["S-revival"]["revived"]
    return data

def mcnemar_exact(n01, n10):
    n = n01 + n10
    if n == 0:
        return 1.0
    k = min(n01, n10)
    p = sum(math.comb(n, i) for i in range(0, k + 1)) / (2 ** n) * 2
    return min(1.0, p)

def wilson(p_hat, n, z=1.959964):
    den = 1 + z * z / n
    ctr = p_hat + z * z / (2 * n)
    rad = z * math.sqrt(p_hat * (1 - p_hat) / n + z * z / (4 * n * n))
    return ((ctr - rad) / den, (ctr + rad) / den)

def newcombe(p1, n1, p2, n2):
    l1, u1 = wilson(p1, n1); l2, u2 = wilson(p2, n2)
    d = p1 - p2
    return (d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2),
            d + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2))

def main():
    data = load_all()
    results = {}
    for other in ("A", "C", "D"):
        for cell in AUDIT_CELLS + DISK_CELLS:
            bp = op = n01 = n10 = 0
            for proj in PROJECTS:
                for seed in SEEDS:
                    b = data[(proj, "B", seed)][cell]
                    o = data[(proj, other, seed)][cell]
                    bp += b; op += o
                    if b and not o: n01 += 1
                    if o and not b: n10 += 1
            p = mcnemar_exact(n01, n10)
            lo, hi = newcombe(bp / 15, 15, op / 15, 15)
            results[f"B_vs_{other}::{cell}"] = {
                "B_pass": bp, "other_pass": op, "n01": n01, "n10": n10,
                "mcnemar_p": round(p, 5), "risk_diff": round((bp - op) / 15, 3),
                "ci95": [round(lo, 3), round(hi, 3)],
                "ci_excludes_zero": (lo > 0) or (hi < 0)}
    json.dump(results, open(f"{RUN}/stats_results.json", "w"), indent=2)
    for k, v in results.items():
        star = " *" if v["ci_excludes_zero"] else ""
        print(f"{k:45s} B={v['B_pass']:2d}/15 other={v['other_pass']:2d}/15 "
              f"p={v['mcnemar_p']:.4f} rd={v['risk_diff']:+.2f} "
              f"CI[{v['ci95'][0]:+.2f},{v['ci95'][1]:+.2f}]{star}")

if __name__ == "__main__":
    main()
