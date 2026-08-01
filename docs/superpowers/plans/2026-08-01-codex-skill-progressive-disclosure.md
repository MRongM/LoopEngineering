# Codex Skill Progressive Disclosure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Inline execution has already been selected; do not dispatch implementation subagents.

**Goal:** Reduce the always-loaded Codex `$loop-engine` entrypoint by at least 35% while preserving every Protocol 0.3.0 safety and execution invariant through four directly routed playbooks.

**Architecture:** `adapters/codex/SKILL.md` becomes the always-visible safety kernel and stage router. Four Markdown files under `adapters/codex/references/` own Intake, Goal bridge, execution, and lifecycle details. Adapter contract tests separately validate the inline kernel, direct routing, composed semantics, and word budget.

**Tech Stack:** Markdown Skill instructions, Python 3.12+, pytest, PyYAML, existing Loop Engineering CLI.

## Global Constraints

- Core Protocol remains exactly `0.3.0`, Autonomous-only, compatible with `>=0.3,<0.4`.
- Do not modify `src/`, schemas, templates, Core CLI behavior, README, adoption docs, or ADRs.
- Preserve explicit-start admission, one complete contract approval, Goal/Run binding, per-action Gate, append-only intent/result, Checker, fresh evidence, scope and authoritative DONE semantics.
- Keep force-push, history rewriting, `git reset --hard`, automatic merge and automatic deployment permanently denied.
- Add a failing test before modifying Adapter behavior; never delete, skip or weaken a safety assertion.
- Run all Loop validation with `UV_CACHE_DIR` under the current Run directory.
- Do not create branches, worktrees, commits, pushes or PRs; the user selected inline execution and did not authorize Git mutations.
- GSD quick planning and state artifacts are written inline; no GSD implementation subagent or commit step is allowed.

---

## File Structure

| Path | Responsibility |
|---|---|
| `adapters/codex/SKILL.md` | Always-visible admission, hard gate, routing and permanent safety kernel |
| `adapters/codex/references/intake-contract.md` | Pending Draft, Intake, risk disclosure, approval, Run creation and contract revision |
| `adapters/codex/references/goal-bridge.md` | Native Goal creation, reconciliation, continuation, cancellation and completion |
| `adapters/codex/references/execution-loop.md` | Budget, Gate, Maker, evidence, Checker, pause decisions and authoritative completion |
| `adapters/codex/references/lifecycle.md` | User-operated install, update, uninstall and project initialization guidance |
| `tests/test_adapter_contract.py` | Inline kernel, direct routing, composed semantics, prompt budget and regression contract |
| `.planning/quick/260801-kqj-refactor-codex-loop-engine-skill-into-pr/260801-kqj-PLAN.md` | GSD quick task plan and must-haves |
| `.planning/quick/260801-kqj-refactor-codex-loop-engine-skill-into-pr/260801-kqj-SUMMARY.md` | GSD inline execution result and evidence summary |
| `.planning/STATE.md` | Quick-task completion pointer without a commit claim |

## Task 1: Lock progressive disclosure with a failing Adapter contract

**Files:**

- Modify: `tests/test_adapter_contract.py`
- Test: `tests/test_adapter_contract.py`

**Interfaces:**

- Consumes: Current `SKILL.md` frontmatter and body.
- Produces: `SKILL_PATH`, `REFERENCE_PATHS`, `ENTRY_WORD_BUDGET`, `read_skill_body()` and `read_adapter_protocol()` test helpers.

- [ ] **Step 1: Add the shared corpus helpers at the top of the test module**

```python
SKILL_PATH = Path("adapters/codex/SKILL.md")
REFERENCE_PATHS = (
    Path("adapters/codex/references/intake-contract.md"),
    Path("adapters/codex/references/goal-bridge.md"),
    Path("adapters/codex/references/execution-loop.md"),
    Path("adapters/codex/references/lifecycle.md"),
)
ENTRY_WORD_BUDGET = 2113


def read_skill_body() -> str:
    _, _, body = SKILL_PATH.read_text(encoding="utf-8").split("---", 2)
    return body


def read_adapter_protocol() -> str:
    parts = [read_skill_body()]
    parts.extend(
        path.read_text(encoding="utf-8")
        for path in REFERENCE_PATHS
        if path.is_file()
    )
    return "\n".join(parts)
```

- [ ] **Step 2: Add a direct-routing and prompt-budget test**

```python
def test_codex_skill_uses_bounded_progressive_disclosure() -> None:
    body = read_skill_body()

    assert len(body.split()) <= ENTRY_WORD_BUDGET
    for path in REFERENCE_PATHS:
        route = path.relative_to(SKILL_PATH.parent)
        assert path.is_file(), path
        assert f"`{route.as_posix()}`" in body
        assert f"`{path.as_posix()}`" not in body
        assert (SKILL_PATH.parent / route).is_file()

    assert "Read each required reference directly from this routing table" in body
    assert "git clone --depth 1" not in body
    assert "git clone --depth 1" in REFERENCE_PATHS[3].read_text(encoding="utf-8")
```

- [ ] **Step 3: Add an always-visible safety-kernel test**

```python
def test_codex_skill_keeps_the_safety_kernel_inline() -> None:
    body = read_skill_body()

    for required in (
        "Only explicit `$loop-engine` may start a new Loop task.",
        "Compatible Core: >=0.3,<0.4",
        "Do not mutate before the complete Loop Contract is explicitly approved.",
        "Never scan `.loop-runs/` for a newest Draft or Run.",
        "Never use prose as evidence of `DONE`.",
        "force-push, history rewriting, `git reset --hard`, automatic merge and automatic deployment",
    ):
        assert required in body
```

- [ ] **Step 4: Route detailed existing assertions through the composed corpus without weakening them**

Use `read_adapter_protocol()` in these tests while preserving every existing required and obsolete tuple:

- `test_codex_skill_is_autonomous_only`
- `test_codex_skill_runs_the_autonomous_decision_loop`
- `test_codex_skill_pauses_only_at_hard_boundaries`
- `test_codex_skill_completion_requires_fresh_evidence`
- `test_codex_skill_supports_task_scoped_goal_bound_continuation`
- `test_codex_skill_accepts_natural_language_approval_without_a_fixed_phrase`
- `test_codex_skill_uses_one_autonomous_pre_execution_approval`
- `test_codex_skill_defaults_every_new_task_to_autonomous`
- `test_codex_skill_keeps_control_files_inside_target_project`
- `test_codex_skill_bundles_autonomous_risk_acceptance`

Keep frontmatter assertions and the new always-visible kernel assertions scoped to `SKILL.md` itself.

- [ ] **Step 5: Run the new routing test and preserve RED evidence**

Run through Loop evidence:

```text
UV_CACHE_DIR=<run-dir>/inputs/uv-cache loop-engine evidence run <run-dir> VAL-1
```

Expected: recorded failure because the four reference files do not yet exist and the entrypoint exceeds the 2113-word budget. The failure must name the missing first reference or the word-budget assertion; unrelated import or environment failure is not acceptable RED evidence.

## Task 2: Split the Skill into the safety kernel and four playbooks

**Files:**

- Modify: `adapters/codex/SKILL.md`
- Create: `adapters/codex/references/intake-contract.md`
- Create: `adapters/codex/references/goal-bridge.md`
- Create: `adapters/codex/references/execution-loop.md`
- Create: `adapters/codex/references/lifecycle.md`
- Test: `tests/test_adapter_contract.py`

**Interfaces:**

- Consumes: Approved design and the exact existing Skill semantics.
- Produces: Direct stage-to-reference routing; a composed corpus satisfying all existing positive and negative assertions.

- [ ] **Step 1: Create `intake-contract.md`**

Move, without semantic changes, the complete rules for Pending Draft binding, hard-gated contract drafting, Autonomous 0.3 Intake, risk disclosure, validation, Ready-to-execute summary, natural-language approval, Run creation and contract revision. Include these headings:

```markdown
# Intake and contract playbook
## Pending Draft binding
## Read-only Intake
## Contract drafting and validation
## Complete execution approval
## Run creation
## Contract revision
## Approval mistakes
```

Keep exact Goal operation disclosure requirements in the contract section, but leave native Goal tool sequencing to `goal-bridge.md`.

- [ ] **Step 2: Create `goal-bridge.md`**

Move the canonical `$loop-engine goal-bridge/v1` objective, `get_goal`, `create_goal`, `update_goal`, Goal Gate, intent/result, resume, cancellation and completion-cleanup rules. Include these headings:

```markdown
# Codex Goal bridge playbook
## Canonical binding
## Create and reconcile the Goal
## Resume a Goal/Run binding
## Yield and cancellation
## Complete the Goal
## Independent budgets
```

Preserve the rules that an unrelated Goal is a hard gate, a pending create intent is reconciled before retry, `token_budget` is never inferred, and `update_goal blocked` is forbidden.

- [ ] **Step 3: Create `execution-loop.md`**

Move the autonomous decision table, Maker action protocol, engineering rules, Checker protocol, pause boundaries, approval matrix and CompletionContext rules. Include these headings:

```markdown
# Execution loop playbook
## Autonomous decision loop
## Maker action protocol
## Engineering and persistence
## Checker protocol
## Hard pause and stop boundaries
## Completion
```

Keep every exact Core command, `shell=False` requirement, retry limit, current-fingerprint rule, scope derivation and authoritative `run complete` rule.

- [ ] **Step 4: Create `lifecycle.md`**

Move Unix and PowerShell install references plus update, uninstall, managed-checkout validation and restart requirements. Include project initialization guidance already present in repository adoption documentation, but do not let the Adapter perform install, update or uninstall.

- [ ] **Step 5: Rewrite `SKILL.md` as the safety kernel and direct router**

Retain unchanged frontmatter and `Compatible Core: >=0.3,<0.4`. The body must contain:

```markdown
## Always-on safety kernel
## Task admission
## Required project reads
## Stage routing
## Contract and mutation hard gate
## Permanent denies
```

The routing table must directly name all four reference paths and say:

```text
Read each required reference directly from this routing table before acting.
If a required reference is missing, unreadable, ambiguous, or incompatible, stop.
```

Spell the routes as `references/intake-contract.md`, `references/goal-bridge.md`,
`references/execution-loop.md` and `references/lifecycle.md`, and resolve them from the
directory containing `SKILL.md` rather than the target project's working directory.

Keep the explicit-start rule, no-newest-Run rule, preapproval draft-only write, current authorization requirement, no-prose-DONE rule and permanent deny list in the entrypoint even when detailed copies also exist in playbooks.

- [ ] **Step 6: Run the complete Adapter contract**

Run:

```text
.venv/bin/python -m pytest tests/test_adapter_contract.py -q
```

Expected: all Adapter contract tests pass. If a moved invariant is missing, restore it in the owning playbook or safety kernel; do not delete or loosen the assertion.

- [ ] **Step 7: Verify the entrypoint budget explicitly**

Run:

```text
wc -w adapters/codex/SKILL.md
```

Expected: no more than 2113 words.

## Task 3: Verify, review and close the inline GSD quick task

**Files:**

- Create: `.planning/quick/260801-kqj-refactor-codex-loop-engine-skill-into-pr/260801-kqj-PLAN.md`
- Create: `.planning/quick/260801-kqj-refactor-codex-loop-engine-skill-into-pr/260801-kqj-SUMMARY.md`
- Modify: `.planning/STATE.md`
- Verify: all files changed by Tasks 1 and 2

**Interfaces:**

- Consumes: Green Adapter contract and actual repository diff.
- Produces: GSD tracking, fresh contract validators, independent Checker verdict and authoritative Loop completion facts.

- [ ] **Step 1: Write the compact GSD quick PLAN.md**

Record the task boundary, must-have truths, artifact paths, key links and the three Tasks in this plan. State that execution is inline and Git commits are prohibited by the approved contract.

- [ ] **Step 2: Run fresh Loop validators with the run-local cache**

Run `VAL-1` through `VAL-4` using:

```text
UV_CACHE_DIR=<run-dir>/inputs/uv-cache loop-engine evidence run <run-dir> <VAL-ID>
```

Expected: every evidence record has `passed: true`, `exit_code: 0`, Contract v1 and the same final code fingerprint.

- [ ] **Step 3: Perform scope and raw-diff checks**

Run:

```text
loop-engine scope check <run-dir>/contract.yaml
git status --short --untracked-files=all
git diff --check
```

Expected: scope is valid; every changed path is contract-approved; `.loop-runs/` remains ignored; diff check is silent.

- [ ] **Step 4: Obtain an independent Checker verdict**

The Checker reads Contract v1, approved design, actual diff and raw current-fingerprint evidence. It edits nothing and returns only `ACCEPT`, `REVISE` or `BLOCK` with concrete findings. Record the verdict with `loop-engine run checker`; `REVISE` returns to inline implementation and consumes at most one of two approved revisions.

- [ ] **Step 5: Write the GSD SUMMARY and update STATE**

The summary records files changed, RED and GREEN evidence IDs, final validator results, Checker verdict, no commits, and any deferred project-preflight or resume-snapshot work. Append a Quick Tasks Completed row whose Commit column is `uncommitted`, matching the repository's existing convention.

- [ ] **Step 6: Build CompletionContext and complete authoritatively**

Populate the context only from current events, status, scope, Checker and evidence. Run `completion evaluate`, then `run complete` only on exit code zero. Gate and record Goal completion afterward. Never infer DONE from this plan or summary.

## Plan Self-Review

- Spec coverage: AC-1 is covered by the approved design and Task 3 review; AC-2 and AC-3 by Task 2 plus routing tests; AC-4 by Task 1 RED and Task 2 GREEN; AC-5 by Task 3 validators.
- Placeholder scan: the plan contains no incomplete marker, deferred implementation placeholder or undefined file path.
- Interface consistency: the same four `REFERENCE_PATHS`, 2113-word budget, Run ID and GSD quick ID are used throughout.
- Scope check: all production paths are present in Contract v1; Core, public docs, dependencies and Git remain out of scope.
