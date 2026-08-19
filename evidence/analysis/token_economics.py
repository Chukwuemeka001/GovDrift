#!/usr/bin/env python3
"""Token economics per arm — native vs packet (and the two controls).

Measures, per lineage, POST-FORK only (from the first compact_boundary = the fork
point, so the shared worker prefix is excluded and arms are comparable):
  - output tokens, fresh input tokens, cache-creation tokens, cache-read tokens
  - assistant turn count and tool-call count (work volume)
  - the size of each compaction summary the production compactor wrote
    (isCompactSummary records) -> tests the Tier-3 "compactor offload" hypothesis
  - the treatment payload size actually delivered (from payloads/ manifests)
Outputs token_economics.json + a printed per-arm table.
"""
import json, os, re
from collections import defaultdict

RUN = os.path.dirname(os.path.abspath(__file__))
PROJECTS = ("p1", "p2", "p3")
ARMS = ("A", "B", "C", "D")

def lineage_files(proj):
    st = json.load(open(f"{RUN}/state_{proj}_lineages.json"))["lineages"]
    for lid, lin in sorted(st.items()):
        yield lid, lin, f"{RUN}/transcripts/{proj}_final_{lid}_{lin['sid']}.jsonl"

def analyze(path):
    """Return metrics computed from the FIRST compact_boundary onward."""
    m = dict(out=0, inp=0, cc=0, cr=0, turns=0, tools=0,
             summaries=[], summary_chars=[], post_fork_lines=0, total_lines=0)
    started = False
    with open(path, errors="replace") as fh:
        lines = fh.readlines()
    m["total_lines"] = len(lines)
    for line in lines:
        if not started:
            if '"compact_boundary"' in line:
                started = True
            else:
                continue
        m["post_fork_lines"] += 1
        try:
            rec = json.loads(line)
        except Exception:
            continue
        # compaction summaries written by the production compactor
        if rec.get("isCompactSummary"):
            msg = rec.get("message") or {}
            c = msg.get("content")
            if isinstance(c, list):
                c = " ".join(x.get("text", "") for x in c if isinstance(x, dict))
            c = c or ""
            m["summaries"].append(len(c) // 4)      # ~tokens
            m["summary_chars"].append(len(c))
            continue
        msg = rec.get("message") or {}
        u = msg.get("usage")
        if u and msg.get("role") == "assistant":
            m["turns"] += 1
            m["out"] += u.get("output_tokens") or 0
            m["inp"] += u.get("input_tokens") or 0
            m["cc"] += u.get("cache_creation_input_tokens") or 0
            m["cr"] += u.get("cache_read_input_tokens") or 0
        c = msg.get("content")
        if isinstance(c, list):
            for b in c:
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    m["tools"] += 1
    return m

def payload_tokens():
    """Treatment payload sizes actually delivered, per project/gen/arm."""
    out = {}
    for proj in PROJECTS:
        g1 = json.load(open(f"{RUN}/payloads/{proj}/gen1/payload_manifest.json"))
        g2 = json.load(open(f"{RUN}/payloads/{proj}/gen2/payload_manifest.json"))
        out[proj] = {"gen1": g1["token_estimates_chars_div_4"], "gen2": g2["files"]}
    return out

def main():
    rows = {}
    for proj in PROJECTS:
        for lid, lin, path in lineage_files(proj):
            if not os.path.exists(path):
                print("missing", path); continue
            m = analyze(path)
            m["cost"] = lin.get("cost", 0.0)
            rows[(proj, lid)] = m

    per_arm = defaultdict(lambda: defaultdict(float))
    per_arm_sum = defaultdict(list)
    for (proj, lid), m in rows.items():
        arm = lid[0]
        for k in ("out", "inp", "cc", "cr", "turns", "tools", "cost"):
            per_arm[arm][k] += m[k]
        per_arm[arm]["n"] += 1
        per_arm_sum[arm].extend(m["summaries"])

    pay = payload_tokens()
    result = {"per_lineage": {f"{p}/{l}": m for (p, l), m in rows.items()},
              "payload_tokens": pay, "per_arm": {}}

    print(f"{'arm':4s} {'n':>3s} {'out':>9s} {'fresh_in':>9s} {'cache_cr':>10s} "
          f"{'cache_rd':>11s} {'turns':>6s} {'tools':>6s} {'cost$':>7s} {'summ_tok(mean)':>15s}")
    for arm in ARMS:
        a = per_arm[arm]; n = int(a["n"])
        sums = per_arm_sum[arm]
        mean_sum = sum(sums) / len(sums) if sums else 0
        result["per_arm"][arm] = {
            "n": n, "output_tokens": int(a["out"]), "fresh_input_tokens": int(a["inp"]),
            "cache_creation_tokens": int(a["cc"]), "cache_read_tokens": int(a["cr"]),
            "assistant_turns": int(a["turns"]), "tool_calls": int(a["tools"]),
            "cost_usd": round(a["cost"], 2),
            "compaction_summaries_seen": len(sums),
            "summary_tokens_mean": round(mean_sum, 1),
            "summary_tokens_all": sums}
        print(f"{arm:4s} {n:3d} {int(a['out']):9,d} {int(a['inp']):9,d} {int(a['cc']):10,d} "
              f"{int(a['cr']):11,d} {int(a['turns']):6d} {int(a['tools']):6d} "
              f"{a['cost']:7.2f} {mean_sum:15.1f}")
    json.dump(result, open(f"{RUN}/token_economics.json", "w"), indent=2)
    print("\npayload tokens delivered (per lineage, per generation):")
    print(json.dumps(pay, indent=2))

if __name__ == "__main__":
    main()
