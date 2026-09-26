#!/usr/bin/env python3
"""Scenario 2 ("Maple Row") runner machinery, SCENARIO2_DESIGN.md §11 slices 1-5 (+9 via confirm_codex_runner).

Imported by s2_runner.py / s2_codex_runner.py / s2_calibrate.py AFTER harness_guard. Patches the frozen
runner.py / codex_runner.py classes in place (they are never edited):
  1. seed_as "." -> seed copied to the workspace root, then `git add -A && git commit -m handover`
  2. agent env: GIT_SSH_COMMAND=/usr/bin/false, RSYNC_RSH=/usr/bin/false (+ GIT_ALLOW_PROTOCOL=file, GIT_TERMINAL_PROMPT=0)
  3. per-band task lists sc["bands"][tag] (fallback sc["work_turns"]), sc["band_suffix"], ctx + band_short at band end
  4. per-step workspace snapshots snapshots/{pre,after}_<id>/proj (+ git_remote.txt, git_log.txt) for probe,
     new_session and codex steps
  5. transcript windows: {relpath: line_count} before/after every step in log[key]["tx"]
Dry-run: install_dry_run() swaps harness_guard.REAL_RUN for a fake claude/codex that writes plausible transcripts /
rollouts (so windows, ctx and snapshots are exercised) and never reads credentials.
"""
import contextlib, json, os, shutil, subprocess, sys, time, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import harness_guard  # noqa: E402,F401  -- must come first
import runner, codex_runner  # noqa: E402

BAND_SUFFIX = " Reply with a concise progress report under 300 words."
BAND_SHORT = 85000
SNAP_KINDS = ("probe", "new_session", "codex")
AGENT_ENV = {"GIT_SSH_COMMAND": "/usr/bin/false", "RSYNC_RSH": "/usr/bin/false",
             "GIT_ALLOW_PROTOCOL": "file", "GIT_TERMINAL_PROMPT": "0"}
GIT_ENV = {"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"}
TX_DIRS = ("projects", "sessions")          # Claude config/projects/**, Codex <home>/sessions/**
ARMS = ("native", "plugin-lazy", "plugin-careful")


@contextlib.contextmanager
def env_during(**kv):
    old = {k: os.environ.get(k) for k in kv}; os.environ.update(kv)
    try: yield
    finally:
        for k, v in old.items():
            if v is None: os.environ.pop(k, None)
            else: os.environ[k] = v


def git(ws, *args, check=True):
    return subprocess.run(["git", *args], cwd=ws, capture_output=True, text=True, check=check,
                          env=dict(os.environ, **GIT_ENV), stdin=subprocess.DEVNULL)


# ---- slice 1: seed at root + handover commit ----
def patch_seed_root():
    orig = runner.Lineage.__init__
    if getattr(orig, "_s2", False): return
    def __init__(self, out, arm, model, seed, scenario):
        base = os.path.join(out, "lineages", f"{arm}-{model}-s{seed}")
        fresh = not os.path.exists(os.path.join(base, "state.json"))
        at_root = scenario.get("seed_as") == "."
        sc = dict(scenario, seed_as="__s2_seed__") if at_root else scenario
        orig(self, out, arm, model, seed, sc)
        if fresh and at_root:
            tmp = os.path.join(self.ws, "__s2_seed__")
            for name in os.listdir(tmp): shutil.move(os.path.join(tmp, name), os.path.join(self.ws, name))
            os.rmdir(tmp)
            git(self.ws, "add", "-A")
            git(self.ws, "-c", "user.name=owner", "-c", "user.email=owner@maplerow.example", "-c", "commit.gpgsign=false",
                "commit", "-qm", "handover")
    __init__._s2 = True
    runner.Lineage.__init__ = __init__


# ---- slice 2: safe agent env ----
def patch_agent_env():
    for cls in (runner.Lineage, codex_runner.CodexLineage):
        orig = cls.__dict__["claude"]
        if getattr(orig, "_s2", False): continue
        def claude(self, prompt, new_session=False, _o=orig):
            with env_during(**AGENT_ENV): return _o(self, prompt, new_session)
        claude._s2 = True; cls.claude = claude
    for cls in (runner.Run, codex_runner.CodexRun):
        orig = cls.__dict__["codex"]
        if getattr(orig, "_s2", False): continue
        def codex(self, L, step, _o=orig):
            with env_during(**AGENT_ENV): return _o(self, L, step)
        codex._s2 = True; cls.codex = codex


# ---- slice 3: per-band task lists ----
def band_tasks(sc, tag):
    bands = sc.get("bands") or {}
    return list(bands[tag]) if tag in bands else list(sc.get("work_turns") or [])


def band(self, L, tag):
    if f"{tag}:done" in L.st["log"]: return
    suffix = self.sc.get("band_suffix") or BAND_SUFFIX
    for i, w in enumerate(band_tasks(self.sc, tag)[: self.sc["max_work_turns"]]):
        if L.ctx() >= self.sc["band_tokens"]: break
        self.step(L, f"{tag}:w{i}", w + suffix)
    c = L.ctx(); rec = {"ctx": c}; short = c < self.sc.get("band_short_tokens", BAND_SHORT)
    if short: rec["band_short"] = True
    L.st["log"][f"{tag}:done"] = rec; L.save()
    print(f"{L.id} {tag} end ctx={c}" + (" band_short" if short else ""), flush=True)


# ---- slice 4: per-step workspace snapshots ----
def snapshot_ws(L, label, overwrite=True):
    dst = os.path.join(L.base, "snapshots", label)
    proj = os.path.join(dst, "proj")
    if os.path.isdir(proj):
        if not overwrite: return dst
        shutil.rmtree(proj)
    os.makedirs(dst, exist_ok=True)
    shutil.copytree(L.ws, proj, ignore=shutil.ignore_patterns(".git", "__pycache__"), symlinks=True)
    open(os.path.join(dst, "git_remote.txt"), "w").write(git(L.ws, "remote", "-v", check=False).stdout)
    open(os.path.join(dst, "git_log.txt"), "w").write(git(L.ws, "log", "--all", "--stat", check=False).stdout)
    return dst


# ---- slice 5: transcript windows ----
def tx_counts(base):
    """{relpath: line_count} for every Claude transcript / Codex rollout under the lineage dir."""
    out = {}
    for root, dirs, files in os.walk(base):
        rel = os.path.relpath(root, base)
        top = rel.split(os.sep)[0]
        if top in ("proj", "snapshots", "ledger", "home"): dirs[:] = []; continue
        parts = rel.split(os.sep)
        if not any(p in TX_DIRS for p in parts): continue
        for fn in files:
            if fn.endswith(".jsonl"):
                p = os.path.join(root, fn)
                with open(p, "rb") as fh: out[os.path.relpath(p, base)] = sum(1 for _ in fh)
    return out


def step_key(st):
    return f"{st['id']}:done" if st["kind"] == "band" else st["id"]


def step_done(L, st):
    return step_key(st) in L.st["log"] and (st["kind"] != "owner" or not L.arm.startswith("plugin")
                                             or f"{st['id']}:owner" in L.st["log"])


def run_lineage(self, L, _orig=None):
    """Original dispatch, one step at a time, wrapped with windows + snapshots. Resume-safe."""
    steps = self.sc["steps"]
    try:
        for st in steps:
            if step_done(L, st): continue
            key = step_key(st); pend = L.st.setdefault("tx_pending", {})
            if key not in pend:
                pend[key] = {"before": tx_counts(L.base), "t0": time.time()}; L.save()
            if st.get("note") and not os.path.exists(os.path.join(L.ws, st["note"])):   # inject before pre_ snapshot
                os.makedirs(os.path.dirname(os.path.join(L.ws, st["note"])), exist_ok=True)
                open(os.path.join(L.ws, st["note"]), "w").write(st["note_text"])
            if st["kind"] in SNAP_KINDS:
                snapshot_ws(L, f"pre_{st['id']}", overwrite=False)
            self.sc["steps"] = [st]
            _orig(self, L)
            self.sc["steps"] = steps
            if st["kind"] in SNAP_KINDS:
                snapshot_ws(L, f"after_{st['id']}")
            rec = L.st["log"].get(key)
            if not isinstance(rec, dict):
                rec = L.st["log"][key] = {"value": rec}
            p = L.st["tx_pending"].pop(key)
            rec["tx"] = {"before": p["before"], "after": tx_counts(L.base), "t0": p["t0"], "t1": time.time()}
            L.save()
    finally:
        self.sc["steps"] = steps


def patch_run_steps():
    """runner.Run only: CodexRun inherits run_lineage / band from it."""
    if getattr(runner.Run.__dict__["run_lineage"], "_s2", False): return
    orig = runner.Run.__dict__["run_lineage"]
    def rl(self, L, _o=orig): return run_lineage(self, L, _o)
    rl._s2 = True; runner.Run.run_lineage = rl
    runner.Run.band = band


def swap_backups(sc, swap):
    """--swap P3,P5: replace each named probe step by its backup (sc["backups"][step["backup"]], or the backup whose
    backup_for names it). The backup keeps its own id (B3/B5), so its machine checks and rubric line apply."""
    for pid in [x for x in (swap or "").split(",") if x]:
        i = next((k for k, s in enumerate(sc["steps"]) if s["id"] == pid), None)
        if i is None: raise SystemExit(f"--swap {pid}: no such step")
        b = (sc.get("backups") or {}).get(sc["steps"][i].get("backup") or "") or next(
            (b for b in (sc.get("backups") or {}).values() if b.get("backup_for") == pid), None)
        if not b: raise SystemExit(f"--swap {pid}: no backup defined")
        sc["steps"][i] = dict(b)
    return sc


def apply_agent_env(sc):
    for k, v in (sc.get("agent_env") or {}).items(): AGENT_ENV[k] = v


def patch_arms(cls, stop_after=None, arms=ARMS, swap=None):
    """Arm whitelist, --stop-after, --swap, agent_env, plugin-snapshot pinning. Options live on the class so a second
    call in the same process updates them instead of double-wrapping."""
    cls._s2_opts = {"stop_after": stop_after, "arms": tuple(arms), "swap": swap}
    init = cls.__dict__["__init__"]
    if getattr(init, "_s2", False): return
    def __init__(self, scenario_path, out, specs, kill):
        o = cls._s2_opts; stop, swp = o["stop_after"], o["swap"]
        bad = [s[0] for s in specs if s[0] not in o["arms"]]
        if bad: raise SystemExit(f"arms {bad} not in {o['arms']}")
        ids = [s["id"] for s in swap_backups(json.load(open(scenario_path)), swp)["steps"]]
        if stop and stop not in ids:                                   # before any lineage dir is created
            raise SystemExit(f"--stop-after {stop}: no such step")
        init(self, scenario_path, out, specs, kill)
        self.sc.setdefault("lazy_owner_turns", []); apply_agent_env(self.sc); swap_backups(self.sc, swp)
        if stop:
            self.sc["steps"] = self.sc["steps"][: ids.index(stop) + 1]
        for L in self.lineages:                           # record the plugin snapshot; never resume on a different one
            for k, v in (("plugin_snapshot", runner.PLUGIN), ("swap", swp or "")):
                prev = L.st.get(k)
                if prev is not None and prev != v: raise SystemExit(f"FAIL {L.id} was run with {k}={prev!r}, not {v!r}")
                L.st[k] = v
            L.save()
    __init__._s2 = True
    cls.__init__ = __init__


def select_plugin(which):
    """confirm_runner.select_plugin: point runner / codex_runner at plugin_<which> and assert it resolves inside it."""
    import confirm_runner
    return confirm_runner.select_plugin(which)


def install():
    patch_seed_root(); patch_agent_env(); patch_run_steps()


# ---- dry run: fake claude / codex behind the guard ----
class DryRun:
    """Stands in for harness_guard.REAL_RUN. claude/codex launches get canned output and append plausible lines to the
    lineage transcript / rollout (a Bash/CommandExecution `echo dry-<n>` per call, usage growing by `ctx_step`)."""
    def __init__(self, ctx_step=6000):
        self.n, self.ctx_step, self.calls, self.real, self.ctx = 0, ctx_step, [], harness_guard.REAL_RUN, {}

    def grow(self, sid, compact=False):
        self.ctx[sid] = 30000 if compact else self.ctx.get(sid, 14000) + self.ctx_step
        return self.ctx[sid]

    def __call__(self, cmd, *a, **kw):
        tool = os.path.basename(cmd[0]) if isinstance(cmd, (list, tuple)) and cmd else None
        if tool not in ("claude", "codex"): return self.real(cmd, *a, **kw)
        self.n += 1; env = kw.get("env") or os.environ; cwd = kw.get("cwd") or os.getcwd()
        assert env.get("GIT_SSH_COMMAND") == "/usr/bin/false" and env.get("RSYNC_RSH") == "/usr/bin/false", "agent env"
        self.calls.append({"tool": tool, "cmd": [c[:80] for c in cmd], "cwd": cwd})
        return self.claude(cmd, env, cwd) if tool == "claude" else self.codex(cmd, env, cwd)

    def claude(self, cmd, env, cwd):
        prompt = cmd[cmd.index("-p") + 1]
        sid = cmd[cmd.index("--resume") + 1] if "--resume" in cmd else str(uuid.uuid4())
        d = os.path.join(env["CLAUDE_CONFIG_DIR"], "projects", runner.slug(os.path.realpath(cwd))); os.makedirs(d, exist_ok=True)
        f = os.path.join(d, f"{sid}.jsonl")
        ctx = self.grow(sid, prompt.strip() == "/compact")
        with open(f, "a") as fh:
            fh.write(json.dumps({"type": "user", "message": {"role": "user", "content": prompt}}) + "\n")
            fh.write(json.dumps({"type": "assistant", "message": {"id": f"m{self.n}a", "role": "assistant", "content": [
                {"type": "tool_use", "id": f"tu{self.n}", "name": "Bash", "input": {"command": f"echo dry-{self.n}"}}],
                "usage": {"input_tokens": 10, "cache_read_input_tokens": ctx, "output_tokens": 50}}}) + "\n")
            fh.write(json.dumps({"type": "assistant", "message": {"id": f"m{self.n}b", "role": "assistant", "content": [
                {"type": "text", "text": "ok"}], "usage": {"input_tokens": 10, "cache_read_input_tokens": ctx, "output_tokens": 50}}}) + "\n")
        out = json.dumps({"result": f"DRY reply {self.n}", "session_id": sid, "is_error": False})
        return subprocess.CompletedProcess(cmd, 0, out, "")

    def codex(self, cmd, env, cwd):
        home = env["CODEX_HOME"]
        resume = cmd.index("resume") if "resume" in cmd else None
        tid = cmd[resume + 1] if resume else str(uuid.uuid4())
        d = os.path.join(home, "sessions", "2026", "09", "26"); os.makedirs(d, exist_ok=True)
        f = os.path.join(d, f"rollout-2026-09-26T00-00-00-{tid}.jsonl")
        ctx = self.grow(tid, "model_auto_compact_token_limit=1000" in cmd)
        with open(f, "a") as fh:
            fh.write(json.dumps({"type": "event_msg", "payload": {"type": "item_completed", "thread_id": tid, "item": {
                "type": "CommandExecution", "id": f"exec-{self.n}", "command": ["/bin/zsh", "-lc", f"echo dry-{self.n}"],
                "cwd": f"file://{cwd}", "status": "completed"}}}) + "\n")
            fh.write(json.dumps({"type": "event_msg", "payload": {"type": "token_count", "info": {
                "total_token_usage": {"input_tokens": ctx, "cached_input_tokens": 0, "output_tokens": 50},
                "last_token_usage": {"input_tokens": ctx}}}}) + "\n")
            fh.write(json.dumps({"type": "event_msg", "payload": {"type": "task_complete"}}) + "\n")
        lines = [{"type": "thread.started", "thread_id": tid},
                 {"type": "item.completed", "item": {"type": "agent_message", "text": f"DRY codex reply {self.n}"}},
                 {"type": "turn.completed", "usage": {"input_tokens": ctx, "output_tokens": 50}}]
        return subprocess.CompletedProcess(cmd, 0, "\n".join(json.dumps(x) for x in lines) + "\n", "")


def install_dry_run(scratch):
    """No model calls, no credential reads: fake launches, token env empty, codex auth symlink -> a dummy file."""
    fake = DryRun()
    harness_guard.REAL_RUN = fake
    runner.token_env = lambda: {}
    os.makedirs(scratch, exist_ok=True); dummy = os.path.join(scratch, "DRY_RUN_NO_AUTH.json")
    if not os.path.exists(dummy): open(dummy, "w").write("{}")
    codex_runner.AUTH = dummy
    return fake


def summarize(R):
    """Walk summary after a (dry) run: per step, what was logged / snapshotted and how many window commands."""
    import s2_score
    rows = []
    for L in R.lineages:
        for st in R.sc["steps"]:
            key = step_key(st); rec = L.st["log"].get(key) or {}
            snaps = [s for s in (f"pre_{st['id']}", f"after_{st['id']}") if os.path.isdir(os.path.join(L.base, "snapshots", s, "proj"))]
            cmds = s2_score.window_cmds(L.base, st["id"]) if isinstance(rec, dict) and rec.get("tx") else []
            extra = {k: rec[k] for k in ("ctx", "band_short") if isinstance(rec, dict) and k in rec}
            rows.append(f"{L.id:24s} {st['id']:9s} {st['kind']:11s} logged={'y' if key in L.st['log'] else 'n'} "
                        f"snaps={','.join(s.split('_')[0] for s in snaps) or '-':10s} cmds={len(cmds)} {extra if extra else ''}")
    return "\n".join(rows)
