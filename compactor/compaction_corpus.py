"""Compactor-forgetting corpus (S1).

  python3 compaction_corpus.py [out_dir]     (default results/compactor; run from eval/)

Claude: unique isCompactSummary texts from tier2 + tier2c -> blinded bundle/<id>.txt + MAPPING.secret.json.
Codex: tier2b 'compacted' entries -> codex_retention.csv (governing owner turns retained verbatim?).
Read-only on all lineage data.
"""
import csv, glob, hashlib, json, os, random, re, sys, time
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SEED = 20260925
REDACT = re.compile(r"Drift Ledger|driftledger|drift-ledger|ledger|\bL\d+\b|PROPOSE[D]?|governing|handoff notice|drift\w*", re.I)  # drift\w*: acceptance needs 0 residual (generic "drift" in 16 spots)
ARMS = ("plugin-lazy", "plugin", "native")


def arm_of(name):
    return next(a for a in ARMS if name.startswith(a + "-"))


def model_of(name):
    return next((m for m in ("haiku", "sonnet", "opus", "sol6") if f"-{m}-" in name), "?")


def jsonl(path):
    for line in open(path, errors="replace"):
        try:
            yield json.loads(line)
        except ValueError:
            continue  # partial trailing line (live writer) or junk


def text_of(c):
    if isinstance(c, str):
        return c
    return "\n".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")


def claude(res):
    summ = {}  # sha1 -> record
    for tier in ("tier2", "tier2c"):
        for d in sorted(glob.glob(os.path.join(res, tier, "lineages", "*"))):
            lid = os.path.basename(d); seen = {}
            for p in glob.glob(os.path.join(d, "config", "projects", "*", "*.jsonl")):
                for e in jsonl(p):
                    if not e.get("isCompactSummary"):
                        continue
                    t = text_of(e.get("message", {}).get("content", ""))
                    h = hashlib.sha1(t.encode()).hexdigest(); ts = e.get("timestamp", "")
                    if h not in seen or ts < seen[h][0]:
                        seen[h] = (ts, t)
            for n, (h, (ts, t)) in enumerate(sorted(seen.items(), key=lambda kv: kv[1][0]), 1):
                r = summ.setdefault(h, {"sha1": h, "text": t, "tier": tier, "lineages": [], "ordinals": {}, "arms": set(), "models": set()})
                r["lineages"].append(lid); r["ordinals"][lid] = n
                r["arms"].add(arm_of(lid)); r["models"].add(model_of(lid))
                if r["tier"] != tier:
                    r["tier"] = "mixed"
    return summ


def codex(res, sc):
    gov = [(s["id"], s["text"]) for s in sc["steps"] if s.get("kind") == "owner" and s.get("governing")]
    rows = []
    for d in sorted(glob.glob(os.path.join(res, "tier2b", "lineages", "*"))):
        lid = os.path.basename(d)
        for p in sorted(glob.glob(os.path.join(d, "codexhome", "sessions", "**", "*.jsonl"), recursive=True)):
            for e in jsonl(p):
                if e.get("type") != "compacted":
                    continue
                pl = e.get("payload", {}); rh = pl.get("replacement_history") or []
                um = ["\n".join(b.get("text", "") for b in (m.get("content") or []) if isinstance(b, dict) and b.get("type") == "input_text")
                      for m in rh if isinstance(m, dict) and m.get("role") == "user"]
                blob = "\n".join(um)
                row = {"lineage": lid, "arm": arm_of(lid), "window_number": pl.get("window_number"), "timestamp": e.get("timestamp", ""),
                       "file": os.path.basename(p), "n_user_msgs": len(um), "total_chars": len(blob)}
                for tid, txt in gov:
                    row[tid] = "exact" if txt in blob else ("prefix80" if txt[:80] in blob else "missing")
                rows.append(row)
    return rows, [g[0] for g in gov]


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join("results", "compactor")
    res = os.path.join(HERE, "results")
    sc = json.load(open(os.path.join(HERE, "scenarios", "nclex_remediation.json")))
    snapshot = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    os.makedirs(os.path.join(out, "bundle"), exist_ok=True)
    for f in glob.glob(os.path.join(out, "bundle", "*.txt")):
        os.remove(f)

    summ = claude(res)
    recs = sorted(summ.values(), key=lambda r: r["sha1"])  # stable order before seeded shuffle
    rng = random.Random(SEED); ids = [f"C{n:03d}" for n in range(1, len(recs) + 1)]; rng.shuffle(ids)
    mapping, hits, disagree, stats = {}, 0, [], Counter()
    for bid, r in zip(ids, recs):
        t, n = REDACT.subn("[X]", r["text"]); hits += n
        open(os.path.join(out, "bundle", f"{bid}.txt"), "w").write(t)
        ords = sorted(set(r["ordinals"].values()))
        if len(ords) > 1:
            disagree.append({"id": bid, "ordinals": r["ordinals"]})
        arm = "/".join(sorted(r["arms"])); model = "/".join(sorted(r["models"]))
        mapping[bid] = {"sha1": r["sha1"], "tier": r["tier"], "model": model, "arm": arm, "lineages": sorted(r["lineages"]),
                        "ordinals": r["ordinals"], "ordinal": ords[0] if len(ords) == 1 else ords, "chars": len(r["text"]),
                        "redactions": n}
        stats[f"{r['tier']}|{model}|{arm}|{ords}"] += 1
    json.dump({"seed": SEED, "snapshot": snapshot, "items": mapping}, open(os.path.join(out, "MAPPING.secret.json"), "w"), indent=1)

    rows, gids = codex(res, sc)
    cols = ["lineage", "arm", "window_number", "timestamp", "file", "n_user_msgs", "total_chars"] + gids
    with open(os.path.join(out, "codex_retention.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, cols); w.writeheader(); w.writerows(rows)
    full = sum(all(r[g] == "exact" for g in gids) for r in rows)
    per = {g: sum(r[g] == "exact" for r in rows) for g in gids}
    line = f"governing turns retained verbatim: {full}/{len(rows)} compactions complete (per turn exact: {per})"

    json.dump({"snapshot": snapshot, "seed": SEED, "claude_unique_summaries": len(recs),
               "claude_by_tier_model_arm_ordinal": dict(sorted(stats.items())),
               "claude_ordinal_disagreements": disagree,
               "codex_compactions": len(rows),
               "codex_by_arm_window": dict(sorted(Counter(f"{r['arm']}|w{r['window_number']}" for r in rows).items())),
               "codex_summary": line, "redaction_hits": hits},
              open(os.path.join(out, "corpus_stats.json"), "w"), indent=1)
    json.dump([{"index": i, "item": t} for i, t in enumerate(sc["ground_truth"], 1)], open(os.path.join(out, "items.json"), "w"), indent=1)
    print(f"snapshot {snapshot}: {len(recs)} unique Claude summaries -> {out}/bundle ({hits} redactions, {len(disagree)} ordinal disagreements)")
    print(f"codex: {len(rows)} compactions; {line}")


if __name__ == "__main__":
    main()
