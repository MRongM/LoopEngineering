# Codex Skill Progressive Disclosure 0.1 Backport Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Inline execution is selected; do not dispatch implementation subagents.

**Goal:** Backport the routed progressive-disclosure architecture while preserving the target branch's exact Protocol `0.1.0` behavior and release identity.

**Architecture:** `adapters/codex/SKILL.md` becomes the always-visible 0.1 safety kernel and direct stage router. Four focused Markdown playbooks own Intake, Goal, execution and lifecycle details; tests validate both the entrypoint and the fixed composed corpus.

**Tech Stack:** Markdown Skill instructions, Python 3.12+, pytest, PyYAML and the existing Loop Engineering CLI.

## Global Constraints

- Protocol, package and Adapter identity remain exactly `0.1.0`; do not add a compatibility range or migration path.
- Preserve `.loop-engine/`, `mode: autonomous`, one `contract_approval`, execution closure, Goal/Run binding, Gate, intent/result, Checker, isolated evidence and authoritative DONE semantics.
- Do not modify `PROTOCOL.md`, `pyproject.toml`, Core, Schema, templates, README, adoption docs or ADRs.
- Do not introduce `.loop-runs/`, `.loop-engineering/` as a control root, Protocol 0.3 wording or legacy gates.
- Add failing tests before changing Adapter production documents; never delete or weaken a safety assertion.
- Do not create branches, worktrees, commits, pushes, PRs, merges or deployments.
- Execute inline and keep fresh RED, GREEN, full-suite, Ruff, diff and patch-application evidence.

---

## File Structure

| Path | Responsibility |
|---|---|
| `adapters/codex/SKILL.md` | Always-visible 0.1 identity, admission, hard gate, direct routing and permanent denies |
| `adapters/codex/references/intake-contract.md` | Pending Draft, execution-closed contract, approval, Run creation and revision |
| `adapters/codex/references/goal-bridge.md` | Goal binding, reconciliation, continuation, cancellation and completion |
| `adapters/codex/references/execution-loop.md` | Maker loop, budget, Gate, evidence, Checker, pause boundaries and DONE |
| `adapters/codex/references/lifecycle.md` | User-operated lifecycle and project initialization guidance |
| `tests/test_adapter_contract.py` | Entrypoint budget/routing, safety kernel, composed semantics and 0.1 residue checks |
| `.planning/quick/260801-my8-backport-codex-skill-progressive-disclos/260801-my8-PLAN.md` | GSD quick plan |
| `.planning/quick/260801-my8-backport-codex-skill-progressive-disclos/260801-my8-SUMMARY.md` | Fresh implementation and validation evidence |
| `.planning/STATE.md` | Quick-task result without a commit claim |

### Task 1: Lock the 0.1 progressive-disclosure contract with RED tests

**Files:**

- Modify: `tests/test_adapter_contract.py`
- Test: `tests/test_adapter_contract.py`

**Interfaces:**

- Consumes: current `SKILL_PATH` and `skill_parts()` helper.
- Produces: `REFERENCE_PATHS`, `ENTRY_WORD_BUDGET`, `read_adapter_protocol()` and entry/composed-corpus assertions.

- [ ] **Step 1: Add the fixed reference corpus and budget**

```python
REFERENCE_PATHS = (
    Path("adapters/codex/references/intake-contract.md"),
    Path("adapters/codex/references/goal-bridge.md"),
    Path("adapters/codex/references/execution-loop.md"),
    Path("adapters/codex/references/lifecycle.md"),
)
ENTRY_WORD_BUDGET = 2113


def read_adapter_protocol() -> str:
    _, body = skill_parts()
    return "\n".join(
        [body]
        + [path.read_text(encoding="utf-8") for path in REFERENCE_PATHS if path.is_file()]
    )
```

- [ ] **Step 2: Add routing, budget and safety-kernel tests**

Require every direct relative route, reject nested playbook routes, keep lifecycle commands out of the entry, and require these inline facts: explicit start, `Core Protocol: 0.1.0`, approval-before-mutation, no newest-Run adoption, no prose-DONE and the permanent deny list.

- [ ] **Step 3: Add a first-release residue test**

```python
def test_codex_skill_composed_corpus_remains_first_release_only() -> None:
    protocol = read_adapter_protocol()

    assert "Core Protocol: 0.1.0" in protocol
    assert "`protocol_version: 0.1.0`" in protocol
    assert "`.loop-engine/`" in protocol
    for obsolete in ("Compatible Core:", "0.3.0", ".loop-runs/", ".loop-engineering/"):
        assert obsolete.casefold() not in protocol.casefold()
```

- [ ] **Step 4: Route detailed existing assertions through `read_adapter_protocol()`**

Keep identity and safety-kernel assertions scoped to `SKILL.md`. Change only detailed contract, decision-loop, hard-boundary, control-root, evidence, Goal and CLI assertions to use the composed corpus; retain every existing required and obsolete item.

- [ ] **Step 5: Run focused RED validation**

Run: `.venv/bin/python -m pytest tests/test_adapter_contract.py -q`

Expected: failure because the four references and route table do not exist and the current 3327-word entry exceeds the 2113-word budget. An environment/import failure is not acceptable RED evidence.

### Task 2: Split the target 0.1 Skill without semantic drift

**Files:**

- Modify: `adapters/codex/SKILL.md`
- Create: `adapters/codex/references/intake-contract.md`
- Create: `adapters/codex/references/goal-bridge.md`
- Create: `adapters/codex/references/execution-loop.md`
- Create: `adapters/codex/references/lifecycle.md`
- Test: `tests/test_adapter_contract.py`

**Interfaces:**

- Consumes: the exact target `master` Skill at `41cae1f` and the RED contract from Task 1.
- Produces: four direct routes and a composed corpus with unchanged Protocol 0.1 semantics.

- [ ] **Step 1: Create `intake-contract.md`**

Move the current Pending Draft rules, preapproval path constraints, execution-closed Intake fields, exact risk disclosures, one complete approval, Run creation and contract revision. Keep `protocol_version: 0.1.0`, `.loop-engine/`, `execution_plan.design_decisions`, exact `actions`, one `contract_approval` and no separate dangerous-action gate.

- [ ] **Step 2: Create `goal-bridge.md`**

Move the current canonical objective, `get_goal`/`create_goal`/`update_goal`, Goal Gate, intent/result, resume, cancellation and completion rules. Preserve unrelated-Goal pause, create-intent reconciliation, explicit-only `token_budget`, ledger authority and no `update_goal blocked` mapping.

- [ ] **Step 3: Create `execution-loop.md`**

Move the current decision table, Maker protocol, engineering persistence, Checker, hard boundaries and CompletionContext rules. Preserve isolated validation under `.loop-engine/cache/`, exact action containment by `execution_plan`, retry limits, scope derivation and authoritative `run complete`.

- [ ] **Step 4: Create `lifecycle.md`**

Move the exact target Unix/PowerShell install, update/status/uninstall and fail-closed manager guidance. Keep managed checkout `skills/loop-engine`, Shell CLI `loop-engine`, Python package `loop-engineering`, and user-operated project initialization.

- [ ] **Step 5: Rewrite `SKILL.md` as the 0.1 safety kernel and direct router**

Keep the existing frontmatter and `Core Protocol: 0.1.0`. Retain explicit-start admission, ledger authority, approval-before-mutation, project reads, protocol/mode identity, `.loop-engine/` preapproval boundaries, authorization summary, no-prose-DONE and permanent denies. Directly route stages to all four `references/*.md` files and fail closed on missing or incompatible references.

- [ ] **Step 6: Run focused GREEN validation and budget check**

Run: `.venv/bin/python -m pytest tests/test_adapter_contract.py -q`

Expected: all Adapter contract tests pass.

Run: `wc -w adapters/codex/SKILL.md`

Expected: no more than 2113 words.

### Task 3: Verify the complete migration and produce an applicable patch

**Files:**

- Create: `.planning/quick/260801-my8-backport-codex-skill-progressive-disclos/260801-my8-SUMMARY.md`
- Modify: `.planning/STATE.md`
- Verify: every file changed by Tasks 1 and 2

**Interfaces:**

- Consumes: final Adapter corpus and working-tree diff.
- Produces: fresh verification evidence and a patch that applies to target `41cae1f`.

- [ ] **Step 1: Run the full quality gates**

Run: `.venv/bin/python -m pytest -q`

Expected: all tests pass.

Run: `.venv/bin/ruff check src tests adapters/codex/scripts`

Expected: `All checks passed!`

Run: `git diff --check`

Expected: no output and exit code zero.

- [ ] **Step 2: Verify release identity and scope**

Assert `git diff -- PROTOCOL.md pyproject.toml` is empty. Search the composed Adapter files for forbidden 0.3 and old control-root residues. Review `git status --short --untracked-files=all` and confirm all paths are Adapter, test, approved design/plan or GSD tracking files.

- [ ] **Step 3: Write GSD summary and state evidence**

Record exact RED cause, focused/full counts, Ruff result, entry word count, release-residue result, changed paths, no Git delivery and the target-write sandbox limitation. Add an `uncommitted` Quick Tasks Completed row to `.planning/STATE.md` without changing milestone `v0.1.0`.

- [ ] **Step 4: Generate and validate the complete patch**

Build a temporary Git index outside the repository, populate it from `HEAD`, add the complete
working tree to that temporary index, then run its cached binary diff against `HEAD` into
`/private/tmp/loop-engine-0.1-progressive-disclosure.patch`. Do not mutate the real index.

Expected: the patch contains tracked edits and every untracked playbook/design/GSD file.

Run against a fresh clone of target `41cae1f`:

```bash
git apply --check /private/tmp/loop-engine-0.1-progressive-disclosure.patch
git apply /private/tmp/loop-engine-0.1-progressive-disclosure.patch
.venv/bin/python -m pytest tests/test_adapter_contract.py -q
```

Expected: patch check and application succeed, every expected path exists, and all focused tests
pass in the fresh clone. Do not apply to the read-only target path and do not commit.

## Plan Self-Review

- Spec coverage: Task 1 locks structure and 0.1 identity; Task 2 performs the semantic-preserving split; Task 3 validates release identity, regressions and patch applicability.
- Placeholder scan: no implementation placeholder or deferred behavior remains.
- Interface consistency: all tasks use the same four reference paths, 2113-word budget, target commit `41cae1f` and Quick ID `260801-my8`.
- Scope: no Core, release-version, dependency, network or Git-delivery change is planned.
