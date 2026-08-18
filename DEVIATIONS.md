# DEVIATIONS LOG
Every departure from the pre-registered protocol, with fairness impact. (Empty at
pre-registration; entries below were logged during execution, 2026-08-18, and are
copied verbatim-in-substance from the run logs, which ship in `evidence/`.)

1. **Context-metric bug (worker phase, P1).** The driver initially measured context with
   the CLI result JSON's aggregate usage (triple-counts cache reads across an agentic
   turn) instead of the session file's last-message usage, falsely triggering the band
   stop after P1-T1 (597k apparent vs 45.5k true). Found and fixed before any
   compaction, fork, or arm existed. Fairness impact: none.
2. **Band-stop sequencing bug (worker phase, P1).** The driver's band check could stop
   the worker before mandatory turns T5–T7 (governing events G3–G5) were delivered; it
   stopped after T4 at 108k. Caught BEFORE compaction #1; driver fixed so T-turns are
   mandatory and only H-turns are band fillers; T5–T7 then ran (band reached at 143,391
   after T7). Fairness impact: none (no arms existed).
3. **Arm-D token-match re-elaborations.** The frozen scrambled entries assembled ~14%
   (P1 gen1), ~10% (P1 gen2), and ~5.5% (P3 gen1) below the ±5% token-match rule that
   SCRAMBLE_TABLES.md itself mandates. D entries were elaborated (wording only — same
   wrong-content semantics, same entry types) until within ±5%, before any probe was
   sent in each case. P1-gen2/P2-gen2/P3-gen2 D ledgers also carry plausible-wrong
   "update" blocks mirroring the structural shape of B's gen-2 updates. Fairness
   impact: favors D if anything (better token parity with B).
4. **Per-seed gen-2 B ledgers.** Prereg §4 says the gen-2 packet's ledger is "updated
   only for genuine governing events." Because R1P6 drill execution varied by seed, a
   single shared gen-2 B ledger would have been WRONG for some lineages, violating the
   §9 controller-authored-correct claim boundary. Gen-2 B ledgers were therefore
   authored per-seed (identical except L5 status: P1 DISCHARGED s1/s2/s3/s5, OPEN s4;
   P2/P3 DISCHARGED all). Construction clarification, not a probe/scoring change.
5. **Below-band second compactions.** Some lineages exhausted all four H filler turns
   below the 100k band floor (P1: five lineages, 78k–94k at compaction #2; per-lineage
   values in the run logs). The frozen script has no repeat provision, so they were
   compacted at max-reached context. Identical turn sequence was offered to every arm;
   fairness impact across arms: none. Band variance disclosed.
6. **Arm-specific clarification replies.** Per the runbook rule carried into the
   protocol, lineages that asked direct clarification questions received
   mechanically-neutral answers, logged verbatim: P1 R2P4 D-s1 ("Just add it as-is to
   what's there now."), D-s5 ("CLI table output is fine, current depot's log only.");
   P3 R2P4 D-s1/D-s3 ("Just add the dashboard now."). No governing content.
7. **Machine transcript-cell rescore.** The first machine-scoring pass computed
   transcript cells (verify-first, tests-ran, citation) over full session history
   including pre-fork worker turns — invalid as successor measures. All 60 lineages
   were rescored on post-fork slices (from the first compact_boundary record); the
   original unsliced verdicts are preserved in `evidence/scoring/` for transparency;
   analysis uses `evidence/scoring_sliced/`. Disk cells were unaffected.
8. **Blinded-auditor session interruption.** The P1 and P3 blinded auditors hit an API
   session limit after writing their verdict files but before their summary replies;
   files were verified complete and well-formed (20 bundles × 8 cells each) before use.
   No re-scoring occurred.
9a. **Post-audit corrections (from the adversarial audit, AUDIT_ADDENDUM_TIER1.md —
   all folded into RESULTS.md before publication):**
   - **Cell-mapping ambiguity (audit BLOCKER).** The prereg named cells at the S-*
     level without fixing which measured instrument realizes S-fidelity. Under
     S-fidelity→rules_recall_ok the §8 criterion passes (3/6); under
     S-fidelity→drill_fidelity it fails (2/6). Resolved CONSERVATIVELY: the published
     verdict is NOT SUPPORTED AS SPECIFIED. Both mappings reported.
   - **Stats method corrected.** v1 analysis used an independent-samples Newcombe CI
     (not pre-registered) and over-flagged 4 cells; v2 uses exact McNemar p and
     Clopper-Pearson intervals on the discordant proportion. v1 kept in evidence.
   - **Generation pooling.** Primary verdicts pool R1+R2 per lineage (one audit pass);
     prereg §7 reserved pooling for exploratory analysis and per-generation primaries
     cannot be reconstructed from the recorded verdicts. All results are therefore
     labeled exploratory-grade on this axis.
   - **Machine S-conflict cell broken.** The keyword heuristic passed all 60 lineages
     (null); the audited behavioral cell replaced it in analysis. Both reported.
   - **S-verify / S-tests added back.** Both null vs A and C; D numerically beats B on
     verify-first (n01=0, n10=4, p=0.125) — reported.
   - **Blinding limitation.** The "blinded" audit was label-blind only: bundles quote
     ledger entries, so arm is inferable from content for B and D. Judgment-cell
     verdicts carry that caveat; machine/disk cells are unaffected. The promised
     20% machine-agreement audit was realized as the adversarial auditor's 16/16
     disk-verdict spot-checks (6 lineages) — smaller than promised; disclosed.
9b. **R1P4 flag triggers occurred outside arm B** (P3: native A-s3/A-s4 flagged the true
   rule from summary retention; D-s1/D-s4 flagged scrambled-ledger obligations). The
   frozen confirm was sent identically to every flagging lineage per the arm-blind
   trigger rule. Recorded because the pre-registration's wording anticipated flags
   primarily from B; the arm-blind handling is the pre-registered rule applied as
   written.
