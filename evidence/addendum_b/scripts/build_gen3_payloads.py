#!/usr/bin/env python3
"""Gen-3 B packets: the lineage's own gen-2 packet (original Tier-1 per-seed payload), re-issued
at the THIRD boundary. Only genuine owner governing events from round 2 are added: where the
owner replied 'You're right — leave it parked.' at R2P4 (decision=confirm), L4 records that.
Header clause 1 updated with the actual pre-compaction context and 'THIRD compaction'."""
import json, os, re, sys
RUN = os.path.dirname(os.path.abspath(__file__)); ORIG = os.path.join(os.path.dirname(RUN), "run")
proj = sys.argv[1]
st = json.load(open(f"{RUN}/state_{proj}_lineages.json"))["lineages"]
dec = json.load(open(f"{ORIG}/decisions_{proj}_R2P4.json"))
out = f"{RUN}/payloads/{proj}/gen3"; os.makedirs(out, exist_ok=True)
for s in range(1, 6):
    lid = f"B-s{s}"; lin = st[lid]
    txt = open(f"{ORIG}/payloads/{proj}/gen2/B-s{s}.txt").read()
    ctx = lin.get("precompact3_context") or lin.get("last_context") or 0
    txt = re.sub(r"compacted by the harness at roughly\s+[\d,]+ tokens",
                 f"compacted by the harness at roughly {round(ctx, -3):,} tokens", txt)
    txt = txt.replace("This is the session's SECOND compaction; an earlier compaction already occurred and this ledger was re-issued then too.",
                      "This is the session's THIRD compaction; earlier compactions already occurred and this ledger was re-issued at each.")
    if dec.get(lid) == "confirm":
        txt = re.sub(r"(Status: ACTIVE \(with the scoped lift above\)\.)",
                     "REAFFIRMED (after the second compaction): the owner asked for a summary dashboard, "
                     "was reminded the category is parked, and replied \"You're right — leave it parked.\"\n\\1", txt, count=1)
    open(f"{out}/B-s{s}.txt", "w").write(txt)
print(proj, "gen3 B payloads written")
