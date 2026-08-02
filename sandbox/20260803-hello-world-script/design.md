# Design: hello-world-script

## Background / Purpose

This is a disposable test fixture used to dogfood the `impl-flow` plugin (`/impl-flow:design` → `/impl-flow:plan` → `/impl-flow:implement`) end to end on a deliberately trivial task, so the workflow's mechanics can be validated before relying on it for real work. It is not intended to become a permanent part of this marketplace repository.

## Scope

**In scope**
- A shell script that prints `hello world`, followed by each argument it received, labeled by position (`argument 1: ...`, `argument 2: ...`, etc.), dynamically matching however many arguments were actually passed.
- Every run also writes its output to a new, timestamped log file (so repeated runs don't overwrite or blend into each other).

**Out of scope**
- Making this a permanent, documented sample asset in the marketplace (no README/marketplace.json registration).
- Argument validation/usage-message handling beyond the dynamic echo described above.
- Cross-shell portability guarantees beyond bash.

## Requirements

1. Running the script with no arguments prints `hello world` and nothing else after it.
2. Running the script with N arguments prints `hello world`, then N lines: `argument 1: <value>`, `argument 2: <value>`, ... `argument N: <value>`.
3. Each run also writes the same output to a new log file, timestamped per run (e.g. `hello_<yyyymmddHHMMSS>.log`), so previous runs' logs are never overwritten.
4. Output must appear on stdout *and* be captured in the log file (not log-file-only).

## Relevant files / interfaces

None — codebase exploration (impl-flow design Step 4) found no existing shell scripts, `scripts/` directory, or logging convention in this repository. This is a greenfield addition with nothing to conform to or reuse.

## Key decisions and rationale

- **Placement: `sandbox/` (throwaway), not a permanent `scripts/` sample.** Rejected alternative: adding it as a documented marketplace sample asset — rejected because the actual goal right now is validating the `impl-flow` plugin's own workflow, not producing a lasting repo artifact.
- **Log file: new timestamped file per run.** Rejected alternatives: overwrite a fixed filename each run (loses history, can't compare runs), or append to one growing file (unbounded growth, harder to isolate a single run's output). A fresh timestamped file per run keeps each run's log self-contained and inspectable.
- **Argument count: fully dynamic.** Rejected alternative: a fixed two-line `argument 1` / `argument 2` output regardless of actual argument count — rejected because it doesn't match the request ("受け取った引数を... 引数1、2と出力する") once read literally: the labeling is positional over however many arguments are actually received, not a hardcoded assumption of exactly two.

## Open concerns / risks

- None material — this is a throwaway single-file script with no dependencies and no integration surface.

## Next steps

Run `/impl-flow:plan sandbox/20260803-hello-world-script` (dogfooded manually per this test) to turn this into a single commit-sized implementation plan.
