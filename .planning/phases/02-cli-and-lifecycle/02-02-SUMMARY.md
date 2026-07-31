---
phase: 02-cli-and-lifecycle
plan: "02"
subsystem: lifecycle
tags: [uv, codex-adapter, cli-validation, tdd]
requires:
  - phase: 02-cli-and-lifecycle
    provides: Unique loop-engine Python console script from Plan 02-01
provides:
  - Distribution-aware install, update and uninstall lifecycle
  - Exact loop-engine version verification and legacy alias rejection
  - Fail-closed checkout retention until executable removal is proven
affects: [03-autonomous-codex-skill, 04-release-convergence]
tech-stack:
  added: []
  patterns: [separate-distribution-checkout-skill-and-cli-identities]
key-files:
  created: []
  modified:
    - adapters/codex/scripts/manage.py
    - adapters/codex/SKILL.md
    - tests/test_codex_installer.py
    - tests/test_adapter_contract.py
key-decisions:
  - "uv continues to manage distribution loop-engineering while runtime probes use only loop-engine."
  - "A discoverable legacy CLI alias fails installation verification instead of being tolerated."
patterns-established:
  - "Lifecycle mutations are followed by exact executable-state verification before success or checkout deletion."
requirements-completed: [LIFE-01]
duration: 13min
completed: 2026-07-31
---

# Phase 2 Plan 02: Distribution/executable lifecycle separation Summary

**Codex lifecycle operations now manage the `loop-engineering` distribution while installing, probing and removing only the `loop-engine` executable**

## Performance

- **Duration:** 13 min
- **Started:** 2026-07-31T15:05:17Z
- **Completed:** 2026-07-31T15:18:20Z
- **Tasks:** 1 TDD feature
- **Files modified:** 4

## Accomplishments

- Introduced explicit distribution, checkout, Skill trigger and CLI identity constants.
- Required Protocol 0.3, package version 0.3.0 and an exact single-script mapping before lifecycle operations.
- Added post-install/update `loop-engine --version` verification and rejection of both legacy aliases.
- Added post-uninstall executable absence verification before recursive checkout removal.
- Preserved argv subprocess execution with `shell=False` and all existing Git, path, dirty-state and explicit-removal gates.

## TDD Evidence

- **RED:** focused lifecycle matrix — 10 failed, 38 deselected for missing identity constants, probes, alias rejection, metadata rejection and uninstall retention.
- **GREEN:** the same matrix — 10 passed, 38 deselected.
- **Integration RED:** full lifecycle suite — 13 failed, exposing stale 0.2 fixtures and one residual `TOOL_NAME` production reference.
- **Integration GREEN:** lifecycle suite — 47 passed; lifecycle plus Adapter contract suite — 62 passed.
- **Regression:** full repository suite — 225 passed.
- **Static:** focused and full Ruff checks passed; `git diff --check` passed.

## Task Commits

No commit was created because the linked worktree Git metadata is outside the writable sandbox and the user did not request a commit.

## Files Created/Modified

- `adapters/codex/scripts/manage.py` - Separates identities and verifies CLI state around uv lifecycle operations.
- `adapters/codex/SKILL.md` - Declares Core 0.3 compatibility and uses `loop-engine --version` in lifecycle examples.
- `tests/test_codex_installer.py` - Covers exact metadata, executable probes, alias rejection and removal retention.
- `tests/test_adapter_contract.py` - Locks the lifecycle compatibility marker and executable verification command.

## Decisions Made

- Kept the checkout directory and Python distribution named `loop-engineering`; only the Agent Shell executable is `loop-engine`.
- Used `shutil.which` plus an argv `--version` probe rather than adding shims or inspecting shell state.
- Required exact script metadata so unexpected or legacy executable registration fails before installation.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Removed a residual deleted identifier from update completion output**

- **Found during:** full lifecycle GREEN verification
- **Issue:** `_update` still formatted its success message with undefined `TOOL_NAME`.
- **Fix:** Used the explicit `CODEX_SKILL_NAME` identity constant.
- **Files modified:** `adapters/codex/scripts/manage.py`
- **Verification:** all 47 lifecycle tests and the full 225-test suite pass.
- **Committed in:** not committed due sandbox Git metadata restriction

---

**Total deviations:** 1 auto-fixed bug.
**Impact on plan:** The correction is required for the successful update path and adds no scope.

## Issues Encountered

- The first full lifecycle run revealed that the shared checkout fixture still described Protocol 0.2. It was migrated to the approved 0.3 package markers and all failure-isolation tests were retained.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 2 implementation is complete and ready for code review and goal verification.
- Phase 3 can replace remaining Adapter mode branches with the Autonomous-only decision loop.

## Self-Check: PASSED

- Required source and test files exist.
- All task acceptance criteria and plan verification commands pass.
- No legacy console script is registered by package metadata.
- No unresolved issue remains.

---
*Phase: 02-cli-and-lifecycle*
*Completed: 2026-07-31*
