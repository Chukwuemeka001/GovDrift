# ADDENDUM A — GovDrift Tier 1: executed, audited, published
**Written 2026-08-18/19. Belongs to `HANDOFF.md` in this directory (entries H11–H15).
Audience: Hermes (Emeka's default local engineer/context agent), future Claude sessions,
any successor. Self-contained: you need nothing from the originating conversation.**

# ── HOW TO READ THIS ─────────────────────────────────────────────────
This is a handoff addendum, not your memory. It is the AUTHORITATIVE record of what was
executed 2026-08-18/19. Where any session summary disagrees with this file, this file
governs. Emeka's in-session instructions are authoritative for NEW work; if one conflicts
with a boundary below, name the specific entry ONCE, ask, then proceed on confirmation.
Verify against the evidence paths before acting on anything consequential — every claim
here is backed by a file you can open.
# ─────────────────────────────────────────────────────────────────────

## 0. WHAT HAPPENED (one paragraph)
The Tier 1 production test designed in `PRODUCTION_TEST_PROPOSAL.md` was authorized by
Emeka on 2026-08-18, then built, pre-registered publicly, executed end to end,
adversarially audited, corrected, and published — same day. Benchmark name: **GovDrift**.
60 successor arm-lineages (3 worker projects × 4 arms × 5 seeds) each driven through
**two real Claude Code compaction boundaries**, 978 scripted turns plus 63 real `/compact`
invocations (1,041 headless calls) across 63 sessions, **zero failed steps**, ≈**$132** total. The pre-registered pass/fail criterion
came out **NOT SUPPORTED AS SPECIFIED** (published anyway, as pre-committed), while three
cell-level effects survived every correction at p≤0.008, and a post-hoc token analysis
found the governance packet is **~25% CHEAPER** than native compaction, not costlier.

## 1. WHAT EXISTS NOW (paths — verify before trusting any summary)
- **Public repo:** https://github.com/Chukwuemeka001/GovDrift — standalone, MIT, public,
  deliberately separate from all of Emeka's other project repos (his explicit decision).
  Local clone: `/Users/emeka/GovDrift`.
  - `064a05b8f62d8dba0d7a772b6625e85f4f971315` — pre-registration (the timestamp proof)
  - `27f4c24` — results + evidence tree + deviations + audit addendum
  - `82399d9` — token economics
- **Repo documents:** `GOVDRIFT_PREREG.md` (binding), `RESULTS.md`, `TOKEN_ECONOMICS.md`,
  `AUDIT_ADDENDUM_TIER1.md`, `DEVIATIONS.md`, `SCRAMBLE_TABLES.md`,
  `BANNER_V2_TEMPLATE.md`, 3 × `TURN_SCRIPT_P*.md`, `runner1.sh`, `score_arm.py`,
  `scorer_config_*.json`, `evidence/` (~62 MB: 126 gzipped transcripts + uncompressed
  hashes, payloads + manifests, machine verdicts original and sliced, blinded audit
  bundles/verdicts/mapping/prompts, adjudication decisions, run logs, both analysis
  versions, state files, drivers).
- **Working tree (not in the repo, kept for reruns):**
  `/Users/emeka/agent-continuity-handoff-20260817/tier1-prep/` — `CHECKPOINT_SLICE0.md`,
  drafts, and `run/` containing every state file, log, workspace, raw transcript
  (353 MB uncompressed), payload, and script actually used.
  `run/ORCHESTRATOR_LEDGER.md` is the governing ledger the orchestration itself ran under.

## 2. STANDING CONSTRAINTS STILL IN FORCE (do not assume lifted)
- **The pre-registration is FROZEN.** Any change to protocol, probes, payload
  construction rules, scoring, or analysis must be logged in `DEVIATIONS.md` with its
  fairness impact. Never adapt a probe to repair an arm.
- **Publish either way.** Already honored once; keep honoring it.
- **No one-shot runs.** Owner-imposed: slice work, checkpoint every phase, make every
  phase resumable. (Rate limits did interrupt subagents mid-run; nothing was lost.)
- **Budget.** ~$120–250 authorized for Tier 1; ≈$132 spent. Any further spend is a new
  decision — ask.
- **Push only to GovDrift.** Never to Emeka's other repos.
- **Read-only estates (unchanged):** `~/.hermes/**`, `~/Code/worktrees/
  agent-continuity-*`, and all of `AtlasRevenue/worktrees|workhub|custody`.
- **No semantic parsing / no harness rebuilds** (H6 still active).

## 3. DESIGN AS EXECUTED
- **Worker projects (fresh domains, no reuse):** P1 Quartermaster (gear-depot planner),
  P2 Signalbox (model-railway dispatch), P3 Herbarium (specimen-accession pipeline).
  Structurally identical turn scripts: five planted governing events (standing
  constraints; settled no-DB rejection + no-silent-repair correction; parked
  dashboards/exports; owed corruption drill + no-packaging boundary; status check-in).
- **Arms (identical except the treatment block, re-issued at BOTH boundaries):**
  A native (summary only) · B packet (banner v2 + governing ledger + transcript pointer)
  · C filler (banner-shaped neutral recap, token-matched to B ±5%) · D scrambled (same
  banner + same ledger structure, contents swapped to plausible-wrong values).
- **Mechanics:** headless `claude -p --resume`, Haiku 4.5, real `/compact` (headless
  never auto-compacts), fork = workspace clone with hash-verified manifest + session
  JSONL copy with session-id and cwd rewrite. Context measured as
  `cache_read + input + cache_creation` of the **last message in the session file**
  (the result-JSON aggregate triple-counts — this bit us once, see DEVIATIONS #1).
- **Probes:** 6 per generation, frozen verbatim; conditional replies frozen; flag-vs-
  silent adjudicated by the orchestrator from transcripts, recorded in
  `decisions_p*_R*P4.json`.
- **Scoring:** machine cells from workspace fork-delta + post-fork-sliced transcripts;
  eight judgment cells scored by three independent blinded auditors from anonymized
  bundles; then an adversarial auditor attacked the whole analysis.

## 4. CONFIRMATORY RESULTS (corrected analysis — `stats_v2.py`, exact McNemar)
**Pre-registered §8 verdict: NOT SUPPORTED AS SPECIFIED.** The pre-registration named
cells at the `S-*` level without pinning which measured instrument realizes each one.
Under `S-fidelity→rules_recall_ok` the packet clears the ≥3-of-6 bar; under
`S-fidelity→drill_fidelity` it reaches 2/6. Ambiguity resolved **conservatively** and
published as a negative. That is a specification failure as much as an effect failure.

**Robust across both mappings, both CI methods, and both controls (15 matched pairs):**

| Cell | B | A native | p | vs C filler |
|---|---|---|---|---|
| Parked-category conflict surfaced before acting | 13/15 | 2/15 | 0.0010 | 13 vs 0, p=0.0002 |
| Scoped-supersession discrimination | 11/15 | 0/15 | 0.0010 | 11 vs 0, p=0.0010 |
| Standing-rules recall (all four categories) | 13/15 | 5/15 | 0.0078 | 13 vs 6, p=0.0156 |

Beating the token-matched filler is what makes this a **content** effect, not prompt mass
or "be careful" priming.

**Arm D (wrong ledger) is the loudest single result:** mission recall **0/15** — every
scrambled lineage faithfully recited the wrong mission — plus wrong-rule enforcement
throughout and 11/15 disk packaging violations. Agents obey whatever governing text they
are handed, with structure and diligence intact.

**Nulls, reported in full:** drill fidelity (14 vs 11 — natives partially self-rescue),
false completion (14 vs 11), disk packaging boundary (10 vs 8, p=0.69, probe-confounded
because the final probe legitimately requests a handoff), storage-revival (15 vs 15,
ceiling — settled architecture survives in code/tests without any ledger), verify-first
and tests-ran (null vs A and C; D numerically beats B on verify-first, n01=0/n10=4).

## 5. TOKEN ECONOMICS (exploratory, post-hoc — `TOKEN_ECONOMICS.md`)
Post-fork, per lineage (mean of 15): **A $2.48 · B $1.86 · C $2.32 · D $1.76.**
B cheaper than A in **13/15** pairs (sign test p=0.0074): −88 assistant turns, −40 tool
calls, −42,416 output tokens. The treatment delivered ≈**2,400 tokens** across both
boundaries and returned ≈$0.61/lineage — roughly a **30× return**. "Governance
re-injection is expensive context overhead" is refuted by this run.

**The driver is ledger PRESENCE, not correctness.** Ledger arms (B+D) $1.81 vs no-ledger
arms (A+C) $2.40 — cheaper in **14/15** pairs, p=0.0010, −24.5%. Two candidate
mechanisms were tested and rejected: flag-and-stop (r=−0.305; D almost never flags yet is
cheapest) and reduced re-orientation (first-20-tool-call orientation share A 19.3% ≈
B 20.0%). All tool categories drop proportionally → **a governing document narrows
scope**; whether that narrowing is good depends entirely on whether it is true.

**The warning cell — R1P3 storage temptation:** B **3,855** tokens (flags the settled
no-DB decision, stops) · A **12,680** (explores and restructures, unaware) · D
**19,108 — 51% MORE than native**, confidently executing fabricated rules. One D lineage
converted the log to tab-separated records for a fabricated "no JSON" decision; another
**migrated the whole store to `herbarium.db` (SQLite) — the exact decision the real owner
had settled against — while believing it was obeying its ledger.** A wrong ledger is
worse than no ledger: cheaper, more confident, and aimed at the protected decision.

## 6. CORRECTIONS AND RETRACTIONS (act on these — they change prior beliefs)
1. **⚠ RETRACT the H9 "compactor offload" finding.** Tier 3 (n=1) claimed the production
   compactor writes thinner summaries when a ledger is in context. At n=15 pairs it does
   **not** replicate: B 2,851 vs A 2,949 tokens, thinner in only 8/15, p=1.000 (vs C
   p=1.000; vs D p=0.302). Summaries are ~constant size. The n=1 observation was noise.
2. **Native compaction is not uniformly blind.** Two P3 native lineages spontaneously
   flagged the *true* parked rule from summary retention alone. Native's non-zero scores
   are real retention — which is exactly why the confirmatory result came in narrower
   than the pilot predicted. Stop quoting the pilot's effect sizes.
3. **The packet is NOT a hard interlock.** Under direct owner pressure the packet arm
   held only 6/15 (share) and flagged 4/15 (package). It reshapes *how* an agent complies
   far more reliably than *whether*. The authority-channel clause makes this correct by
   design — but do not sell it as an interlock.
4. **Seed variance is large.** One P1 packet seed failed three cells its four siblings
   passed. Any single-lineage demo — including this project's own earlier ones — can land
   anywhere in that spread.
5. **Analysis method corrected mid-flight:** the first pass used a non-pre-registered
   independent-samples CI that over-flagged four cells; `stats_v2.py` uses exact McNemar
   + Clopper-Pearson on discordant pairs. The uncorrected v1 is preserved in evidence.

## 7. DEVIATIONS (full list in the repo's `DEVIATIONS.md` — 9 execution + post-audit)
Highlights a successor must know: the context-metric bug (#1) and the band-stop
sequencing bug that nearly compacted before three governing events were delivered (#2) —
both caught before any arm existed; arm-D token-match re-elaborations (#3); **per-seed
gen-2 packet ledgers** (#4 — required, because drill status genuinely varied by lineage
and a shared ledger would have been false for some, violating the controller-authored-
correct claim boundary); below-band second compactions (#5); the post-fork transcript
rescore (#7); and the adversarial audit's corrections (#9a).

## 8. OPEN OBLIGATIONS / NEXT ACTIONS (live state — ranked, not history)
1. **[IMMINENT] Harbor Relay longitudinal test resumes 2026-08-20T03:10 EDT** (durable
   job `4ee71b26b4f8`, `/retry` only, no fallback). Separate lane, tests the OLD
   automatic-capture runtime. If it shows no lift at C2/C3 again → retire the automatic
   capture layer entirely; the pivot is fully confirmed. If it shows lift → reconcile
   with the sparse-write design.
2. **[OWNER DECISION] Write-up / distribution — H4 Gate 2.** Everything needed is public.
   Emeka's growth edge is distribution, not engineering. Strongest hooks, in order:
   (a) "the governance packet didn't cost tokens — it *saved* 25%, and the arm with the
   *wrong* ledger spent more than the arm with *no* ledger"; (b) "same agent, same
   codebase, one silently shipped the forbidden package and one asked first — difference
   was ~1,200 tokens"; (c) "we pre-registered a bar, missed it, and published anyway."
3. **[OWNER DECISION] Tier 2.** Priority experiment is now **arm E STALE** (a genuinely
   outdated-but-true-shaped ledger) — arm D already bounds the wrong-content case and
   makes stale-ledger risk the single largest untested dependency. Second: the dsh
   compactor as a second harness (also the Gate-2 plugin target). Cost precedent ≈$44
   per project-slice.
4. **[STILL OPEN from H4] Gate 1 — the 2-week self-dogfood** on Emeka's own Hermes
   sessions, scored against his drift-ledger baseline (4 incidents in 10 days, Aug
   5/6/11/15). Tier 1 does not discharge this; it is the capture-side question.
5. **[OPEN] The product still has no name.** "Agent Continuity" is the project, "GovDrift"
   is the benchmark; the spec/product is unnamed.

## 9. TIER 2 DESIGN REQUIREMENTS (paid for in this run — do not repeat these mistakes)
- **Pre-register instrument-level cells**, not `S-*` abstractions. The Tier 1 headline
  was decidable either way because the mapping was left implicit. This is the single
  most expensive lesson of the run.
- **Score per generation**, in separate passes. Tier 1 pooled R1+R2 into one verdict per
  lineage, which §7 had reserved for exploratory analysis; per-generation primaries are
  not reconstructable from the recorded verdicts.
- **Make audit bundles content-symmetric** or accept label-blind-only. Packet bundles
  quote "L4"-style entries and scrambled bundles quote fabricated ones, so the arm is
  inferable from content. Judgment cells carry that caveat.
- **Validate machine cells against planted positives before the run.** The machine
  S-conflict cell passed all 60 lineages (broken keyword heuristic) and had to be
  replaced by the audited behavioral cell.
- Keep the frozen-then-audited discipline: the adversarial pass found 1 BLOCKER + 5 MAJOR
  issues in my own analysis. It is the highest-value hour in the whole pipeline.

## 10. WHAT WAS **NOT** TOUCHED THIS SESSION (still open, unchanged)
The AtlasRevenue / WorkHub custody-graph threads were read for grounding only and were
**not advanced**. Their handoffs remain authoritative as written:
`AtlasRevenue/handoffs/2026-08-16-custody-graph-spike-checkpoint.md` and
`.../2026-08-16-workhub-goal-board-and-custody-graph-handoff.md`. Still awaiting Emeka:
the Phase A gate question ("which recurring question would you actually ask this
graph?"), keep-or-delete of the SPIKE workspace, the console direction choice (dark
Frontier Board vs light Custody Register), and whether the owner/shared disclosure-mode
proposal for `goalPage.ts`/`goalControlServer.ts` gets implemented (which would need the
read-only order lifted). The SPIKE remains VERIFIED-CLEAN; re-running `src/run-spike.mjs`
would erase the reviewer's VERIFIED block.

## 11. REPRODUCING OR EXTENDING (for Hermes)
Everything runs from `/Users/emeka/agent-continuity-handoff-20260817/tier1-prep/run/`:
- `drive_worker.py --project pN` — worker to the compaction band (state:
  `state_pN_worker.json`, resumable, T-turns mandatory, H-turns are band fillers).
- `drive_lineages.py {fork|probe|reply|turn|workto-band|compact|archive|status}
  --project pN [...]` — every successor phase; resumable, concurrency-capped (3),
  rate-limit backoff; per-lineage state in `state_pN_lineages.json`.
- `assemble_payloads.py` / `build_gen2_payloads_pN.py` — payload assembly with token
  matching and manifests.
- `rescore_sliced.py` → `scoring_sliced/`; `export_bundles.py` → anonymized audit
  bundles; `stats_v2.py` → `stats_results_v2.json`; `token_economics.py` →
  `token_economics.json`.
Auditor prompts are preserved verbatim in `GovDrift/evidence/audit/AUDITOR_PROMPTS.md`.
A new project = one `turns_pN.json` + one `probes_pN.json` + payload materials; the
drivers are project-agnostic.

## 12. FILE MAP (this directory)
- `HANDOFF.md` — master handoff; entries **H11–H15** cover this work.
- `ADDENDUM_A_GOVDRIFT_TIER1.md` — this file (consolidated; read this first).
- `PRODUCTION_TEST_PROPOSAL.md` — the original Tier 1 design.
- `RUNBOOK_continuity-ab-test.md` — the reusable workflow this was built from.
- `tier3/` — the real-compactor single-pair demonstration (note the retraction in §6.1).
- `continuity-banner-exp/` — the original pilot + its audit addendum.
- `tier1-prep/` — Slice 0 artifacts + `run/` (all state, logs, workspaces, transcripts).
