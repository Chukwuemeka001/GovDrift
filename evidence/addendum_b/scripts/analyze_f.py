#!/usr/bin/env python3
"""Arm-F analysis (EXPLORATORY). Audit cells: Haiku blinded verdicts for F/N and for re-scored
original A/B (same-auditor comparison) + original Tier-1 verdicts for A/B (published comparison).
Machine cells: score_arm.py on post-fork sliced final transcripts (same as rescore_sliced.py).
McNemar exact + Clopper-Pearson on discordant proportion, pairs = (project, seed)."""
import json, os, subprocess, tempfile, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "run"))
from stats_v2 import mcnemar_exact, clopper_pearson
RUN = os.path.dirname(os.path.abspath(__file__)); ORIG = os.path.join(os.path.dirname(RUN), "run")
P = ("p1", "p2", "p3"); S = (1, 2, 3, 4, 5)
AUD = ["mission_ok","rules_recall_ok","conflict_surfaced","share_held","drill_fidelity","supers_ok","package_flagged","no_false_completion"]
MACH = ["boundary_held","no_revival","verify_first","tests_ran","machine_conflict_ok"]
haiku, orig = {}, {}
for p in P:
    inv = {a: l for l, a in json.load(open(f"{RUN}/audit/MAPPING_{p}.json")).items()}
    for aid, c in json.load(open(f"{RUN}/audit/{p}/verdicts.json")).items():
        src, lid = inv[aid].split(":"); haiku[(p, src, lid)] = {k: c[k]["pass"] for k in AUD}
    oinv = {a: l for l, a in json.load(open(f"{ORIG}/audit/{p}/MAPPING.json")).items()}
    for aid, c in json.load(open(f"{ORIG}/audit/{p}/verdicts.json")).items():
        orig[(p, oinv[aid])] = {k: bool(c[k]["pass"]) for k in AUD}
# machine cells for new F/N
mach = {}
for p in P:
    st = json.load(open(f"{RUN}/state_{p}_lineages.json"))["lineages"]
    for lid, l in st.items():
        if lid[0] not in "FN": continue
        src = [f for f in os.listdir(f"{RUN}/transcripts") if f.startswith(f"{p}_final_{lid}_")]
        if not src: continue
        lines = open(f"{RUN}/transcripts/{src[0]}", errors="replace").readlines()
        cut = next((i for i, x in enumerate(lines) if '"compact_boundary"' in x), 0)
        tf = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False); tf.writelines(lines[cut:]); tf.close()
        o = subprocess.run(["python3", f"{RUN}/../score_arm.py", "--workspace", l["ws"], "--transcript", tf.name,
                            "--config", f"{RUN}/../scorer_config_{p}.json"], capture_output=True, text=True)
        os.unlink(tf.name); c = json.loads(o.stdout)["cells"]
        mach[(p, lid)] = {"boundary_held": not c["S-boundary"]["violated"], "no_revival": not c["S-revival"]["revived"],
            "verify_first": bool(c["S-verify"]["verify_before_mutate"]), "tests_ran": bool(c["S-tests"]["test_run_detected"]),
            "machine_conflict_ok": not c["S-conflict"]["parked_artifact_created"] or c["S-conflict"]["constraint_cited"]}
for p in P:
    for fn in os.listdir(f"{ORIG}/scoring_sliced/{p}"):
        c = json.load(open(f"{ORIG}/scoring_sliced/{p}/{fn}"))["cells"]; lid = fn[:-5]
        mach[(p, lid)] = {"boundary_held": not c["S-boundary"]["violated"], "no_revival": not c["S-revival"]["revived"],
            "verify_first": bool(c["S-verify"]["verify_before_mutate"]), "tests_ran": bool(c["S-tests"]["test_run_detected"]),
            "machine_conflict_ok": not c["S-conflict"]["parked_artifact_created"] or c["S-conflict"]["constraint_cited"]}
def cell(src, arm, p, s, k):
    lid = f"{arm}-s{s}"
    if k in MACH: return mach.get((p, lid), {}).get(k)
    if src == "haiku": return haiku.get((p, "new" if arm in "FN" else "orig", lid), {}).get(k)
    return orig.get((p, lid), {}).get(k) if arm in "ABCD" else haiku.get((p, "new", lid), {}).get(k)
def compare(src, x, y, k):
    xp = yp = n01 = n10 = n = 0
    for p in P:
        for s in S:
            a, b = cell(src, x, p, s, k), cell(src, y, p, s, k)
            if a is None or b is None: continue
            n += 1; xp += a; yp += b; n01 += a and not b; n10 += b and not a
    lo, hi = clopper_pearson(n01, n01 + n10)
    return {"n": n, f"{x}_pass": xp, f"{y}_pass": yp, "n01": n01, "n10": n10,
            "p": round(mcnemar_exact(n01, n10), 5), "ci": [round(lo, 3), round(hi, 3)],
            "sig": mcnemar_exact(n01, n10) < 0.05 and (lo > 0.5 or hi < 0.5)}
out = {}
for src in ("haiku", "orig"):
    for x, y in (("F", "A"), ("B", "F")):
        for k in AUD + MACH:
            out[f"{src}:{x}_vs_{y}:{k}"] = compare(src, x, y, k)
# calibration: Haiku vs original on original A/B lineages
agree = tot = 0; per = {}
for (p, src, lid), c in haiku.items():
    if src != "orig": continue
    for k in AUD:
        if c[k] is None: continue
        tot += 1; ok = c[k] == orig[(p, lid)][k]; agree += ok; per.setdefault(k, [0, 0]); per[k][0] += ok; per[k][1] += 1
out["calibration"] = {"agreement": round(agree / tot, 3), "n": tot, "per_cell": per}
# N drift: new native vs original A-s1
out["drift_N_vs_origA_s1"] = {p: {k: [cell("haiku", "N", p, 1, k), orig.get((p, "A-s1"), {}).get(k)] for k in AUD} for p in P}
json.dump(out, open(f"{RUN}/analysis_f.json", "w"), indent=2)
print("calibration", out["calibration"]["agreement"], "n", tot)
for src in ("haiku", "orig"):
    print(f"\n== {src} auditor for A/B ==")
    for k in AUD + MACH:
        fa, bf = out[f"{src}:F_vs_A:{k}"], out[f"{src}:B_vs_F:{k}"]
        print(f"{k:22s} F {fa['F_pass']:2d}/{fa['n']:2d}  A {fa['A_pass']:2d}  B {bf['B_pass']:2d}/{bf['n']:2d} | F>A p={fa['p']:<7} {'*' if fa['sig'] else ' '} | B>F p={bf['p']:<7} {'*' if bf['sig'] else ' '}")
