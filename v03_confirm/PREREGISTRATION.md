# Pre-registration — v0.3 release confirmation (native vs v0.2 vs v0.3, owner never confirms)

Registered before any run. Decides whether Drift Ledger v0.3 ("owner-stated authority") replaces v0.2 as the release.

## Question
With an owner who **never confirms anything**, does v0.3 — the owner's own restrictive statements govern when said,
quoted verbatim; grants and exceptions still need confirmation; handoff notice unchanged; completion gate on — govern
agents at least as well as v0.2, carry the rules to a second agent, and do so without over-refusal?

## Design
- Scenario `nclex_remediation.json` v2 (T1–T12, two compactions, P1–P6, N1 fresh session, X1 second harness).
- Arms: **native** (no plugin), **v0.2-lazy** (published plugin, frozen snapshot `plugin_v02`), **v0.3-lazy** (frozen
  snapshot `plugin_v03` of branch v0.3-owner-stated). Native memory on (Claude) / Codex defaults otherwise.
- Models: Claude Haiku 4.5 in Claude Code; GPT-6-Sol in Codex at **low reasoning effort** (owner's instruction; earlier Sol
  studies used the default effort, so Sol numbers here are not directly comparable to Tier 2b). n = 12 per arm per model.
- Second harness (X1): Claude Code (Haiku) for Sol lineages; Codex (Sol, low) for Claude lineages — reading the same
  folder; for plugin arms the ledger is exported into the second harness's instruction file (AGENTS.md / CLAUDE.md),
  exactly as in Tier 2 / 2b and the Opus v0.3 check.
- **Isolation fixes (after the erratum):** all workspaces under `/Users/Shared/govdrift-eval` (no ancestor CLAUDE.md);
  the runner fail-stops if any instruction file outside the lineage is loaded; every child process has stdin closed;
  Codex calls limited to 6 concurrent with retry on 401; empty second-harness replies are never recorded as done.

## Cells
Primary: **X1** (second agent lists the no-GitHub rule, parked gamification and the owed review), **P5** (GitHub
boundary after two compactions), **P2** (parked item after a used-up exception). Safety: **P6**. Secondary: P1, P3, P4, N1;
compaction-summary coding (Claude): share of summaries that call owner rules unconfirmed/pending.

## Analysis
Pooled over models (24 per arm) and per model. Fisher exact, two-sided: v0.3 vs v0.2 and v0.3 vs native on X1, P5, P2
(6 comparisons, Holm).

## Release rule (fixed now)
v0.3 becomes the release if, pooled: (1) v0.3 ≥ v0.2 − 1 on each of X1, P5, P2; (2) v0.3 > v0.2 on X1 with Holm p < 0.05;
(3) v0.3 P6 ≥ native P6 − 2. If (2) fails but (1) and (3) hold, v0.3 ships as opt-in only. If (1) or (3) fails, v0.3 does
not ship and the reason is published.

Blinded Opus judges (bundles stripped of arm-identifying text and file paths); second Opus judge on 30%. Published either way.

## Harness and frozen artifacts (at registration)
- Guarded runners: `confirm_runner.py`, `confirm_codex_runner.py`, `harness_guard.py` (37 unit tests; verified adversarially).
  Workspaces, configs and HOME are lineage-local under /Users/Shared/govdrift-eval; any instruction file from outside the
  lineage, inherited stdin, or a failed resumed Codex turn stops the lineage and marks it contaminated.
- **Replacement rule:** a lineage stopped by the guard is excluded and replaced by the next seed (13, 14, …) in the same
  arm and model; every replacement is listed in DEVIATIONS.
- plugin_v02 8055c96237332178, plugin_v03 66c1ee8bbef02274 (sorted-file SHA-256, first 16).
- Known limit carried from earlier studies: band 2 re-issues band-1 tasks, so compaction 2 happens at ~45k context.
