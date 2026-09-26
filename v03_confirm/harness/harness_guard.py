#!/usr/bin/env python3
"""govdrift-eval harness guard (H1). Import FIRST from a wrapper runner; it patches the frozen runners in place.

  import harness_guard  # noqa  -- before anything else touches runner / codex_runner

Guards against the three failures we must never repeat:
 (a) owner-private context leaking in: every claude/codex launch must run with cwd, CLAUDE_CONFIG_DIR / CODEX_HOME
     outside the home directory (Claude Code loads CLAUDE.md from ANCESTOR dirs regardless of CLAUDE_CONFIG_DIR);
     lineage out dirs under home are refused; after every Claude call the lineage transcripts are scanned for
     instruction attachments (CLAUDE.md / AGENTS.md / memory files) whose path is outside the lineage -> fail-stop,
     naming the path only (never the contents).
 (b) inherited stdin appended to `claude -p` prompts: every claude/codex subprocess gets stdin=DEVNULL.
 (c) Codex 401 / rate-limit refresh races: a Codex step whose reply is empty, or whose stderr / --json error events /
     new rollout lines show 401 / Unauthorized / rate-limit, is retried after RETRY_WAIT s up to RETRIES times,
     then fail-stops; an empty or failed reply is never recorded as a completed step (second-harness X1/X2 too).
     Concurrent Codex subprocesses across processes are capped by an fcntl slot lock (GOVDRIFT_CODEX_MAX, default 6).
 (a') Codex analogue: after each Codex call, new rollout lines are scanned for skill roots (Codex lists
     $HOME/.agents/skills regardless of CODEX_HOME) and AGENTS.md sources outside the lineage -> fail-stop. Wrappers
     avoid it by giving codex a lineage-local HOME.
"""
import contextlib, fcntl, glob, json, os, re, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import runner  # noqa: E402
import codex_runner  # noqa: E402

HOME = os.path.realpath(os.path.expanduser("~"))
RECOMMENDED_ROOT = "/Users/Shared/govdrift-eval"
LOCK_DIR = os.path.join(RECOMMENDED_ROOT, ".codex-slots")      # overridable: GOVDRIFT_LOCK_DIR
RETRIES, RETRY_WAIT = 3, 60
AUTH_RE = re.compile(r"\b401\b|unauthori[sz]ed|rate[ _-]?limit|\b429\b|too many requests|usage limit", re.I)
INSTR_TYPES = ("instructions", "nested_memory")
REAL_RUN = subprocess.run          # tests replace this with a fake
sleep = time.sleep                 # tests replace this
LAST = {}                          # last guarded launch: {"tool": "claude"|"codex", "proc": CompletedProcess}
_SCANNED = {}                      # transcript path -> bytes already scanned


class GuardFail(SystemExit):
    """Every guard fail-stop. A step that ends in one is dropped from the log and the lineage marked contaminated."""


def fail(msg):
    raise GuardFail(f"GUARD FAIL {msg}")


def contaminate(L, key, reason):
    """Drop the step (never keep a step that failed a guard check), then mark the lineage so it cannot resume."""
    if key is not None and key in L.st["log"]:
        L.st["log"].pop(key); L.save()
    L.st["contaminated"] = reason; L.save()


def under(p, root):
    p, root = os.path.realpath(p), os.path.realpath(root)
    return p == root or p.startswith(root.rstrip(os.sep) + os.sep)


def check_outside_home(path, what):
    if under(path, HOME):
        fail(f"{what} {path} is under the home directory {HOME}: Claude Code would load the operator's ancestor "
             f"CLAUDE.md files. Use an out dir under {RECOMMENDED_ROOT}.")


# ---- (c) cross-process Codex concurrency cap ----
@contextlib.contextmanager
def codex_slot():
    n = max(1, int(os.environ.get("GOVDRIFT_CODEX_MAX", "6")))
    d = os.environ.get("GOVDRIFT_LOCK_DIR") or LOCK_DIR
    os.makedirs(d, exist_ok=True)
    while True:
        for i in range(n):
            f = open(os.path.join(d, f"slot{i}.lock"), "a")
            try:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                f.close(); continue
            try:
                yield i
            finally:
                fcntl.flock(f, fcntl.LOCK_UN); f.close()
            return
        time.sleep(0.5)


# ---- (a)(b) guarded subprocess, swapped into runner / codex_runner ----
class GuardedSubprocess:
    def __getattr__(self, k):
        return getattr(subprocess, k)

    def run(self, cmd, *a, **kw):
        tool = os.path.basename(cmd[0]) if isinstance(cmd, (list, tuple)) and cmd else None
        if tool not in ("claude", "codex"):
            return REAL_RUN(cmd, *a, **kw)
        if "input" in kw or kw.get("stdin") not in (None, subprocess.DEVNULL):
            fail(f"{tool} launched with stdin/input: inherited stdin is appended to the prompt")
        kw["stdin"] = subprocess.DEVNULL
        check_outside_home(kw.get("cwd") or os.getcwd(), f"{tool} working directory")
        env = kw.get("env") or os.environ
        var = "CLAUDE_CONFIG_DIR" if tool == "claude" else "CODEX_HOME"
        if not env.get(var): fail(f"{tool} launched without {var}: it would use the operator's own config")
        check_outside_home(env[var], f"{tool} {var}")
        if not env.get("HOME"): fail(f"{tool} launched without HOME: give it a lineage-local HOME")
        check_outside_home(env["HOME"], f"{tool} HOME")
        LAST.clear()
        if tool == "codex":
            with codex_slot(): p = REAL_RUN(cmd, *a, **kw)
        else:
            p = REAL_RUN(cmd, *a, **kw)
        LAST.update(tool=tool, proc=p, codex_home=env.get("CODEX_HOME"))
        return p


# ---- (a) transcript scan ----
def _instr_paths(o):
    if isinstance(o, dict):
        if o.get("type") in INSTR_TYPES:
            if isinstance(o.get("path"), str): yield o["path"]
            for f in o.get("files") or []:
                if isinstance(f, dict) and isinstance(f.get("path"), str): yield f["path"]
        for v in o.values(): yield from _instr_paths(v)
    elif isinstance(o, list):
        for v in o: yield from _instr_paths(v)


def instruction_leaks(base):
    """Paths of instruction files loaded into any Claude transcript under `base` (config dirs = */projects/) that are
    not inside `base`. Incremental: only bytes not scanned before are read."""
    leaks = set()
    if not os.path.isdir(base): return []
    for top in os.listdir(base):
        proj = os.path.join(base, top, "projects")
        if not os.path.isdir(proj): continue
        for root, _, files in os.walk(proj):
            for fn in files:
                if not fn.endswith(".jsonl"): continue
                f = os.path.join(root, fn); off = _SCANNED.get(f, 0)
                if os.path.getsize(f) < off: off = 0          # file shrank / was rewritten: rescan from the start
                with open(f, "rb") as fh:
                    fh.seek(off); data = fh.read()
                cut = data.rfind(b"\n") + 1; _SCANNED[f] = off + cut
                for line in data[:cut].splitlines():
                    if not any(t.encode() in line for t in INSTR_TYPES): continue
                    try: d = json.loads(line)
                    except ValueError: continue
                    leaks.update(p for p in _instr_paths(d) if not under(p, base))
    return sorted(leaks)


def assert_no_leaks(base, lid):
    leaks = instruction_leaks(base)
    if leaks:
        fail(f"{lid}: instruction file(s) from outside the lineage were loaded: {', '.join(leaks)} "
             f"-- this lineage is contaminated; delete it and rerun from a root outside home")


SKILL_ROOT_RE = re.compile(r"`r\d+` = `([^`]+)`")
AGENTS_SRC_RE = re.compile(r"AGENTS\.md instructions for (/[^\s\\\"]+)")


def codex_context_leaks(cxhome, base, marks=None):
    """Skill roots / AGENTS.md sources outside `base` in rollout lines appended since `marks` (all lines if None)."""
    leaks = set()
    for f in glob.glob(os.path.join(cxhome, "sessions", "**", "*.jsonl"), recursive=True):
        with open(f, "rb") as fh:
            fh.seek((marks or {}).get(f, 0)); data = fh.read().decode("utf-8", "replace")
        for line in data.splitlines():
            if "Skill roots" not in line and "AGENTS.md instructions for" not in line: continue
            try: d = json.loads(line)
            except ValueError: continue
            p = d.get("payload") if isinstance(d.get("payload"), dict) else {}
            if p.get("type") in ("function_call_output", "custom_tool_call_output", "exec_command_end", "item_completed"): continue
            t = json.dumps(d, ensure_ascii=False).replace("\\n", "\n")
            leaks.update(x for x in SKILL_ROOT_RE.findall(t) + AGENTS_SRC_RE.findall(t) if not under(x, base))
    return sorted(leaks)


def assert_no_codex_leaks(cxhome, base, lid, marks=None):
    leaks = codex_context_leaks(cxhome, base, marks) if cxhome else []
    if leaks:
        fail(f"{lid}: Codex loaded skill roots / AGENTS.md from outside the lineage: {', '.join(leaks)} "
             f"-- give codex a lineage-local HOME; this lineage is contaminated, delete it")


# ---- (c) auth / rate-limit detection ----
def _text_auth(text):
    return any(AUTH_RE.search(l) and re.search(r"error|unauthori|status|fail", l, re.I) for l in (text or "").splitlines())


def _auth_error(o):
    """True if a dict carries an auth / rate-limit error: an `error` value (incident shape:
    {"error":{"message":"unexpected status 401 Unauthorized: ..."},"codex_error_info":"other"}) or an error-typed event."""
    if isinstance(o, dict):
        if "error" in o and AUTH_RE.search(json.dumps(o["error"])): return True
        if o.get("type") in ("error", "stream_error", "turn.failed") and AUTH_RE.search(json.dumps(o)): return True
        return any(_auth_error(v) for v in o.values())
    if isinstance(o, list): return any(_auth_error(v) for v in o)
    return False


def _events(p):
    for l in (getattr(p, "stdout", None) or "").splitlines():
        if l.startswith("{"):
            try: yield json.loads(l)
            except ValueError: pass


def proc_auth(p):
    """Any auth / rate-limit signal in this launch (stderr error lines or --json error events)."""
    return p is not None and (_text_auth(p.stderr) or any(_auth_error(e) for e in _events(p)))


def auth_ended_turn(p):
    """A 401/429 error event ended the turn: turn.failed with auth, or an auth error after the last turn.completed."""
    last_ok = last_auth = -1
    for i, e in enumerate(_events(p)):
        if e.get("type") == "turn.completed": last_ok = i
        if _auth_error(e):
            if e.get("type") == "turn.failed": return True
            last_auth = i
    return last_auth > last_ok


def rollout_marks(cxhome):
    return {f: os.path.getsize(f) for f in glob.glob(os.path.join(cxhome, "sessions", "**", "*.jsonl"), recursive=True)}


def rollout_auth(cxhome, marks):
    """401 / rate-limit error events appended to any rollout since `marks`."""
    for f in glob.glob(os.path.join(cxhome, "sessions", "**", "*.jsonl"), recursive=True):
        with open(f, "rb") as fh:
            fh.seek(marks.get(f, 0)); data = fh.read()
        for line in data.splitlines():
            if b"error" not in line: continue
            try: d = json.loads(line)
            except ValueError: continue
            if _auth_error(d): return True
    return False


def _note_recovered(L, what):
    """Codex hit 401/429 but recovered by itself (non-empty reply, turn completed): keep the reply, never re-send."""
    L.st.setdefault("guard_recovered_auth", []).append({"step": what, "t": time.time()}); L.save()
    print(f"GUARD {L.id} {what}: auth/rate-limit seen but Codex recovered -- reply kept (guard_recovered_auth)", flush=True)


def _note_retry(L, what, why, attempt):
    L.st.setdefault("guard_retries", []).append({"step": what, "why": why, "attempt": attempt, "t": time.time()})
    L.save()
    if attempt > RETRIES:
        fail(f"{L.id} {what}: {why} after {RETRIES} retries -- step NOT recorded")
    print(f"GUARD {L.id} {what}: {why}; waiting {RETRY_WAIT}s, retry {attempt}/{RETRIES}", flush=True)
    sleep(RETRY_WAIT)


def lineage_marks(base):
    """Rollout sizes of every Codex home inside a lineage (main codexhome and any X1 home)."""
    m = {}
    for s in glob.glob(os.path.join(base, "*", "sessions")): m.update(rollout_marks(os.path.dirname(s)))
    return m


# ---- method wrappers ----
def guard_lineage_init(orig):
    def __init__(self, out, *a, **k):
        check_outside_home(out, "lineage out dir")
        orig(self, out, *a, **k)
        if self.st.get("contaminated"):
            raise GuardFail(f"GUARD FAIL {self.id} is contaminated ({self.st['contaminated'][:200]}) -- refusing to "
                            f"resume; delete {self.base}")
    __init__._guarded = True
    return __init__


def guard_run_step(orig):
    """Run.step: a guard fail-stop inside a step drops that step and marks the lineage contaminated."""
    def step(self, L, key, *a, **k):
        try: return orig(self, L, key, *a, **k)
        except GuardFail as e:
            contaminate(L, key, str(e)); raise
    step._guarded = True
    return step


def guard_claude(orig):
    """Claude Code main step: scan the lineage's transcripts for out-of-lineage instructions before the reply is
    returned (i.e. before Run.step records it)."""
    def claude(self, prompt, new_session=False):
        r = orig(self, prompt, new_session)
        assert_no_leaks(self.base, self.id)
        return r
    claude._guarded = True
    return claude


def guard_codex_claude(orig):
    """Codex main step (CodexLineage.claude drives Codex). A failed turn (empty reply, non-zero exit with an auth
    signal, or a 401/429 that ended the turn) is retried only in a FRESH session; a failed RESUMED turn is never
    re-sent into the same thread -> fail-stop, lineage contaminated. Auth seen but recovered -> reply kept, logged."""
    def claude(self, prompt, new_session=False):
        key = "sid2" if new_session else "sid"; before = self.st.get(key)
        for attempt in range(1, RETRIES + 2):
            marks = rollout_marks(self.cxhome); LAST.clear(); err = None
            try: reply = orig(self, prompt, new_session)
            except SystemExit as e: reply, err = None, e
            assert_no_codex_leaks(self.cxhome, self.base, self.id, marks)
            p = LAST.get("proc"); auth = proc_auth(p) or rollout_auth(self.cxhome, marks)
            if err is not None and not auth: raise err
            failed = err is not None or not (reply or "").strip() or auth_ended_turn(p)
            why = "auth/rate-limit" if auth else "empty reply"
            if not failed:
                if auth: _note_recovered(self, prompt[:60])
                return reply
            if before:
                fail(f"{self.id}: resumed Codex turn failed ({why}) in thread {before} -- not re-sent into the same "
                     f"thread; lineage contaminated")
            self.st[key] = None            # a failed fresh session is never resumed
            _note_retry(self, prompt[:60], why, attempt)
    claude._guarded = True
    return claude


def step_failure(rec, p, rollout_hit=False):
    if p is None: return "no guarded subprocess launched"
    empty = not str((rec or {}).get("reply") or "").strip()
    if LAST.get("tool") == "codex":
        auth = rollout_hit or proc_auth(p)
        if empty or p.returncode: return "auth/rate-limit" if auth else ("empty reply" if empty else f"rc={p.returncode}")
        return "auth/rate-limit" if auth_ended_turn(p) else None
    if empty: return "empty reply"
    if p.returncode: return f"rc={p.returncode}"
    o = p.stdout or ""; b = o.find("{")
    try: d = json.loads(o[b:]) if b >= 0 else None
    except ValueError: d = None
    if not isinstance(d, dict) or d.get("is_error"): return "claude error result"
    return None


def guard_step(orig):
    """Second-harness steps (Run.codex / CodexRun.codex: X1, X2), always fresh sessions: leak checks run before the
    reply is accepted; an empty or failed reply is dropped and retried; any guard fail-stop contaminates the lineage."""
    def codex(self, L, step):
        sid = step["id"]
        try:
            for attempt in range(1, RETRIES + 2):
                if sid in L.st["log"]: return
                marks = lineage_marks(L.base); LAST.clear()
                orig(self, L, step)
                tool, p, cx = LAST.get("tool"), LAST.get("proc"), LAST.get("codex_home")
                if tool == "claude": assert_no_leaks(L.base, L.id)
                if tool == "codex": assert_no_codex_leaks(cx, L.base, L.id, marks)
                hit = bool(tool == "codex" and cx and rollout_auth(cx, marks))
                why = step_failure(L.st["log"].get(sid), p, hit)
                if not why:
                    if tool == "codex" and (hit or proc_auth(p)): _note_recovered(L, sid)
                    return
                L.st["log"].pop(sid, None); L.save()
                kind = "auth" if "auth" in why else "empty" if "empty" in why else why
                print(f"{L.id} {sid} rejected ({kind}) — " + ("retrying" if attempt <= RETRIES else "giving up"), flush=True)
                _note_retry(L, sid, why, attempt)
        except GuardFail as e:
            contaminate(L, sid, str(e)); raise
    codex._guarded = True
    return codex


def auth_links(L):
    """{path: is_symlink} for every auth.json in a lineage's Codex homes."""
    return {f: os.path.islink(f) for f in glob.glob(os.path.join(L.base, "*", "auth.json"))}


def end_of_run_summary(lineages):
    """After a run: for any lineage that logged retries or recovered auth, report whether auth.json is still a symlink
    to the isolated login (a regular file = Codex rewrote credentials into the lineage). Asserts they all are."""
    bad = []
    for L in lineages:
        links = auth_links(L)
        if L.st.get("guard_retries") or L.st.get("guard_recovered_auth"):
            print(f"GUARD SUMMARY {L.id}: retries={len(L.st.get('guard_retries') or [])} "
                  f"recovered_auth={len(L.st.get('guard_recovered_auth') or [])} auth.json symlink="
                  + (", ".join(f"{os.path.relpath(f, L.base)}:{'yes' if v else 'NO'}" for f, v in links.items()) or "none"),
                  flush=True)
        bad += [f for f, v in links.items() if not v]
    if bad: fail(f"auth.json is no longer a symlink (credentials copied into the lineage?): {', '.join(bad)}")


def install():
    for mod in (runner, codex_runner): mod.subprocess = GuardedSubprocess()
    for cls, name, wrap in ((runner.Lineage, "__init__", guard_lineage_init), (runner.Lineage, "claude", guard_claude),
                            (codex_runner.CodexLineage, "claude", guard_codex_claude),
                            (runner.Run, "codex", guard_step), (codex_runner.CodexRun, "codex", guard_step),
                            (runner.Run, "step", guard_run_step)):
        f = cls.__dict__[name]
        if not getattr(f, "_guarded", False): setattr(cls, name, wrap(f))


install()
