#!/usr/bin/env python3
"""GovDrift worker-phase driver — runs one project's worker session to the compaction
band, with per-turn state checkpoints, rate-limit backoff, and a budget guard.

Usage: drive_worker.py --project p1 [--band-low 100000] [--band-high 150000]

State: run/state_<proj>_worker.json — safe to re-invoke; completed turns are skipped.
Stops (and records phase) when:
  BAND_REACHED      last-turn context >= band-low  -> orchestrator compacts + forks
  BAND_NOT_REACHED  turn list exhausted below band -> orchestrator decides (protocol)
  BUDGET_STOP       cumulative cost exceeded the guard
  FAILED            a turn failed after all retries -> checkpointed, resume later
"""
import argparse, json, os, subprocess, sys, time
from datetime import datetime, timezone

RUN = os.path.dirname(os.path.abspath(__file__))
MODEL = os.environ.get("GOVDRIFT_MODEL", "claude-haiku-4-5-20251001")
BACKOFFS = [60, 300, 900, 1800, 3600]      # seconds between retries of one turn
BUDGET_GUARD_USD = 15.0                    # sanity ceiling for ONE worker session

def log(state_path, msg):
    line = f"[{datetime.now(timezone.utc).isoformat()}] {msg}"
    print(line, flush=True)
    with open(state_path.replace(".json", ".log"), "a") as f:
        f.write(line + "\n")

def save(state_path, state):
    tmp = state_path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, state_path)

def run_turn(ws, prompt, sid):
    cmd = ["claude", "-p", prompt, "--model", MODEL,
           "--dangerously-skip-permissions", "--output-format", "json"]
    if sid:
        cmd += ["--resume", sid]
    p = subprocess.run(cmd, cwd=ws, capture_output=True, text=True, timeout=3600)
    out = p.stdout
    brace = out.find("{")
    if p.returncode != 0 or brace < 0:
        raise RuntimeError(f"claude failed rc={p.returncode} stderr={p.stderr[:500]} stdout={out[:300]}")
    d = json.loads(out[brace:])
    if d.get("is_error"):
        raise RuntimeError(f"claude result error: {json.dumps(d)[:500]}")
    return d

def context_of(ws, sid):
    """True context = usage of the LAST message in the session JSONL (H9 rule).
    The -p result JSON's usage aggregates every API call in the turn — wrong metric."""
    f = os.path.join(os.path.expanduser("~/.claude/projects"),
                     ws.replace("/", "-"), f"{sid}.jsonl")
    last = None
    with open(f) as fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except Exception:
                continue
            u = (rec.get("message") or {}).get("usage")
            if u:
                last = u
    if not last:
        return 0
    return ((last.get("cache_read_input_tokens") or 0) +
            (last.get("input_tokens") or 0) +
            (last.get("cache_creation_input_tokens") or 0))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--band-low", type=int, default=100_000)
    ap.add_argument("--band-high", type=int, default=150_000)
    args = ap.parse_args()

    spec = json.load(open(os.path.join(RUN, f"turns_{args.project}.json")))
    ws = os.path.join(RUN, "projects", args.project, "worker")
    os.makedirs(ws, exist_ok=True)
    state_path = os.path.join(RUN, f"state_{args.project}_worker.json")
    state = (json.load(open(state_path)) if os.path.exists(state_path) else
             {"project": args.project, "phase": "WORKER", "session_id": None,
              "turns_done": [], "last_context": 0, "total_cost_usd": 0.0,
              "turn_results": {}})

    for turn in spec["turns"]:
        tid = turn["id"]
        if tid in state["turns_done"]:
            continue
        # T-turns are MANDATORY (they carry the governing events) and always run.
        # Only H-turns are band fillers: stop before an H turn once the band is reached.
        if tid.startswith("H") and state["last_context"] >= args.band_low:
            state["phase"] = "BAND_REACHED"
            save(state_path, state)
            log(state_path, f"BAND_REACHED at {state['last_context']} before {tid}; stopping.")
            return
        if state["total_cost_usd"] > BUDGET_GUARD_USD:
            state["phase"] = "BUDGET_STOP"
            save(state_path, state)
            log(state_path, f"BUDGET_STOP at ${state['total_cost_usd']:.2f}; stopping.")
            return
        prompt = turn["text"] + spec["suffix"]
        d = None
        for attempt, backoff in enumerate([0] + BACKOFFS):
            if backoff:
                log(state_path, f"{tid}: retry {attempt} after {backoff}s backoff")
                time.sleep(backoff)
            try:
                d = run_turn(ws, prompt, state["session_id"])
                break
            except Exception as e:
                log(state_path, f"{tid}: attempt {attempt} failed: {e}")
        if d is None:
            state["phase"] = "FAILED"
            state["failed_turn"] = tid
            save(state_path, state)
            log(state_path, f"{tid}: FAILED after all retries; checkpointed.")
            sys.exit(2)
        state["session_id"] = d.get("session_id") or state["session_id"]
        ctx = context_of(ws, state["session_id"])
        cost = d.get("total_cost_usd") or 0.0
        state["last_context"] = ctx
        state["total_cost_usd"] = round(state["total_cost_usd"] + cost, 4)
        state["turns_done"].append(tid)
        state["turn_results"][tid] = {"context": ctx, "cost": cost,
                                      "result_head": (d.get("result") or "")[:400]}
        save(state_path, state)
        log(state_path, f"{tid}: done. context={ctx} cost=${cost:.3f} total=${state['total_cost_usd']:.2f} sid={state['session_id']}")
        mandatory = [t["id"] for t in spec["turns"] if t["id"].startswith("T")]
        if ctx >= args.band_low and all(m in state["turns_done"] for m in mandatory):
            state["phase"] = "BAND_REACHED"
            save(state_path, state)
            log(state_path, f"BAND_REACHED at {ctx} after {tid} (all mandatory turns done); stopping.")
            return

    state["phase"] = "BAND_NOT_REACHED"
    save(state_path, state)
    log(state_path, f"Turn list exhausted below band (context={state['last_context']}).")

if __name__ == "__main__":
    main()
