#!/usr/bin/env python3
"""Blinded bundles: new F (5) + N (1) lineages mixed with ORIGINAL Tier-1 A (5) + B (5)
lineages (calibration: Haiku auditors vs original verdicts). Same KEEP set/format as run/export_bundles.py."""
import json, os, random
RUN = os.path.dirname(os.path.abspath(__file__)); ORIG = os.path.join(os.path.dirname(RUN), "run")
KEEP = ["R1:R1P2","R1:R1P4","R1:R1P5","R1:R1P6","R2:R2P2","R2:R2P4","R2:R2P5","R2:R2P6"]
rng = random.Random(20260923)
for proj in ("p1","p2","p3"):
    new = json.load(open(f"{RUN}/state_{proj}_lineages.json"))["lineages"]
    old = json.load(open(f"{ORIG}/state_{proj}_lineages.json"))["lineages"]
    pool = {f"new:{k}": v for k, v in new.items() if k[0] in "FN"}
    pool.update({f"orig:{k}": v for k, v in old.items() if k[0] in "AB"})
    lids = sorted(pool); anon = [f"Y{n:02d}" for n in range(1, len(lids)+1)]; rng.shuffle(anon)
    mapping = dict(zip(lids, anon)); out = f"{RUN}/audit/{proj}"; os.makedirs(out, exist_ok=True)
    json.dump(mapping, open(f"{RUN}/audit/MAPPING_{proj}.json", "w"), indent=2)  # outside auditor dir
    for lid, aid in mapping.items():
        r = {k.split(":")[1]: v for k, v in pool[lid].get("responses", {}).items() if k in KEEP}
        json.dump({"id": aid, "project": proj, "responses": r}, open(f"{out}/bundle_{aid}.json", "w"), indent=2)
    print(proj, len(lids), "bundles")
