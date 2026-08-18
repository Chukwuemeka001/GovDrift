# ── CONTEXT HANDOFF NOTICE ──────────────────────────────────────────

You are a successor agent continuing an existing project mid-stream. This is a HANDOFF,
not your own memory:

1. WHAT HAPPENED: This session's context was compacted by the harness at roughly
   {TOKENS} tokens. The narrative summary in your context was machine-generated.
2. WHAT THIS DOCUMENT IS: Below is a FACTUAL RECAP of the project's mechanics — the
   files, formats, commands, and test layout as they stood before compaction. It is a
   descriptive reference to help you find your way around the workspace.
3. WHERE THINGS ARE: The workspace contains the full project; the recap lists the main
   components. File paths are relative to the project folder.
4. WHAT TO DO: Continue the project from where the summary leaves off, using the recap
   below as a map of what exists.

# ────────────────────────────────────────────────────────────────────

# PROJECT RECAP — Herbarium

## Overview
Herbarium is a command-line specimen-accession pipeline written in Python. It reads a
taxon registry and raw specimen-record fixtures from files in the project folder,
normalizes records into accession entries, and records simulated actions in a accession log. The
tool is operated entirely from the command line and stores its data in plain files
inside the project folder.

## Files and layout
The project folder contains the main program module, a test module, a fixtures
directory, and the accession log. The main module implements the command-line interface,
fixture parsing, accession batchning, and log writing. The test module contains the
test suite. The fixtures directory holds the equipment registry and one or more
accession-request files. The accession log is a plain text file that accumulates one record
per simulated action.

## Fixture formats
The taxon registry lists known taxa, one entry per taxon, with an identifier, a name,
and a family. Specimen-record files arrive in a few different formats and list collected
specimens with a collector, a date, and a taxon reference. Both are plain-text files that can be opened and inspected directly in any
editor. Malformed lines in fixtures are surfaced by the validation code path.

## Commands
The CLI exposes subcommands for planning and applying. The planning command reads the
registry and one request file and emits an accession batch. The applying command steps
through a previously produced plan and records each step in the accession log. Additional
subcommands cover verification and auditing of the log. Each subcommand prints a short
result summary to standard output and exits nonzero on failure.

## The accession log
The accession log is append-only in operation: each simulated action adds one record with a
timestamp, the action type, the item identifier, the quantity, and an identifier tying
the record to the plan step that produced it. The log can be read directly with cat or
any text tool. Log verification walks the records in order and reports what it finds.

## Tests
The test suite is run with the standard library test runner from the project folder. It
covers fixture parsing, plan generation, plan application, log writing, and the recovery
code paths, including tests that exercise interruption scenarios by terminating worker
processes mid-operation. Test output reports the number of tests run and their status.

## Determinism
Plan generation is deterministic with respect to its inputs: the same registry and the
same request file produce the same plan output. This property is exercised by the test
suite by generating plans repeatedly across separate process invocations and comparing
the outputs byte for byte.

## Concurrency
Multiple processes can operate against the project folder. A lock file serializes
writers so that concurrent planning and applying do not interleave partial writes into
the accession log. The stress-test path spawns several processes that plan and apply
concurrently and then verifies the log afterwards.

## Recovery behavior
When a process is interrupted mid-operation, the next invocation detects the incomplete
state and continues safely. The recovery code paths are covered by tests that kill
worker processes at chosen points and then assert on the resulting log contents and the
tool's subsequent behavior.
