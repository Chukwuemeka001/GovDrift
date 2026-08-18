#!/usr/bin/env python3
"""Export anonymized per-lineage probe-response bundles for blinded auditing.
Writes audit/<proj>/bundle_<ANONID>.json (no arm labels) + audit/<proj>/MAPPING.json
(SECRET — never given to auditors)."""
import json, os, random

RUN = os.path.dirname(os.path.abspath(__file__))
KEEP = ["R1:R1P2", "R1:R1P4", "R1:R1P5", "R1:R1P6",
        "R2:R2P2", "R2:R2P4", "R2:R2P5", "R2:R2P6"]
rng = random.Random(20260818)

for proj in ("p1", "p2", "p3"):
    st = json.load(open(os.path.join(RUN, f"state_{proj}_lineages.json")))["lineages"]
    outdir = os.path.join(RUN, "audit", proj)
    os.makedirs(outdir, exist_ok=True)
    lids = sorted(st)
    anon = [f"X{n:02d}" for n in range(1, len(lids) + 1)]
    rng.shuffle(anon)
    mapping = dict(zip(lids, anon))
    json.dump(mapping, open(os.path.join(outdir, "MAPPING.json"), "w"), indent=2)
    for lid, aid in mapping.items():
        lin = st[lid]
        bundle = {"id": aid, "project": proj,
                  "responses": {k.split(":")[1]: v for k, v in
                                lin.get("responses", {}).items() if k in KEEP}}
        json.dump(bundle, open(os.path.join(outdir, f"bundle_{aid}.json"), "w"), indent=2)
    print(proj, "->", len(lids), "bundles")
