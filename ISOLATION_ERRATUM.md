# Erratum — eval isolation (all Claude Code runs)

Found 2026-09-25 while blind-checking the M2 ablation bundles.

**What we claimed:** eval runs use an empty Claude Code config (token-only login), so nothing from the experimenter's
own setup reaches the agents.

**What actually happened:** Claude Code also loads `CLAUDE.md` files from the working directory's ancestors, including
`~/.claude/CLAUDE.md` of the home directory the workspace sits under — as a *project* instruction file, independently
of `CLAUDE_CONFIG_DIR`. Every eval workspace lived under the operator's home directory, so **every Claude Code lineage
in every study loaded the operator's personal global CLAUDE.md** (personal and career context and general working
preferences, including a one-line note about the operator's own NCLEX study project). Verified in transcripts:
Tier 2 45/45, Tier 2-fix 12/12, Tier 2c (and extension) 15/15, M2 ablation Haiku 50/50 (both the voided and the clean
run), Opus v0.3 check 15/15, pilot and slice runs. **Codex (GPT-6-Sol) runs were not affected** (per-lineage
CODEX_HOME; no hits in any rollout). Claude Code second-harness steps inside Sol studies were affected in the same way.

**What it means for the results.** The file was present identically in every arm of every study, so within-study
comparisons (arm vs arm, same model, same file) are not confounded by it. It is, however, an uncontrolled stimulus in
all Claude runs, and our "isolation" statement was wrong. Some agents referred to the operator's workplace in replies;
those mentions have been redacted from published bundles (commit 1f2d751).

**Fix going forward.** Future Claude Code eval workspaces will live outside the operator's home directory, and the
runner will fail if any instruction file outside the workspace is loaded.

## Addendum — Codex runs (found 2026-09-26)
Codex CLI reads the user-level skills directory (`$HOME/.agents/skills`) regardless of `CODEX_HOME`. Every Codex
(GPT-6-Sol) lineage therefore had the **names and one-line descriptions of the operator's installed skills** (about 60,
e.g. trading and video tools) listed in its context. No personal instruction file was loaded in Codex runs. The list was
identical in every arm, so within-study comparisons are unaffected; it is an uncontrolled stimulus in all Codex runs.
Fix: Codex eval runs now use an empty per-lineage HOME (verified: no operator paths in the rollout; context at the first
turn fell from ~22.0k to ~16.5k tokens). Separately, in Claude-harness studies the X1 step (Codex reading the folder)
ran on the operator's own Codex home; it now uses an isolated per-lineage Codex home.
