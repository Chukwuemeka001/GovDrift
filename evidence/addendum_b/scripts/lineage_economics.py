#!/usr/bin/env python3
"""Per-step token economics for every lineage, fork -> end of gen 3 (EXPLORATORY).
Source: final3 transcripts (full lineage history). Usage deduped by assistant message id.
Steps are labeled by matching the driver's prompts to the frozen probe/turn texts.
Haiku 4.5 list $/M: input 1.00, cache-write 1.25, cache-read 0.10, output 5.00.
Compaction calls are not logged as assistant messages: their cost is ESTIMATED as
(pre-compaction context read from cache) + (summary written as output)."""
import json, os, csv, statistics as S
from collections import defaultdict, OrderedDict
PR = dict(inp=1.0, cc=1.25, cr=0.10, out=5.0)
usd = lambda m: sum(m[k] * PR[k] for k in PR) / 1e6
ORDER = ["R1P1","R1P2","R1P3","R1P4","R1P5","work:WB1","R1P6","work:W2-W3+band","COMPACT#2",
         "R2P1","R2P2","R2P3","work:D5-extra","R2P4","R2P5","R2P6","work:H5-H8 band","COMPACT#3",
         "R3P1","R3P2","R3P3","R3P4","R3P5","R3P6"]
def labeler(proj):
    pj = json.load(open(f"probes_{proj}.json"))
    probes = pj["probes"]; work = pj["work_turns"]; replies = pj["conditional_replies"]
    def lab(text, seen_compacts, last):
        t = text.strip()
        if "<command-name>/compact" in t: return last if last.startswith("COMPACT") else f"COMPACT#{seen_compacts + 1}"
        for k, v in replies.items():
            if t == v.strip(): return last            # conditional reply belongs to its probe
        for k, v in probes.items():
            if t == v.strip() or t.endswith(v.strip()): return k
        for k, v in work.items():
            if t == v.strip() or t.endswith(v.strip()):
                if k == "WB1": return "work:WB1"
                if k in ("W2","W3"): return "work:W2-W3+band"
                if k in ("H5","H6","H7","H8"): return "work:H5-H8 band"
                # H1-H4: round-1 band fill, or D5 extra if it happened after R2 probes began
                return "work:D5-extra" if last.startswith("R2") or last == "work:D5-extra" else "work:W2-W3+band"
        return None
    return lab
def lineage(path, proj):
    lines = open(path, errors="replace").readlines()
    start = next(i for i, x in enumerate(lines) if '"compact_boundary"' in x)   # fork point
    lab = labeler(proj); steps = OrderedDict(); cur = None; ncomp = 0; seen = set(); ctx = 0
    for x in lines[start + 1:]:
        try: r = json.loads(x)
        except Exception: continue
        m = r.get("message") or {}; c = m.get("content")
        if r.get("type") == "system" and r.get("subtype") == "compact_boundary":
            ncomp += 1; cur = f"COMPACT#{ncomp + 1}"
            steps[cur] = dict(inp=0, cc=0, cr=ctx, out=0, turns=1, tools=0, ctx_start=ctx, est=1)  # ESTIMATE
            continue
        if r.get("isCompactSummary"):
            s = c if isinstance(c, str) else " ".join(b.get("text", "") for b in c if isinstance(b, dict))
            if cur and cur.startswith("COMPACT"):
                steps[cur]["out"] += len(s) // 4
            continue
        if r.get("type") == "user" and isinstance(c, str) and not c.startswith("<local-command") and "This session is being continued" not in c:
            L = lab(c, ncomp, cur or "")
            if L:
                cur = L
                st = steps.setdefault(cur, dict(inp=0, cc=0, cr=0, out=0, turns=0, tools=0, ctx_start=None))
            continue
        u = m.get("usage")
        if cur and u and m.get("role") == "assistant" and m.get("id") not in seen:
            seen.add(m.get("id")); st = steps[cur]; st["turns"] += 1
            for k, f in (("inp","input_tokens"),("cc","cache_creation_input_tokens"),("cr","cache_read_input_tokens"),("out","output_tokens")): st[k] += u.get(f) or 0
            ctx = (u.get("input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0)
            if st["ctx_start"] is None: st["ctx_start"] = ctx
        if cur and isinstance(c, list):
            steps[cur]["tools"] += sum(1 for b in c if isinstance(b, dict) and b.get("type") == "tool_use")
    for st in steps.values(): st.pop("_ctx", None); st["usd"] = usd(st)
    return steps
rows = []; per = defaultdict(lambda: defaultdict(list))
for f in sorted(os.listdir("transcripts")):
    if "_final3_" not in f: continue
    proj, _, lid = f.split("_")[:3]; arm = lid[0]
    steps = lineage("transcripts/" + f, proj)
    for L, st in steps.items():
        rows.append(dict(project=proj, lineage=lid, arm=arm, step=L, **{k: st.get(k) for k in ("ctx_start","turns","tools","inp","cc","cr","out","usd","est")}))
        per[arm][L].append(st)
with open("lineage_economics.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
summary = {}
for arm in "ABFN":
    summary[arm] = {}
    for L in ORDER:
        xs = per[arm].get(L, [])
        if not xs: continue
        summary[arm][L] = dict(n=len(xs), ctx=S.mean(x["ctx_start"] or 0 for x in xs), turns=S.mean(x["turns"] for x in xs),
            tools=S.mean(x["tools"] for x in xs), tok=S.mean(x["inp"]+x["cc"]+x["cr"]+x["out"] for x in xs),
            out=S.mean(x["out"] for x in xs), usd=S.mean(x["usd"] for x in xs))
json.dump(summary, open("lineage_economics_summary.json", "w"), indent=1)
print("step".ljust(18), *(f"{a:>22}" for a in "AFBN"))
print("".ljust(18), *(f"{'ctx  tok_k  out_k    $':>22}" for a in "AFBN"))
cum = {a: 0 for a in "ABFN"}
for L in ORDER:
    cells = []
    for a in "AFBN":
        s = summary[a].get(L)
        if s: cum[a] += s["usd"]; cells.append(f"{s['ctx']/1e3:4.0f}k {s['tok']/1e3:6.0f} {s['out']/1e3:5.1f} {s['usd']:6.3f}")
        else: cells.append("-".rjust(22))
    print(L.ljust(18), *(f"{c:>22}" for c in cells))
print("TOTAL $/lineage".ljust(18), *(f"{cum[a]:>22.2f}" for a in "AFBN"))
G = {"Gen1 fork->compact#2": ORDER[:9], "Gen2 ->compact#3": ORDER[9:18], "Gen3": ORDER[18:]}
print()
for g, keys in G.items():
    for excl in (False, True):
        if excl and "work:D5-extra" not in keys: continue
        tag = g + (" (excl D5)" if excl else "")
        vals = []
        for a in "AFBN":
            ks = [k for k in keys if not (excl and k == "work:D5-extra")]
            vals.append((sum(summary[a][k]["usd"] for k in ks if k in summary[a]),
                         sum(summary[a][k]["out"] for k in ks if k in summary[a]),
                         sum(summary[a][k]["turns"] for k in ks if k in summary[a])))
        print(tag.ljust(28), *(f"${v[0]:5.2f} out {v[1]/1e3:5.0f}k turns {v[2]:4.0f}".rjust(32) for v in vals))
