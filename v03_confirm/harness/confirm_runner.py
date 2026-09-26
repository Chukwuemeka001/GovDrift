#!/usr/bin/env python3
"""Confirm run (Claude Code): the frozen Tier-2 runner behind harness_guard, a chosen frozen plugin snapshot and a
TRULY lazy owner (never confirms). Arms: native, plugin-lazy. Scenario unchanged (nclex_remediation.json incl. X1).

  python3 confirm_runner.py --plugin v02|v03 [--stop-after STEP] <scenario.json> --out /Users/Shared/govdrift-eval/DIR \
      --runs native:haiku:1,plugin-lazy:haiku:1

Deviation from Tier 2 (forced by the guard): the X1 second harness (codex exec) runs with an isolated per-lineage
CODEX_HOME (auth.json symlinked to the isolated login; model/effort = the operator defaults Tier 2 inherited, gpt-6-luna
/ low) instead of the operator's own ~/.codex (its MCP servers, plugins and AGENTS.md), and with a lineage-local
empty HOME (Codex lists $HOME/.agents/skills regardless of CODEX_HOME). Claude main steps also get that lineage-local
HOME (login = CLAUDE_CODE_OAUTH_TOKEN from the token env file). The guard refuses any launch with HOME under the real home.
"""
import contextlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import harness_guard  # noqa: E402,F401  -- must come first
import runner, codex_runner  # noqa: E402

ARMS = ("native", "plugin-lazy")
X1_CODEX = 'model = "gpt-6-luna"\nmodel_reasoning_effort = "low"\n'


def pop_opt(name, default=None):
    if name not in sys.argv: return default
    i = sys.argv.index(name); v = sys.argv[i + 1]; del sys.argv[i:i + 2]; return v


def select_plugin(which):
    """Point runner / codex_runner at the frozen snapshot, then assert everything resolves inside it."""
    if which not in ("v02", "v03"): raise SystemExit("--plugin must be v02 or v03")
    snap = os.path.join(os.path.dirname(HERE), f"plugin_{which}")
    runner.PLUGIN = snap
    sys.path.insert(0, snap)
    codex_runner.HOOK = os.path.join(snap, "hooks", "dl_hook.py")
    codex_runner.MCP = os.path.join(snap, "mcp", "server.py")
    check_snapshot(snap)
    return snap


def check_snapshot(snap):
    import driftledger
    got = {"driftledger": os.path.dirname(driftledger.__file__), "runner.PLUGIN": runner.PLUGIN,
           "codex_runner.HOOK": codex_runner.HOOK, "codex_runner.MCP": codex_runner.MCP}
    bad = {k: v for k, v in got.items() if not harness_guard.under(v, snap) or not os.path.exists(v)}
    if bad: raise SystemExit(f"FAIL plugin snapshot {snap}: not inside it / missing: {bad}")


def check_stop_after(scenario_path, stop_after):
    if stop_after and stop_after not in [s["id"] for s in json.load(open(scenario_path))["steps"]]:
        raise SystemExit(f"--stop-after {stop_after}: no such step in {scenario_path}")


def patch_run(cls, stop_after):
    init = cls.__init__
    def __init__(self, scenario_path, out, specs, kill):
        bad = [s[0] for s in specs if s[0] not in ARMS]
        if bad: raise SystemExit(f"arms {bad} not in {ARMS}")
        check_stop_after(scenario_path, stop_after)      # before any lineage dir is created
        init(self, scenario_path, out, specs, kill)
        self.sc["lazy_owner_turns"] = []                  # never confirms
        if stop_after:
            ids = [s["id"] for s in self.sc["steps"]]
            self.sc["steps"] = self.sc["steps"][: ids.index(stop_after) + 1]
        for L in self.lineages:                           # record the snapshot; never resume on a different one
            prev = L.st.get("plugin_snapshot")
            if prev and prev != runner.PLUGIN: raise SystemExit(f"FAIL {L.id} was run with {prev}, not {runner.PLUGIN}")
            L.st["plugin_snapshot"] = runner.PLUGIN; L.save()
    cls.__init__ = __init__


def patch_ledger():
    orig = runner.Lineage.ledger
    def ledger(self):
        L = orig(self)
        import driftledger
        if not os.path.realpath(driftledger.__file__).startswith(os.path.realpath(runner.PLUGIN) + os.sep):
            raise SystemExit(f"FAIL driftledger resolved to {driftledger.__file__}, not {runner.PLUGIN}")
        return L
    runner.Lineage.ledger = ledger


@contextlib.contextmanager
def env_during(**kv):
    old = {k: os.environ.get(k) for k in kv}; os.environ.update(kv)
    try: yield
    finally:
        for k, v in old.items():
            if v is None: os.environ.pop(k, None)
            else: os.environ[k] = v


def codex_home_dir(L):
    """Empty lineage-local HOME for codex launches (no ~/.agents/skills, ~/.zshrc, ~/.gitconfig of the operator)."""
    h = os.path.join(L.base, "home"); os.makedirs(h, exist_ok=True); return h


def patch_claude_home():
    """Claude main steps run with the same lineage-local HOME as Codex."""
    guarded = runner.Lineage.claude
    def claude(self, prompt, new_session=False):
        with env_during(HOME=codex_home_dir(self)): return guarded(self, prompt, new_session)
    runner.Lineage.claude = claude


def patch_x1_codex_home():
    guarded = runner.Run.codex
    def codex(self, L, step):
        home = os.path.join(L.base, "codex_x1_home")
        if not os.path.exists(home):
            os.makedirs(home); os.symlink(codex_runner.AUTH, os.path.join(home, "auth.json"))
            open(os.path.join(home, "config.toml"), "w").write(X1_CODEX)
        with env_during(CODEX_HOME=home, HOME=codex_home_dir(L)): guarded(self, L, step)
    runner.Run.codex = codex


def main(run_cls, kill_default, done_msg):
    """runner.main / codex_runner.main plus the guard's end-of-run summary (auth.json still a symlink)."""
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("scenario"); ap.add_argument("--out", required=True); ap.add_argument("--runs", required=True)
    ap.add_argument("--kill", type=float, default=kill_default)
    a = ap.parse_args()
    specs = [(x.split(":")[0], x.split(":")[1], int(x.split(":")[2])) for x in a.runs.split(",")]
    R = run_cls(a.scenario, a.out, specs, a.kill)
    try:
        for L in R.lineages: R.run_lineage(L)
    finally:
        harness_guard.end_of_run_summary(R.lineages)
    print(done_msg(R))


if __name__ == "__main__":
    select_plugin(pop_opt("--plugin") or "")
    patch_run(runner.Run, pop_opt("--stop-after")); patch_ledger(); patch_claude_home(); patch_x1_codex_home()
    main(runner.Run, 40.0, lambda R: f"DONE spend=${R.total_spend():.2f} (Claude, transcript-derived; Codex uncounted)")
