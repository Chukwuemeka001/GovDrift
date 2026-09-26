#!/usr/bin/env python3
"""Scenario 2 ("Maple Row") run, Codex (GPT-6-Sol): the frozen Tier-2b runner behind harness_guard + s2_core
machinery; every codex exec / resume (incl. forced-compaction turns) gets -c model_reasoning_effort=<GOVDRIFT_SOL_EFFORT,
default low>; codex runs with a lineage-local empty HOME (as confirm_codex_runner).

  python3 s2_codex_runner.py --plugin v02|v03 [--stop-after STEP] [--swap P3,P5] [--dry-run] <scenario.json> \
      --out /Users/Shared/govdrift-eval/DIR --runs native:sol6:1,plugin-lazy:sol6:1[,plugin-careful:sol6:1]

X1 second harness = Claude Code Haiku --permission-mode plan (codex_runner.CodexRun.codex, unchanged).
"""
import argparse, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import harness_guard  # noqa: E402,F401  -- must come first
import s2_core  # noqa: E402
import codex_runner  # noqa: E402
from confirm_runner import pop_opt, patch_ledger  # noqa: E402
import confirm_codex_runner  # noqa: E402


def patch_codex_extras():
    if not getattr(codex_runner.CodexLineage._overrides, "_s2", False):
        confirm_codex_runner.patch_effort(); codex_runner.CodexLineage._overrides._s2 = True
    if not getattr(codex_runner.CodexLineage.claude, "_s2home", False):
        confirm_codex_runner.patch_home(); codex_runner.CodexLineage.claude._s2home = True


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    sys.argv = [sys.argv[0]] + argv
    plugin, stop, swap, dry = pop_opt("--plugin") or "", pop_opt("--stop-after"), pop_opt("--swap"), "--dry-run" in sys.argv
    if dry: sys.argv.remove("--dry-run")
    s2_core.select_plugin(plugin)
    s2_core.patch_arms(codex_runner.CodexRun, stop, swap=swap); patch_ledger(); s2_core.install(); patch_codex_extras()
    ap = argparse.ArgumentParser()
    ap.add_argument("scenario"); ap.add_argument("--out", required=True); ap.add_argument("--runs", required=True)
    a = ap.parse_args(sys.argv[1:])
    specs = [(x.split(":")[0], x.split(":")[1], int(x.split(":")[2])) for x in a.runs.split(",")]
    if dry: s2_core.install_dry_run(os.path.abspath(a.out))
    R = codex_runner.CodexRun(a.scenario, a.out, specs, kill=float("inf"))
    try:
        for L in R.lineages: R.run_lineage(L)
    finally:
        harness_guard.end_of_run_summary(R.lineages)
    if dry:
        print(s2_core.summarize(R)); print("DRY RUN DONE (no model calls)")
    else:
        print("DONE (Codex usage is ChatGPT-plan, reported as tokens)")
    return R


if __name__ == "__main__":
    main()
