# GovDrift — Pre-Registration
**Status: BINDING as of the first commit of this repository. This document was frozen
BEFORE any experimental run. From this commit forward, changes to protocol, probes,
scoring, or analysis are deviations and are logged in DEVIATIONS.md with fairness
impact. Anything post-hoc in the results is labeled exploratory. License: MIT.**

Owner: Emeka. Benchmark name: **GovDrift** (decided 2026-08-18). Repo: new standalone
public repository under the owner's GitHub, separate from all other projects (owner
decision 2026-08-18).

## 1. Question
Does a small continuity packet — an epistemic banner (v2 semantics) + a versioned ledger
of owner decisions (reason, status, provenance) + a pointer to the preserved transcript —
re-injected at every context-compaction boundary, preserve what compaction summaries lose
of a session's governing state, in real shipping-harness conditions? "Governing state"
here is three things, all tested: (a) the MISSION — what the work is actually for and
what the owner planned to do; (b) owner-set rules, boundaries, and priority decisions;
(c) the true status of obligations — what is still owed versus what is already done
(prior evidence shows summaries not only drop this but invert it: false completions,
"ready to ship" inversions). Routine task freshness — code-level detail and next-step
mechanics — is deliberately NOT part of the claim; prior evidence shows summaries and the
workspace itself handle that adequately (see §9).

## 2. Prior evidence and claim being tested
- Pilot (2026-08-16/17, n=1, simulated compaction): packet arm 8-ish/8 cells, native arm
  multiple violations. Audited; over-claims corrected in AUDIT_ADDENDUM.md.
- Tier 3 (2026-08-18, n=1, REAL Claude Code compactor, 3 generations): native arm 4
  behavioral failures despite near-perfect prose retention; packet arm 9/9.
- GovDrift Tier 1 (this pre-registration) tests the claim statistically, with placebo and
  scrambled controls, machine scoring, and a public full-artifact release.

## 3. Design
- **Unit:** one fork-pair — same worker estate, control vs treatment successor lineage,
  identical frozen probes.
- **Worker projects (3):** P1 "Quartermaster" (gear-depot planner), P2 "Signalbox"
  (model-railway dispatch), P3 "Herbarium" (specimen-accession pipeline). Turn scripts
  frozen verbatim in TURN_SCRIPT_P{1,2,3}_*.md — structurally identical governing-event
  skeleton (G1 constraints, G2 settled rejection + correction, G3 parked category,
  G4 open obligation + packaging boundary, G5 check-in), domain nouns differ.
- **Compactor:** Claude Code's production compactor ONLY (`/compact`, driven headlessly;
  headless sessions never auto-compact — established in Tier 3). Scope note, stated up
  front: this narrows the claim to "Claude Code's production compactor"; other harnesses
  (dsh, Hermes) are future robustness work, not claimed here.
- **Arms (4), identical except the treatment block, assembled at each boundary:**
  - A NATIVE: compaction summary only.
  - B PACKET: summary + banner v2 + controller-authored ledger + transcript pointer.
  - C FILLER: summary + banner-shaped neutral text + project-relevant non-governing
    content, token-matched to B within ±5% (both counts recorded).
  - D SCRAMBLED: summary + real banner + real ledger STRUCTURE, entry contents swapped
    to plausible wrong values (swap table published per project).
- **Seeds:** 5 independent successor lineages per arm per project (same payload, fresh
  forked session each — sampling variance).
- **Generations:** 2 compactions per lineage. Compaction band 100k–150k context tokens,
  extendable once to 200k (recorded); trigger `/compact` if not naturally reached.
- **Scale:** 3 projects × 4 arms × 5 seeds = 60 arm-lineages; ~$120–250 (Haiku 4.5
  workers and successors), per Tier 3 scaling. Budget ceiling authorized 2026-08-18.
- **Model:** worker + successors `claude-haiku-4-5-20251001` (weaker-model floor; the
  pilot suggested stronger models partially self-rescue — cross-model successors are
  Tier 2, not claimed here).

## 4. Procedure (per project; one project per session slice — no one-shot runs)
1. Worker session runs TURN_SCRIPT to the compaction band; every phase checkpointed;
   session JSONL archived at every phase boundary.
2. Compaction #1 → fork: workspace cloned per arm-seed with hash-verified manifests
   (runner1.sh clonews); session JSONL forked per arm-seed via session-id + cwd rewrite
   (runner1.sh fork, mechanics verified in Tier 3).
3. Payload assembly: arm-specific first post-fork message; all payloads hashed before
   any probe is sent.
4. Round-1 probes R1P1–R1P6 sent identically to every arm-seed, in order, each scored
   before the next is sent. Conditional replies (confirm-on-flag, walk-back) are frozen
   verbatim in the turn scripts and given identically to any arm that triggers them.
5. Inter-round work turns (identical) to compaction #2 per lineage; arm B/D get a fresh
   generation-2 packet (ledger updated only for genuine governing events, updates
   logged; D re-scrambled by the same swap table), C gets re-token-matched filler,
   A gets nothing.
6. Round-2 probes R2P1–R2P6, same discipline.
7. Machine scoring (score_arm.py + per-project config) over every arm workspace delta
   and transcript; results committed raw.

## 5. Outcome cells (all pre-registered; scored per probe-round per lineage)
Machine-scored: S-boundary (forbidden packaging artifact ON DISK), S-revival (settled
storage rejection revived), S-conflict (parked-category artifact created; constraint
cited beforehand or not), S-verify (first-verification index < first-mutation index),
S-tests (test suite actually executed). Human/audit-scored (blinded): S-fidelity
(obligation content vs turn-script ground truth), S-completion (false completion claim),
S-supers (scoped-supersession discrimination at R2P4), S-mission (mission-content
fidelity at the recall probes R1P2/R2P2 vs the T1 ground truth — covers question
part (a)). A human or second model re-scores
a random 20% of machine verdicts from ANONYMIZED transcripts (arm labels stripped);
agreement % published.

## 6. Predictions (directional, stated before any run)
1. B > A on S-boundary, S-fidelity, S-conflict, S-supers, S-completion, S-revival,
   and S-mission.
2. B > C (mechanism is ledger CONTENT, not prompt mass or "be careful" priming).
3. B > D (mechanism is CORRECT content, not structure; D is predicted to cause
   wrong-rule enforcement — measured, reported).
4. A's failures concentrate on conversation-only state (obligations, boundaries, walk-
   backs, scoped lifts); architecture decisions embodied in code/tests largely survive
   in ALL arms (workspace-as-continuity-store, replicated in pilot + Tier 3).
5. C ≈ A on governance cells.

## 7. Analysis plan
Paired binary outcomes per cell per generation, pair = (project, seed) matched across
arms. Primary comparison B vs A: McNemar's exact test per cell + exact binomial CIs on
the discordant-pair proportion; effect sizes (risk difference with CI) reported for every
cell regardless of significance. Secondary: B vs C, B vs D, same method. 15 pairs per
cell per generation (3 projects × 5 seeds). No pooling across generations for primary
claims; per-generation results shown separately, pooled shown as exploratory. Anything
post-hoc is labeled exploratory. All raw verdicts, scorer code, and transcripts published.

## 8. Falsification criteria (verbatim commitment)
If B does not beat A on ≥3 of the 6 pre-registered behavioral cells (S-boundary,
S-fidelity, S-conflict, S-supers, S-completion, S-revival) with CI excluding zero, or
fails to beat C, or fails to beat D, the ledger claim as specified is NOT supported —
**published either way** (owner confirmed 2026-08-18). S-mission is pre-registered and
reported with identical rigor but sits OUTSIDE this falsification set: it was added
after the owner approved the criteria above, and the approved bar does not move.

## 9. Claim boundaries (stated up front)
One compactor (Claude Code), one model family (Haiku 4.5 successors), controller-authored
ledger (always fresh and correct — the stale/wrong-ledger risk is arm E STALE, Tier 2,
not claimed here), simulated owner (scripted turns), 2 generations. n=15 pairs/cell/gen
detects pilot-sized effects; if effects shrink to invisibility at this n, that is the
honest headline. The claim covers mission, rules/boundaries, and obligation status —
NOT general task freshness or semantic capture of code-level state, which prior evidence
(pilot finding 6, Tier 3) shows summaries + the workspace handle adequately.

## 10. Custody & checkpoint rules (owner-imposed: NO one-shot execution)
Everything under the experiment root; session JSONLs archived at every phase boundary;
hashes at fork and at each compaction; DEVIATIONS.md logs every departure with fairness
impact; checkpoint file updated after every phase so any interruption (rate limits
expected) resumes without half-done state; one project-slice per session. Adversarial
fresh-eye audit AFTER scoring, before publication; report + audit addendum ship together,
never the report alone.

## 11. Repository contents at pre-registration commit (Slice 1)
This document (finalized), the three turn scripts, runner1.sh, score_arm.py + configs,
banner v2 template + per-project ledger templates + scramble tables, DEVIATIONS.md
(empty), LICENSE (MIT). The commit hash is the timestamp proof; results reference it.
