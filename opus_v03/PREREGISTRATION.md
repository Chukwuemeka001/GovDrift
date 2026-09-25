# Pre-registration — Opus, three compactions: v0.3 "owner-stated authority" vs v0.2 vs native (descriptive)

Registered 2026-09-25 before any run. Requested by the owner after the M2 Haiku interim.

## Question
Does v0.3 — the owner's own restrictive statements are in force when said, no confirmation needed — change what Claude
Opus does after three compactions (~250k context), compared with v0.2 and with native Claude Code + memory, when the
owner **never confirms anything**?

## Design (descriptive, n = 5 per arm)
- Model: Claude Opus 5.5 in Claude Code, isolated config, native auto-memory ON in every arm.
- Arms: **native**; **v0.2-lazy** (published plugin, frozen snapshot `plugin_v02`); **v0.3-lazy** (branch
  v0.3-owner-stated @133364f, frozen snapshot `plugin_v03`). "Lazy" = the owner never confirms or runs a ledger command.
  Under v0.2 nothing the agent proposes governs; under v0.3 restrictive rules quoted from the owner govern at once.
- Scenario: `nclex_remediation.json` (T1–T12, two compactions, P1–P6, N1, X1) then `nclex_longctx_ext.json` (work to
  ~250k tokens, third compaction, G1–G5, N2 fresh session, X2 second harness).
- Plugin snapshot hashes (sorted-file SHA-256, first 16): plugin_v02 8055c96237332178, plugin_v03 66c1ee8bbef02274.

## What we look at
Blinded Opus judging with the existing rubrics (P1–P6, N1, X1, G1–G5, N2, X2) plus: what the ledger actually contains
(entries in force vs agent notes), whether compaction summaries call owner rules pending/unconfirmed, and tokens.
Expectation (stated, not tested for significance at n=5): native Opus is near ceiling inside one harness, as in
Tier 2c; v0.3-lazy ≥ v0.2-lazy on the fresh-session and second-harness cells (N1, N2, X1, X2), because under v0.2
a lazy owner's rules never govern. Any v0.3 over-refusal on P6 is reported prominently.

Descriptive only; published whatever it shows.
