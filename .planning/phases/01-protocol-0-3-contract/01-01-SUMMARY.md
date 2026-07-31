---
phase: 01-protocol-0-3-contract
plan: "01"
subsystem: protocol
tags: [pydantic, json-schema, autonomous, compatibility, tdd]
requires: []
provides:
  - Core Protocol 0.3.0 Autonomous-only contract semantics
  - Fail-closed legacy 0.1/0.2 compatibility rules
  - Synchronized contract model, templates, package version and generated Schema
affects: [01-02-bound-authorization, cli-lifecycle, codex-adapter, release-docs]
tech-stack:
  added: []
  patterns: [strict-version-aware-validation, model-generated-schema, fail-closed-legacy-loading]
key-files:
  created:
    - docs/superpowers/specs/2026-07-31-loop-engineering-0.3-autonomous-only-design.md
  modified:
    - PROTOCOL.md
    - src/loop_engineering/models/contract.py
    - schemas/loop-contract.schema.json
    - templates/contract.yaml
    - src/loop_engineering/project.py
key-decisions:
  - "Only 0.3 contracts may omit mode; they resolve to autonomous."
  - "Legacy contracts that omit mode fail closed because their historical default was collaborative."
  - "0.3 reuses 0.2 complete risk-disclosure validation while 0.1 keeps its final gate."
patterns-established:
  - "Compatibility is explicit by protocol version and never inferred from historical defaults."
  - "Checked-in JSON Schema is deterministically generated from the strict Pydantic model."
requirements-completed: [CORE-01, CORE-02, CORE-03, CORE-05, CORE-06, TEST-01]
duration: 6min
completed: 2026-07-31
---

# Phase 1 Plan 01: Protocol 0.3 Contract Surface Summary

**Core 0.3 now exposes one Autonomous control mode with fail-closed legacy parsing and synchronized model, templates, project defaults, package metadata, and Schema**

## Performance

- **Duration:** 6 min
- **Started:** 2026-07-31T14:41:01Z
- **Completed:** 2026-07-31T14:47:18Z
- **Tasks:** 1 TDD feature
- **Files modified:** 14

## Accomplishments

- Added the superseding approved 0.3 design and updated the normative protocol.
- Made 0.3 omission resolve to Autonomous while rejecting every explicit collaborative value and every ambiguous legacy omission.
- Preserved explicit 0.1/0.2 Autonomous loading and extended complete 0.2 risk disclosure checks to 0.3.
- Synchronized package/project versions, templates, factories, and deterministically generated JSON Schema.

## TDD Evidence

- **RED:** `UV_CACHE_DIR=/private/tmp/loop-engineering-uv-cache uv run python -m pytest tests/test_contract.py tests/test_project.py tests/test_package.py -q` — 9 failed, 49 passed. Failures covered unsupported 0.3, legacy omission acceptance, collaborative acceptance, old Schema/default constraint, and package version.
- **GREEN:** the same focused suite — 60 passed.
- **Static:** focused Ruff checks and `git diff --check` both passed.
- **Generated artifact:** `uv run loop-engineering schema export schemas` regenerated all three schemas; only the contract Schema changed.

## Task Commits

No commit was created. The linked worktree's Git administrative directory is outside the writable sandbox, so Git cannot create `index.lock`; changes and fresh command evidence remain in the working tree without fabricated commit hashes.

## Files Created/Modified

- `docs/superpowers/specs/2026-07-31-loop-engineering-0.3-autonomous-only-design.md` - Superseding contract and compatibility design.
- `PROTOCOL.md` - Normative 0.3 Autonomous-only rules.
- `src/loop_engineering/models/contract.py` - Strict version-aware parsing and shared 0.2/0.3 risk validation.
- `src/loop_engineering/project.py` - New 0.3 default with readable 0.2 project constraints.
- `pyproject.toml`, `uv.lock`, `src/loop_engineering/__init__.py` - Package version 0.3.0.
- `templates/contract.yaml`, `templates/project.yaml` - New-project 0.3 defaults.
- `schemas/loop-contract.schema.json` - Singleton Autonomous mode and legacy explicit-mode condition.
- `tests/factories.py`, `tests/test_contract.py`, `tests/test_project.py`, `tests/test_package.py` - Behavioral and synchronization coverage.

## Decisions Made

- Rejected omitted `mode` on 0.1/0.2 instead of silently converting their historical collaborative default into Autonomous authority.
- Kept one Pydantic model with explicit version branches; a parallel migration model would add complexity without a current need.
- Kept the old `>=0.2,<0.3` project constraint readable but made initialization emit only `>=0.3,<0.4`.

## Deviations from Plan

None in product scope. The planned atomic Git commits could not be written because of sandbox permissions; no safety or test gate was bypassed.

## Issues Encountered

- The shell has no `python` executable. Verification uses the locked Python 3.12 environment through `uv run python`.
- The default uv cache is read-only in this sandbox. Setting `UV_CACHE_DIR=/private/tmp/loop-engineering-uv-cache` restored deterministic local execution.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- The contract surface is ready for Plan 01-02 to extend ledger authorization and policy gates from 0.2 to 0.3.
- Current ledger and policy code still recognizes bound authorization only for 0.2; that is the intentional next RED target.

---
*Phase: 01-protocol-0-3-contract*
*Completed: 2026-07-31*
