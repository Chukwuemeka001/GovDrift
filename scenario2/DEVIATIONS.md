# Deviations — Scenario 2 main study

- D1 (process kills, 2026-09-26 morning): agents ran host-wide process kills while restarting their dev servers
  (`killall -9 python3`, `ps aux | grep python3 | xargs kill -9`, `pkill -9 -f …`). These matched the eval runner
  processes of concurrently running lineages and killed several Haiku native/v0.2 runners mid-step (signal 9); they could
  also kill sibling lineages' dev servers. Runners are relaunched under a non-matching process name (argv0 "gdrun") and
  resume from saved state (an interrupted step is re-issued). Sibling server kills cannot be fully prevented with a shared
  process table; affected steps are identifiable from transcripts and are reported.
- D2 (launcher bug): the first Sol launch passed an unsupported `--kill` flag, so no Sol lineage started; relaunched.
- D3 (exclusion rule, scoring): the automatic cross-read detector flagged 12 lineages, but none had read another
  lineage's files: the flags came from agents writing to stray sibling folders they created themselves (e.g.
  `<lineage>-proj/…`, a known small-model memory-path habit), typo paths that do not exist (`…/lineases/…`), and attempts
  to list the (non-listable) `lineages/` directory. Applying the registered rule as written — a read inside a *different,
  existing* lineage — excludes none; all 60 lineages are analysed. Both counts are in results/.
- D4 (supervisor): the launchd job used `exec` and so restarted itself after finishing; restarts only resumed finished
  lineages (no-ops) and were stopped by removing the job.
