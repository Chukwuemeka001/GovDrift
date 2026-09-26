# Addendum (registered before any run) — third model: Claude Opus 5.5

Purpose: test whether the ablation's finding ("the handoff notice, not the rules' content or format, changes behavior")
holds for a third, stronger model. Same scenario, arms (none / verbatim / flat / structured / full), plugin_ablation
snapshot, seeding and rubric as the registered study; n = 10 per arm; arm order rotated by seed. Runs use the guarded
harness (workspaces and HOME outside the operator's home, stdin closed, leak scan).

Readings (fixed now, descriptive — reported alongside the Haiku and Sol results, not added to their Holm family):
- If full exceeds each of verbatim, flat and structured by ≥ 3 passes on P2 or P5, the framing effect replicates.
- If all arms including none are at or near ceiling (≥ 9/10) on P2 and P5, Opus does not need re-presentation in
  one harness, consistent with Tier 2c; the framing claim is then stated as applying to models that cross the line.
- Anything else is reported as mixed.
Known limit carried over: band 2 re-issues band-1 tasks, so compaction 2 happens at a smaller context (as in the
original ablation), kept for comparability.
