---
phase: 01-protocol-0-3-contract
plan: "02"
subsystem: authorization
tags: [ledger, policy, risk-gates, pydantic, tdd]
requires:
  - phase: 01-protocol-0-3-contract
    provides: Autonomous-only 0.3 contract surface and explicit legacy parsing
provides:
  - Bound 0.2/0.3 contract authorization persisted in the run ledger
  - Protocol-aware policy authorization and monotonic upgrade enforcement
  - Preserved 0.1 dangerous-action/final-acceptance and universal permanent denies
affects: [cli-lifecycle, autonomous-codex-skill, release-verification]
tech-stack:
  added: []
  patterns: [protocol-bound-authority, monotonic-protocol-upgrades, explicit-human-gates]
key-files:
  created: []
  modified:
    - src/loop_engineering/models/run.py
    - src/loop_engineering/ledger.py
    - src/loop_engineering/policy.py
    - tests/test_ledger.py
    - tests/test_policy.py
key-decisions:
  - "0.2 and 0.3 share the exact bound authorization path; 0.1 remains deliberately unbound."
  - "Authorization equality includes protocol version in addition to contract version, hash and risk IDs."
  - "All supported protocol replacements use one ordered monotonicity check."
patterns-established:
  - "An authorization object from another protocol version grants no authority even when hash and risk IDs match."
  - "Permanent denials are asserted across every readable protocol version."
requirements-completed: [SAFE-01, SAFE-02, SAFE-03]
duration: 4min
completed: 2026-07-31
---

# Phase 1 Plan 02: Bound Authorization Summary

**0.3 approvals now bind protocol, contract version, canonical hash, and complete risk IDs while preserving legacy gates and permanent denials**

## Performance

- **Duration:** 4 min
- **Started:** 2026-07-31T14:47:18Z
- **Completed:** 2026-07-31T14:51:47Z
- **Tasks:** 1 TDD feature
- **Files modified:** 7

## Accomplishments

- Extended `ContractAuthorization`, ledger approval persistence, stale detection, and summaries to 0.3.
- Required policy authorization to match the exact protocol as well as contract version, fingerprint, and risks.
- Replaced one pair-specific downgrade rule with complete monotonic checks for 0.1/0.2/0.3.
- Parameterized safety coverage across 0.2/0.3, retained 0.1 gates, and removed the collaborative policy path.

## TDD Evidence

- **RED:** `UV_CACHE_DIR=/private/tmp/loop-engineering-uv-cache uv run python -m pytest tests/test_ledger.py tests/test_policy.py tests/test_evidence.py tests/e2e/test_risk_gates.py -q` — 14 failed, 51 passed. Failures isolated missing 0.3 authorization, missing downgrade rejection, and cross-protocol authorization leakage.
- **GREEN:** the same focused suite — 65 passed.
- **Phase regression:** contract/project/package plus ledger/policy/evidence/e2e — 125 passed.
- **Static:** focused Ruff checks and `git diff --check` both passed.

## Task Commits

No commit was created because the linked worktree Git administrative directory is outside the writable sandbox. The working tree and command evidence are retained without inventing hashes.

## Files Created/Modified

- `src/loop_engineering/models/run.py` - Accepts bound 0.2 and 0.3 authorization records.
- `src/loop_engineering/ledger.py` - Persists/reloads exact bindings and enforces monotonic protocol upgrades.
- `src/loop_engineering/policy.py` - Applies bound grants to 0.2/0.3 and verifies protocol equality.
- `tests/test_ledger.py` - Approval, tamper, upgrade, and downgrade matrix.
- `tests/test_policy.py` - Exact grant, stale/mismatched authority, legacy gate, and permanent-deny coverage.
- `tests/test_evidence.py` - Explicit final gates remain enforced without a mode branch.
- `tests/e2e/test_risk_gates.py` - 0.2/0.3 Checker behavior and legacy high-risk final acceptance.

## Decisions Made

- Kept `_uses_autonomous_risk_grant` as the existing policy seam, but its only discriminator is now protocol version because all valid contracts are Autonomous.
- Compared protocol versions through a closed ordered map, matching the model's three accepted literals and avoiding lexical-version assumptions.
- Treated protocol mismatch as stale authorization even when every other fingerprint component matches.

## Deviations from Plan

None in product scope. Atomic commits remain unavailable under the workspace sandbox.

## Issues Encountered

None beyond the already documented Git administrative-directory restriction.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Core 0.3 contract and authorization semantics are ready for phase-level review and verification.
- The console script still uses the old executable name by design; Phase 2 owns that change.

---
*Phase: 01-protocol-0-3-contract*
*Completed: 2026-07-31*
