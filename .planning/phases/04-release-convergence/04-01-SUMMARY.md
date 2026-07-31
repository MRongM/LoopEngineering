---
phase: 04-release-convergence
plan: "01"
subsystem: release-documentation
tags: [cli, compatibility, documentation, autonomous-only, tdd]
requires:
  - phase: 03-autonomous-codex-skill
    provides: Autonomous-only Skill and unique loop-engine runtime examples
provides:
  - Current 0.3 install, adoption and naming guidance
  - Canonical protocol and CLI compatibility matrix
  - Executable active-document residue contract
affects: [04-02-release-evidence]
tech-stack:
  added: []
  patterns: [active-surface-command-scan, explicit-identity-matrix]
key-files:
  created:
    - docs/compatibility.md
  modified:
    - tests/test_adapter_contract.py
    - README.md
    - docs/adoption.md
    - CONTEXT.md
    - docs/adr/0001-require-manual-skill-invocation.md
key-decisions:
  - "Current copyable guidance uses loop-engine; historical superpowers artifacts remain non-normative audit records."
  - "One compatibility matrix separates product, distribution, checkout, Skill trigger and executable identities."
requirements-completed: [CLI-03, NAME-01]
duration: 7min
completed: 2026-07-31
---

# Phase 4 Plan 01: Current 0.3 command and compatibility surface Summary

**Every active executable example now uses `loop-engine`, while one fail-closed compatibility guide preserves stable product/package/Skill identities and rejects aliases or collaborative migration**

## Performance

- **Duration:** 7 min
- **Started:** 2026-07-31T15:39:00Z
- **Completed:** 2026-07-31T15:45:47Z
- **Tasks:** 1 TDD feature
- **Files modified:** 6

## Accomplishments

- Updated Unix and PowerShell install/update probes plus project initialization examples to use `loop-engine`.
- Advanced README and adoption guidance to Protocol 0.3.0 and fixed Autonomous contracts without a mode choice.
- Added `docs/compatibility.md` with the exact identity matrix, supported explicit legacy Autonomous reads, rejected legacy omission/collaborative behavior and no-migration rule.
- Corrected current vocabulary and ADR consequences so the distribution `loop-engineering` is never confused with the `loop-engine` executable.
- Preserved historical design/plan bodies as audit records and labeled them non-normative through the current compatibility entry point.
- Added a regex-backed contract that scans every active release document for copyable legacy commands while allowing legitimate package names and negative alias statements.

## TDD Evidence

- **RED:** 5 focused documentation tests failed against stale 0.2 prose, old positive CLI examples and the missing compatibility guide.
- **GREEN:** the focused documentation set passed 6/6 after the minimum prose and compatibility changes.
- **Adapter integration:** all 21 Adapter/documentation contract tests passed.
- **Static/structural:** focused Ruff and `git diff --check` passed.
- **Residue audit:** active release documents contain no executable `loop-engineering` or `loop-agent` command.

## Task Commits

No commit was created because the linked worktree Git metadata is outside the writable sandbox and the user did not request a commit.

## Files Created/Modified

- `docs/compatibility.md` - Canonical 0.3 identity and contract/Run compatibility matrix.
- `README.md` - Current release, lifecycle examples, safety version and naming entry point.
- `docs/adoption.md` - Autonomous-only adoption flow and `loop-engine` examples.
- `CONTEXT.md` - Correct current definitions for trigger, distribution, CLI and control mode.
- `docs/adr/0001-require-manual-skill-invocation.md` - Updated consequence for Protocol 0.3 and unique CLI.
- `tests/test_adapter_contract.py` - Positive current examples and negative active-surface residue tests.

## Decisions Made

- Historical `docs/superpowers/` files are not rewritten because the approved 0.3 design retains them as audit history; current entry points now link the 0.3 design and label history non-normative.
- Legacy executable names remain legal only when describing rejected aliases or lifecycle negative tests, never as copyable execution commands.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- One first GREEN run exposed an exact compatibility sentence split across a Markdown table. The normative sentence was made atomic so the contract remains deterministic without weakening the assertion.

## User Setup Required

None - no global lifecycle action or external service configuration was performed.

## Next Phase Readiness

- Active release guidance is converged and ready for Plan 04-02 cross-layer build and regression evidence.
- Historical files are intentionally excluded from executable residue scans by the documented audit boundary.

## Self-Check: PASSED

- All Plan 04-01 acceptance criteria pass.
- Focused RED and GREEN evidence is preserved above.
- No legacy executable command remains in an active release document.

---
*Phase: 04-release-convergence*
*Completed: 2026-07-31*
