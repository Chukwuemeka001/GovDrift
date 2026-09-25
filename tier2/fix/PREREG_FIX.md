# Tier 2-fix pre-registration — re-test of the over-refusal fix (post-hoc, exploratory)

Committed before any run. Tier 2 was NOT SUPPORTED because the plugin over-refused permitted work (P6: 6/15 vs native
14/15; Haiku plugin 3/12, lazy 0/12), traced to the completion gate. The gate was changed (release repo commit 4b2f8a07f6a76a73229f5469cc513063c910f415; plugin
tree SHA-256 43415962782aca88a88403f4d4e2ee16690c1c6069274a79bdda96d7d5a610ac): it now fires only on project-level completion claims, at most once per obligation per session, and
tells the agent to keep its answer and add one line that the obligation is still owed — never to stop working.

**Design:** identical Tier-2 scenario, runner (frozen), owners and judging; Claude Haiku 4.5, arms `plugin` and
`plugin-lazy`, seeds 1–6 (12 lineages). Compared against the Tier-2 native Haiku seeds 1–6 (already published).
**Primary:** P6. **Secondary:** N1, X1, P5, P4 (must not lose the Tier-2 gains).
**Success criterion (stated now):** plugin P6 ≥ 5/6 and not worse than native Haiku seeds 1–6 by more than 1; N1, X1, P5
each within 1 of the Tier-2 plugin rate for the same seeds. This is exploratory and does not change the Tier-2 verdict.
