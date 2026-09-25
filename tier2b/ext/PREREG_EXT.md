# Tier 2b-ext pre-registration — GPT-6-Sol at realistic long context (descriptive)

Committed before any extension run. Product commit e9442bb588d178a1a3c29f0442be38bccaacb6d1. Same design as `tier2c/ext/PREREG_EXT.md` (neutral work turns,
third compaction, new-wording probes G1–G5, a brand-new session N2, second harness X2, blinded Opus judge + 30% second
judge), applied to the 30 Tier-2b lineages after each finishes the base scenario, with one difference: Sol's context
window is 258,400 tokens and Codex auto-compacts near it, so the work target is **220k live tokens (~85% of the window)**
before the forced compaction; if Codex auto-compacts earlier during work, that natural compaction is recorded.
X2's second harness is Claude Code (Haiku), as in Tier 2b.
**Predictions:** (1) the plugin's N2 and X2 advantages over native persist after a long-context compaction; (2) the lazy
arm is the most likely to fail G3 (its GitHub boundary was never confirmed).
