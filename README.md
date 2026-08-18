# GovDrift

A pre-registered benchmark asking one question: **when an agent's context is compacted,
does a small governance packet — an epistemic banner + a ledger of owner decisions
(reason, status, provenance) — preserve the session's governing state (mission, rules
and boundaries, what's owed vs. already done) that compaction summaries lose?**

This repository IS the pre-registration. The first commit freezes the protocol, the
verbatim worker turn scripts and probes, the scoring rubric and scorer code, the
placebo/scrambled control constructions, the analysis plan, and the falsification
criteria — before any experimental run. Results will reference this commit hash.
Deviations are logged in `DEVIATIONS.md`. **Results publish either way**, including a
null: the falsification criteria are in `GOVDRIFT_PREREG.md` §8.

- `GOVDRIFT_PREREG.md` — the pre-registration: question, design (3 projects × 4 arms ×
  5 seeds × 2 compaction generations, real Claude Code compactor), cells, predictions,
  analysis plan, falsification criteria, claim boundaries.
- `TURN_SCRIPT_P{1,2,3}_*.md` — frozen verbatim worker scripts, probes, and
  controller-ledger templates for the three worker projects.
- `BANNER_V2_TEMPLATE.md` — the treatment banner (v2 semantics).
- `SCRAMBLE_TABLES.md` — frozen wrong-content ledgers for the scrambled control arm.
- `runner1.sh` — headless session driver (run / compact / fork / archive), used for all
  arms identically.
- `score_arm.py` + `scorer_config_*.json` — machine scorer for the script-checkable
  outcome cells; the remaining cells are blind-audited from anonymized transcripts.

Prior evidence that motivated this benchmark (single-pair pilot and a real-compactor
demonstration run) will be linked from the results write-up. License: MIT.
