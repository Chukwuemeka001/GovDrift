#!/usr/bin/env python3
"""Confirm run (Codex / GPT-6-Sol): the frozen Tier-2b runner behind harness_guard, a chosen frozen plugin snapshot
(hook + MCP overrides point at it) and a TRULY lazy owner (never confirms). Arms: native, plugin-lazy. Scenario
unchanged (nclex_remediation.json incl. X1 = Claude Code Haiku second harness).

  python3 confirm_codex_runner.py --plugin v02|v03 [--stop-after STEP] <scenario.json> \
      --out /Users/Shared/govdrift-eval/DIR --runs native:sol6:1,plugin-lazy:sol6:1

Owner instruction: every codex exec / resume (incl. forced-compaction turns, not the Claude X1 step) runs with
-c model_reasoning_effort="<GOVDRIFT_SOL_EFFORT, default low>".
Deviation from Tier 2b (forced by the guard): codex runs with a lineage-local empty HOME -- Codex lists
$HOME/.agents/skills (the operator's 61 skills) regardless of CODEX_HOME. The Claude X1 step gets the same HOME
(login = CLAUDE_CODE_OAUTH_TOKEN). A failed RESUMED Codex turn is never re-sent: that lineage fail-stops, contaminated.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import harness_guard  # noqa: E402,F401  -- must come first
import runner, codex_runner  # noqa: E402
from confirm_runner import pop_opt, select_plugin, patch_run, patch_ledger, env_during, codex_home_dir, main  # noqa: E402

EFFORT = os.environ.get("GOVDRIFT_SOL_EFFORT", "low")


def patch_effort():
    orig = codex_runner.CodexLineage._overrides
    def _overrides(self, compact_now=False):
        return orig(self, compact_now) + ["-c", f'model_reasoning_effort="{EFFORT}"']
    codex_runner.CodexLineage._overrides = _overrides


def patch_home():
    guarded = codex_runner.CodexLineage.claude
    def claude(self, prompt, new_session=False):
        with env_during(HOME=codex_home_dir(self)): return guarded(self, prompt, new_session)
    codex_runner.CodexLineage.claude = claude
    guarded_x1 = codex_runner.CodexRun.codex
    def codex(self, L, step):
        with env_during(HOME=codex_home_dir(L)): return guarded_x1(self, L, step)
    codex_runner.CodexRun.codex = codex


if __name__ == "__main__":
    select_plugin(pop_opt("--plugin") or "")
    patch_run(codex_runner.CodexRun, pop_opt("--stop-after")); patch_ledger(); patch_effort(); patch_home()
    main(codex_runner.CodexRun, float("inf"), lambda R: "DONE (Codex usage is ChatGPT-plan, reported as tokens)")
