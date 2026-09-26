# Deviations — v0.3 confirmation

- D1 (process kill, 2026-09-26 ~05:32 EDT): all runner processes were terminated together when the operator's tool
  session enforced a command timeout on the process tree that had launched them. Runs were resumed from saved state
  under launchd (independent of the tool session); an interrupted step was re-issued on resume.
- D2 (replacement rule applied): two Sol lineages failed mid-run when a Codex turn ended with no reply and exit code 0
  (plugin-lazy v0.2 seed 3 after compaction 2; plugin-lazy v0.3 seed 4 at P5). Per the pre-registered rule they are
  excluded (kept for audit) and replaced by seed 13 in the same arm. Five lineages in the halted groups had not started
  and were run as planned.
- D3 (replacement rule applied): Sol plugin-lazy v0.2 seed 12 was killed by signal 9 mid-run (cause not determined;
  these runs predate per-lineage ports, and agents were seen running `kill -9` on port holders). Excluded (kept for
  audit) and replaced by seed 14.
