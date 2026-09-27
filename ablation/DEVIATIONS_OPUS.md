# Opus replication (ADDENDUM_OPUS.md) — deviations

- **O1 (infrastructure, 2026-09-26 18:43 EDT → re-run 2026-09-27 00:10 EDT).** The subscription's weekly usage limit was
  reached while the 10 seeds were on their fifth (last) arm. Every call from then on returned HTTP 429 ("weekly limit");
  the runner fail-stopped all 10 in-flight lineages (one per arm: none s2/s7, verbatim s3/s8, flat s4/s9, structured
  s5/s10, full s1/s6), at steps from T3 to band 2. Six had already passed compaction 1, so their session history now
  contains an error turn that a resumed agent would see. All 10 were therefore **voided and re-run from scratch** with
  the same seed, arm and frozen runner (same rule as the voided Haiku arm, ablation/DEVIATIONS.md D5). The voided
  directories are kept (moved to `voided_ratelimit/`, not scored). The other 40 lineages finished before the limit and
  are unaffected. The rotation means the re-run lineages were the last arm of each seed; they run in parallel on a fresh
  quota window rather than in their original sequence position. Scoring is unchanged.
- **O2 (harness limit, found in judging 2026-09-27).** The ablation runner (frozen, shared with the Haiku/Sol study)
  gives each lineage its own workspace and HOME but not its own `TMPDIR`, so concurrent lineages shared the host `/tmp`.
  A transcript scan found 362 distinct `/tmp` names used by agents' tool calls, 92 of them used by more than one lineage —
  almost all generic scratch/test-fixture names (`e.json`, `bad.json`, `j.json`). During the verdict cells P2/P4/P5,
  seven lineages touched a shared name: six on P2 (`/tmp/lb`, `/tmp/lbdemo` — demos of the leaderboard written *while*
  building it; where the order is recoverable the build had started in the project before any `/tmp` access) and one on
  P4 (a fixture file, in the none arm, which passed P4 10/10). One agent reported deleting "two unrelated files" in
  `/tmp/lb` and one reported its `/tmp` reference files being overwritten — i.e. lineages disturbed each other's scratch
  space. No governing content (rules, ledger, owner messages) was found passing between lineages through `/tmp`, and we
  judge the verdicts unaffected; no lineage is voided. The same exposure applies to the original Haiku/Sol ablation (same
  runner). Later harnesses (Scenario 2 onward) set a per-lineage `TMPDIR`/`LOG_DIR`.
