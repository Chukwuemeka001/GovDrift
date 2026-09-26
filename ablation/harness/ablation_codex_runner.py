#!/usr/bin/env python3
"""M2 ablation runner (S5) — Codex / GPT-6-Sol. Wraps codex_runner.py + ablation_runner.py without modifying them.

  python3 ablation_codex_runner.py <scenario.json> --out <dir> --runs abl-verbatim:sol6:1,abl-none:sol6:1 [--dry]

Same arms, seeding, fail-stops and X1 skip as ablation_runner.py. Codex wiring = codex_runner's per-run `-c` hook/MCP
overrides, but pointing at plugin_ablation, with every DRIFTLEDGER_* switch both prefixed on each hook command (as
codex_runner does for DRIFTLEDGER_HOME) and set in the codex process env.
Injection check reads the lineage's Codex rollout files (CODEX_HOME/sessions).
"""
import glob, os, shlex, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ablation_runner as ar  # noqa: E402  (puts plugin_ablation first on sys.path)
import codex_runner  # noqa: E402

HOOK = os.path.join(ar.ABL, "hooks", "dl_hook.py")


class AblCodexLineage(ar.AblMixin, codex_runner.CodexLineage):
    def __init__(self, out, arm, model, seed, scenario):
        super().__init__(out, arm, model, seed, scenario); self.abl_init()

    def _overrides(self, compact_now=False):
        args = super()._overrides(compact_now)          # abl-* arm: PostCompact logger (+ compact limit) only
        q = lambda s: s.replace('"', '\\"')
        mk = lambda ev, cmd: ["-c", f'hooks.{ev}=[{{hooks=[{{type="command",command="{q(cmd)}"}}]}}]']
        env = " ".join(f"{k}={shlex.quote(v)}" for k, v in self.abl_env().items())
        for ev in ("SessionStart", "UserPromptSubmit", "Stop", "PreToolUse", "SubagentStart"):
            args += mk(ev, f"{env} python3 {shlex.quote(HOOK)} {ev}")
        return args

    def claude(self, prompt, new_session=False):       # codex_runner builds env from os.environ: patch it for the call
        old = {k: os.environ.get(k) for k in self.abl_env()}
        os.environ.update(self.abl_env())
        try:
            return super().claude(prompt, new_session)
        finally:
            for k, v in old.items():
                if v is None: os.environ.pop(k, None)
                else: os.environ[k] = v

    def command(self, prompt, new_session=False):
        """Capture the exact argv/env codex_runner would use, without running anything."""
        seen = {}
        real = subprocess.run
        def fake(cmd, **kw):
            seen["cmd"], seen["env"] = cmd, kw.get("env") or {}
            raise _Captured()
        codex_runner.subprocess.run = fake
        try: self.claude(prompt, new_session)
        except _Captured: pass
        finally: codex_runner.subprocess.run = real
        extra = {k: seen["env"][k] for k in ("CODEX_HOME", *self.abl_env()) if k in seen["env"]}
        return seen["cmd"], extra

    def transcript_files(self):
        return sorted(glob.glob(os.path.join(self.cxhome, "sessions", "**", "*.jsonl"), recursive=True))

    def snapshot(self, label):
        # D4: on resume a label may already exist; Codex memory .git objects are read-only, so re-copying fails.
        import shutil
        dst = os.path.join(self.base, "snapshots", label); os.makedirs(dst, exist_ok=True)
        mem = os.path.join(self.cxhome, "memories")
        if os.path.isdir(mem) and not os.path.exists(os.path.join(dst, "memory")):
            shutil.copytree(mem, os.path.join(dst, "memory"), ignore=shutil.ignore_patterns(".git"))
        agents = os.path.join(self.ws, "AGENTS.md")
        if os.path.exists(agents): shutil.copy(agents, os.path.join(dst, "workspace_AGENTS.md"))
        L = self.ledger()
        if L.store.exists():
            import shutil; shutil.copy(L.store.path, os.path.join(self.base, "snapshots", label, "ledger_events.jsonl"))


class _Captured(Exception):
    pass


class AblCodexRun(ar.AblRunMixin, codex_runner.CodexRun):
    def __init__(self, scenario_path, out, specs, kill):
        import json
        self.sc = json.load(open(scenario_path)); self.sc["_path"] = os.path.abspath(scenario_path)
        self.out, self.kill = os.path.abspath(out), kill
        self.lineages = [AblCodexLineage(self.out, *s, self.sc) for s in specs]

    def no_mcp(self, L):
        cmd, _ = L.command("x")
        cfg = open(os.path.join(L.cxhome, "config.toml")).read()
        assert not any("mcp_servers" in c for c in cmd) and "mcp_servers" not in cfg, "Codex has an MCP server configured"
        return "Codex: no mcp_servers in -c overrides or CODEX_HOME/config.toml"

    def would_run(self, L, prompt):
        cmd, extra = L.command(prompt)
        return f"cwd={L.ws} env+={{{', '.join(f'{k}={v}' for k, v in extra.items())}}}\n  " + " ".join(shlex.quote(c) for c in cmd)


def main():
    a, specs = ar.parse(); ar.check_driftledger()
    R = AblCodexRun(a.scenario, a.out, specs, float("inf") if a.kill == 40.0 else a.kill)
    if a.dry: return R.dry()
    for L in R.lineages: R.run_lineage(L)
    print("DONE (Codex usage is ChatGPT-plan, reported as tokens)")


if __name__ == "__main__":
    main()
