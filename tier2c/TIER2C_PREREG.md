# GovDrift Tier 2c — pre-registration: Claude Opus 5.5 as the main agent (descriptive)

**Status:** PRE-REGISTRATION before any Tier-2c run. Publish either way. Deviations → `tier2c/DEVIATIONS.md`.
Date: 2026-09-25. Identical to `tier2/TIER2_PREREG.md` (scenario v2, rubric, owners, probes, arms, blinded Opus
judging, primary cells N1/X1/P5, falsification rule) except:
- **Agent:** `claude-opus-5-5` via Claude Code 2.1.280 headless, native auto-memory ON; wrapper
  `tier2c/harness/opus_runner.py` over the unchanged frozen `runner.py`; product commit **31090a7402531c01677496829cbe90c0c8e02e85**.
- **n = 5 lineages per arm** (seeds 1–5), 15 total. This tier is **descriptive**: with n=5 no McNemar test can reach
  p<0.05 unless 5/5 pairs are discordant, so results are reported as counts and compared to Tier 2 (Haiku/Sonnet) and
  Tier 2b (GPT-6-Sol) — not used for the confirmatory claim.
- Usage is Max-plan metered; reported as tokens.

## Predictions (stated before running)
1. Opus native passes P1–P5 more often than Haiku native; the plugin's cross-boundary advantage (N1, X1) remains,
   because it does not depend on model strength (native memory is invisible to a second harness; a fresh session only
   sees what was recorded).
2. P4 (forged note): Opus resists in both arms at least as often as Sonnet.
3. Owner hypothesis: the ledger's in-session benefit shrinks as agents get smarter; its cross-boundary benefit does not.
