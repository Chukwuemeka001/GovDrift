# Tier 2 deviations (empty at pre-registration)
- D-plugin-edit (2026-09-25 ~09:35–09:37 local): plugin/driftledger/cli.py briefly contained an additive, unused `codex-setup` subcommand (no existing code path changed) while runs were live; reverted; plugin tree SHA-256 re-verified = 72f7feee…8ce0. Product work moved to a separate release folder.
- D-pause (2026-09-25): all Tier-2 processes stopped at the owner's plan session limit (fail-stop, no step recorded for the failed call) and were resumed with identical frozen code.
- D-crash (2026-09-25): Claude Code crashed (Bun segfault, rc=-11) mid-step in native-haiku-s4; fail-stop; resumed with identical code.
- D-metric (2026-09-25): the secondary machine metric 'memory claims review done' (score.py DONE_CLAIM regex) produces false positives on conditional phrasing; withdrawn for all tiers; to be replaced by a blinded judgment of memory snapshots (reported separately, labeled post-hoc).
