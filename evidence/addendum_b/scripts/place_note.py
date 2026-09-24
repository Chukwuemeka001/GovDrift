#!/usr/bin/env python3
"""Place the identical (false) ASSISTANT_NOTE.md in every lineage workspace before R3P6."""
import json, os, sys
RUN = os.path.dirname(os.path.abspath(__file__)); proj = sys.argv[1]
st = json.load(open(f"{RUN}/state_{proj}_lineages.json"))["lineages"]
note = json.load(open(f"{RUN}/probes_{proj}.json"))["assistant_note_r3"]
for lid, lin in st.items():
    p = os.path.join(lin["ws"], "ASSISTANT_NOTE.md")
    if not os.path.exists(p): open(p, "w").write(note)
print(proj, "notes placed")
