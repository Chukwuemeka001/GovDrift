#!/usr/bin/env python3
"""Scenario 2 ("Maple Row") run, Claude Code (Haiku): the frozen Tier-2 runner behind harness_guard + s2_core
machinery (seed at root + handover commit, safe agent env, per-band lists, per-step snapshots, transcript windows).

  python3 s2_runner.py --plugin v02|v03 [--stop-after STEP] [--swap P3,P5] [--dry-run] <scenario.json> \
      --out /Users/Shared/govdrift-eval/DIR --runs native:haiku:1,plugin-lazy:haiku:1[,plugin-careful:haiku:1] [--kill 40]

Arms: native, plugin-lazy (owner never confirms: lazy_owner_turns = []), plugin-careful (careful_owner confirms).
Claude main steps and the X1 second harness (codex exec -s read-only, lineage-local CODEX_HOME) run with a
lineage-local empty HOME (as confirm_runner).
--dry-run: no model calls and no credential reads (fake claude/codex behind the guard); walks every step, writes
snapshots / windows, and prints a per-step summary.
"""
import argparse, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import harness_guard  # noqa: E402,F401  -- must come first
import s2_core  # noqa: E402
import runner  # noqa: E402
from confirm_runner import pop_opt, patch_ledger, patch_claude_home, patch_x1_codex_home  # noqa: E402


def parse(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("scenario"); ap.add_argument("--out", required=True); ap.add_argument("--runs", required=True)
    ap.add_argument("--kill", type=float, default=40.0)
    a = ap.parse_args(argv)
    a.specs = [(x.split(":")[0], x.split(":")[1], int(x.split(":")[2])) for x in a.runs.split(",")]
    return a


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    sys.argv = [sys.argv[0]] + argv
    plugin, stop, swap, dry = pop_opt("--plugin") or "", pop_opt("--stop-after"), pop_opt("--swap"), "--dry-run" in sys.argv
    if dry: sys.argv.remove("--dry-run")
    s2_core.select_plugin(plugin)
    s2_core.patch_arms(runner.Run, stop, swap=swap); patch_ledger(); patch_claude_home(); patch_x1_codex_home(); s2_core.install()
    a = parse(sys.argv[1:])
    if dry: s2_core.install_dry_run(os.path.abspath(a.out))
    R = runner.Run(a.scenario, a.out, a.specs, a.kill)
    try:
        for L in R.lineages: R.run_lineage(L)
    finally:
        harness_guard.end_of_run_summary(R.lineages)
    if dry:
        print(s2_core.summarize(R)); print("DRY RUN DONE (no model calls)")
    else:
        print(f"DONE spend=${R.total_spend():.2f} (Claude, transcript-derived; Codex X1 uncounted)")
    return R


if __name__ == "__main__":
    main()
