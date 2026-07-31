---
phase: 02-cli-and-lifecycle
plan: "01"
subsystem: cli
tags: [argparse, packaging, console-script, tdd]
requires:
  - phase: 01-protocol-0-3-contract
    provides: Package and Core version 0.3.0
provides:
  - Unique loop-engine Python console script
  - Unchanged command groups under the new argparse program name
affects: [02-02-lifecycle, codex-adapter, release-docs]
tech-stack:
  added: []
  patterns: [distribution-name-separated-from-executable]
key-files:
  created: []
  modified:
    - pyproject.toml
    - src/loop_engineering/cli.py
    - tests/test_cli.py
    - tests/test_package.py
key-decisions:
  - "One existing main function serves the renamed executable; no wrapper or alias is added."
patterns-established:
  - "Python distribution identity and Shell executable identity are tested independently."
requirements-completed: [CLI-01, CLI-02]
duration: 3min
completed: 2026-07-31
---

# Phase 2 Plan 01: Unique CLI Entry Summary

**The `loop-engineering` distribution now installs only `loop-engine`, with every existing command group served by the unchanged CLI implementation**

## Performance

- **Duration:** 3 min
- **Started:** 2026-07-31T15:01:20Z
- **Completed:** 2026-07-31T15:04:21Z
- **Tasks:** 1 TDD feature
- **Files modified:** 4

## Accomplishments

- Replaced the sole project console-script key with `loop-engine`.
- Updated argparse help/error identity without copying or changing subcommand implementations.
- Added exact metadata, no-alias, program-name, and complete command-group assertions.
- Refreshed the locked editable environment and proved only `.venv/bin/loop-engine` exists.

## TDD Evidence

- **RED:** focused CLI/package suite — 2 failed, 11 passed; failures were the old script key and old usage name.
- **GREEN:** the same suite — 13 passed.
- **Runtime:** `uv run loop-engine --version` → `0.3.0`.
- **Entrypoints:** new script executable exists; `loop-engineering` and `loop-agent` scripts are absent.
- **Static:** focused Ruff and `git diff --check` passed.

## Task Commits

No commit was created because the linked worktree Git metadata remains outside the writable sandbox.

## Files Created/Modified

- `pyproject.toml` - Registers only `loop-engine`.
- `src/loop_engineering/cli.py` - Uses `loop-engine` as argparse program name.
- `tests/test_cli.py` - Verifies new usage and all ten command groups.
- `tests/test_package.py` - Verifies distribution name and exact script mapping.

## Decisions Made

- Kept distribution `loop-engineering` and import package `loop_engineering` unchanged.
- Used metadata and generated-environment checks instead of adding a compatibility shim.

## Deviations from Plan

None in product scope; Git commits remain unavailable under sandbox permissions.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Lifecycle management can now distinguish the stable distribution from the new executable.
- Plan 02-02 will verify install/update/uninstall outcomes and 0.3 checkout markers.

---
*Phase: 02-cli-and-lifecycle*
*Completed: 2026-07-31*
