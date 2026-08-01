---
quick_id: 260801-ah4
status: complete
subsystem: terminal-dashboard
tags: [cli, tui, pydantic, read-only, tdd]
provides:
  - Project-discovered read-only Loop Run dashboard
  - Top-level loop-engine watch and loop-engine watch --all commands
  - Adaptive TTY and plain non-TTY rendering without new dependencies
key-files:
  created:
    - src/loop_engineering/watch.py
    - tests/test_watch.py
    - docs/superpowers/specs/2026-08-01-terminal-watch-dashboard-design.md
  modified:
    - src/loop_engineering/cli.py
    - tests/test_cli.py
    - tests/test_adapter_contract.py
    - README.md
    - docs/adoption.md
key-decisions:
  - "Watch discovers only the nearest configured project and accepts no Run directory."
  - "Default output includes all non-terminal and paused Runs; --all adds terminal history."
  - "Dashboard facts are informational and never adopt, resume, authorize, validate or complete a Run."
duration: 23min
completed: 2026-08-01
---

# Quick Task 260801-ah4: Project-level Terminal Watch Dashboard Summary

**Loop Engineering now exposes one project-level, strictly read-only terminal dashboard through `loop-engine watch`, with `--all` for terminal history.**

## Performance

- **Duration:** 23 min
- **Started:** 2026-08-01T07:35:00+08:00
- **Completed:** 2026-08-01T07:58:33+08:00
- **Tasks:** 3 TDD tasks
- **Implementation, test and user-document files changed:** 8

## Accomplishments

- Added nearest-project discovery through `.loop-engineering/project.yaml` and bounded enumeration of direct, non-link `.loop-runs` children.
- Added strict Pydantic dashboard snapshots for status, current-contract recorded evidence, authorization, budgets, unresolved intents, Checker state and recent events.
- Added adaptive wide/compact rendering, distinct success/failure/exhaustion markers, budget bars, ANSI colors, Unicode/ASCII fallback and terminal-control sanitization.
- Added a safe polling lifecycle: TTY refresh, non-TTY one-shot output, final terminal frame retention, Ctrl-C cleanup and no runtime dependency.
- Added only the top-level `watch` command and `--all`; no Run-directory argument, nested alias, daemon or mutation path exists.
- Documented invocation, discovery, filtering, TTY behavior and the non-authoritative read-only boundary.

## TDD Evidence

- **Snapshot/lifecycle RED:** the initial focused Watch suite failed at import because `loop_engineering.watch` did not exist.
- **CLI RED:** `tests/test_cli.py` reported 2 failed and 12 passed because top-level `watch` was absent.
- **Documentation RED:** the new documentation contract failed 1/1 because neither active guide exposed the commands.
- **Hardening RED:** focused regressions each failed before implementation for missing Checker/no-progress display, indistinguishable terminal outcomes, untrusted ANSI/control text and stale-contract validator intent state.
- **Focused GREEN:** `tests/test_watch.py tests/test_cli.py tests/test_adapter_contract.py` — 48 passed in 0.88s.
- **Full GREEN:** `uv run python -m pytest -q` — 248 passed in 5.88s.
- **Static:** `uv run ruff check .` — all checks passed.
- **Build:** `uv build` — source distribution and wheel built successfully; the wheel contains `loop_engineering/watch.py`.
- **Diff integrity:** `git diff --check` exited 0 with no output.

## Files Created/Modified

- `src/loop_engineering/watch.py` - Project discovery, read-only aggregation, sanitization, rendering and Watch lifecycle.
- `src/loop_engineering/cli.py` - Top-level parser and dispatch for `watch` and `watch --all`.
- `tests/test_watch.py` - Discovery, aggregation, ordering, contract-version, rendering, safety and lifecycle coverage.
- `tests/test_cli.py` - Public CLI shape, automatic project discovery, filtering and no-alias coverage.
- `tests/test_adapter_contract.py` - Active-document contract for the two commands and strict read-only semantics.
- `README.md`, `docs/adoption.md` - User-facing invocation and behavior guidance.
- `docs/superpowers/specs/2026-08-01-terminal-watch-dashboard-design.md` - Approved design contract.

## Decisions Made

- Kept filtering in the renderer so one immutable dashboard snapshot can serve default and `--all` views.
- Kept unresolved intents from every contract version visible because they remain authoritative blockers, but only current-contract validator intents may mark evidence as running.
- Used standard-library ANSI refresh instead of curses, Rich or Textual to preserve packaging and non-TTY behavior.
- Sanitized contract/event text, warnings and project paths before rendering so persisted text cannot inject terminal control sequences.

## Deviations from Plan

### Auto-fixed design gaps

- Added distinct terminal markers/colors and the planned Checker-revision/no-progress counters after focused RED tests exposed ambiguous output.
- Added terminal-control sanitization and stale-contract validator coverage as required read-only display hardening.
- Isolated malformed per-Run payloads behind warnings so one corrupt Run cannot hide valid project progress.

These changes stay inside the approved dashboard scope and add no protocol, schema, dependency or mutation behavior.

## Task Commits

No commit was created. The user requested inline execution but did not authorize a Git commit, and repository instructions prohibit committing without that explicit request.

## Issues Encountered

- The linked worktree's `.venv/bin/pytest` shebang targets the base checkout. All authoritative tests therefore used `uv run python -m pytest` from this worktree.
- The default uv cache is outside the writable sandbox. Verification used `UV_CACHE_DIR=/private/tmp/loop-engineering-uv-cache`.

## User Setup Required

Target projects must have `.loop-engineering/project.yaml`; initialize once with `loop-engine project init --root "<project-root>"` when absent.

## Self-Check: PASSED

- Every plan checkbox is complete.
- Focused and full tests, Ruff, package build and whitespace validation have fresh passing evidence.
- No Core protocol, state machine, gate, schema or dependency changed.

---
*Quick task: 260801-ah4-add-project-level-terminal-watch-dashboa*
*Completed: 2026-08-01*
