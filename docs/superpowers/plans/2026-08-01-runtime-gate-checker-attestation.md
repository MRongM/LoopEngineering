# Runtime Gate and Checker Attestation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking. This approved execution uses inline
> `superpowers:executing-plans` and does not dispatch subagents.

**Goal:** Make Core-controlled action, validation, result and Checker paths enforce the approved
Loop Contract and bind medium/high-risk completion to a fresh Checker attestation.

**Architecture:** Add one checked action-intent boundary in `RunStore`, retain specialized trusted
producers for validation and Git results, and make completion reconstruct Checker freshness from
contract hash, source fingerprints, evidence digests and ledger ordering. Keep Codex Goal identity
in the Adapter and document that arbitrary host-tool interception is outside tool-independent Core.

**Tech Stack:** Python 3.12+, strict Pydantic models, argparse CLI, append-only JSONL ledger, pytest,
Ruff, Markdown Skill playbooks.

## Global Constraints

- Protocol and package identity remain exactly `0.1.0`; the only mode remains `autonomous`.
- Add a failing test before every production behavior change and retain fresh RED/GREEN evidence.
- All subprocesses remain argv-based with `shell=False` and explicit timeouts where applicable.
- Core remains tool-independent; Codex Goal rules stay under `adapters/codex/`.
- Do not weaken Gate, Schema, tests or the authoritative `DONE` reconstruction.
- Do not create a branch, worktree, commit, push, PR, merge or deployment.
- Do not add dependencies or implement a scheduler, daemon or adversarial host sandbox.

---

## File Structure

| Path | Responsibility |
|---|---|
| `src/loop_engineering/models/run.py` | Strict Git result and Checker-attestation event payloads |
| `src/loop_engineering/ledger.py` | Checked action intent, specialized results, Checker binding and completion reconstruction |
| `src/loop_engineering/evidence.py` | Validation authorization/state/budget preflight |
| `src/loop_engineering/cli.py` | Request-bound intent/result and Checker CLI surfaces |
| `tests/test_ledger.py` | Action admission, reserved result and ledger-pairing behavior |
| `tests/test_evidence.py` | Validation preflight and Checker freshness behavior |
| `tests/test_cli.py` | Machine-facing CLI contract for checked requests and Checker IDs |
| `tests/test_git_automation.py` | Trusted Git result remains automatically recorded and authoritative |
| `tests/e2e/test_loop_dry_run.py` | End-to-end approved validation and completion flow |
| `adapters/codex/references/execution-loop.md` | Exact checked CLI usage and Checker identifier/freshness rules |
| `adapters/codex/references/goal-bridge.md` | Request-bound platform-state intent/result guidance |
| `PROTOCOL.md` | Normative Core entry and Checker-attestation invariants |
| `docs/adr/0001-require-manual-skill-invocation.md` | Remove stale Protocol 0.3 identity |
| `.planning/debug/runtime-gate-checker-binding.md` | Persistent diagnosis and fresh evidence |

### Task 1: Enforce checked action intents and typed result provenance

**Files:**

- Modify: `tests/test_ledger.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_git_automation.py`
- Modify: `src/loop_engineering/models/run.py`
- Modify: `src/loop_engineering/ledger.py`
- Modify: `src/loop_engineering/cli.py`

**Interfaces:**

- Consumes: `ActionRequest`, `GatePolicy`, `budget_status`, current Run authorization/state.
- Produces: `RunStore.record_action_intent(...)`, request-bound CLI `run intent`, reserved producer
  methods for Git/evidence results, and strict `GitResult` validation.

- [x] **Step 1: Write failing admission and forged-result tests**

Add tests proving that an unapproved action intent, an action outside `executing`, and an unplanned
request are rejected; an approved planned request is persisted under `payload.request`; generic
`run result` rejects reserved `git` and `evidence` payloads; and only the Git executor's result can
satisfy delivery reconstruction.

- [x] **Step 2: Run the focused tests and retain RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_ledger.py tests/test_cli.py tests/test_git_automation.py -q
```

Expected: new tests fail because generic intent accepts no `ActionRequest` and generic result accepts
reserved authoritative payloads.

- [x] **Step 3: Implement the minimal checked boundary**

Implement these responsibilities without a new abstraction layer:

```python
def record_action_intent(
    self,
    *,
    actor: str,
    summary: str,
    request: ActionRequest,
    payload: dict[str, Any],
) -> str: ...

def record_result(..., payload: dict[str, Any], ...) -> LoopEvent: ...
def record_git_result(..., result: GitResult) -> LoopEvent: ...
def record_evidence_result(..., evidence: EvidenceRecord) -> LoopEvent: ...
```

`record_action_intent` loads the persisted contract, requires current authorization, evaluates the
real Gate, enforces the appropriate state and available budget, then writes the exact serialized
request into the intent. Generic results reject reserved `git`/`evidence` keys but remain able to
close a real pending intent after a failure or authorization change.

- [x] **Step 4: Bind CLI arguments to the checked request**

Make `loop-engine run intent` require a request JSON path. Keep optional supplemental payload JSON;
do not allow it to replace the canonical request. Preserve machine-readable sanitized errors.

- [x] **Step 5: Run focused GREEN tests**

Run the Task 1 command and require all selected tests to pass.

### Task 2: Gate validation at its authoritative entry

**Files:**

- Modify: `tests/test_evidence.py`
- Modify: `tests/e2e/test_loop_dry_run.py`
- Modify: `src/loop_engineering/evidence.py`
- Modify: `src/loop_engineering/ledger.py`

**Interfaces:**

- Consumes: current contract authorization, `LoopStatus.VERIFYING`, `budget_status`.
- Produces: a fail-closed `ValidationRunner.run()` preflight and specialized evidence result.

- [x] **Step 1: Prepare existing positive validation fixtures**

Move positive test Runs through discovering, contract drafting, awaiting approval, one bound approval,
planning, executing and verifying before invoking the validator. This strengthens setup without
changing the tested validation outcomes.

- [x] **Step 2: Write failing negative validation tests**

Add tests proving that validation does not execute or write an intent before approval, in the wrong
state, with stale authorization, with a pending intent, or after authoritative budget exhaustion.

- [x] **Step 3: Run validation tests and retain RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_evidence.py tests/e2e/test_loop_dry_run.py -q
```

Expected: negative cases fail because `ValidationRunner.run()` currently begins execution without
checking authorization, state or budget.

- [x] **Step 4: Implement minimal validation preflight**

Before fingerprinting or recording an intent, require the supplied contract to equal the persisted
contract, current bound authorization to exist, Run state to be `verifying`, budget to be available,
and no unresolved intent to exist. Use the specialized evidence-result method so generic result JSON
cannot manufacture validator evidence.

- [x] **Step 5: Run focused GREEN tests**

Run the Task 2 command and require all selected tests to pass.

### Task 3: Bind Checker acceptance to current facts

**Files:**

- Modify: `tests/test_evidence.py`
- Modify: `tests/test_ledger.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_watch.py`
- Modify: `src/loop_engineering/models/run.py`
- Modify: `src/loop_engineering/ledger.py`
- Modify: `src/loop_engineering/cli.py`

**Interfaces:**

- Consumes: current contract hash, repository fingerprints, authoritative evidence records and
  append-only event sequence.
- Produces: strict `CheckerAttestation`, fresh `checker_id` CLI input and completion-time freshness
  evaluation.

- [x] **Step 1: Write failing Checker state, identity and freshness tests**

Add tests proving Checker recording requires current authorization and `checking`; reserved or reused
Checker IDs are rejected; the event binds contract SHA-256, source fingerprints and evidence digests;
and any later action/result or validation makes the prior `ACCEPT` unusable for medium/high `DONE`.

- [x] **Step 2: Run focused Checker tests and retain RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_ledger.py tests/test_evidence.py tests/test_cli.py tests/test_watch.py -q
```

Expected: new tests fail because the existing Checker event contains only verdict/findings and is
accepted solely by contract version.

- [x] **Step 3: Implement strict attestation and reconstruction**

Define a strict Checker payload with a fresh host-provided ID, current contract hash, repository
fingerprints, deterministic evidence-record digests, verdict and findings. Derive all fact bindings
inside Core. Record only in `checking`, reject reserved/reused IDs, and mark an attestation stale when
its bindings differ or a later intent/result exists.

- [x] **Step 4: Make completion consume only a current attestation**

The authoritative completion path must pass `CheckerVerdict.ACCEPT` to `DoneEvaluator` only when the
latest attestation validates against current facts. `run status` must expose whether the verdict is
current without treating an unverified actor string as identity proof.

- [x] **Step 5: Run focused GREEN tests**

Run the Task 3 command and require all selected tests to pass.

### Task 4: Align Protocol, Adapter and active documentation

**Files:**

- Modify: `PROTOCOL.md`
- Modify: `adapters/codex/references/execution-loop.md`
- Modify: `adapters/codex/references/goal-bridge.md`
- Modify: `tests/test_adapter_contract.py`
- Modify: `docs/adr/0001-require-manual-skill-invocation.md`
- Modify: `.planning/REQUIREMENTS.md`

**Interfaces:**

- Consumes: final checked CLI syntax and Checker-attestation fields.
- Produces: one consistent Protocol 0.1 description and regression assertions.

- [x] **Step 1: Add failing Adapter/document assertions**

Require request-bound action intent, reserved authoritative result producers, actual host Checker ID,
fresh fact binding and an explicit cooperative-host trust boundary. Include accepted/amended ADRs in
the active first-release residue check.

- [x] **Step 2: Run Adapter RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_adapter_contract.py -q
```

Expected: failure on missing new instructions and stale `Protocol 0.3` ADR text.

- [x] **Step 3: Update normative and routed documentation**

Describe what Core enforces, what only the Adapter can mediate, exact Checker freshness behavior and
the fact that Loop Engineering is not an adversarial sandbox for arbitrary host tools. Correct ADR
0001 to Protocol `0.1.0` and add traceable requirements without introducing a new protocol version.

- [x] **Step 4: Run Adapter GREEN**

Run the Task 4 command and require all Adapter tests to pass within the existing entry word budget.

### Task 5: Verify and close the inline debug workflow

**Files:**

- Modify: `.planning/debug/runtime-gate-checker-binding.md`
- Modify: `.planning/STATE.md`
- Verify: every changed production, test, protocol and Adapter file

**Interfaces:**

- Consumes: complete implementation and fresh command output.
- Produces: resolved diagnosis, synchronized project state and final evidence.

- [x] **Step 1: Run all quality gates**

```bash
.venv/bin/python -m pytest -q
.venv/bin/ruff check src tests adapters/codex/scripts
git diff --check
```

- [x] **Step 2: Rebuild and verify committed schemas**

Export schemas to a temporary directory, compare all three outputs byte-for-byte with `schemas/`, and
update checked-in schemas only if a public exported model changed.

- [x] **Step 3: Build release artifacts in an isolated output directory**

Run `uv build --out-dir <temporary-directory>` and verify wheel/sdist identity remains `0.1.0` and
the wheel exposes only `loop-engine`.

- [x] **Step 4: Inspect final scope and repository state**

Run `git diff --check`, `git status --short --untracked-files=all`, inspect the complete diff, and
confirm no runtime data, secrets, branch, commit or dependency change was introduced.

- [x] **Step 5: Resolve GSD evidence**

Fill Root Cause/Fix/Verification/Files Changed in the debug record, set it to `resolved`, and update
`.planning/STATE.md` with exact fresh counts and the absence of Git delivery.

## Plan Self-Review

- Spec coverage: Tasks 1–3 close Core-controlled action, validation, result and Checker paths;
  Task 4 aligns Protocol/Adapter/docs; Task 5 supplies fresh completion evidence.
- Trust boundary: arbitrary raw host-tool interception is explicitly documented rather than being
  incorrectly modeled inside tool-independent Core.
- Placeholder scan: no deferred implementation placeholder is part of an executable task.
- Type consistency: `ActionRequest`, `GitResult`, `CheckerAttestation` and `EvidenceRecord` remain
  strict Pydantic facts; completion consumes only Core-derived bindings.
- Scope: no dependency, release version, scheduler, daemon, deployment or Git-delivery behavior is
  added.
