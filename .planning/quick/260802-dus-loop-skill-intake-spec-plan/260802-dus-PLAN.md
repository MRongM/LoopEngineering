---
quick_id: 260802-dus
status: complete
mode: inline
description: 让 Loop Skill 在 Intake 时告知用户可通过现有 spec 或 plan 生成契约，并在已提供文档时确认采用
must_haves:
  truths:
    - Every explicit new Intake tells the user once that an existing spec or plan can supply contract source material.
    - An already supplied spec or plan is acknowledged and mapped into the draft.
    - An absent spec or plan never blocks Intake or becomes another approval gate.
    - Source material never substitutes for contract completeness, repository facts or explicit approval.
  artifacts:
    - adapters/codex/references/intake-contract.md
    - tests/test_adapter_contract.py
  key_links:
    - adapters/codex/SKILL.md routes every explicit new task to references/intake-contract.md.
    - tests/test_adapter_contract.py validates the routed Intake text through REFERENCE_PATHS[0].
---

# Quick Task 260802-dus: Loop Skill Intake Spec/Plan Prompt

> Execute inline. Do not create implementation subagents, branches, worktrees or Git commits.

**Goal:** Tell every explicit new Loop Intake how an existing spec or plan can be used to generate
the Loop Contract without adding a blocking question or approval gate.

**Canonical design:** `docs/superpowers/specs/2026-08-02-loop-skill-intake-spec-plan-design.md`

**Canonical implementation plan:** `docs/superpowers/plans/2026-08-02-loop-skill-intake-spec-plan.md`

## Task 1: Establish RED evidence and add the Intake notice

- [x] Add the focused Adapter contract assertion before changing the Intake playbook.
- [x] Run the exact test and retain its expected missing-notice failure.
- [x] Add only the approved conditional, non-blocking notice to `intake-contract.md`.
- [x] Run the complete Adapter contract module and retain GREEN evidence.

## Task 2: Verify and record the result

- [x] Run full pytest, Ruff, whitespace and scoped-diff checks.
- [x] Confirm Core, CLI, Schema and templates are unchanged by this task.
- [x] Write the GSD summary and update STATE with `uncommitted` Git delivery.

## Constraints

- Preserve Protocol `0.1.0`, autonomous mode, execution closure and the single approval gate.
- Do not implement a spec/plan parser, CLI generator, Schema field or source-tracking feature.
- Preserve all unrelated working-tree changes.
- Do not branch, commit, push, create a PR, merge, deploy, reset or rewrite history.
