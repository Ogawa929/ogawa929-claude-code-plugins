---
depends_on: [none]
files:
  - sandbox/20260803-hello-world-script/hello.sh
---

# Plan: hello-world-script

## Purpose / Goal

Implement a disposable bash script, `hello.sh`, used solely to dogfood the `impl-flow` plugin's full workflow (`/impl-flow:design` → `/impl-flow:plan` → `/impl-flow:implement`) on a deliberately trivial task. It is a throwaway test fixture living under a dated sandbox directory — it is explicitly NOT intended to become a permanent, documented sample asset in this marketplace repository.

The script must:
1. Always print `hello world` as its first line of output.
2. If invoked with N positional arguments (N >= 0), print exactly N additional lines after `hello world`, one per argument, in the form `argument 1: <value>`, `argument 2: <value>`, ... `argument N: <value>`, labeled dynamically to match however many arguments were actually passed (with 0 arguments, no additional lines are printed at all).
3. On every run, write the exact same combined output (both the `hello world` line and the argument lines, no more and no less) to a brand-new timestamped log file, named `hello_<yyyymmddHHMMSS>.log` (e.g. `hello_20260803092715.log`), placed in the same directory as the script itself, so that repeated runs never overwrite or blend into a previous run's log.
4. Output must be visible on stdout AND simultaneously captured in the log file — the log file must not be the only place the output appears (i.e. don't redirect stdout away, and don't only write to the log without also printing to the terminal).

## Prerequisites / Background restated

This task has no dependency on any other plan (`depends_on: [none]`) and no dependency on existing code in this repository. Per the design doc, there is no existing shell script, `scripts/` directory, or logging convention anywhere in this repository to follow or integrate with — this is greenfield work. The task-set directory `sandbox/20260803-hello-world-script/` already exists and contains only `design.md`; this plan adds `hello.sh` alongside it. Log files produced by running the script (e.g. `hello_20260803092715.log`) will also land in that same directory as a natural side effect of running the script — they are run-time artifacts, not something this plan needs to create ahead of time, and do not need to be pre-created or listed as files this plan touches.

Out of scope for this plan (per the design doc): making this a permanent documented sample, argument validation or usage/help messages, and portability to shells other than bash.

## Implementation Steps

1. Create the file `sandbox/20260803-hello-world-script/hello.sh` with a `#!/usr/bin/env bash` (or `#!/bin/bash`) shebang.
2. Compute a timestamp for this run in `yyyymmddHHMMSS` format (e.g. via `date +%Y%m%d%H%M%S`) and derive the log file path from it: `hello_<timestamp>.log`, written into the same directory the script lives in (use something like `"$(dirname "$0")/hello_${timestamp}.log"` so the log lands next to the script regardless of the caller's current working directory).
3. Build the full output text as follows:
   - First line: `hello world`.
   - Then, for each positional argument in order (`$1`, `$2`, ... `$#`), append a line `argument <position>: <value>` where `<position>` is the 1-based index and `<value>` is that argument's literal value. If there are zero arguments (`$# -eq 0`), append nothing further.
4. Emit that output so it appears on stdout AND is written verbatim to the log file. The simplest reliable approach for a script this small: pipe the generated output through `tee` targeting the log file (e.g. build the output in a block and pipe the whole block through `tee "$log_file"`), which writes to both the terminal and the file in one pass without duplicating logic. A reasonable reference shape:
   ```bash
   #!/usr/bin/env bash
   timestamp="$(date +%Y%m%d%H%M%S)"
   script_dir="$(cd "$(dirname "$0")" && pwd)"
   log_file="${script_dir}/hello_${timestamp}.log"

   {
     echo "hello world"
     i=1
     for arg in "$@"; do
       echo "argument ${i}: ${arg}"
       i=$((i + 1))
     done
   } | tee "$log_file"
   ```
   The implementer may adjust variable names/style but must preserve the exact output format and dual stdout+file behavior.
5. Ensure the script is executable (`chmod +x sandbox/20260803-hello-world-script/hello.sh`) so it can be run directly as `./hello.sh` during verification.
6. Do not add argument validation, usage/help text, or non-bash portability shims — these are explicitly out of scope.

## Verification Method and Definition of Done

Verification method (manual execution check, as chosen by the user): run the script directly with 0, 1, and multiple (e.g. 3) arguments, and confirm both stdout and the generated log file's content match the requirements exactly.

Concretely, from `sandbox/20260803-hello-world-script/`:

1. **Zero arguments**: run `./hello.sh`.
   - Expected stdout: exactly one line, `hello world`, and nothing else after it.
   - A new log file `hello_<timestamp>.log` should be created; its content should be exactly `hello world` (one line, nothing more).
2. **One argument**: run `./hello.sh foo`.
   - Expected stdout: `hello world` followed by `argument 1: foo`.
   - A new (different) log file should be created containing exactly those two lines, matching stdout verbatim.
3. **Three arguments**: run `./hello.sh foo bar baz`.
   - Expected stdout: `hello world`, `argument 1: foo`, `argument 2: bar`, `argument 3: baz`.
   - A new log file should be created containing exactly those four lines, matching stdout verbatim.
4. Confirm that each run produced a distinct log filename (no overwriting of prior runs' logs) by listing the directory (e.g. `ls hello_*.log`) and seeing three separate files after the three runs above.

Definition of done: all three runs above produce stdout matching the required format precisely (no extra/missing lines), each run's log file content is identical to that run's stdout, and each run creates its own new timestamped log file without clobbering previous ones.

## Suggested Commit Message

```
Add hello.sh test fixture for impl-flow dogfooding

Disposable script that prints hello world plus labeled positional
arguments and logs each run's output to a timestamped file, used to
exercise the impl-flow design/plan/implement workflow end to end.
```
