# Autonomous Single Risk Acceptance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Autonomous Core `0.2.0` accept all precisely disclosed risks with one contract approval, while preserving exact scope, Checker, compatibility, and permanent prohibitions.

**Architecture:** Add version-aware risk metadata to the strict contract, bind approvals to a canonical contract fingerprint in the append-only ledger, and make GatePolicy consume that persisted authorization. The Codex Adapter drives `gate check` from a run directory so exact Autonomous risks—including production and sensitive-data operations—continue without another human prompt; new scope becomes one complete contract revision.

**Tech Stack:** Python 3.12+, Pydantic 2, append-only JSONL ledger, argparse CLI, YAML/JSON Schema, pytest 9, Ruff, Markdown Agent Skill.

## Global Constraints

- Read `PROTOCOL.md` and `docs/superpowers/specs/2026-07-31-autonomous-single-risk-acceptance-design.md` before changing behavior.
- Use strict Pydantic models, argv subprocesses and `shell=False`.
- Add and observe a failing test before each production behavior change.
- Preserve `0.1.0` run semantics; new defaults and generated assets use `0.2.0`.
- Never permit force-push, history rewrite, `reset --hard`, automatic merge or automatic deployment.
- Do not access a real production system or persist secrets while testing this feature.
- Do not weaken tests, schemas, Checker requirements or exact path checks.
- Do not commit, push, create a branch or rewrite history; execution is inline in the user-approved current worktree.

---

## File Structure

| File | Responsibility |
|---|---|
| `src/loop_engineering/models/contract.py` | Version-aware strict risk grant and final-gate validation |
| `src/loop_engineering/models/run.py` | Typed persisted contract authorization |
| `src/loop_engineering/contract.py` | Stable canonical contract fingerprint |
| `src/loop_engineering/ledger.py` | Bind approvals to current contract hash and risk IDs |
| `src/loop_engineering/policy.py` | Decide allow/revision/legacy danger/deny from exact authorization |
| `src/loop_engineering/cli.py` | Load run-backed GatePolicy and expose required gate |
| `templates/`, `schemas/`, `src/loop_engineering/project.py` | Publish `0.2.0` defaults and generated schema |
| `adapters/codex/SKILL.md` | One risk table, one approval, no Autonomous runtime danger/final gate |
| `PROTOCOL.md`, design/adoption/README documents | Normative semantics and migration guidance |
| `tests/` | RED/GREEN coverage for model, ledger, policy, CLI, completion and Skill |

### Task 1: Versioned Risk Grant Model

**Files:**
- Modify: `tests/factories.py`
- Modify: `tests/test_contract.py`
- Modify: `tests/test_package.py`
- Modify: `src/loop_engineering/models/contract.py`
- Modify: `src/loop_engineering/__init__.py`
- Modify: `pyproject.toml`

**Interfaces:**
- Produces: `PROTOCOL_VERSION == "0.2.0"` and a version-aware `AuthorizedOperation`.
- Preserves: parsing of legacy `protocol_version: 0.1.0` contracts.

- [ ] **Step 1: Add RED contract tests**

Add helpers that build a `0.2.0` Autonomous high-risk contract with one exact operation:

```python
def autonomous_risk_contract_data(kind: str = "production_access") -> dict[str, Any]:
    data = valid_contract_data(protocol_version="0.2.0")
    data["mode"] = "autonomous"
    data["risk_level"] = "high"
    data["human_gates"] = ["contract_approval"]
    data["permissions"][kind] = True
    data["authorized_operations"] = [{
        "risk_id": "RISK-1",
        "kind": kind,
        "target": "production/customer-index",
        "risk_level": "high",
        "impact": "Reads the approved production index",
        "worst_case": "Sensitive records may be exposed",
        "recovery": "Stop access and rotate affected credentials",
        "evidence": "AC-1 requires production verification",
    }]
    return data
```

Assert that the model accepts this without `final_acceptance`, rejects missing disclosure fields, duplicate `risk_id`, and non-high production/sensitive risks. Assert a legacy `0.1.0` operation without disclosure remains valid and still requires high-risk final acceptance.

- [ ] **Step 2: Verify RED**

Run:

```bash
uv run pytest tests/test_contract.py tests/test_package.py -q
```

Expected: failures show unsupported `0.2.0`, missing risk fields/final-gate semantics, and old package version.

- [ ] **Step 3: Implement the minimal strict model**

Set `PROTOCOL_VERSION = "0.2.0"`, accept `Literal["0.1.0", "0.2.0"]`, and add optional fields to `AuthorizedOperation`:

```python
risk_id: str | None = Field(default=None, pattern=r"^RISK-[1-9][0-9]*$")
risk_level: RiskLevel | None = None
impact: str | None = Field(default=None, min_length=1)
worst_case: str | None = Field(default=None, min_length=1)
recovery: str | None = Field(default=None, min_length=1)
evidence: str | None = Field(default=None, min_length=1)
```

In the parent validator, require every field for `0.2.0`, enforce unique risk IDs, require production/sensitive operations to be `high`, require the matching permission, and require final acceptance only for Collaborative `0.2.0` or Collaborative/high-risk `0.1.0`.

- [ ] **Step 4: Verify GREEN**

Run the Task 1 command and require zero failures.

### Task 2: Cryptographically Bound Approval Ledger

**Files:**
- Modify: `tests/test_ledger.py`
- Modify: `src/loop_engineering/models/run.py`
- Modify: `src/loop_engineering/contract.py`
- Modify: `src/loop_engineering/ledger.py`

**Interfaces:**
- Produces: `contract_fingerprint(contract: LoopContract) -> str`.
- Produces: `ContractAuthorization(contract_version, contract_sha256, accepted_risk_ids)`.
- Produces: `RunStore.current_contract_authorization() -> ContractAuthorization | None`.

- [ ] **Step 1: Add RED ledger tests**

Test that an approved `0.2.0` contract event includes protocol version, current version,
64-character SHA-256 and sorted accepted risk IDs. Test rejection returns no authorization,
tampering with the contract invalidates authorization, and a revised contract creates a new
binding while old-version events remain unusable. Test legacy approvals keep their old payload.

- [ ] **Step 2: Verify RED**

Run:

```bash
uv run pytest tests/test_ledger.py -q
```

Expected: approval payload lacks binding fields and `current_contract_authorization` is absent.

- [ ] **Step 3: Implement fingerprint and typed authorization**

Canonicalize `contract.model_dump(mode="json")` with sorted keys, compact separators and UTF-8,
then return SHA-256. `record_approval` automatically adds the binding only for approved
`contract_approval`/`contract_revision` events on `0.2.0`. `current_contract_authorization`
reads only current-version events, uses the latest relevant decision, validates the typed payload,
and compares the stored digest to the current persisted contract.

- [ ] **Step 4: Verify GREEN**

Run the Task 2 command and require zero failures.

### Task 3: Run-Backed Autonomous Gate Policy

**Files:**
- Modify: `tests/test_policy.py`
- Modify: `tests/test_cli.py`
- Modify: `src/loop_engineering/policy.py`
- Modify: `src/loop_engineering/cli.py`

**Interfaces:**
- Produces: `GateRequirement` values `contract_approval`, `contract_revision`, `dangerous_action`.
- Changes: `GatePolicy(contract, authorization=None)`.
- Changes: `loop-engineering gate check <run-dir-or-contract> <request-json>`.

- [ ] **Step 1: Add RED policy tests**

Cover these exact cases:

```text
0.2 Autonomous + matching hash/risk ID + permission + production/sensitive => ALLOW
0.2 Autonomous + no/stale approval => PAUSE, required_gate=contract_approval
0.2 Autonomous + new target or permission => PAUSE, required_gate=contract_revision
0.2 Collaborative + production/sensitive => PAUSE, required_gate=dangerous_action
0.1 production/sensitive => original fresh danger gate
all versions + permanent prohibition => DENY
```

Add a CLI test that creates a run, records contract approval, passes the run directory to
`gate check`, and receives `allow` without a `confirmation` field. A direct `0.2.0` contract
path must pause because it cannot prove ledger approval.

- [ ] **Step 2: Verify RED**

Run:

```bash
uv run pytest tests/test_policy.py tests/test_cli.py -q
```

Expected: production/sensitive still pause and the CLI treats a run directory as a file.

- [ ] **Step 3: Implement explicit gate requirements**

Resolve the exact `AuthorizedOperation` object, validate category permissions, and compare its
risk ID with the bound authorization. Check permanent prohibitions first. For Autonomous
`0.2.0`, route missing approval to `contract_approval` and any unmatched action/target/permission
to `contract_revision`; never produce a standalone danger confirmation for either route.

In the CLI, detect a directory, open `RunStore`, and construct GatePolicy with
`store.current_contract_authorization()`. Retain contract-file loading for compatibility. Add
`confirmation` only when `required_gate` is `dangerous_action`.

- [ ] **Step 4: Verify GREEN**

Run the Task 3 command and require zero failures.

### Task 4: Autonomous Completion Semantics

**Files:**
- Modify: `tests/e2e/test_risk_gates.py`
- Modify: `tests/e2e/test_loop_dry_run.py` only if its default version requires new data.
- Verify: `src/loop_engineering/evidence.py`
- Verify: `src/loop_engineering/ledger.py`

**Interfaces:**
- Preserves: Medium/High Checker `ACCEPT` requirement.
- Changes: high-risk Autonomous `0.2.0` has no implicit final acceptance gate.

- [ ] **Step 1: Add RED E2E tests**

Assert a `0.2.0` high-risk Autonomous contract with `human_gates=["contract_approval"]` reaches
completion with fresh evidence and Checker `ACCEPT`, but not with Checker `REVISE`. Assert a
Collaborative `0.2.0` contract and high-risk Autonomous `0.1.0` contract still require human final
acceptance.

- [ ] **Step 2: Verify RED, then implement only required completion changes**

Run:

```bash
uv run pytest tests/e2e/test_risk_gates.py tests/test_evidence.py -q
```

The model validator is expected to provide most behavior. Change completion code only if a test
demonstrates an additional implicit high-risk final gate.

- [ ] **Step 3: Verify GREEN**

Re-run the Task 4 command and require zero failures.

### Task 5: Protocol, Schema, Template and Codex Skill

**Files:**
- Modify: `tests/test_adapter_contract.py`
- Modify: `tests/test_protocol_coverage.py` if a new invariant name is required.
- Modify: `PROTOCOL.md`
- Modify: `docs/superpowers/specs/2026-07-30-loop-engineering-protocol-design.md`
- Modify: `docs/superpowers/specs/2026-07-31-single-execution-approval-design.md`
- Modify: `adapters/codex/SKILL.md`
- Modify: `templates/contract.yaml`, `templates/project.yaml`
- Regenerate: `schemas/loop-contract.schema.json`
- Modify: `src/loop_engineering/project.py`, `adapters/codex/scripts/manage.py`
- Modify: installer/project/adapter tests that assert compatibility text.

**Interfaces:**
- Codex calls `gate check "<run-dir>" "<request-json>"`.
- Ready-to-execute summary includes one structured risk table and one acceptance question.

- [ ] **Step 1: Add RED documentation contract tests**

Assert the Skill includes `Autonomous Risk Acceptance`, all risk disclosure fields, run-backed
gate check, contract-revision routing, no default Autonomous final acceptance, and the permanent
deny list. Assert obsolete statements that production/sensitive always pause or high-risk
Autonomous always needs final acceptance are absent from current protocol/Skill text.

- [ ] **Step 2: Verify RED**

Run:

```bash
uv run pytest tests/test_adapter_contract.py tests/test_protocol_coverage.py tests/test_project.py tests/test_codex_installer.py -q
```

Expected: new `0.2.0` interaction phrases and compatibility values are missing.

- [ ] **Step 3: Implement the positive interaction recipe**

Update the normative protocol and design documents. In the Skill, require one table ordered as
`risk_id, kind, exact target, impact, worst case, recovery, evidence`; after approval record the
bound contract event. Route `required_gate=contract_revision` into a new complete contract summary,
not a standalone risk prompt. State that Autonomous has no risk-derived final gate and that
platform-level approval prompts remain external hard gates.

- [ ] **Step 4: Publish `0.2.0` assets**

Update package/project/installer/template compatibility, then regenerate schemas with:

```bash
uv run loop-engineering schema export schemas
```

Do not rewrite historical implementation plans that explicitly document `0.1.0`.

- [ ] **Step 5: Verify GREEN**

Re-run the Task 5 command and require zero failures.

### Task 6: Full Verification and Scope Review

**Files:**
- Review every changed file; no additional behavior is introduced in this task.

- [ ] **Step 1: Run focused safety and lifecycle tests**

```bash
uv run pytest tests/test_contract.py tests/test_ledger.py tests/test_policy.py tests/test_cli.py tests/e2e/test_risk_gates.py tests/test_adapter_contract.py -q
```

- [ ] **Step 2: Run static checks**

```bash
uv run ruff check src tests adapters/codex/scripts
git diff --check
```

- [ ] **Step 3: Run the complete suite and build**

```bash
uv run pytest -q
uv build
```

- [ ] **Step 4: Review exact scope and invariants**

Use `git diff --stat`, `git diff` and targeted `rg` searches. Confirm permanent deny operations,
Checker requirements, `shell=False`, strict models, legacy semantics and no committed runtime data.
Report any platform-level confirmation that Loop cannot remove. Do not commit or push.
