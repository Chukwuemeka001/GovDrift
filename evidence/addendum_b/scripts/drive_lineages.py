#!/usr/bin/env python3
"""GovDrift lineage driver — fork, probes, inter-round work, per-lineage compaction.

All phases are resumable: lineage state lives in run/state_<proj>_lineages.json and each
lineage records the last completed step. Failed lineages checkpoint and can be re-driven
by re-invoking the same command. Concurrency across lineages is capped (default 3).

Commands
  fork      --project p1                       clone workspace + fork session per arm-seed
  probe     --project p1 --round 1 --probe R1P1 [--payload-dir payloads/p1/gen1]
            sends the frozen probe to every lineage that hasn't done it; for the FIRST
            probe of a round, arm B/C/D lineages get <payload file> + probe prepended
            (payload file: <dir>/<ARM>.txt). Responses recorded in state.
  reply     --project p1 --round 1 --probe R1P4 --decisions <json>
            decisions: {"<lineage>": "confirm"|"none"} — sends the frozen conditional
            reply to lineages marked confirm (text from probes_<proj>.json).
  turn      --project p1 --round 1 --step WB1|W2|W3|H1.. sends a frozen work turn to all
  compact   --project p1 --round 1                  /compact each lineage in band
  archive   --project p1 --label <label>            archive every lineage session JSONL
  status    --project p1                            print per-lineage stage table

Probe/turn texts come from probes_<proj>.json (frozen from the turn scripts).
"""
import argparse, concurrent.futures, json, os, subprocess, sys, threading, time, uuid
from datetime import datetime, timezone

RUN = os.path.dirname(os.path.abspath(__file__))
MODEL = os.environ.get("GOVDRIFT_MODEL", "claude-haiku-4-5-20251001")
ORIG_RUN = os.path.join(os.path.dirname(RUN), "run")
# Arm F = CLAUDE.md baseline (gen-1 B ledger content verbatim, static, in workspace CLAUDE.md,
# no banner, nothing prepended). Arm N = native re-run drift control (same as original A).
LINEAGE_PLAN = [("F", s) for s in (1, 2, 3, 4, 5)] + [("N", 1)]
CONCURRENCY = int(os.environ.get("GOVDRIFT_CONCURRENCY", "3"))
BACKOFFS = [60, 300, 900, 1800]
LOCK = threading.Lock()

def now(): return datetime.now(timezone.utc).isoformat()

def slug(path): return path.replace("/", "-")
def projdir(ws): return os.path.expanduser(f"~/.claude/projects/{slug(ws)}")

def log(proj, msg):
    line = f"[{now()}] {msg}"
    print(line, flush=True)
    with open(os.path.join(RUN, f"state_{proj}_lineages.log"), "a") as f:
        f.write(line + "\n")

def state_path(proj): return os.path.join(RUN, f"state_{proj}_lineages.json")

def load_state(proj):
    p = state_path(proj)
    return json.load(open(p)) if os.path.exists(p) else {"lineages": {}}

def save_state(proj, st):
    with LOCK:
        tmp = state_path(proj) + ".tmp"
        json.dump(st, open(tmp, "w"), indent=2)
        os.replace(tmp, state_path(proj))

def sha_manifest(root):
    out = []
    for r, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in sorted(files):
            full = os.path.join(r, f)
            h = subprocess.run(["shasum", "-a", "256", full], capture_output=True, text=True)
            out.append(h.stdout.split()[0] + "  " + os.path.relpath(full, root))
    return "\n".join(sorted(out, key=lambda l: l.split("  ")[1]))

def clone_ws(src, dst):
    if os.path.exists(dst):
        return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    subprocess.run(["rm", "-rf", os.path.join(src, "__pycache__")], capture_output=True)
    for r, dirs, _ in os.walk(src):
        for d in list(dirs):
            if d == "__pycache__":
                subprocess.run(["rm", "-rf", os.path.join(r, d)], capture_output=True)
    m1 = sha_manifest(src)
    subprocess.run(["cp", "-R", src, dst], check=True)
    m2 = sha_manifest(dst)
    if m1 != m2:
        raise RuntimeError(f"clone mismatch {src} -> {dst}")
    with open(os.path.join(dst, "FORK_MANIFEST.sha256"), "w") as f:
        f.write(m1 + "\n")

def fork_session(src_ws, sid, dst_ws):
    src_f = os.path.join(projdir(src_ws), sid + ".jsonl")
    new_sid = str(uuid.uuid4())
    os.makedirs(projdir(dst_ws), exist_ok=True)
    data = open(src_f).read().replace(sid, new_sid).replace(src_ws, dst_ws)
    with open(os.path.join(projdir(dst_ws), new_sid + ".jsonl"), "w") as f:
        f.write(data)
    return new_sid

def run_claude(ws, prompt, sid):
    cmd = ["claude", "-p", prompt, "--model", MODEL,
           "--dangerously-skip-permissions", "--output-format", "json",
           "--resume", sid]
    p = subprocess.run(cmd, cwd=ws, capture_output=True, text=True, timeout=3600)
    out = p.stdout
    brace = out.find("{")
    if p.returncode != 0 or brace < 0:
        raise RuntimeError(f"rc={p.returncode} err={p.stderr[:400]}")
    d = json.loads(out[brace:])
    if d.get("is_error"):
        raise RuntimeError(f"result error: {json.dumps(d)[:400]}")
    return d

def ctx_of(ws, sid):
    """True context = usage of the LAST message in the session JSONL (H9 rule)."""
    f = os.path.join(projdir(ws), f"{sid}.jsonl")
    last = None
    try:
        with open(f) as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                u = (rec.get("message") or {}).get("usage")
                if u:
                    last = u
    except FileNotFoundError:
        return 0
    if not last:
        return 0
    return ((last.get("cache_read_input_tokens") or 0) + (last.get("input_tokens") or 0) +
            (last.get("cache_creation_input_tokens") or 0))

def with_retries(proj, lid, fn):
    for attempt, backoff in enumerate([0] + BACKOFFS):
        if backoff:
            log(proj, f"{lid}: retry {attempt} after {backoff}s")
            time.sleep(backoff)
        try:
            return fn()
        except Exception as e:
            log(proj, f"{lid}: attempt {attempt} failed: {e}")
    return None

def drive_step(proj, st, lid, prompt, step_key, record_response=True):
    lin = st["lineages"][lid]
    if step_key in lin["steps_done"]:
        return True
    d = with_retries(proj, lid, lambda: run_claude(lin["ws"], prompt, lin["sid"]))
    if d is None:
        lin["failed_step"] = step_key
        save_state(proj, st)
        return False
    lin["sid"] = d.get("session_id") or lin["sid"]
    lin["last_context"] = ctx_of(lin["ws"], lin["sid"])
    lin["cost"] = round(lin.get("cost", 0) + (d.get("total_cost_usd") or 0), 4)
    lin["steps_done"].append(step_key)
    if record_response:
        lin.setdefault("responses", {})[step_key] = (d.get("result") or "")[:3000]
    lin.pop("failed_step", None)
    save_state(proj, st)
    log(proj, f"{lid}: {step_key} done ctx={lin['last_context']} cost=${lin['cost']:.2f}")
    return True

def parallel_over_lineages(proj, st, lids, fn):
    ok = True
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        futs = {ex.submit(fn, lid): lid for lid in lids}
        for fut in concurrent.futures.as_completed(futs):
            if not fut.result():
                ok = False
    return ok

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("--project", required=True)
    ap.add_argument("--round", type=int, default=1)
    ap.add_argument("--probe")
    ap.add_argument("--step")
    ap.add_argument("--payload-dir")
    ap.add_argument("--decisions")
    ap.add_argument("--label")
    ap.add_argument("--band-low", type=int, default=100_000)
    args = ap.parse_args()
    proj = args.project
    probes = json.load(open(os.path.join(RUN, f"probes_{proj}.json")))
    st = load_state(proj)

    if args.cmd == "fork":
        wstate = json.load(open(os.path.join(ORIG_RUN, f"state_{proj}_worker.json")))
        src_ws, sid = os.path.join(ORIG_RUN, "projects", proj, "worker"), wstate["session_id"]
        claudemd = open(os.path.join(RUN, f"claudemd_{proj}.md")).read()
        for arm, seed in LINEAGE_PLAN:
            lid = f"{arm}-s{seed}"
            if lid in st["lineages"]:
                continue
            dst = os.path.join(RUN, "projects", proj, "arms", lid)
            clone_ws(src_ws, dst)
            if arm == "F":
                p = os.path.join(dst, "CLAUDE.md")
                open(p, "w").write(claudemd)
                h = subprocess.run(["shasum", "-a", "256", p], capture_output=True, text=True).stdout.split()[0]
                # CLAUDE.md is part of the arm's starting state: add to fork manifest so
                # disk-delta scoring does not count it as successor-created.
                with open(os.path.join(dst, "FORK_MANIFEST.sha256"), "a") as f:
                    f.write(f"{h}  CLAUDE.md\n")
            new_sid = fork_session(src_ws, sid, dst)
            st["lineages"][lid] = {"arm": arm, "seed": seed, "ws": dst,
                                   "sid": new_sid, "steps_done": [], "cost": 0.0}
            save_state(proj, st)
            log(proj, f"forked {lid} sid={new_sid}")
        log(proj, f"fork complete: {len(st['lineages'])} lineages")
        return

    if args.cmd == "fork-orig":
        # Continue original Tier-1 A and B lineages (post-R2P6 final state) into generation 3.
        ost = json.load(open(os.path.join(ORIG_RUN, f"state_{proj}_lineages.json")))["lineages"]
        for arm in ("A", "B"):
            for seed in (1, 2, 3, 4, 5):
                lid = f"{arm}-s{seed}"
                if lid in st["lineages"]:
                    continue
                o = ost[lid]
                dst = os.path.join(RUN, "projects", proj, "arms", lid)
                clone_ws(o["ws"], dst)
                new_sid = fork_session(o["ws"], o["sid"], dst)
                st["lineages"][lid] = {"arm": arm, "seed": seed, "ws": dst, "sid": new_sid,
                                       "steps_done": [], "cost": 0.0, "origin": "tier1-final"}
                save_state(proj, st)
                log(proj, f"forked original {lid} sid={new_sid}")
        return

    if args.cmd == "snapshot":
        # gen-3 fork point manifest (after compaction #3) for disk-delta scoring
        for lid, lin in st["lineages"].items():
            p = os.path.join(lin["ws"], f"GEN{args.round}_MANIFEST.sha256")
            if not os.path.exists(p):
                open(p, "w").write(sha_manifest(lin["ws"]) + "\n")
        log(proj, f"snapshot GEN{args.round} manifests written")
        return

    if args.cmd == "status":
        for lid, lin in sorted(st["lineages"].items()):
            print(f"{lid}: steps={len(lin['steps_done'])} last={lin['steps_done'][-1] if lin['steps_done'] else '-'} "
                  f"ctx={lin.get('last_context','-')} cost=${lin.get('cost',0):.2f} "
                  f"failed={lin.get('failed_step','-')}")
        return

    if args.cmd == "probe":
        text = probes["probes"][args.probe]
        first_of_round = probes["first_probe"][str(args.round)] == args.probe

        def go(lid):
            lin = st["lineages"][lid]
            prompt = text
            if first_of_round and lin["arm"] in ("B", "C", "D"):
                per_seed = os.path.join(RUN, args.payload_dir, f"{lin['arm']}-s{lin['seed']}.txt")
                pf = per_seed if os.path.exists(per_seed) else \
                    os.path.join(RUN, args.payload_dir, f"{lin['arm']}.txt")
                prompt = open(pf).read().rstrip() + "\n\n" + text
            return drive_step(proj, st, lid, prompt, f"R{args.round}:{args.probe}")
        ok = parallel_over_lineages(proj, st, sorted(st["lineages"]), go)
        log(proj, f"probe {args.probe} round {args.round} {'complete' if ok else 'INCOMPLETE — re-run to resume'}")
        sys.exit(0 if ok else 3)

    if args.cmd == "reply":
        decisions = json.load(open(args.decisions))
        reply_text = probes["conditional_replies"][args.probe]

        def go(lid):
            if decisions.get(lid) != "confirm":
                return True
            return drive_step(proj, st, lid, reply_text, f"R{args.round}:{args.probe}-reply")
        ok = parallel_over_lineages(proj, st, sorted(st["lineages"]), go)
        log(proj, f"reply {args.probe} {'complete' if ok else 'INCOMPLETE'}")
        sys.exit(0 if ok else 3)

    if args.cmd == "turn":
        text = probes["work_turns"][args.step]

        def go(lid):
            return drive_step(proj, st, lid, text, f"R{args.round}:{args.step}", record_response=False)
        ok = parallel_over_lineages(proj, st, sorted(st["lineages"]), go)
        log(proj, f"turn {args.step} {'complete' if ok else 'INCOMPLETE'}")
        sys.exit(0 if ok else 3)

    if args.cmd == "workto-band":
        # send H-turns in order to each lineage below band until band reached
        hseq = probes.get(f"band_filler_sequence_r{args.round}", probes["band_filler_sequence"])

        def go(lid):
            lin = st["lineages"][lid]
            done_key = f"R{args.round}:band:done"
            if done_key in lin["steps_done"]:
                return True   # D5 fix: never re-run band filling after it completed (resume-safe)
            for h in hseq:
                if lin.get("last_context", 0) >= args.band_low:
                    return True
                key = f"R{args.round}:band:{h}"
                if key in lin["steps_done"]:
                    continue
                if not drive_step(proj, st, lid, probes["work_turns"][h], key, record_response=False):
                    return False
            lin["steps_done"].append(done_key); save_state(proj, st)
            return True
        ok = parallel_over_lineages(proj, st, sorted(st["lineages"]), go)
        log(proj, f"workto-band {'complete' if ok else 'INCOMPLETE'}")
        sys.exit(0 if ok else 3)

    if args.cmd == "compact":
        def go(lid):
            return drive_step(proj, st, lid, "/compact", f"R{args.round}:compact", record_response=False)
        ok = parallel_over_lineages(proj, st, sorted(st["lineages"]), go)
        log(proj, f"compact round {args.round} {'complete' if ok else 'INCOMPLETE'}")
        sys.exit(0 if ok else 3)

    if args.cmd == "archive":
        os.makedirs(os.path.join(RUN, "transcripts"), exist_ok=True)
        for lid, lin in sorted(st["lineages"].items()):
            src = os.path.join(projdir(lin["ws"]), lin["sid"] + ".jsonl")
            dst = os.path.join(RUN, "transcripts", f"{proj}_{args.label}_{lid}_{lin['sid']}.jsonl")
            subprocess.run(["cp", src, dst], check=True)
        log(proj, f"archived {len(st['lineages'])} lineage transcripts label={args.label}")
        return

    print("unknown cmd", file=sys.stderr); sys.exit(1)

if __name__ == "__main__":
    main()
