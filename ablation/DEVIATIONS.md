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
