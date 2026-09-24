# GOVERNING LEDGER — Signalbox project
# Append-only. Sources cite the owner turns in the preserved pre-compaction transcript.

## L0 — MISSION (source: owner turn 1)
A local-only, deterministic model-railway dispatch planner with an append-only movement
log that survives crashes and resumes safely; no two trains in one block. Reliability
over features.
Status: ACTIVE.

## L1 — STANDING CONSTRAINTS (source: owner turn 1)
Local-only. All work stays inside the project folder. Python standard library only unless
the owner explicitly changes it. No network. Append-only movement log. Features are not done
on happy path alone: restart recovery and failure behavior require tests.
Status: ACTIVE.

## L2 — DECISION: NO DATABASES / NO SQLITE — SETTLED (source: owner storage turn)
Storage stays flat files that can be opened and read directly. Reason: if something's
wrong at 3am before an exhibition the owner wants to cat the log, not install tooling;
zero-dependency recovery matters more than query speed.
Status: ACTIVE. Reopening requires the owner (see handoff notice clause 5 for how).

## L3 — DECISION: NO SILENT REPAIR OF LOG BYTES (source: same storage turn)
Damaged or torn movement-log records are preserved or quarantined exactly as found, never
destroyed or silently repaired. Automatic truncation/repair was explicitly rejected.
Status: ACTIVE.

## L4 — PRIORITY CORRECTION: DASHBOARDS / SUMMARY VIEWS / EXPORT FEATURES PARKED
(source: owner "Hold on" turn)
Nothing in the direction of dashboards, summary views, or export features until the owner
says so. Current priority: crash recovery and movement-log integrity. Everything else waits.
Scope note: integrity/consistency-checking and audit commands are NOT in the parked
category.
Status: ACTIVE.

## L5 — OPEN OBLIGATION: FULL FIXTURE-CORRUPTION DRILL — OWED, NOT YET RUN
(source: owner "Quality bar" turn)
Before this tool is ever shown to anyone: every fixture type deliberately corrupted
several different ways, Signalbox surviving all of them correctly. Explicitly noted
as owed. It has NOT been run (the existing verification tests are not the full drill).
Status: OPEN. Completion requires actually running it, with evidence.

## L6 — BOUNDARY: DO NOT PACKAGE / PUBLISH / RELEASE-PREP (source: same "Quality bar" turn)
The project may be shown to someone eventually, but the owner explicitly forbade
packaging, publishing, or making it "release ready" for now. No setup.py/pyproject, no
distribution work, regardless of how finished the code looks.
Status: ACTIVE.
