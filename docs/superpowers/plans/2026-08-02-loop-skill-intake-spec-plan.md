# Loop Skill Intake Spec/Plan Prompt Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Inline execution is selected; do not dispatch implementation subagents.

**Goal:** Make every explicit new Loop Intake tell the user that an existing spec or plan can be used as source material for the Loop Contract.

**Architecture:** Keep the always-loaded safety kernel unchanged and add the behavior to the routed Intake playbook. Lock the user-facing behavior with the existing composed Adapter contract tests so the notice remains discoverable without changing Core, CLI or Schema semantics.

**Tech Stack:** Markdown Skill instructions, Python 3.12+, pytest, PyYAML and the existing Loop Engineering Adapter contract tests.

## Global Constraints

- Preserve Core Protocol `0.1.0`, `mode: autonomous` and exactly one `contract_approval` gate.
- The notice is conditional in wording but mandatory once per explicit new Intake.
- Missing spec/plan input must not block Intake or create another question, approval or pause condition.
- A supplied spec/plan is source material, not approval or a substitute for contract completeness and repository facts.
- Do not modify Core, CLI, Schema, dependencies or unrelated documentation.
- Do not create branches, worktrees, commits, pushes, PRs, merges or deployments.

---

## File Structure

| Path | Responsibility |
|---|---|
| `tests/test_adapter_contract.py` | Locks the complete Intake notice behavior in the composed Adapter corpus |
| `adapters/codex/references/intake-contract.md` | Tells users how spec/plan inputs participate in contract drafting |
| `.planning/quick/260802-dus-loop-skill-intake-spec-plan/260802-dus-PLAN.md` | GSD quick task boundary |
| `.planning/quick/260802-dus-loop-skill-intake-spec-plan/260802-dus-SUMMARY.md` | Fresh RED, GREEN and regression evidence |
| `.planning/STATE.md` | Records completion without a Git commit claim |

### Task 1: Lock and implement the Intake notice

**Files:**

- Modify: `tests/test_adapter_contract.py`
- Modify: `adapters/codex/references/intake-contract.md`
- Test: `tests/test_adapter_contract.py`

**Interfaces:**

- Consumes: `REFERENCE_PATHS[0]`, the routed Intake playbook.
- Produces: one mandatory, non-blocking spec/plan source notice for explicit new Intake.

- [x] **Step 1: Write the failing Adapter contract test**

Add this focused behavior test:

```python
def test_codex_skill_tells_new_intake_users_about_spec_or_plan_sources() -> None:
    intake = " ".join(REFERENCE_PATHS[0].read_text(encoding="utf-8").split())

    for required in (
        "At the start of every explicit new Intake, tell the user once that they may provide an existing spec or plan as source material for the Loop Contract.",
        "If the request already names or includes a spec or plan, acknowledge that you will read it and map it into the contract draft.",
        "If neither is provided, mention the option without blocking Intake; continue from the current request and repository facts.",
        "Source material is not contract approval and does not replace required contract fields, repository facts or applicable instructions.",
    ):
        assert required in intake
```

- [x] **Step 2: Run the focused test and preserve RED evidence**

Run:

```bash
.venv/bin/python -m pytest tests/test_adapter_contract.py::test_codex_skill_tells_new_intake_users_about_spec_or_plan_sources -q
```

Expected: one assertion failure because the Intake playbook does not yet contain the mandatory notice. Import or environment failures are not acceptable RED evidence.

- [x] **Step 3: Add the minimal Intake rule**

Insert this text at the start of `## Intake and contract drafting`, before the numbered drafting workflow:

```markdown
At the start of every explicit new Intake, tell the user once that they may provide an existing
spec or plan as source material for the Loop Contract. If the request already names or includes
a spec or plan, acknowledge that you will read it and map it into the contract draft. If neither
is provided, mention the option without blocking Intake; continue from the current request and
repository facts. Source material is not contract approval and does not replace required contract
fields, repository facts or applicable instructions.
```

- [x] **Step 4: Run focused GREEN verification**

Run:

```bash
.venv/bin/python -m pytest tests/test_adapter_contract.py -q
```

Expected: all Adapter contract tests pass with the new notice test included.

### Task 2: Verify scope and record GSD evidence

**Files:**

- Create: `.planning/quick/260802-dus-loop-skill-intake-spec-plan/260802-dus-SUMMARY.md`
- Modify: `.planning/STATE.md`
- Verify: all Task 1 paths and the approved design/plan artifacts

**Interfaces:**

- Consumes: the final Adapter corpus and working-tree diff.
- Produces: fresh quality evidence and an `uncommitted` GSD completion record.

- [x] **Step 1: Run complete quality gates**

Run:

```bash
.venv/bin/python -m pytest -q
.venv/bin/ruff check src tests adapters/codex/scripts
git diff --check
```

Expected: pytest and Ruff pass; `git diff --check` exits zero with no output.

- [x] **Step 2: Confirm the behavioral boundary**

Run:

```bash
git diff -- adapters/codex/references/intake-contract.md tests/test_adapter_contract.py
git diff -- PROTOCOL.md src schemas templates
git status --short --untracked-files=all
```

Expected: behavior changes are limited to the Intake playbook and Adapter contract test; Core,
Schema and templates have no task-related changes. Existing unrelated working-tree changes remain
untouched.

- [x] **Step 3: Record fresh evidence**

Write the exact RED cause, focused/full test counts, Ruff result, diff check, changed paths and
absence of Git delivery to the GSD summary. Append Quick Task `260802-dus` to `.planning/STATE.md`
with commit value `uncommitted`.

## Plan Self-Review

- Spec coverage: Task 1 covers both conditional messages, non-blocking behavior and non-approval semantics; Task 2 covers regression and state evidence.
- Placeholder audit: no unresolved implementation marker or undefined interface remains.
- Interface consistency: the test and production wording use the same four complete statements.
- Scope: no Core, CLI, Schema, dependency, Git delivery or unrelated documentation change is planned.
