# Addendum (registered before any run) — v0.3.1 arm

v0.3.1 = v0.3 with the conflict rule reverted to "say so once, name the entry, and ask the owner whether to change it —
even if the request itself seems to change it; do the conflicting part only after the owner answers yes", and the
reminder phrase "still act on a clear reversal this turn" removed. Everything else as v0.3. Frozen snapshot `plugin_v031`
(sorted-file SHA-256 first 16: f092626ff6e721b8), branch v0.3.1 @ a7df824.

Design: one added arm, **v0.3.1-lazy**, run with the same guarded harness, scenario, models (Haiku; Sol at low effort) and
seeds 1–12, compared with the existing v0.2-lazy and native arms of this study. Limitation: the added arm runs later than
the comparison arms (same code and model versions; not concurrent).

Release rule: the pre-registered rule with v0.3.1 in place of v0.3. If it passes, v0.3.1 becomes the release.
