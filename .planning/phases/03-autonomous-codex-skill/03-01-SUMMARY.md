---
phase: 03-autonomous-codex-skill
plan: "01"
subsystem: codex-adapter
tags: [autonomous, goal-binding, continuation, tdd]
requires:
  - phase: 02-cli-and-lifecycle
    provides: Unique loop-engine runtime command
provides:
  - Autonomous-only Protocol 0.3 admission instructions
  - Durable Goal/Run/ledger revalidation before continuation
  - Runtime command migration inside the Codex Skill
affects: [03-02-autonomous-loop, 04-release-convergence]
tech-stack:
  added: []
  patterns: [durable-authority-before-continuation]
key-files:
  created: []
  modified:
    - adapters/codex/SKILL.md
    - tests/test_adapter_contract.py
key-decisions:
  - "The Adapter has one Autonomous Protocol 0.3 path and rejects incompatible mode input."
  - "Goal metadata remains a pointer; ledger-bound authorization is revalidated on every continuation."
patterns-established:
  - "Adapter prose contracts pair required clauses with explicit forbidden legacy clauses."
requirements-completed: [CORE-04, AUTO-01, AUTO-05]
duration: 5min
completed: 2026-07-31
---

# Phase 3 Plan 01: Autonomous-only admission and durable continuation Summary

**The Codex Skill now creates only Autonomous Protocol 0.3 tasks and revalidates canonical Goal, Run, ledger authorization, budget and pending intents before continuation**

## Performance

- **Duration:** 5 min
- **Started:** 2026-07-31T15:25:00Z
- **Completed:** 2026-07-31T15:29:55Z
- **Tasks:** 1 TDD feature
- **Files modified:** 2

## Accomplishments

- Removed every collaborative selection, display, downgrade and dedicated execution path from the Skill body.
- Fixed new-task admission to `protocol_version: 0.3.0` and `mode: autonomous` without a mode prompt.
- Migrated every runtime Core command in the Skill from the distribution name to `loop-engine`.
- Strengthened each continuation with current contract protocol/version/hash/risk binding, budget and pending-intent reconciliation.
- Preserved Pending Draft uniqueness, canonical Goal markers, create/complete intent-result pairs and newest-Run prohibition.

## TDD Evidence

- **RED:** 5 focused Adapter tests failed for old commands, mode branches, missing fixed 0.3 fields and incomplete resume revalidation.
- **GREEN:** the same focused set passed 5/5.
- **Integration:** all 16 Adapter contract tests passed.
- **Static:** Ruff and `git diff --check` passed.

## Task Commits

No commit was created because the linked worktree Git metadata is outside the writable sandbox and the user did not request a commit.

## Files Created/Modified

- `adapters/codex/SKILL.md` - Defines one Autonomous admission path and durable continuation checks.
- `tests/test_adapter_contract.py` - Requires 0.3 Autonomous fields/new CLI commands and forbids legacy mode behavior.

## Decisions Made

- Rejected incompatible mode input instead of attempting any Adapter migration or fallback.
- Kept legacy 0.1 Autonomous dangerous-action semantics as a versioned Core gate, not as an alternate control mode.
- Retained `loop-engineering` only where it denotes the Python distribution, repository or managed checkout.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Admission and resume invariants are stable for Plan 03-02 to consolidate the evidence-driven autonomous decision loop.

## Self-Check: PASSED

- Skill body contains no collaborative token or alternate control-mode path.
- Focused and complete Adapter tests pass.
- Runtime command and durable authorization assertions are active.

---
*Phase: 03-autonomous-codex-skill*
*Completed: 2026-07-31*
