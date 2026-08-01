---
quick_id: 260801-kqj
status: complete
mode: inline
description: Refactor Codex loop-engine Skill into progressive-disclosure playbooks with validated routing
must_haves:
  truths:
    - The always-loaded Skill retains admission, approval, authorization and permanent safety boundaries.
    - Four directly routed playbooks preserve the complete existing Adapter semantics.
    - The Skill entrypoint is at least 35 percent smaller than the 3251-word baseline.
    - Focused and full validation pass without weakening existing assertions.
  artifacts:
    - adapters/codex/SKILL.md
    - adapters/codex/references/intake-contract.md
    - adapters/codex/references/goal-bridge.md
    - adapters/codex/references/execution-loop.md
    - adapters/codex/references/lifecycle.md
    - tests/test_adapter_contract.py
  key_links:
    - SKILL.md directly routes every stage to a bounded reference with fail-closed wording.
    - Adapter contract tests validate both the inline safety kernel and the composed protocol corpus.
    - Loop Contract v1, current-fingerprint evidence and an independent Checker remain authoritative.
---

# Quick Task 260801-kqj: Codex Skill Progressive Disclosure

> Execute inline in this session. Do not create implementation subagents, branches, worktrees or Git commits.

**Goal:** Reduce the always-loaded `$loop-engine` entrypoint by at least 35% while preserving every Protocol 0.3.0 invariant through directly routed playbooks.

**Canonical design:** `docs/superpowers/specs/2026-08-01-codex-skill-progressive-disclosure-design.md`

**Canonical implementation plan:** `docs/superpowers/plans/2026-08-01-codex-skill-progressive-disclosure.md`

## Task 1: Establish RED contract evidence

**Files:** `tests/test_adapter_contract.py`

- [x] Add fixed reference paths, composed-corpus helpers, the 2113-word entry budget, direct-routing assertions and always-visible safety-kernel assertions.
- [x] Preserve every existing positive and negative semantic assertion while routing detailed checks through the composed corpus.
- [x] Run `VAL-1` with the Run-local `UV_CACHE_DIR` and retain the expected missing-reference or word-budget failure.

## Task 2: Implement the progressive-disclosure Adapter

**Files:** `adapters/codex/SKILL.md`, `adapters/codex/references/*.md`

- [x] Create the Intake/contract playbook.
- [x] Create the Codex Goal bridge playbook.
- [x] Create the execution-loop playbook.
- [x] Create the user-operated lifecycle playbook.
- [x] Rewrite `SKILL.md` as the always-visible safety kernel and direct stage router.
- [x] Run focused GREEN validation and confirm the entrypoint is no more than 2113 words.

## Task 3: Verify and close

**Files:** this quick-task directory and `.planning/STATE.md`

- [x] Run fresh `VAL-1` through `VAL-4` at one shared code fingerprint.
- [x] Verify contract scope and inspect the raw diff.
- [x] Obtain and record an independent Checker verdict.
- [x] Write `260801-kqj-SUMMARY.md` and append an `uncommitted` quick-task row to STATE.
- [x] Build CompletionContext and use only authoritative Loop completion commands.

## Constraints

- No Core, CLI, Schema, template, README, adoption or ADR changes.
- No dependency, network, production or sensitive-data access.
- No weakening, deleting, skipping or hiding tests, gates or schemas.
- No force-push, history rewrite, reset-hard, merge or deployment behavior.
- No Git delivery operation is authorized.
