#!/usr/bin/env python3
"""Tier 1 token economics, CORRECTED (supersedes the token/turn figures of token_economics.py).

Erratum: token_economics.py summed `usage` once per transcript RECORD. Claude Code writes one record per content block,
and every record of one assistant message repeats the same `usage`, so output tokens, fresh/cache input tokens and
assistant turns were counted ~2-3x. Here usage and turns are counted once per assistant message id (all records of one
id carry identical usage; verified). Tool calls were never inflated (one tool_use block per record) and are unchanged.

Scope as before: POST-FORK only (from each lineage's first compact_boundary). Cost = Haiku 4.5 list $/M
(input 1.00, cache-write 1.25, cache-read 0.10, output 5.00) on deduplicated usage; the driver's `cost` field
(published $1.86/$2.48) is also reported. Compaction calls themselves are not logged as assistant messages and are
not included (as before). Per-probe attribution: each driver prompt is matched to the frozen probe/work texts.

  cd evidence/analysis && python3 token_economics_v2.py   -> token_economics_v2.json + printed tables
"""
import gzip, json, os, re
from collections import defaultdict
from math import comb

HERE = os.path.dirname(os.path.abspath(__file__))
TR = os.path.join(HERE, "..", "transcripts")
ST = os.path.join(HERE, "..", "state")
PR = dict(inp=1.00, cc=1.25, cr=0.10, out=5.00)
CONFLICT = ("R1P4", "R1P5", "R2P4", "R2P5")          # the starred rows of TOKEN_ECONOMICS.md §3
usd = lambda m: sum(m[k] * PR[k] for k in PR) / 1e6


def labeler(proj):
    pj = json.load(open(os.path.join(HERE, f"probes_{proj}.json")))
    probes, work, replies = pj["probes"], pj["work_turns"], pj["conditional_replies"]

    def lab(t, last):
        t = t.strip()
        if any(t == v.strip() for v in replies.values()):
            return last
        for k, v in probes.items():
            if t == v.strip() or t.endswith(v.strip()):
                return k
        for k, v in work.items():
            if t == v.strip() or t.endswith(v.strip()):
                return "work"
        return None
    return lab


def analyze(path, proj):
    lab = labeler(proj)
    seen, tools, per_step = {}, 0, defaultdict(int)
    started, cur = False, "pre"
    with gzip.open(path, "rt", errors="replace") as fh:
        for line in fh:
            if not started:
                started = '"compact_boundary"' in line
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("isCompactSummary"):
                continue
            m = r.get("message") or {}
            c = m.get("content")
            if r.get("type") == "user" and isinstance(c, str) and not c.startswith("<local-command") \
                    and "This session is being continued" not in c:
                cur = lab(c, cur) or cur
                continue
            u = m.get("usage")
            if u and m.get("role") == "assistant":
                mid = m.get("id") or r.get("uuid")
                if mid not in seen:
                    seen[mid] = dict(inp=u.get("input_tokens") or 0, cc=u.get("cache_creation_input_tokens") or 0,
                                     cr=u.get("cache_read_input_tokens") or 0, out=u.get("output_tokens") or 0)
                    per_step[cur] += seen[mid]["out"]
            if isinstance(c, list):
                tools += sum(1 for b in c if isinstance(b, dict) and b.get("type") == "tool_use")
    tot = defaultdict(int)
    for v in seen.values():
        for k, x in v.items():
            tot[k] += x
    return dict(**tot, turns=len(seen), tools=tools, usd=usd(tot), per_step=dict(per_step))


def sign_p(k, n):
    x = max(k, n - k)
    return min(1.0, 2 * sum(comb(n, i) for i in range(x, n + 1)) / 2 ** n)


def main():
    driver = {}
    for p in ("p1", "p2", "p3"):
        for lid, l in json.load(open(os.path.join(ST, f"state_{p}_lineages.json")))["lineages"].items():
            driver[(p, lid)] = l["cost"]
    rows = {}
    for f in sorted(os.listdir(TR)):
        mt = re.match(r"(p\d)_final_([ABCD]-s\d+)_.*\.jsonl\.gz$", f)
        if mt:
            rows[mt.groups()] = analyze(os.path.join(TR, f), mt.group(1))
    assert len(rows) == 60, len(rows)
    mean = lambda arm, k: sum(r[k] for (p, l), r in rows.items() if l[0] == arm) / 15
    out = {"method": __doc__.split("\n\n")[1], "per_arm": {}, "per_lineage": {f"{p}/{l}": r for (p, l), r in rows.items()}}
    print(f"{'arm':3s} {'usd':>6s} {'driver$':>8s} {'out':>8s} {'turns':>6s} {'tools':>6s} {'cache_rd':>9s}")
    for a in "ABCD":
        d = {k: mean(a, k) for k in ("usd", "out", "inp", "cc", "cr", "turns", "tools")}
        d["driver_usd"] = sum(v for (p, l), v in driver.items() if l[0] == a) / 15
        out["per_arm"][a] = d
        print(f"{a:3s} {d['usd']:6.2f} {d['driver_usd']:8.2f} {d['out']:8.0f} {d['turns']:6.0f} {d['tools']:6.0f} {d['cr']/1e6:8.1f}M")
    pairs = [(p, l[2:]) for (p, l) in rows if l[0] == "A"]
    g = lambda p, arm, s, k="usd": rows[(p, f"{arm}-{s}")][k]
    ba = [g(p, "B", s) < g(p, "A", s) for p, s in pairs]
    d_turns = sum(g(p, "B", s, "turns") - g(p, "A", s, "turns") for p, s in pairs) / 15
    d_out = sum(g(p, "B", s, "out") - g(p, "A", s, "out") for p, s in pairs) / 15
    d_usd = sum(g(p, "B", s) - g(p, "A", s) for p, s in pairs) / 15
    led = [(g(p, "B", s) + g(p, "D", s)) / 2 for p, s in pairs]
    nol = [(g(p, "A", s) + g(p, "C", s)) / 2 for p, s in pairs]
    k2 = sum(x < y for x, y in zip(led, nol))
    out["paired"] = dict(B_cheaper_than_A=sum(ba), sign_p=sign_p(sum(ba), 15), mean_diff_usd=d_usd,
                         mean_diff_turns=d_turns, mean_diff_out=d_out,
                         reduction_B_vs_A=1 - out["per_arm"]["B"]["usd"] / out["per_arm"]["A"]["usd"],
                         ledger_usd=sum(led) / 15, noledger_usd=sum(nol) / 15, ledger_cheaper=k2,
                         ledger_sign_p=sign_p(k2, 15), ledger_reduction=1 - sum(led) / sum(nol))
    print(json.dumps(out["paired"], indent=1))
    probes = ["R1P3", "R1P5", "R2P4", "R2P5", "R1P4"]
    ps = {}
    for a in "ABD":
        ps[a] = {pr: sum(r["per_step"].get(pr, 0) for (p, l), r in rows.items() if l[0] == a) / 15 for pr in probes}
        tot = mean(a, "out")
        ps[a]["conflict"] = sum(ps[a][pr] for pr in CONFLICT)
        ps[a]["neutral"] = tot - ps[a]["conflict"]
    out["per_probe_output_mean"] = ps
    for pr in probes + ["conflict", "neutral"]:
        print(f"{pr:9s} A {ps['A'][pr]:8.0f}  B {ps['B'][pr]:8.0f}  D {ps['D'][pr]:8.0f}  B vs A {100*(ps['B'][pr]/ps['A'][pr]-1):+.1f}%")
    json.dump(out, open(os.path.join(HERE, "token_economics_v2.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
