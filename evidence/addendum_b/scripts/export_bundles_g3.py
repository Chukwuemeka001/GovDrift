#!/usr/bin/env python3
"""Blinded gen-3 bundles: every lineage that completed R3P6. Responses R1P6, R2P6 (history
for drill-honesty judgment) + R3P2..R3P6. Original A/B earlier responses come from Tier-1 state."""
import json, os, random, sys
RUN = os.path.dirname(os.path.abspath(__file__)); ORIG = os.path.join(os.path.dirname(RUN), "run")
KEEP = ["R1:R1P6", "R2:R2P6", "R3:R3P2", "R3:R3P3", "R3:R3P4", "R3:R3P5", "R3:R3P6"]
rng = random.Random(20260924)
for proj in sys.argv[1:]:
    st = json.load(open(f"{RUN}/state_{proj}_lineages.json"))["lineages"]
    old = json.load(open(f"{ORIG}/state_{proj}_lineages.json"))["lineages"]
    lids = sorted(l for l, v in st.items() if "R3:R3P6" in v["steps_done"])
    anon = [f"Z{n:02d}" for n in range(1, len(lids)+1)]; rng.shuffle(anon)
    mapping = dict(zip(lids, anon)); out = f"{RUN}/audit_g3/{proj}"; os.makedirs(out, exist_ok=True)
    json.dump(mapping, open(f"{RUN}/audit_g3/MAPPING_{proj}.json", "w"), indent=2)
    for lid, aid in mapping.items():
        r = dict(old[lid]["responses"]) if st[lid].get("origin") == "tier1-final" else {}
        r.update(st[lid]["responses"])
        json.dump({"id": aid, "project": proj, "responses": {k.split(":")[1]: r[k] for k in KEEP if k in r}},
                  open(f"{out}/bundle_{aid}.json", "w"), indent=2)
    print(proj, len(lids), "gen-3 bundles")
