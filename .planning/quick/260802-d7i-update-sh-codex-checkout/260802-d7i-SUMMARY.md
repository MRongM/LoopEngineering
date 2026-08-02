---
quick_id: 260802-d7i
status: complete
mode: inline
commit: uncommitted
date: 2026-08-02
---

# Quick Task 260802-d7i Summary

## Outcome

The repository root now provides an executable POSIX `update.sh` for the canonical Codex
managed checkout. The wrapper resolves its own checkout, honors `CODEX_HOME` with the documented
`$HOME/.codex` fallback, and delegates to `adapters/codex/scripts/manage.py update` with exact,
quoted argv. The lifecycle manager remains the only implementation of Git, origin, branch,
fast-forward, checkout-marker, CLI reinstall, and version gates.

README documents the wrapper without removing the existing Unix one-line or Windows PowerShell
flows. No Core behavior, schema, dependency, release identity, or update policy changed.

## Files

- Added executable `update.sh` as the thin managed-update entrypoint.
- Added `tests/test_update_script.py` with real subprocess coverage.
- Updated `README.md` with the checked-in Unix wrapper command.
- Added the approved design, detailed implementation plan, and this GSD quick-task record.

## TDD Evidence

- RED: `4 failed in 0.23s`; every failure reported `root update.sh is missing` before production
  code existed.
- Focused GREEN: `4 passed in 1.06s`; post-refactor rerun: `4 passed in 0.74s`.
- Wrapper plus lifecycle-manager regression: `48 passed in 1.00s`.

## Verification Evidence

- Full pytest: `268 passed in 13.87s`.
- Ruff: `All checks passed!`.
- POSIX parse: `/bin/sh -n update.sh` exited `0` with no output.
- Executable mode: `-rwxr-xr-x` (`755`).
- Missing both `CODEX_HOME` and `HOME` failed closed with exit `1` and an explicit diagnostic.
- `git diff --check` exited `0`.

## Review

Inline plan-alignment, code-quality, architecture, security, test, and documentation review found
no Critical, Important, or Minor findings. A path assignment was made explicitly quoted during
GREEN refactoring to match repository path-handling style.

## Constraints Preserved

- No branch, worktree, commit, push, PR, merge, deployment, reset, or history rewrite occurred.
- No tests, Gates, schemas, checkout-preservation checks, or release markers were weakened.
- No dependency, runtime data, secret, token, or complete model reasoning was added.
