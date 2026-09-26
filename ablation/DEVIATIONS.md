# Deviations — M2 ablation

- D1 (disk full, 2026-09-25 ~15:35 EDT): the host disk filled; all runs were paused (SIGSTOP) and resumed after space
  was freed. One lineage (abl-flat-haiku-s3) had its first /compact run during the outage: no compaction happened
  (no summary written, context unchanged) and the runner's injection check fail-stopped it. Its compact1 step was reset
  and the lineage resumed from the same session. All other lineages were checked: every recorded compaction has a
  matching summary/compacted event. The Sol pilot lineage that crashed in the outage is excluded (pilot).
- D2 (blinding method): arm-identifying text is replaced by neutral wording ("the owner's rules", "rule", lower-cased
  status words) rather than a visible [X] marker, which would itself identify ledger arms.
- D3 (Codex auth, 2026-09-25 ~18:40 EDT): the isolated Codex login returned 401 for a few minutes (likely a token-refresh
  race across ~20 concurrent Codex processes sharing one login); 4 Sol lineages fail-stopped mid-band
  (abl-full-s1, abl-status-s10, abl-verbatim-s3, abl-flat-s4) and 6 groups were paused. The 401 occurred before any model
  output; on resume the interrupted work turn was re-sent (the owner prompt may appear twice in those threads).
  Groups were relaunched staggered to reduce refresh collisions.
- D4 (harness, 2026-09-25 ~20:20 EDT): resuming fail-stopped Sol lineages crashed in the snapshot helper (re-copying
  Codex memory's read-only .git objects into an existing snapshot). The Codex ablation runner's snapshot now skips an
  existing memory snapshot and ignores .git (same fix as the Tier 2b extension). Snapshots are audit artifacts only; no
  agent-facing behavior changed. Updated harness copy committed alongside.
- D5 (Haiku arm VOIDED and re-run, found 2026-09-25 ~20:45 EDT): the Haiku runners were launched from a Python script
  fed on stdin; child `claude -p` processes inherited that stdin and appended the launcher text (which names the arms and
  the ablation runner) to EVERY owner prompt in 46/50 Haiku lineages (4 relaunched lineages were clean). Found during
  blinding checks when an agent remarked on "an ablation-runner test harness" in a reply. All 50 Haiku lineages
  (and their judged interim results) are void and preserved under results/ablation_void_haiku_stdin/ for audit; the
  Haiku arm is re-run from scratch with stdin=/dev/null (launch_haiku_ablation.py). Sol lineages are unaffected (Codex
  is invoked with stdin closed; checked: no launcher text in any Sol user message). Other studies checked: Tier 2/2b/2c,
  Tier 2-fix, the pilot and the Opus v0.3 check contain no launcher text.
