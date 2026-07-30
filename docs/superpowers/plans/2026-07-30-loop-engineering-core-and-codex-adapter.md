# Loop Engineering Core and Codex Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a tool-independent Loop Engineering core, a recoverable CLI, and a Codex Skill adapter that let any Git project choose collaborative or autonomous execution under an approved, evidence-gated contract.

**Architecture:** A small Python package owns strict domain models, state transitions, append-only run storage, evidence capture, safety policy, and Git automation. Codex remains the agentic driver: its Skill invokes the CLI before and after real actions, dispatches an independent Checker when required, and stops only at protocol terminal states or human gates. Target projects install the CLI and link the Skill; they do not copy Core rules.

**Tech Stack:** Python 3.12+, uv, Pydantic 2.12+, PyYAML 6.0+, filelock 3.16+, pytest 9+, Ruff, Git CLI, GitHub CLI.

**Scope Check:** The Core, CLI and Codex Skill are not independently useful products:
the Skill depends on the CLI, the CLI depends on the state/evidence Core, and Git
delivery depends on the same contract and ledger. They remain one plan, split into
reviewable vertical tasks that each leave the package testable.

## Global Constraints

- Initial protocol and package version is exactly `0.1.0`.
- Python floor is exactly `>=3.12`; code must also run on the available Python 3.14 environment.
- The package name is `loop-engineering`; the import package is `loop_engineering`; the CLI is `loop-engineering`.
- `collaborative` and `autonomous` are the only control modes. Mode is never inherited; absence means `collaborative`.
- First release accepts only user-initiated tasks. Do not add discovery, scheduling, queues, a daemon, or an Agent SDK.
- Never implement force-push, history rewriting, `git reset --hard`, automatic merge, automatic deployment, or implicit production access.
- Every subprocess call uses an argument vector with `shell=False`; every filesystem target is resolved and boundary-checked first.
- Runtime records must not contain secrets, access tokens, full model reasoning, or unredacted sensitive responses.
- `DONE` requires fresh evidence for every acceptance criterion; medium/high risk requires Checker `ACCEPT`; high risk also requires human acceptance.
- Runtime data lives under `<project>/.loop-runs/` and is never committed by default.
- All implementation tasks use TDD and end in an independently reviewable commit. Commit steps are executable only after the implementation Loop Contract explicitly authorizes Git operations.
- The approved design remains authoritative: `docs/superpowers/specs/2026-07-30-loop-engineering-protocol-design.md`.

---

## File and Responsibility Map

| Path | Responsibility |
|---|---|
| `pyproject.toml` | Package metadata, dependencies, CLI entry point, pytest and Ruff configuration |
| `AGENTS.md` | Repository-local engineering and safety constraints |
| `PROTOCOL.md` | Normative, tool-independent protocol extracted from the approved design |
| `README.md` | Installation, quick start, current limitations and links |
| `src/loop_engineering/models/contract.py` | Strict contract, permission, validation and Git policy models |
| `src/loop_engineering/models/run.py` | State, event, budget usage and Checker verdict models |
| `src/loop_engineering/models/evidence.py` | Evidence and completion-evaluation models |
| `src/loop_engineering/contract.py` | YAML loading, contract validation and JSON Schema export |
| `src/loop_engineering/state_machine.py` | Legal transitions and budget evaluation |
| `src/loop_engineering/redaction.py` | Recursive secret and sensitive-value redaction |
| `src/loop_engineering/ledger.py` | Atomic snapshots, append-only events and interrupted-action reconciliation |
| `src/loop_engineering/evidence.py` | Safe command execution, output capture, fingerprints and DONE evaluation |
| `src/loop_engineering/paths.py` | Shared normalized relative-path boundary checks |
| `src/loop_engineering/policy.py` | Scope/permission decisions and human-gate rendering |
| `src/loop_engineering/git_automation.py` | Exact-target worktree, commit, push and PR operations |
| `src/loop_engineering/project.py` | Target-project configuration and initialization |
| `src/loop_engineering/cli.py` | Thin argparse command surface over Core interfaces |
| `schemas/*.schema.json` | Versioned generated schemas for contract, state and event records |
| `templates/contract.yaml` | Valid starter contract with safe defaults |
| `templates/project.yaml` | Valid project integration configuration |
| `templates/final-report.md` | Required final report structure |
| `adapters/codex/SKILL.md` | Codex workflow, gates, Maker/Checker protocol and stop rules |
| `docs/adoption.md` | Manual use plus CLI/Skill onboarding for other projects |
| `tests/` | Unit, integration, security, static adapter and end-to-end tests |

## Stable Public Interfaces

The following names are fixed for all tasks in this plan:

```python
load_contract(path: Path) -> LoopContract
export_schemas(output_dir: Path) -> tuple[Path, Path, Path]
transition(state: LoopState, target: LoopStatus, reason: str, *, now: datetime | None = None) -> LoopState
budget_status(contract: LoopContract, state: LoopState, *, now: datetime | None = None) -> BudgetStatus
RunStore.create(project_root: Path, contract: LoopContract) -> RunStore
RunStore.open(run_dir: Path) -> RunStore
RunStore.replace_contract(contract: LoopContract, *, actor: str, summary: str) -> LoopState
RunStore.complete(*, actor: str, reason: str) -> LoopState
ValidationRunner.run(command_id: str) -> EvidenceRecord
evaluate_scope(contract: LoopContract) -> ScopeEvaluation
DoneEvaluator.evaluate(context: CompletionContext) -> CompletionEvaluation
GatePolicy.evaluate(request: ActionRequest) -> GateDecision
GitAutomation.prepare_worktree() -> Path
GitAutomation.commit(paths: Sequence[str], message: str) -> str
GitAutomation.push() -> None
GitAutomation.create_pr(title: str, body: str) -> str
initialize_project(root: Path, *, update_gitignore: bool = False) -> ProjectConfig
main(argv: Sequence[str] | None = None) -> int
```

### Task 1: Package Foundation and Repository Rules

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `AGENTS.md`
- Create: `README.md`
- Create: `src/loop_engineering/__init__.py`
- Create: `src/loop_engineering/__main__.py`
- Create: `tests/__init__.py`
- Create: `tests/test_package.py`

**Interfaces:**
- Produces: `loop_engineering.__version__: str == "0.1.0"`
- Produces: console entry point `loop-engineering = loop_engineering.cli:main`; `cli.py` is created in Task 8.

- [ ] **Step 1: Write the failing package metadata test**

```python
# tests/test_package.py
from loop_engineering import __version__


def test_package_version_matches_protocol_version() -> None:
    assert __version__ == "0.1.0"
```

- [ ] **Step 2: Run the test and verify the package does not exist**

Run: `uv run pytest "tests/test_package.py" -q`

Expected: FAIL during collection with `ModuleNotFoundError: No module named 'loop_engineering'`.

- [ ] **Step 3: Add the minimal package and tool configuration**

```toml
# pyproject.toml
[project]
name = "loop-engineering"
version = "0.1.0"
description = "Evidence-gated loops for coding agents"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
  "filelock>=3.16,<4",
  "pydantic>=2.12.5,<3",
  "PyYAML>=6.0.3,<7",
]

[project.scripts]
loop-engineering = "loop_engineering.cli:main"

[dependency-groups]
dev = [
  "pytest>=9.0.3,<10",
  "ruff>=0.14,<1",
]

[build-system]
requires = ["hatchling>=1.27,<2"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/loop_engineering"]

[tool.pytest.ini_options]
addopts = "-ra"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py312"
```

```python
# src/loop_engineering/__init__.py
__version__ = "0.1.0"
```

```python
# tests/__init__.py
```

```python
# src/loop_engineering/__main__.py
from loop_engineering.cli import main

raise SystemExit(main())
```

```gitignore
# .gitignore
.venv/
__pycache__/
.pytest_cache/
.ruff_cache/
dist/
*.egg-info/
.loop-runs/
```

```markdown
<!-- AGENTS.md -->
# LoopEngineering repository instructions

- Read `PROTOCOL.md` and the approved design before changing behavior.
- Use Python 3.12+, strict Pydantic models, argv subprocesses and `shell=False`.
- Add a failing test before production code and preserve fresh command evidence.
- Never weaken gates, tests or schemas to obtain a passing result.
- Never add automatic merge, deployment, force-push, history rewrite or production access.
- Do not commit runtime data, secrets, tokens or complete model reasoning.
- Keep Core tool-independent; Codex-specific behavior belongs in `adapters/codex/`.
```

```markdown
<!-- README.md -->
# Loop Engineering

Evidence-gated, recoverable execution loops for coding agents.

The implementation is built from the approved design in
`docs/superpowers/specs/2026-07-30-loop-engineering-protocol-design.md`.
```

- [ ] **Step 4: Synchronize dependencies and run focused checks**

Run: `uv sync --dev`

Expected: dependencies resolve and `uv.lock` is created.

Run: `uv run pytest "tests/test_package.py" -q`

Expected: `1 passed`.

Run: `uv run ruff check "src" "tests"`

Expected: `All checks passed!`

- [ ] **Step 5: Commit the independently working package foundation**

```bash
git add ".gitignore" "AGENTS.md" "README.md" "pyproject.toml" "uv.lock" "src/loop_engineering/__init__.py" "src/loop_engineering/__main__.py" "tests/__init__.py" "tests/test_package.py"
git commit -m "chore: bootstrap Loop Engineering package"
```

### Task 2: Strict Loop Contract and Schema Export

**Files:**
- Create: `src/loop_engineering/models/__init__.py`
- Create: `src/loop_engineering/models/contract.py`
- Create: `src/loop_engineering/paths.py`
- Create: `src/loop_engineering/contract.py`
- Create: `tests/factories.py`
- Create: `tests/test_contract.py`
- Create: `templates/contract.yaml`
- Create: `schemas/loop-contract.schema.json`

**Interfaces:**
- Produces: `PROTOCOL_VERSION = "0.1.0"`
- Produces: `LoopContract`, `RepositoryTarget`, `ValidationCommand`, `PermissionPolicy`, `GitPolicy`, `Budget`, `AcceptanceCriterion`
- Produces: normalized, platform-neutral relative-path boundary helpers
- Produces: `load_contract(path: Path) -> LoopContract`
- Produces: `write_contract_schema(path: Path) -> Path`

- [ ] **Step 1: Write contract validation tests**

```python
# tests/factories.py
from pathlib import Path
from typing import Any


def valid_contract_data() -> dict[str, Any]:
    return {
        "loop_id": "loop-example-001",
        "contract_version": 1,
        "protocol_version": "0.1.0",
        "objective": "Add one verified example behavior",
        "mode": "collaborative",
        "repositories": [
            {
                "id": "target",
                "path": str(Path.cwd()),
                "base_branch": "master",
                "allowed_paths": ["src/", "tests/"],
                "depends_on": [],
            }
        ],
        "in_scope": ["Implement the approved behavior"],
        "out_of_scope": ["Deployment"],
        "acceptance_criteria": [
            {
                "id": "AC-1",
                "description": "Focused tests pass",
                "required_evidence": ["VAL-1"],
            }
        ],
        "validation_commands": [
            {
                "id": "VAL-1",
                "repository_id": "target",
                "cwd": ".",
                "argv": ["python", "-m", "pytest", "tests/test_example.py", "-q"],
                "criterion_ids": ["AC-1"],
                "timeout_seconds": 600,
            }
        ],
        "risk_level": "low",
        "permissions": {
            "network": False,
            "dependency_changes": False,
            "database_changes": False,
            "production_access": False,
            "sensitive_data": False,
        },
        "git_policy": {
            "targets": [
                {
                    "repository_id": "target",
                    "create_worktree": False,
                    "commit": False,
                    "push": False,
                    "create_pr": False,
                }
            ],
            "force_push": False,
            "history_rewrite": False,
            "merge": False,
            "deploy": False,
        },
        "budget": {
            "max_iterations": 3,
            "max_minutes": 30,
            "max_checker_revisions": 0,
            "max_same_strategy_retries": 1,
        },
        "human_gates": ["contract_approval", "final_acceptance"],
        "assumptions": ["The repository uses Python"],
        "stop_conditions": ["done", "blocked", "budget_exhausted"],
    }
```

```python
# tests/test_contract.py
import json
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from loop_engineering.contract import load_contract, write_contract_schema
from loop_engineering.models.contract import LoopContract
from tests.factories import valid_contract_data


def test_valid_contract_is_strict_and_defaults_to_collaborative(tmp_path: Path) -> None:
    data = valid_contract_data()
    data.pop("mode")
    path = tmp_path / "contract.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    contract = load_contract(path)

    assert contract.mode.value == "collaborative"
    assert contract.protocol_version == "0.1.0"


def test_contract_rejects_unknown_fields() -> None:
    data = valid_contract_data()
    data["unapproved"] = True

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        LoopContract.model_validate(data)


@pytest.mark.parametrize("field", ["force_push", "history_rewrite", "merge", "deploy"])
def test_contract_can_never_enable_forbidden_git_actions(field: str) -> None:
    data = valid_contract_data()
    data["git_policy"][field] = True

    with pytest.raises(ValidationError):
        LoopContract.model_validate(data)


def test_push_requires_exact_branch_and_remote() -> None:
    data = valid_contract_data()
    data["git_policy"]["targets"][0]["push"] = True

    with pytest.raises(ValidationError, match="branch and remote"):
        LoopContract.model_validate(data)


@pytest.mark.parametrize(
    ("field", "value"),
    [("branch", "--force"), ("remote", "--force"), ("pr_target", "main:admin")],
)
def test_git_targets_reject_option_like_or_refspec_values(
    field: str,
    value: str,
) -> None:
    data = valid_contract_data()
    data["git_policy"]["targets"][0].update(
        {
            "commit": True,
            "branch": "feat/safe",
            "worktree_path": "worktree",
        }
    )
    data["git_policy"]["targets"][0][field] = value
    with pytest.raises(ValidationError):
        LoopContract.model_validate(data)


def test_pr_requires_push_and_exact_target_branch() -> None:
    data = valid_contract_data()
    data["git_policy"]["targets"][0].update(
        {"create_pr": True, "branch": "feat/example", "remote": "origin"}
    )

    with pytest.raises(ValidationError, match="create_pr requires push and pr_target"):
        LoopContract.model_validate(data)


def test_cross_repository_dependency_graph_must_be_acyclic() -> None:
    data = valid_contract_data()
    first = data["repositories"][0]
    first["depends_on"] = ["shared"]
    data["repositories"].append(
        {
            "id": "shared",
            "path": str(Path.cwd()),
            "base_branch": "master",
            "allowed_paths": ["src/"],
            "depends_on": ["target"],
        }
    )

    with pytest.raises(ValidationError, match="contains a cycle"):
        LoopContract.model_validate(data)


def test_network_validation_requires_network_permission() -> None:
    data = valid_contract_data()
    data["validation_commands"][0]["requires_network"] = True
    with pytest.raises(ValidationError, match="requires unapproved network"):
        LoopContract.model_validate(data)


def test_collaborative_contract_requires_final_acceptance_gate() -> None:
    data = valid_contract_data()
    data["human_gates"] = ["contract_approval"]
    with pytest.raises(ValidationError, match="requires final_acceptance"):
        LoopContract.model_validate(data)


def test_every_contract_requires_one_contract_approval_gate() -> None:
    data = valid_contract_data()
    data["mode"] = "autonomous"
    data["human_gates"] = ["final_acceptance"]
    with pytest.raises(ValidationError, match="requires contract_approval"):
        LoopContract.model_validate(data)


def test_validation_command_rejects_inline_secret_flags() -> None:
    data = valid_contract_data()
    data["validation_commands"][0]["argv"] = ["curl", "--token", "secret"]
    with pytest.raises(ValidationError, match="inline secret flags"):
        LoopContract.model_validate(data)


@pytest.mark.parametrize(
    "boundary",
    ["../src", "/system", "C:\\system", "src/*.py", "$PROJECT_ROOT/src"],
)
def test_contract_rejects_unsafe_allowed_path_boundaries(boundary: str) -> None:
    data = valid_contract_data()
    data["repositories"][0]["allowed_paths"] = [boundary]
    with pytest.raises(ValidationError, match="unsafe relative path"):
        LoopContract.model_validate(data)


def test_schema_export_is_deterministic(tmp_path: Path) -> None:
    first = write_contract_schema(tmp_path / "first.json")
    second = write_contract_schema(tmp_path / "second.json")

    assert json.loads(first.read_text()) == json.loads(second.read_text())
    assert json.loads(first.read_text())["title"] == "LoopContract"
```

- [ ] **Step 2: Run the focused tests and verify missing contract modules**

Run: `uv run pytest "tests/test_contract.py" -q`

Expected: FAIL during collection because `loop_engineering.contract` does not exist.

- [ ] **Step 3: Implement shared path boundaries and strict contract models**

```python
# src/loop_engineering/paths.py
from pathlib import PurePosixPath


def normalized_relative(value: str) -> PurePosixPath:
    path = PurePosixPath(value.replace("\\", "/"))
    has_drive = bool(path.parts and path.parts[0].endswith(":"))
    unresolved = any(character in value for character in "*?[]{}$%~")
    if (
        path.is_absolute()
        or has_drive
        or ".." in path.parts
        or not path.parts
        or unresolved
    ):
        raise ValueError(f"unsafe relative path: {value}")
    return path


def normalized_allowed_boundary(value: str) -> PurePosixPath:
    normalized = value.replace("\\", "/")
    if normalized in {".", "./"}:
        return PurePosixPath(".")
    return normalized_relative(normalized.rstrip("/"))


def is_allowed_path(value: str, allowed_paths: list[str]) -> bool:
    candidate = normalized_relative(value)
    for allowed in allowed_paths:
        boundary = normalized_allowed_boundary(allowed)
        if boundary == PurePosixPath("."):
            return True
        if candidate == boundary or candidate.is_relative_to(boundary):
            return True
    return False
```

```python
# src/loop_engineering/models/contract.py
from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from loop_engineering.paths import normalized_allowed_boundary

PROTOCOL_VERSION = "0.1.0"


def _validate_git_ref(value: str) -> str:
    forbidden = ("..", "@{", "\\", "~", "^", ":", "?", "*", "[")
    if (
        not value
        or value.startswith(("-", ".", "/"))
        or value.endswith(("/", ".", ".lock"))
        or "//" in value
        or any(character.isspace() for character in value)
        or any(token in value for token in forbidden)
    ):
        raise ValueError(f"unsafe Git ref: {value}")
    return value


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ControlMode(StrEnum):
    COLLABORATIVE = "collaborative"
    AUTONOMOUS = "autonomous"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RepositoryTarget(StrictModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]*$")
    path: Path
    base_branch: str = Field(min_length=1)
    allowed_paths: list[str] = Field(min_length=1)
    depends_on: list[str] = Field(default_factory=list)

    @field_validator("base_branch")
    @classmethod
    def validate_base_branch(cls, value: str) -> str:
        return _validate_git_ref(value)

    @field_validator("allowed_paths")
    @classmethod
    def validate_allowed_paths(cls, values: list[str]) -> list[str]:
        for value in values:
            normalized_allowed_boundary(value)
        return values


class AcceptanceCriterion(StrictModel):
    id: str = Field(pattern=r"^AC-[1-9][0-9]*$")
    description: str = Field(min_length=1)
    required_evidence: list[str] = Field(min_length=1)


class ValidationCommand(StrictModel):
    id: str = Field(pattern=r"^VAL-[1-9][0-9]*$")
    repository_id: str
    cwd: str
    argv: list[str] = Field(min_length=1)
    criterion_ids: list[str] = Field(min_length=1)
    timeout_seconds: int = Field(default=600, ge=1, le=3600)
    requires_network: bool = False

    @field_validator("argv")
    @classmethod
    def reject_inline_secret_arguments(cls, argv: list[str]) -> list[str]:
        secret_flags = {"--token", "--password", "--api-key", "--api_key", "authorization"}
        lowered = {argument.lower().split("=", 1)[0] for argument in argv}
        if lowered & secret_flags:
            raise ValueError("validation argv must not contain inline secret flags")
        return argv


class PermissionPolicy(StrictModel):
    network: bool = False
    dependency_changes: bool = False
    database_changes: bool = False
    production_access: bool = False
    sensitive_data: bool = False


class AuthorizedOperation(StrictModel):
    kind: str = Field(min_length=1)
    repository_id: str | None = None
    target: str = Field(min_length=1)


class GitTarget(StrictModel):
    repository_id: str
    create_worktree: bool = False
    commit: bool = False
    push: bool = False
    create_pr: bool = False
    branch: str | None = None
    remote: str | None = Field(default=None, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
    pr_target: str | None = None
    worktree_path: Path | None = None

    @field_validator("branch", "pr_target")
    @classmethod
    def validate_optional_refs(cls, value: str | None) -> str | None:
        return _validate_git_ref(value) if value is not None else None

    @model_validator(mode="after")
    def require_exact_delivery_targets(self) -> "GitTarget":
        if self.commit and not (self.branch and self.worktree_path):
            raise ValueError("commit requires branch and worktree_path")
        if self.push and not (self.branch and self.remote):
            raise ValueError("push requires branch and remote")
        if self.create_pr and not (self.push and self.pr_target):
            raise ValueError("create_pr requires push and pr_target")
        if self.create_worktree and not (self.branch and self.worktree_path):
            raise ValueError("create_worktree requires branch and worktree_path")
        return self


class GitPolicy(StrictModel):
    targets: list[GitTarget] = Field(min_length=1)
    force_push: Literal[False] = False
    history_rewrite: Literal[False] = False
    merge: Literal[False] = False
    deploy: Literal[False] = False


class Budget(StrictModel):
    max_iterations: int = Field(ge=1, le=12)
    max_minutes: int = Field(ge=1, le=240)
    max_checker_revisions: int = Field(ge=0, le=3)
    max_same_strategy_retries: Literal[1] = 1


HumanGate = Literal[
    "contract_approval",
    "design_approval",
    "plan_approval",
    "dangerous_action",
    "final_acceptance",
]


class LoopContract(StrictModel):
    loop_id: str = Field(pattern=r"^loop-[a-z0-9][a-z0-9-]*$")
    parent_loop_id: str | None = None
    contract_version: int = Field(ge=1)
    protocol_version: Literal["0.1.0"] = PROTOCOL_VERSION
    objective: str = Field(min_length=1)
    mode: ControlMode = ControlMode.COLLABORATIVE
    repositories: list[RepositoryTarget] = Field(min_length=1)
    in_scope: list[str] = Field(min_length=1)
    out_of_scope: list[str] = Field(min_length=1)
    acceptance_criteria: list[AcceptanceCriterion] = Field(min_length=1)
    validation_commands: list[ValidationCommand] = Field(min_length=1)
    risk_level: RiskLevel
    permissions: PermissionPolicy
    authorized_operations: list[AuthorizedOperation] = Field(default_factory=list)
    git_policy: GitPolicy
    budget: Budget
    human_gates: list[HumanGate] = Field(min_length=1)
    assumptions: list[str] = Field(default_factory=list)
    stop_conditions: list[Literal["done", "blocked", "budget_exhausted"]] = Field(
        min_length=3,
        max_length=3,
    )

    @model_validator(mode="after")
    def validate_references_and_risk_budget(self) -> "LoopContract":
        repository_ids = {repository.id for repository in self.repositories}
        criterion_ids = {criterion.id for criterion in self.acceptance_criteria}
        evidence_ids = {command.id for command in self.validation_commands}
        if len(repository_ids) != len(self.repositories):
            raise ValueError("repository ids must be unique")
        if len(criterion_ids) != len(self.acceptance_criteria):
            raise ValueError("acceptance criterion ids must be unique")
        if len(evidence_ids) != len(self.validation_commands):
            raise ValueError("validation command ids must be unique")
        for repository in self.repositories:
            unknown = set(repository.depends_on) - repository_ids
            if unknown or repository.id in repository.depends_on:
                raise ValueError(f"invalid repository dependency for {repository.id}")
        dependencies = {
            repository.id: set(repository.depends_on) for repository in self.repositories
        }

        def visit(repository_id: str, path: set[str]) -> None:
            if repository_id in path:
                raise ValueError("repository dependency graph contains a cycle")
            for dependency in dependencies[repository_id]:
                visit(dependency, path | {repository_id})

        for repository_id in repository_ids:
            visit(repository_id, set())
        git_repository_ids = [target.repository_id for target in self.git_policy.targets]
        if len(git_repository_ids) != len(set(git_repository_ids)):
            raise ValueError("Git target repository ids must be unique")
        if not set(git_repository_ids) <= repository_ids:
            raise ValueError("Git target references unknown repository")
        for command in self.validation_commands:
            if command.repository_id not in repository_ids:
                raise ValueError(f"unknown repository id: {command.repository_id}")
            if not set(command.criterion_ids) <= criterion_ids:
                raise ValueError(f"unknown criterion id in {command.id}")
            if command.requires_network and not self.permissions.network:
                raise ValueError(f"{command.id} requires unapproved network")
        for criterion in self.acceptance_criteria:
            if not set(criterion.required_evidence) <= evidence_ids:
                raise ValueError(f"unknown evidence id in {criterion.id}")
        if set(self.stop_conditions) != {"done", "blocked", "budget_exhausted"}:
            raise ValueError("stop_conditions must contain all three terminal states")
        if "contract_approval" not in self.human_gates:
            raise ValueError("every contract requires contract_approval")
        if len(self.human_gates) != len(set(self.human_gates)):
            raise ValueError("human_gates must be unique")
        requires_final_gate = (
            self.mode is ControlMode.COLLABORATIVE or self.risk_level is RiskLevel.HIGH
        )
        if requires_final_gate and "final_acceptance" not in self.human_gates:
            raise ValueError("collaborative/high-risk contract requires final_acceptance")
        expected_revisions = {"low": 0, "medium": 2, "high": 3}[self.risk_level.value]
        if self.budget.max_checker_revisions > expected_revisions:
            raise ValueError("checker revision budget exceeds risk default")
        return self
```

```python
# src/loop_engineering/models/__init__.py
from loop_engineering.models.contract import LoopContract

__all__ = ["LoopContract"]
```

- [ ] **Step 4: Implement safe YAML loading and deterministic schema export**

```python
# src/loop_engineering/contract.py
import json
from pathlib import Path

import yaml

from loop_engineering.models.contract import LoopContract


def load_contract(path: Path) -> LoopContract:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("contract root must be a mapping")
    base = path.resolve().parent
    for repository in raw.get("repositories", []):
        repository_path = Path(repository["path"])
        if not repository_path.is_absolute():
            repository["path"] = str((base / repository_path).resolve())
    for target in raw.get("git_policy", {}).get("targets", []):
        if target.get("worktree_path"):
            worktree_path = Path(target["worktree_path"])
            if not worktree_path.is_absolute():
                target["worktree_path"] = str((base / worktree_path).resolve())
    return LoopContract.model_validate(raw)


def write_contract_schema(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    schema = LoopContract.model_json_schema()
    path.write_text(
        json.dumps(schema, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path
```

Create `templates/contract.yaml` with exactly:

```yaml
loop_id: loop-example-001
contract_version: 1
protocol_version: 0.1.0
objective: Add one verified example behavior
mode: collaborative
repositories:
  - id: target
    path: .
    base_branch: master
    allowed_paths:
      - src/
      - tests/
    depends_on: []
in_scope:
  - Implement the approved behavior
out_of_scope:
  - Deployment
acceptance_criteria:
  - id: AC-1
    description: Focused tests pass
    required_evidence:
      - VAL-1
validation_commands:
  - id: VAL-1
    repository_id: target
    cwd: .
    argv:
      - python
      - -m
      - pytest
      - tests/test_example.py
      - -q
    criterion_ids:
      - AC-1
    timeout_seconds: 600
    requires_network: false
risk_level: low
permissions:
  network: false
  dependency_changes: false
  database_changes: false
  production_access: false
  sensitive_data: false
git_policy:
  targets:
    - repository_id: target
      create_worktree: false
      commit: false
      push: false
      create_pr: false
  force_push: false
  history_rewrite: false
  merge: false
  deploy: false
budget:
  max_iterations: 3
  max_minutes: 30
  max_checker_revisions: 0
  max_same_strategy_retries: 1
human_gates:
  - contract_approval
  - final_acceptance
assumptions:
  - The repository uses Python
stop_conditions:
  - done
  - blocked
  - budget_exhausted
```

`load_contract` resolves the `.` repository path relative to the copied contract.
Generate `schemas/loop-contract.schema.json` with:

Run: `uv run python -c "from pathlib import Path; from loop_engineering.contract import write_contract_schema; write_contract_schema(Path('schemas/loop-contract.schema.json'))"`

Expected: the JSON file is created and parses successfully.

- [ ] **Step 5: Run contract tests and quality checks**

Run: `uv run pytest "tests/test_contract.py" -q`

Expected: all contract tests pass.

Run: `uv run ruff check "src/loop_engineering/models" "src/loop_engineering/paths.py" "src/loop_engineering/contract.py" "tests/test_contract.py" "tests/factories.py"`

Expected: `All checks passed!`

- [ ] **Step 6: Commit the contract slice**

```bash
git add "src/loop_engineering/models" "src/loop_engineering/paths.py" "src/loop_engineering/contract.py" "tests/factories.py" "tests/test_contract.py" "templates/contract.yaml" "schemas/loop-contract.schema.json"
git commit -m "feat: define strict Loop Contract"
```

### Task 3: State Machine and Budget Enforcement

**Files:**
- Create: `src/loop_engineering/models/run.py`
- Create: `src/loop_engineering/state_machine.py`
- Create: `tests/test_state_machine.py`
- Create: `schemas/loop-state.schema.json`
- Create: `schemas/loop-event.schema.json`
- Modify: `src/loop_engineering/contract.py`

**Interfaces:**
- Consumes: `LoopContract.budget`
- Produces: `LoopStatus`, `LoopState`, `BudgetStatus`, `CheckerVerdict`
- Produces: `transition(...)` and `budget_status(...)`
- Changes: `export_schemas(output_dir)` replaces the Task 2 one-schema helper while retaining `write_contract_schema`.

- [ ] **Step 1: Write legal-transition, terminal and budget tests**

```python
# tests/test_state_machine.py
from datetime import datetime, timedelta, timezone

import pytest

from loop_engineering.models.contract import LoopContract
from loop_engineering.models.run import LoopState, LoopStatus
from loop_engineering.state_machine import (
    BudgetCondition,
    IllegalTransition,
    budget_status,
    transition,
)
from tests.factories import valid_contract_data


def state(status: LoopStatus = LoopStatus.INTAKE) -> LoopState:
    now = datetime(2026, 7, 30, tzinfo=timezone.utc)
    return LoopState(
        loop_id="loop-example-001",
        contract_version=1,
        status=status,
        started_at=now,
        updated_at=now,
    )


def test_contract_is_discovered_before_approval() -> None:
    current = transition(state(), LoopStatus.DISCOVERING, "inspect")
    current = transition(current, LoopStatus.CONTRACT_DRAFTING, "draft")
    current = transition(current, LoopStatus.AWAITING_APPROVAL, "present")
    assert current.status is LoopStatus.AWAITING_APPROVAL


def test_execution_entry_increments_iteration() -> None:
    current = state(LoopStatus.PLANNING)
    updated = transition(current, LoopStatus.EXECUTING, "start increment")
    assert updated.iterations_used == 1


@pytest.mark.parametrize(
    "terminal",
    [LoopStatus.DONE, LoopStatus.BLOCKED, LoopStatus.BUDGET_EXHAUSTED],
)
def test_terminal_states_cannot_reopen(terminal: LoopStatus) -> None:
    with pytest.raises(IllegalTransition, match="terminal"):
        transition(state(terminal), LoopStatus.EXECUTING, "retry")


def test_budget_reports_time_and_iteration_exhaustion() -> None:
    contract = LoopContract.model_validate(valid_contract_data())
    current = state(LoopStatus.DECIDING).model_copy(
        update={
            "iterations_used": contract.budget.max_iterations,
            "updated_at": datetime(2026, 7, 30, 1, tzinfo=timezone.utc),
        }
    )
    now = current.started_at + timedelta(minutes=contract.budget.max_minutes)
    result = budget_status(contract, current, now=now)
    assert result.condition is BudgetCondition.EXHAUSTED
    assert set(result.reasons) == {"iteration limit reached", "time limit reached"}


def test_same_strategy_retry_limit_is_one() -> None:
    current = state(LoopStatus.DECIDING).model_copy(
        update={"same_strategy_retries": 1}
    )
    contract = LoopContract.model_validate(valid_contract_data())
    result = budget_status(contract, current, now=current.started_at)
    assert result.condition is BudgetCondition.DIAGNOSIS_REQUIRED
    assert result.reasons == ["same strategy retry limit reached"]


def test_checker_revision_limit_stops_before_an_extra_revision() -> None:
    data = valid_contract_data()
    data["mode"] = "autonomous"
    data["risk_level"] = "medium"
    data["human_gates"] = ["contract_approval"]
    data["budget"]["max_checker_revisions"] = 2
    contract = LoopContract.model_validate(data)
    current = state(LoopStatus.DECIDING).model_copy(
        update={"checker_revisions_used": 2}
    )

    result = budget_status(contract, current, now=current.started_at)

    assert result.condition is BudgetCondition.EXHAUSTED
    assert result.reasons == ["checker revision limit reached"]


def test_two_no_progress_cycles_require_diagnosis_without_terminal_exhaustion() -> None:
    current = state(LoopStatus.DECIDING).model_copy(update={"no_progress_cycles": 2})
    contract = LoopContract.model_validate(valid_contract_data())
    result = budget_status(contract, current, now=current.started_at)
    assert result.condition is BudgetCondition.DIAGNOSIS_REQUIRED
    assert result.reasons == ["two consecutive cycles made no progress"]


def test_paused_run_can_enter_contract_revision_flow() -> None:
    current = state(LoopStatus.PAUSED)
    current = transition(current, LoopStatus.CONTRACT_DRAFTING, "revise scope")
    current = transition(current, LoopStatus.AWAITING_APPROVAL, "present revision")
    assert current.status is LoopStatus.AWAITING_APPROVAL
```

- [ ] **Step 2: Run tests and verify state modules are missing**

Run: `uv run pytest "tests/test_state_machine.py" -q`

Expected: FAIL during collection because `loop_engineering.models.run` does not exist.

- [ ] **Step 3: Implement run models and legal transitions**

```python
# src/loop_engineering/models/run.py
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import Field

from loop_engineering.models.contract import StrictModel


class LoopStatus(StrEnum):
    INTAKE = "intake"
    DISCOVERING = "discovering"
    CONTRACT_DRAFTING = "contract_drafting"
    AWAITING_APPROVAL = "awaiting_approval"
    DESIGNING = "designing"
    PLANNING = "planning"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    CHECKING = "checking"
    DECIDING = "deciding"
    PAUSED = "paused"
    DONE = "done"
    BLOCKED = "blocked"
    BUDGET_EXHAUSTED = "budget_exhausted"


class CheckerVerdict(StrEnum):
    ACCEPT = "accept"
    REVISE = "revise"
    BLOCK = "block"


class LoopState(StrictModel):
    loop_id: str
    contract_version: int = Field(ge=1)
    status: LoopStatus
    iterations_used: int = Field(default=0, ge=0)
    checker_revisions_used: int = Field(default=0, ge=0)
    same_strategy_retries: int = Field(default=0, ge=0)
    no_progress_cycles: int = Field(default=0, ge=0)
    last_event_sequence: int = Field(default=0, ge=0)
    started_at: datetime
    updated_at: datetime
    pause_reason: str | None = None


class EventKind(StrEnum):
    TRANSITION = "transition"
    INTENT = "intent"
    RESULT = "result"
    APPROVAL = "approval"
    EVIDENCE = "evidence"
    CHECKER = "checker"


class LoopEvent(StrictModel):
    sequence: int = Field(ge=1)
    event_id: str
    loop_id: str
    contract_version: int
    timestamp: datetime
    actor: str
    kind: EventKind
    action_id: str | None = None
    from_status: LoopStatus | None = None
    to_status: LoopStatus | None = None
    summary: str
    evidence_refs: list[str] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)
```

```python
# src/loop_engineering/state_machine.py
from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel

from loop_engineering.models.contract import LoopContract
from loop_engineering.models.run import LoopState, LoopStatus

TERMINAL = {
    LoopStatus.DONE,
    LoopStatus.BLOCKED,
    LoopStatus.BUDGET_EXHAUSTED,
}

ALLOWED: dict[LoopStatus, set[LoopStatus]] = {
    LoopStatus.INTAKE: {LoopStatus.DISCOVERING},
    LoopStatus.DISCOVERING: {LoopStatus.CONTRACT_DRAFTING, LoopStatus.BLOCKED},
    LoopStatus.CONTRACT_DRAFTING: {LoopStatus.AWAITING_APPROVAL},
    LoopStatus.AWAITING_APPROVAL: {
        LoopStatus.DESIGNING,
        LoopStatus.PLANNING,
        LoopStatus.PAUSED,
        LoopStatus.BLOCKED,
    },
    LoopStatus.DESIGNING: {LoopStatus.PLANNING, LoopStatus.PAUSED},
    LoopStatus.PLANNING: {LoopStatus.EXECUTING, LoopStatus.PAUSED},
    LoopStatus.EXECUTING: {LoopStatus.VERIFYING, LoopStatus.PAUSED},
    LoopStatus.VERIFYING: {
        LoopStatus.CHECKING,
        LoopStatus.DECIDING,
        LoopStatus.PAUSED,
    },
    LoopStatus.CHECKING: {LoopStatus.DECIDING, LoopStatus.PAUSED},
    LoopStatus.DECIDING: {
        LoopStatus.EXECUTING,
        LoopStatus.PLANNING,
        LoopStatus.PAUSED,
        *TERMINAL,
    },
    LoopStatus.PAUSED: {
        LoopStatus.CONTRACT_DRAFTING,
        LoopStatus.DESIGNING,
        LoopStatus.PLANNING,
        LoopStatus.EXECUTING,
        LoopStatus.VERIFYING,
        LoopStatus.CHECKING,
        LoopStatus.DECIDING,
        LoopStatus.BLOCKED,
        LoopStatus.BUDGET_EXHAUSTED,
    },
    **{terminal: set() for terminal in TERMINAL},
}


class IllegalTransition(ValueError):
    pass


class BudgetCondition(StrEnum):
    AVAILABLE = "available"
    DIAGNOSIS_REQUIRED = "diagnosis_required"
    EXHAUSTED = "exhausted"


class BudgetStatus(BaseModel):
    condition: BudgetCondition
    reasons: list[str]


def transition(
    state: LoopState,
    target: LoopStatus,
    reason: str,
    *,
    now: datetime | None = None,
) -> LoopState:
    if state.status in TERMINAL:
        raise IllegalTransition(f"{state.status.value} is terminal")
    if target not in ALLOWED[state.status]:
        raise IllegalTransition(f"{state.status.value} -> {target.value} is illegal")
    timestamp = now or datetime.now(timezone.utc)
    updates: dict[str, object] = {"status": target, "updated_at": timestamp}
    if target is LoopStatus.EXECUTING:
        updates["iterations_used"] = state.iterations_used + 1
    if target is LoopStatus.PAUSED:
        updates["pause_reason"] = reason
    else:
        updates["pause_reason"] = None
    return state.model_copy(update=updates)


def budget_status(
    contract: LoopContract,
    state: LoopState,
    *,
    now: datetime | None = None,
) -> BudgetStatus:
    current = now or datetime.now(timezone.utc)
    exhaustion_reasons: list[str] = []
    if state.iterations_used >= contract.budget.max_iterations:
        exhaustion_reasons.append("iteration limit reached")
    elapsed_minutes = (current - state.started_at).total_seconds() / 60
    if elapsed_minutes >= contract.budget.max_minutes:
        exhaustion_reasons.append("time limit reached")
    if (
        state.checker_revisions_used > 0
        and state.checker_revisions_used >= contract.budget.max_checker_revisions
    ):
        exhaustion_reasons.append("checker revision limit reached")
    if exhaustion_reasons:
        return BudgetStatus(
            condition=BudgetCondition.EXHAUSTED,
            reasons=exhaustion_reasons,
        )
    diagnosis_reasons: list[str] = []
    if state.same_strategy_retries >= contract.budget.max_same_strategy_retries:
        diagnosis_reasons.append("same strategy retry limit reached")
    if state.no_progress_cycles >= 2:
        diagnosis_reasons.append("two consecutive cycles made no progress")
    if diagnosis_reasons:
        return BudgetStatus(
            condition=BudgetCondition.DIAGNOSIS_REQUIRED,
            reasons=diagnosis_reasons,
        )
    return BudgetStatus(condition=BudgetCondition.AVAILABLE, reasons=[])
```

- [ ] **Step 4: Export state schema alongside the contract schema**

Add to `src/loop_engineering/contract.py`:

```python
from loop_engineering.models.run import LoopEvent, LoopState


def export_schemas(output_dir: Path) -> tuple[Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    models = (
        ("loop-contract.schema.json", LoopContract),
        ("loop-state.schema.json", LoopState),
        ("loop-event.schema.json", LoopEvent),
    )
    paths: list[Path] = []
    for filename, model in models:
        path = output_dir / filename
        path.write_text(
            json.dumps(
                model.model_json_schema(),
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        paths.append(path)
    return paths[0], paths[1], paths[2]
```

Run: `uv run python -c "from pathlib import Path; from loop_engineering.contract import export_schemas; export_schemas(Path('schemas'))"`

Expected: contract, state and event schemas exist.

- [ ] **Step 5: Run state, contract and lint checks**

Run: `uv run pytest "tests/test_contract.py" "tests/test_state_machine.py" -q`

Expected: all tests pass.

Run: `uv run ruff check "src" "tests"`

Expected: `All checks passed!`

- [ ] **Step 6: Commit the state-machine slice**

```bash
git add "src/loop_engineering/models/run.py" "src/loop_engineering/state_machine.py" "src/loop_engineering/contract.py" "tests/test_state_machine.py" "schemas"
git commit -m "feat: enforce Loop state and budgets"
```

### Task 4: Append-Only Ledger, Redaction and Recovery

**Files:**
- Create: `src/loop_engineering/redaction.py`
- Create: `src/loop_engineering/ledger.py`
- Create: `tests/test_redaction.py`
- Create: `tests/test_ledger.py`

**Interfaces:**
- Consumes: `LoopContract`, `LoopState`, `LoopEvent`, `EventKind`
- Produces: `redact(value: object) -> object`
- Produces: `RunStore.create(project_root, contract)`, `RunStore.open(run_dir)`
- Produces: `RunStore.record_intent(...)->str`, `record_result(...)`, `pending_intents()->list[LoopEvent]`, `save_state(...)`

- [ ] **Step 1: Write redaction and interrupted-action tests**

```python
# tests/test_redaction.py
from loop_engineering.redaction import REDACTED, redact


def test_redact_recurses_through_mappings_and_lists() -> None:
    value = {
        "Authorization": "Bearer secret-token",
        "nested": [{"api_key": "sk-private"}, "token=abc123"],
        "safe": "visible",
    }
    assert redact(value) == {
        "Authorization": REDACTED,
        "nested": [{"api_key": REDACTED}, "token=[REDACTED]"],
        "safe": "visible",
    }
```

```python
# tests/test_ledger.py
import json
from pathlib import Path

import pytest

from loop_engineering.ledger import LedgerCorruption, RunStore
from loop_engineering.models.contract import LoopContract
from loop_engineering.models.run import EventKind
from tests.factories import valid_contract_data


def create_store(tmp_path: Path) -> RunStore:
    contract = LoopContract.model_validate(valid_contract_data())
    return RunStore.create(tmp_path, contract)


def test_events_are_monotonic_and_secrets_are_redacted(tmp_path: Path) -> None:
    store = create_store(tmp_path)
    action_id = store.record_intent(
        actor="maker",
        summary="call validator",
        payload={"Authorization": "Bearer secret-token"},
    )
    store.record_result(
        action_id=action_id,
        actor="maker",
        summary="validator passed",
        payload={"token": "hidden"},
    )

    events = store.events()
    assert [event.sequence for event in events] == [1, 2]
    assert [event.kind for event in events] == [EventKind.INTENT, EventKind.RESULT]
    assert events[0].payload["Authorization"] == "[REDACTED]"
    assert events[1].payload["token"] == "[REDACTED]"
    assert store.pending_intents() == []


def test_unmatched_intent_is_reported_for_reconciliation(tmp_path: Path) -> None:
    store = create_store(tmp_path)
    action_id = store.record_intent(actor="maker", summary="push", payload={})
    assert [event.action_id for event in store.pending_intents()] == [action_id]


def test_half_written_tail_is_detected(tmp_path: Path) -> None:
    store = create_store(tmp_path)
    store.record_intent(actor="maker", summary="write", payload={})
    with store.events_path.open("ab") as handle:
        handle.write(b'{"sequence":2')

    with pytest.raises(LedgerCorruption, match="partial tail"):
        store.events()


def test_state_snapshot_is_valid_json(tmp_path: Path) -> None:
    store = create_store(tmp_path)
    state = store.load_state()
    store.save_state(state.model_copy(update={"last_event_sequence": 7}))
    assert json.loads(store.state_path.read_text())["last_event_sequence"] == 7


def test_open_detects_contract_state_version_mismatch(tmp_path: Path) -> None:
    store = create_store(tmp_path)
    state = store.load_state().model_copy(update={"contract_version": 2})
    store.save_state(state)
    with pytest.raises(LedgerCorruption, match="contract and state snapshot disagree"):
        RunStore.open(store.run_dir)


def test_result_updates_progress_and_strategy_counters(tmp_path: Path) -> None:
    store = create_store(tmp_path)
    action_id = store.record_intent(actor="maker", summary="attempt", payload={})
    store.record_result(
        action_id=action_id,
        actor="maker",
        summary="failed without evidence",
        payload={},
        made_progress=False,
        same_strategy=True,
    )
    state = store.load_state()
    assert state.no_progress_cycles == 1
    assert state.same_strategy_retries == 1


def test_result_must_match_one_unresolved_intent(tmp_path: Path) -> None:
    store = create_store(tmp_path)
    with pytest.raises(ValueError, match="unresolved intent"):
        store.record_result(
            action_id="unknown",
            actor="maker",
            summary="invalid",
            payload={},
        )
    action_id = store.record_intent(actor="maker", summary="attempt", payload={})
    store.record_result(
        action_id=action_id,
        actor="maker",
        summary="observed",
        payload={},
    )
    with pytest.raises(ValueError, match="unresolved intent"):
        store.record_result(
            action_id=action_id,
            actor="maker",
            summary="duplicate",
            payload={},
        )
```

- [ ] **Step 2: Run tests and verify ledger modules are missing**

Run: `uv run pytest "tests/test_redaction.py" "tests/test_ledger.py" -q`

Expected: FAIL during collection because `loop_engineering.redaction` and `ledger` do not exist.

- [ ] **Step 3: Implement recursive redaction**

```python
# src/loop_engineering/redaction.py
import re
from collections.abc import Mapping, Sequence
from typing import Any

REDACTED = "[REDACTED]"
SENSITIVE_KEYS = {
    "authorization",
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "password",
    "secret",
    "token",
}
INLINE_SECRET = re.compile(
    r"(?i)(bearer\s+|(?:api[_-]?key|token|password|secret)\s*[=:]\s*)\S+"
)
PRIVATE_KEY = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
    re.DOTALL,
)


def redact(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): REDACTED
            if str(key).lower() in SENSITIVE_KEYS
            else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [redact(item) for item in value]
    if isinstance(value, str):
        without_keys = PRIVATE_KEY.sub(REDACTED, value)
        return INLINE_SECRET.sub(lambda match: f"{match.group(1)}{REDACTED}", without_keys)
    return value
```

- [ ] **Step 4: Implement atomic snapshots and append-only event storage**

```python
# src/loop_engineering/ledger.py
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from filelock import FileLock

from loop_engineering.models.contract import LoopContract
from loop_engineering.models.run import (
    EventKind,
    LoopEvent,
    LoopState,
    LoopStatus,
)
from loop_engineering.redaction import redact


class LedgerCorruption(RuntimeError):
    pass


def _atomic_write(path: Path, content: str) -> None:
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


class RunStore:
    def __init__(self, run_dir: Path) -> None:
        self.run_dir = run_dir
        self.contract_path = run_dir / "contract.yaml"
        self.state_path = run_dir / "state.json"
        self.events_path = run_dir / "events.jsonl"
        self.evidence_dir = run_dir / "evidence"
        self.lock = FileLock(str(run_dir / ".ledger.lock"))

    @classmethod
    def create(cls, project_root: Path, contract: LoopContract) -> "RunStore":
        run_dir = project_root.resolve() / ".loop-runs" / contract.loop_id
        run_dir.mkdir(parents=True, exist_ok=False)
        store = cls(run_dir)
        store.evidence_dir.mkdir()
        _atomic_write(
            store.contract_path,
            yaml.safe_dump(contract.model_dump(mode="json"), sort_keys=False),
        )
        now = datetime.now(timezone.utc)
        store.save_state(
            LoopState(
                loop_id=contract.loop_id,
                contract_version=contract.contract_version,
                status=LoopStatus.INTAKE,
                started_at=now,
                updated_at=now,
            )
        )
        store.events_path.touch(exist_ok=False)
        return store

    @classmethod
    def open(cls, run_dir: Path) -> "RunStore":
        store = cls(run_dir.resolve())
        for required in (store.contract_path, store.state_path, store.events_path):
            if not required.is_file():
                raise FileNotFoundError(required)
        contract = LoopContract.model_validate(
            yaml.safe_load(store.contract_path.read_text(encoding="utf-8"))
        )
        state = store.load_state()
        if (
            contract.loop_id != state.loop_id
            or contract.contract_version != state.contract_version
        ):
            raise LedgerCorruption("contract and state snapshot disagree")
        return store

    def load_state(self) -> LoopState:
        return LoopState.model_validate_json(self.state_path.read_text(encoding="utf-8"))

    def save_state(self, state: LoopState) -> None:
        _atomic_write(
            self.state_path,
            json.dumps(state.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        )

    def events(self) -> list[LoopEvent]:
        raw = self.events_path.read_bytes()
        if raw and not raw.endswith(b"\n"):
            raise LedgerCorruption("partial tail in events.jsonl")
        events: list[LoopEvent] = []
        for line_number, line in enumerate(raw.splitlines(), start=1):
            try:
                events.append(LoopEvent.model_validate_json(line))
            except Exception as error:
                raise LedgerCorruption(f"invalid event at line {line_number}") from error
        expected = list(range(1, len(events) + 1))
        if [event.sequence for event in events] != expected:
            raise LedgerCorruption("event sequence is missing, duplicate, or unordered")
        return events

    def append_event(
        self,
        *,
        actor: str,
        kind: EventKind,
        summary: str,
        action_id: str | None = None,
        from_status: LoopStatus | None = None,
        to_status: LoopStatus | None = None,
        payload: dict[str, Any] | None = None,
    ) -> LoopEvent:
        with self.lock:
            sequence = len(self.events()) + 1
            state = self.load_state()
            event = LoopEvent(
                sequence=sequence,
                event_id=str(uuid.uuid4()),
                loop_id=state.loop_id,
                contract_version=state.contract_version,
                timestamp=datetime.now(timezone.utc),
                actor=actor,
                kind=kind,
                action_id=action_id,
                from_status=from_status,
                to_status=to_status,
                summary=summary,
                payload=redact(payload or {}),
            )
            with self.events_path.open("a", encoding="utf-8") as handle:
                handle.write(event.model_dump_json() + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            self.save_state(state.model_copy(update={"last_event_sequence": sequence}))
            return event

    def record_intent(
        self,
        *,
        actor: str,
        summary: str,
        payload: dict[str, Any],
    ) -> str:
        action_id = str(uuid.uuid4())
        self.append_event(
            actor=actor,
            kind=EventKind.INTENT,
            summary=summary,
            action_id=action_id,
            payload=payload,
        )
        return action_id

    def record_result(
        self,
        *,
        action_id: str,
        actor: str,
        summary: str,
        payload: dict[str, Any],
        made_progress: bool | None = None,
        same_strategy: bool | None = None,
    ) -> LoopEvent:
        pending = {
            event.action_id for event in self.pending_intents() if event.action_id
        }
        if action_id not in pending:
            raise ValueError("result must match one unresolved intent")
        event = self.append_event(
            actor=actor,
            kind=EventKind.RESULT,
            summary=summary,
            action_id=action_id,
            payload=payload,
        )
        state = self.load_state()
        updates: dict[str, int] = {}
        if made_progress is not None:
            updates["no_progress_cycles"] = (
                0 if made_progress else state.no_progress_cycles + 1
            )
        if same_strategy is not None:
            updates["same_strategy_retries"] = (
                state.same_strategy_retries + 1 if same_strategy else 0
            )
        if updates:
            self.save_state(state.model_copy(update=updates))
        return event

    def pending_intents(self) -> list[LoopEvent]:
        events = self.events()
        completed = {
            event.action_id
            for event in events
            if event.kind is EventKind.RESULT and event.action_id
        }
        return [
            event
            for event in events
            if event.kind is EventKind.INTENT and event.action_id not in completed
        ]
```

- [ ] **Step 5: Run recovery and redaction checks**

Run: `uv run pytest "tests/test_redaction.py" "tests/test_ledger.py" -q`

Expected: all tests pass.

Run: `uv run ruff check "src/loop_engineering/redaction.py" "src/loop_engineering/ledger.py" "tests/test_redaction.py" "tests/test_ledger.py"`

Expected: `All checks passed!`

- [ ] **Step 6: Commit the recoverable-ledger slice**

```bash
git add "src/loop_engineering/redaction.py" "src/loop_engineering/ledger.py" "tests/test_redaction.py" "tests/test_ledger.py"
git commit -m "feat: persist recoverable Loop runs"
```

### Task 5: Evidence Runner and Evidence-Gated DONE

**Files:**
- Create: `src/loop_engineering/models/evidence.py`
- Create: `src/loop_engineering/evidence.py`
- Create: `tests/test_evidence.py`

**Interfaces:**
- Consumes: contract validation commands, `RunStore`, Checker and human-gate status
- Consumes: shared path-boundary helpers from Task 2
- Produces: `EvidenceRecord`, `ScopeEvaluation`, `CompletionContext`, `CompletionEvaluation`
- Produces: `ValidationRunner.run(command_id)`
- Produces: `evaluate_scope(contract)`
- Produces: `DoneEvaluator.evaluate(context)`

- [ ] **Step 1: Write safe execution, freshness and completion tests**

```python
# tests/test_evidence.py
import subprocess
from pathlib import Path

from loop_engineering.evidence import (
    DoneEvaluator,
    ValidationRunner,
    evaluate_scope,
    git_fingerprint,
)
from loop_engineering.ledger import RunStore
from loop_engineering.models.contract import LoopContract
from loop_engineering.models.evidence import CompletionContext
from loop_engineering.models.run import CheckerVerdict
from loop_engineering.paths import is_allowed_path
from tests.factories import valid_contract_data


def init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-b", "master", str(path)], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.name", "Test"], check=True)
    (path / "tests").mkdir()
    (path / "tests" / "test_example.py").write_text("def test_ok():\n    assert True\n")
    (path / ".gitignore").write_text(".loop-runs/\n")
    subprocess.run(["git", "-C", str(path), "add", "."], check=True)
    subprocess.run(["git", "-C", str(path), "commit", "-m", "initial"], check=True)


def test_validation_uses_argv_and_records_redacted_output(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    init_git_repo(project)
    data = valid_contract_data()
    data["repositories"][0]["path"] = str(project)
    data["validation_commands"][0]["argv"] = [
        "python",
        "-c",
        "print('token=secret-value')",
    ]
    contract = LoopContract.model_validate(data)
    store = RunStore.create(project, contract)

    evidence = ValidationRunner(contract, store).run("VAL-1")

    assert evidence.passed is True
    assert evidence.shell is False
    assert "[REDACTED]" in (store.evidence_dir / evidence.stdout_file).read_text()
    assert "secret-value" not in (store.evidence_dir / evidence.stdout_file).read_text()


def test_validation_rejects_cwd_escape(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    init_git_repo(project)
    data = valid_contract_data()
    data["repositories"][0]["path"] = str(project)
    data["validation_commands"][0]["cwd"] = "../"
    contract = LoopContract.model_validate(data)
    store = RunStore.create(project, contract)

    try:
        ValidationRunner(contract, store).run("VAL-1")
    except ValueError as error:
        assert "outside repository" in str(error)
    else:
        raise AssertionError("cwd escape was accepted")


def test_done_rejects_stale_or_missing_evidence(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    init_git_repo(project)
    data = valid_contract_data()
    data["repositories"][0]["path"] = str(project)
    contract = LoopContract.model_validate(data)
    evaluation = DoneEvaluator(contract).evaluate(
        CompletionContext(
            evidence=[],
            current_fingerprints={"target": git_fingerprint(project)},
            checker_verdict=None,
            human_accepted=True,
            git_delivered={"target": True},
            scope_valid=True,
            gates_clear=True,
            contract_current=True,
        )
    )
    assert evaluation.done is False
    assert evaluation.reasons == ["AC-1 lacks fresh evidence VAL-1"]


def test_scope_evaluation_reports_out_of_scope_files(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    init_git_repo(project)
    data = valid_contract_data()
    data["repositories"][0]["path"] = str(project)
    contract = LoopContract.model_validate(data)
    (project / "outside.txt").write_text("not approved\n")

    result = evaluate_scope(contract)

    assert result.valid is False
    assert result.violations == ["target:outside.txt"]


def test_scope_evaluation_includes_commits_since_base_branch(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    init_git_repo(project)
    subprocess.run(["git", "-C", str(project), "checkout", "-b", "feat/scope"], check=True)
    (project / "outside.txt").write_text("committed but not approved\n")
    subprocess.run(["git", "-C", str(project), "add", "outside.txt"], check=True)
    subprocess.run(
        ["git", "-C", str(project), "commit", "-m", "outside scope"],
        check=True,
    )
    data = valid_contract_data()
    data["repositories"][0]["path"] = str(project)
    contract = LoopContract.model_validate(data)

    result = evaluate_scope(contract)

    assert result.valid is False
    assert result.violations == ["target:outside.txt"]


def test_repository_root_can_be_an_explicit_allowed_boundary() -> None:
    assert is_allowed_path("README.md", ["."]) is True
    assert is_allowed_path("../secret.txt", ["."]) is False


def test_fingerprint_requires_the_exact_git_root(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    init_git_repo(project)
    try:
        git_fingerprint(project / "tests")
    except ValueError as error:
        assert "exact Git root" in str(error)
    else:
        raise AssertionError("repository subdirectory was accepted as a Git root")


def test_medium_risk_requires_checker_accept(tmp_path: Path) -> None:
    data = valid_contract_data()
    data["mode"] = "autonomous"
    data["human_gates"] = ["contract_approval"]
    data["risk_level"] = "medium"
    data["budget"]["max_checker_revisions"] = 2
    contract = LoopContract.model_validate(data)
    evaluation = DoneEvaluator(contract).evaluate(
        CompletionContext(
            evidence=[],
            current_fingerprints={},
            checker_verdict=CheckerVerdict.REVISE,
            human_accepted=False,
            git_delivered={"target": True},
            scope_valid=True,
            gates_clear=True,
            contract_current=True,
        )
    )
    assert "checker has not accepted" in evaluation.reasons


def test_done_rejects_scope_drift_unresolved_gate_and_stale_contract() -> None:
    contract = LoopContract.model_validate(valid_contract_data())
    evaluation = DoneEvaluator(contract).evaluate(
        CompletionContext(
            evidence=[],
            current_fingerprints={},
            checker_verdict=None,
            human_accepted=False,
            git_delivered={"target": True},
            scope_valid=False,
            gates_clear=False,
            contract_current=False,
        )
    )
    assert "actual diff is outside approved scope" in evaluation.reasons
    assert "a required gate is unresolved" in evaluation.reasons
    assert "evidence belongs to a stale contract version" in evaluation.reasons


def test_collaborative_mode_requires_final_human_acceptance() -> None:
    contract = LoopContract.model_validate(valid_contract_data())
    evaluation = DoneEvaluator(contract).evaluate(
        CompletionContext(
            evidence=[],
            current_fingerprints={},
            checker_verdict=None,
            human_accepted=False,
            git_delivered={"target": True},
            scope_valid=True,
            gates_clear=True,
            contract_current=True,
        )
    )
    assert "human final acceptance is missing" in evaluation.reasons
```

- [ ] **Step 2: Run tests and verify evidence modules are missing**

Run: `uv run pytest "tests/test_evidence.py" -q`

Expected: FAIL during collection because `loop_engineering.evidence` does not exist.

- [ ] **Step 3: Implement evidence models**

```python
# src/loop_engineering/models/evidence.py
from datetime import datetime

from pydantic import Field

from loop_engineering.models.contract import StrictModel
from loop_engineering.models.run import CheckerVerdict


class EvidenceRecord(StrictModel):
    evidence_id: str
    contract_version: int = Field(ge=1)
    command_id: str
    repository_id: str
    criterion_ids: list[str]
    started_at: datetime
    ended_at: datetime
    exit_code: int
    passed: bool
    shell: bool = False
    code_fingerprint: str
    stdout_file: str
    stderr_file: str
    stdout_sha256: str
    stderr_sha256: str


class CompletionContext(StrictModel):
    evidence: list[EvidenceRecord]
    current_fingerprints: dict[str, str]
    checker_verdict: CheckerVerdict | None
    human_accepted: bool
    git_delivered: dict[str, bool]
    scope_valid: bool
    gates_clear: bool
    contract_current: bool


class CompletionEvaluation(StrictModel):
    done: bool
    reasons: list[str] = Field(default_factory=list)


class ScopeEvaluation(StrictModel):
    valid: bool
    violations: list[str] = Field(default_factory=list)
```

- [ ] **Step 4: Implement safe validation and code fingerprints**

```python
# src/loop_engineering/evidence.py
import hashlib
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

from loop_engineering.ledger import RunStore
from loop_engineering.models.contract import LoopContract, RiskLevel
from loop_engineering.models.evidence import (
    CompletionContext,
    CompletionEvaluation,
    EvidenceRecord,
    ScopeEvaluation,
)
from loop_engineering.models.run import CheckerVerdict
from loop_engineering.paths import is_allowed_path
from loop_engineering.redaction import redact


def _run(argv: list[str], *, cwd: Path, timeout: int = 60) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        argv,
        cwd=cwd,
        check=False,
        capture_output=True,
        shell=False,
        timeout=timeout,
    )


def _git(argv: list[str], *, cwd: Path) -> bytes:
    result = _run(["git", *argv], cwd=cwd)
    if result.returncode != 0:
        raise RuntimeError(f"git {argv[0]} failed with exit code {result.returncode}")
    return result.stdout


def _exact_git_root(repository: Path) -> Path:
    repository = repository.resolve()
    root = Path(
        _git(["rev-parse", "--show-toplevel"], cwd=repository).decode().strip()
    ).resolve()
    if root != repository:
        raise ValueError("repository path must be the exact Git root")
    return root


def git_fingerprint(repository: Path) -> str:
    repository = _exact_git_root(repository)
    head = _git(["rev-parse", "HEAD"], cwd=repository)
    diff = _git(["diff", "--binary", "HEAD"], cwd=repository)
    names = _git(
        [
            "ls-files",
            "--others",
            "--exclude-standard",
            "--exclude=.loop-runs/**",
        ],
        cwd=repository,
    ).decode().splitlines()
    untracked = bytearray()
    for name in sorted(names):
        candidate = (repository / name).resolve()
        untracked.extend(name.encode())
        untracked.extend(b"\0")
        if candidate.is_file() and candidate.is_relative_to(repository):
            untracked.extend(candidate.read_bytes())
        untracked.extend(b"\0")
    return hashlib.sha256(head + b"\0" + diff + b"\0" + bytes(untracked)).hexdigest()


def evaluate_scope(contract: LoopContract) -> ScopeEvaluation:
    violations: list[str] = []
    for repository in contract.repositories:
        root = _exact_git_root(repository.path)
        committed = _git(
            ["diff", "--no-renames", "--name-only", f"{repository.base_branch}...HEAD"],
            cwd=root,
        )
        working = _git(["diff", "--no-renames", "--name-only", "HEAD"], cwd=root)
        untracked = _git(
            [
                "ls-files",
                "--others",
                "--exclude-standard",
                "--exclude=.loop-runs/**",
            ],
            cwd=root,
        )
        changed = {
            line
            for line in (
                committed + b"\n" + working + b"\n" + untracked
            ).decode().splitlines()
            if line
        }
        for path in sorted(changed):
            try:
                allowed = is_allowed_path(path, repository.allowed_paths)
            except ValueError:
                allowed = False
            if not allowed:
                violations.append(f"{repository.id}:{path}")
    return ScopeEvaluation(valid=not violations, violations=violations)


class ValidationRunner:
    def __init__(self, contract: LoopContract, store: RunStore) -> None:
        self.contract = contract
        self.store = store

    def run(self, command_id: str) -> EvidenceRecord:
        command = next(
            item for item in self.contract.validation_commands if item.id == command_id
        )
        repository = next(
            item for item in self.contract.repositories if item.id == command.repository_id
        )
        repository_root = repository.path.resolve()
        cwd = (repository_root / command.cwd).resolve()
        if not cwd.is_relative_to(repository_root):
            raise ValueError("validation cwd is outside repository")
        action_id = self.store.record_intent(
            actor="validator",
            summary=f"run {command.id}",
            payload={"argv": command.argv, "cwd": str(cwd)},
        )
        started = datetime.now(timezone.utc)
        result = _run(command.argv, cwd=cwd, timeout=command.timeout_seconds)
        ended = datetime.now(timezone.utc)
        evidence_id = f"E-{uuid.uuid4().hex}"
        stdout_file = f"{evidence_id}.stdout.txt"
        stderr_file = f"{evidence_id}.stderr.txt"
        stdout_text = str(redact(result.stdout.decode(errors="replace")))
        stderr_text = str(redact(result.stderr.decode(errors="replace")))
        self.store.evidence_dir.joinpath(stdout_file).write_text(
            stdout_text,
            encoding="utf-8",
        )
        self.store.evidence_dir.joinpath(stderr_file).write_text(
            stderr_text,
            encoding="utf-8",
        )
        evidence = EvidenceRecord(
            evidence_id=evidence_id,
            contract_version=self.store.load_state().contract_version,
            command_id=command.id,
            repository_id=repository.id,
            criterion_ids=command.criterion_ids,
            started_at=started,
            ended_at=ended,
            exit_code=result.returncode,
            passed=result.returncode == 0,
            code_fingerprint=git_fingerprint(repository_root),
            stdout_file=stdout_file,
            stderr_file=stderr_file,
            stdout_sha256=hashlib.sha256(stdout_text.encode()).hexdigest(),
            stderr_sha256=hashlib.sha256(stderr_text.encode()).hexdigest(),
        )
        self.store.record_result(
            action_id=action_id,
            actor="validator",
            summary=f"{command.id} exit={result.returncode}",
            payload={"evidence": evidence.model_dump(mode="json")},
        )
        return evidence


class DoneEvaluator:
    def __init__(self, contract: LoopContract) -> None:
        self.contract = contract

    def evaluate(self, context: CompletionContext) -> CompletionEvaluation:
        reasons: list[str] = []
        by_command = {record.command_id: record for record in context.evidence}
        for criterion in self.contract.acceptance_criteria:
            for required in criterion.required_evidence:
                evidence = by_command.get(required)
                expected_repository = next(
                    command.repository_id
                    for command in self.contract.validation_commands
                    if command.id == required
                )
                current = context.current_fingerprints.get(expected_repository)
                if (
                    not evidence
                    or not evidence.passed
                    or evidence.contract_version != self.contract.contract_version
                    or evidence.repository_id != expected_repository
                    or criterion.id not in evidence.criterion_ids
                    or evidence.code_fingerprint != current
                ):
                    reasons.append(f"{criterion.id} lacks fresh evidence {required}")
        if self.contract.risk_level in {RiskLevel.MEDIUM, RiskLevel.HIGH}:
            if context.checker_verdict is not CheckerVerdict.ACCEPT:
                reasons.append("checker has not accepted")
        requires_human = "final_acceptance" in self.contract.human_gates
        if requires_human and not context.human_accepted:
            reasons.append("human final acceptance is missing")
        required_delivery = {
            target.repository_id
            for target in self.contract.git_policy.targets
            if target.push or target.create_pr
        }
        missing_delivery = sorted(
            repository_id
            for repository_id in required_delivery
            if not context.git_delivered.get(repository_id, False)
        )
        if missing_delivery:
            reasons.append(
                "required Git delivery is incomplete: " + ", ".join(missing_delivery)
            )
        if not context.scope_valid:
            reasons.append("actual diff is outside approved scope")
        if not context.gates_clear:
            reasons.append("a required gate is unresolved")
        if not context.contract_current:
            reasons.append("evidence belongs to a stale contract version")
        return CompletionEvaluation(done=not reasons, reasons=reasons)
```

- [ ] **Step 5: Run evidence tests and lint**

Run: `uv run pytest "tests/test_evidence.py" -q`

Expected: all tests pass.

Run: `uv run ruff check "src/loop_engineering/evidence.py" "src/loop_engineering/models/evidence.py" "tests/test_evidence.py"`

Expected: `All checks passed!`

- [ ] **Step 6: Commit evidence-gated completion**

```bash
git add "src/loop_engineering/models/evidence.py" "src/loop_engineering/evidence.py" "tests/test_evidence.py"
git commit -m "feat: require fresh evidence for completion"
```

### Task 6: Safety Policy and Human-Gate Rendering

**Files:**
- Create: `src/loop_engineering/policy.py`
- Create: `tests/test_policy.py`

**Interfaces:**
- Consumes: `LoopContract.permissions`, `authorized_operations`, `git_policy` and
  the shared path-boundary helper from Task 2
- Produces: `ActionKind`, `ActionRequest`, `GateOutcome`, `GateDecision`
- Produces: `GatePolicy.evaluate(request)` and `render_confirmation(request, decision)`

- [ ] **Step 1: Write forbidden, gated and exact-preauthorization tests**

```python
# tests/test_policy.py
import pytest
from pydantic import ValidationError

from loop_engineering.models.contract import LoopContract
from loop_engineering.policy import (
    ActionKind,
    ActionRequest,
    GateOutcome,
    GatePolicy,
    render_confirmation,
)
from tests.factories import valid_contract_data


def policy(data: dict | None = None) -> GatePolicy:
    return GatePolicy(LoopContract.model_validate(data or valid_contract_data()))


def test_merge_deploy_force_and_history_rewrite_are_always_denied() -> None:
    for kind in (
        ActionKind.MERGE,
        ActionKind.DEPLOY,
        ActionKind.FORCE_PUSH,
        ActionKind.HISTORY_REWRITE,
    ):
        decision = policy().evaluate(
            ActionRequest(kind=kind, repository_id="target", target="master")
        )
        assert decision.outcome is GateOutcome.DENY


def test_production_and_sensitive_data_always_pause_for_human() -> None:
    for kind in (ActionKind.PRODUCTION_ACCESS, ActionKind.SENSITIVE_DATA):
        decision = policy().evaluate(ActionRequest(kind=kind, target="production"))
        assert decision.outcome is GateOutcome.PAUSE
        assert decision.requires_confirmation is True


def test_system_permission_and_global_package_changes_pause() -> None:
    for kind in (
        ActionKind.SYSTEM_CONFIG,
        ActionKind.PERMISSION_CHANGE,
        ActionKind.GLOBAL_PACKAGE,
    ):
        decision = policy().evaluate(ActionRequest(kind=kind, target="/system"))
        assert decision.outcome is GateOutcome.PAUSE


def test_exact_authorized_operation_is_allowed() -> None:
    data = valid_contract_data()
    data["authorized_operations"] = [
        {"kind": "file_delete", "repository_id": "target", "target": "tmp/generated.txt"}
    ]
    decision = policy(data).evaluate(
        ActionRequest(
            kind=ActionKind.FILE_DELETE,
            repository_id="target",
            target="tmp/generated.txt",
        )
    )
    assert decision.outcome is GateOutcome.ALLOW


def test_exact_database_operation_also_requires_category_permission() -> None:
    data = valid_contract_data()
    data["authorized_operations"] = [
        {"kind": "database_change", "repository_id": "target", "target": "schema.users"}
    ]
    request = ActionRequest(
        kind=ActionKind.DATABASE_CHANGE,
        repository_id="target",
        target="schema.users",
        forward_plan="add nullable column",
        compatibility_analysis="both versions accept null",
        recovery="drop the unused column before rollout",
    )
    assert policy(data).evaluate(request).outcome is GateOutcome.PAUSE
    data["permissions"]["database_changes"] = True
    assert policy(data).evaluate(request).outcome is GateOutcome.ALLOW


def test_confirmation_contains_required_professional_warning_fields() -> None:
    request = ActionRequest(
        kind=ActionKind.DATABASE_CHANGE,
        repository_id="target",
        target="schema.users",
        forward_plan="add nullable column, then backfill",
        compatibility_analysis="old and new application versions accept null",
        recovery="drop only the unused nullable column before rollout",
    )
    decision = policy().evaluate(request)
    rendered = render_confirmation(request, decision)
    for label in (
        "⚠️ 危险操作检测！",
        "操作类型：",
        "精确目标：",
        "影响范围：",
        "风险评估：",
        "恢复方案：",
        "前向方案：",
        "兼容性分析：",
        "当前证据：",
        "请确认是否继续？",
    ):
        assert label in rendered


def test_file_target_outside_allowed_paths_requires_contract_revision() -> None:
    for target in (
        "src_evil/payload.py",
        "../secret.txt",
        "C:\\secret.txt",
        "src/*.py",
        "$PROJECT_ROOT/src/app.py",
    ):
        decision = policy().evaluate(
            ActionRequest(
                kind=ActionKind.FILE_WRITE,
                repository_id="target",
                target=target,
            )
        )
        assert decision.outcome is GateOutcome.PAUSE
        assert decision.requires_confirmation is True


def test_git_preapproval_matches_repository_and_branch_exactly() -> None:
    data = valid_contract_data()
    data["git_policy"]["targets"][0].update(
        {"commit": True, "branch": "feat/exact", "worktree_path": "worktree"}
    )
    exact = policy(data).evaluate(
        ActionRequest(
            kind=ActionKind.GIT_COMMIT,
            repository_id="target",
            target="feat/exact",
        )
    )
    changed = policy(data).evaluate(
        ActionRequest(
            kind=ActionKind.GIT_COMMIT,
            repository_id="target",
            target="feat/other",
        )
    )
    assert exact.outcome is GateOutcome.ALLOW
    assert changed.outcome is GateOutcome.PAUSE


def test_database_change_requires_forward_compatibility_and_recovery_details() -> None:
    with pytest.raises(ValidationError, match="database change requires"):
        ActionRequest(
            kind=ActionKind.DATABASE_CHANGE,
            repository_id="target",
            target="schema.users",
        )
```

- [ ] **Step 2: Run tests and verify policy module is missing**

Run: `uv run pytest "tests/test_policy.py" -q`

Expected: FAIL during collection because `loop_engineering.policy` does not exist.

- [ ] **Step 3: Implement policy decisions with deny-by-default semantics**

```python
# src/loop_engineering/policy.py
from enum import StrEnum

from pydantic import Field, model_validator

from loop_engineering.models.contract import LoopContract, StrictModel
from loop_engineering.paths import is_allowed_path


class ActionKind(StrEnum):
    FILE_WRITE = "file_write"
    BATCH_WRITE = "batch_write"
    FILE_DELETE = "file_delete"
    BATCH_MOVE = "batch_move"
    DEPENDENCY_CHANGE = "dependency_change"
    GLOBAL_PACKAGE = "global_package"
    DATABASE_CHANGE = "database_change"
    SYSTEM_CONFIG = "system_config"
    PERMISSION_CHANGE = "permission_change"
    NETWORK = "network"
    SENSITIVE_DATA = "sensitive_data"
    PRODUCTION_ACCESS = "production_access"
    GIT_COMMIT = "git_commit"
    GIT_PUSH = "git_push"
    CREATE_PR = "create_pr"
    FORCE_PUSH = "force_push"
    HISTORY_REWRITE = "history_rewrite"
    MERGE = "merge"
    DEPLOY = "deploy"


class GateOutcome(StrEnum):
    ALLOW = "allow"
    PAUSE = "pause"
    DENY = "deny"


class ActionRequest(StrictModel):
    kind: ActionKind
    target: str = Field(min_length=1)
    repository_id: str | None = None
    impact: str = "External state will change"
    risk: str = "The change may be difficult to recover"
    recovery: str = "Use a forward fix or an approved revert"
    evidence: str = "The approved Loop Contract requires this action"
    forward_plan: str | None = None
    compatibility_analysis: str | None = None

    @model_validator(mode="after")
    def require_database_safety_details(self) -> "ActionRequest":
        if self.kind is ActionKind.DATABASE_CHANGE and not (
            self.forward_plan
            and self.compatibility_analysis
            and self.recovery != "Use a forward fix or an approved revert"
        ):
            raise ValueError(
                "database change requires forward plan, compatibility analysis and recovery"
            )
        return self


class GateDecision(StrictModel):
    outcome: GateOutcome
    reason: str
    requires_confirmation: bool = False


class GatePolicy:
    def __init__(self, contract: LoopContract) -> None:
        self.contract = contract

    def evaluate(self, request: ActionRequest) -> GateDecision:
        if request.kind in {
            ActionKind.FORCE_PUSH,
            ActionKind.HISTORY_REWRITE,
            ActionKind.MERGE,
            ActionKind.DEPLOY,
        }:
            return GateDecision(outcome=GateOutcome.DENY, reason="operation is forbidden")
        if request.kind in {ActionKind.PRODUCTION_ACCESS, ActionKind.SENSITIVE_DATA}:
            return GateDecision(
                outcome=GateOutcome.PAUSE,
                reason="operation always requires a fresh human gate",
                requires_confirmation=True,
            )
        if request.kind in {
            ActionKind.FILE_WRITE,
            ActionKind.BATCH_WRITE,
            ActionKind.FILE_DELETE,
            ActionKind.BATCH_MOVE,
        }:
            repository = next(
                (
                    item
                    for item in self.contract.repositories
                    if item.id == request.repository_id
                ),
                None,
            )
            try:
                target_allowed = bool(
                    repository
                    and is_allowed_path(request.target, repository.allowed_paths)
                )
            except ValueError:
                target_allowed = False
            if not target_allowed:
                return GateDecision(
                    outcome=GateOutcome.PAUSE,
                    reason="target is outside approved repository paths",
                    requires_confirmation=True,
                )
        git_target = next(
            (
                target
                for target in self.contract.git_policy.targets
                if target.repository_id == request.repository_id
            ),
            None,
        )
        git_flags = {
            ActionKind.GIT_COMMIT: bool(
                git_target
                and git_target.commit
                and request.target == git_target.branch
            ),
            ActionKind.GIT_PUSH: bool(
                git_target
                and git_target.push
                and request.target == f"{git_target.remote}/{git_target.branch}"
            ),
            ActionKind.CREATE_PR: bool(
                git_target
                and git_target.create_pr
                and request.target == f"{git_target.branch}->{git_target.pr_target}"
            ),
        }
        if request.kind in git_flags:
            allowed = git_flags[request.kind]
            return GateDecision(
                outcome=GateOutcome.ALLOW if allowed else GateOutcome.PAUSE,
                reason="Git action matches contract" if allowed else "Git action is not preauthorized",
                requires_confirmation=not allowed,
            )
        exact = any(
            operation.kind == request.kind.value
            and operation.repository_id == request.repository_id
            and operation.target == request.target
            for operation in self.contract.authorized_operations
        )
        if exact:
            permission_fields = {
                ActionKind.DEPENDENCY_CHANGE: "dependency_changes",
                ActionKind.GLOBAL_PACKAGE: "dependency_changes",
                ActionKind.DATABASE_CHANGE: "database_changes",
                ActionKind.NETWORK: "network",
            }
            permission_field = permission_fields.get(request.kind)
            if permission_field and not getattr(
                self.contract.permissions,
                permission_field,
            ):
                return GateDecision(
                    outcome=GateOutcome.PAUSE,
                    reason=f"contract permission {permission_field} is false",
                    requires_confirmation=True,
                )
            return GateDecision(outcome=GateOutcome.ALLOW, reason="exact operation is preauthorized")
        dangerous = {
            ActionKind.BATCH_WRITE,
            ActionKind.FILE_DELETE,
            ActionKind.BATCH_MOVE,
            ActionKind.DEPENDENCY_CHANGE,
            ActionKind.GLOBAL_PACKAGE,
            ActionKind.DATABASE_CHANGE,
            ActionKind.NETWORK,
            ActionKind.SYSTEM_CONFIG,
            ActionKind.PERMISSION_CHANGE,
        }
        if request.kind in dangerous:
            return GateDecision(
                outcome=GateOutcome.PAUSE,
                reason="dangerous operation needs exact approval",
                requires_confirmation=True,
            )
        return GateDecision(outcome=GateOutcome.ALLOW, reason="low-risk scoped action")


def render_confirmation(request: ActionRequest, decision: GateDecision) -> str:
    database_details = ""
    if request.kind is ActionKind.DATABASE_CHANGE:
        database_details = (
            f"前向方案：{request.forward_plan}\n"
            f"兼容性分析：{request.compatibility_analysis}\n"
        )
    return (
        "⚠️ 危险操作检测！\n"
        f"操作类型：{request.kind.value}\n"
        f"精确目标：{request.target}\n"
        f"影响范围：{request.impact}\n"
        f"风险评估：{request.risk}\n"
        f"恢复方案：{request.recovery}\n"
        f"{database_details}"
        f"当前证据：{request.evidence}；策略判定：{decision.reason}\n\n"
        "请确认是否继续？[需要明确的“是”“确认”“继续”]"
    )
```

- [ ] **Step 4: Run policy tests and lint**

Run: `uv run pytest "tests/test_policy.py" -q`

Expected: all tests pass.

Run: `uv run ruff check "src/loop_engineering/paths.py" "src/loop_engineering/policy.py" "tests/test_policy.py"`

Expected: `All checks passed!`

- [ ] **Step 5: Commit the safety-policy slice**

```bash
git add "src/loop_engineering/policy.py" "tests/test_policy.py"
git commit -m "feat: enforce Loop safety gates"
```

### Task 7: Exact-Target Git, Push and PR Automation

**Files:**
- Create: `src/loop_engineering/git_automation.py`
- Create: `tests/test_git_automation.py`

**Interfaces:**
- Consumes: one `RepositoryTarget` and its exact `GitPolicy` target after the caller's gate check
- Produces: `GitAutomation.prepare_worktree()`, `commit(...)`, `push()`, `create_pr(...)`
- Guarantees: argv-only commands, exact branches/remotes, allowed-path staging, no history rewriting

- [ ] **Step 1: Write temporary-repository integration tests**

```python
# tests/test_git_automation.py
import os
import subprocess
from pathlib import Path

import pytest

from loop_engineering.git_automation import GitAutomation, GitSafetyError
from loop_engineering.models.contract import LoopContract
from tests.factories import valid_contract_data


def run(*argv: str, cwd: Path | None = None) -> str:
    result = subprocess.run(
        list(argv),
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        shell=False,
    )
    return result.stdout.strip()


def git_contract(repo: Path, worktree: Path) -> LoopContract:
    data = valid_contract_data()
    data["repositories"][0].update(
        {"path": str(repo), "allowed_paths": ["src/", "tests/"]}
    )
    data["git_policy"]["targets"][0].update(
        {
            "create_worktree": True,
            "commit": True,
            "push": True,
            "create_pr": True,
            "branch": "feat/loop-test",
            "remote": "origin",
            "pr_target": "master",
            "worktree_path": str(worktree),
        }
    )
    return LoopContract.model_validate(data)


def repositories(tmp_path: Path) -> tuple[Path, Path]:
    remote = tmp_path / "remote.git"
    source = tmp_path / "source"
    run("git", "init", "--bare", str(remote))
    run("git", "init", "-b", "master", str(source))
    run("git", "config", "user.email", "test@example.com", cwd=source)
    run("git", "config", "user.name", "Test", cwd=source)
    (source / "src").mkdir()
    (source / "tests").mkdir()
    (source / "src" / "app.py").write_text("VALUE = 1\n")
    run("git", "add", ".", cwd=source)
    run("git", "commit", "-m", "initial", cwd=source)
    run("git", "remote", "add", "origin", str(remote), cwd=source)
    run("git", "push", "-u", "origin", "master", cwd=source)
    return source, remote


def test_worktree_commit_and_push_use_exact_contract_targets(tmp_path: Path) -> None:
    source, remote = repositories(tmp_path)
    worktree = tmp_path / "worktree"
    automation = GitAutomation(git_contract(source, worktree), "target")

    assert automation.prepare_worktree() == worktree.resolve()
    (worktree / "src" / "app.py").write_text("VALUE = 2\n")
    commit = automation.commit(["src/app.py"], "feat: update value")
    automation.push()

    assert len(commit) == 40
    assert run("git", "--git-dir", str(remote), "rev-parse", "refs/heads/feat/loop-test") == commit


def test_unknown_repository_id_is_not_authorized(tmp_path: Path) -> None:
    source, _ = repositories(tmp_path)
    with pytest.raises(GitSafetyError, match="repository is not authorized"):
        GitAutomation(git_contract(source, tmp_path / "worktree"), "missing")


def test_repository_path_must_be_the_exact_git_root(tmp_path: Path) -> None:
    source, _ = repositories(tmp_path)
    contract = git_contract(source, tmp_path / "worktree")
    contract = contract.model_copy(
        update={
            "repositories": [
                contract.repositories[0].model_copy(update={"path": source / "src"})
            ]
        }
    )
    with pytest.raises(GitSafetyError, match="repository path is not the Git root"):
        GitAutomation(contract, "target")


def test_commit_rejects_paths_outside_allowlist(tmp_path: Path) -> None:
    source, _ = repositories(tmp_path)
    worktree = tmp_path / "worktree"
    automation = GitAutomation(git_contract(source, worktree), "target")
    automation.prepare_worktree()
    (worktree / "secret.txt").write_text("do not stage\n")

    with pytest.raises(GitSafetyError, match="outside allowed paths"):
        automation.commit(["secret.txt"], "bad")


def test_prepare_worktree_does_not_touch_user_changes(tmp_path: Path) -> None:
    source, _ = repositories(tmp_path)
    (source / "local-notes.txt").write_text("user-owned\n")
    worktree = tmp_path / "worktree"

    GitAutomation(git_contract(source, worktree), "target").prepare_worktree()

    assert (source / "local-notes.txt").read_text() == "user-owned\n"
    assert "?? local-notes.txt" in run("git", "status", "--short", cwd=source)


def test_commit_refuses_previously_staged_content(tmp_path: Path) -> None:
    source, _ = repositories(tmp_path)
    worktree = tmp_path / "worktree"
    automation = GitAutomation(git_contract(source, worktree), "target")
    automation.prepare_worktree()
    (worktree / "tests" / "extra.py").write_text("VALUE = 3\n")
    run("git", "add", "tests/extra.py", cwd=worktree)
    (worktree / "src" / "app.py").write_text("VALUE = 2\n")

    with pytest.raises(GitSafetyError, match="index already contains staged paths"):
        automation.commit(["src/app.py"], "feat: update value")


def test_commit_refuses_a_different_checked_out_branch(tmp_path: Path) -> None:
    source, _ = repositories(tmp_path)
    worktree = tmp_path / "worktree"
    automation = GitAutomation(git_contract(source, worktree), "target")
    automation.prepare_worktree()
    run("git", "switch", "-c", "feat/other", cwd=worktree)
    (worktree / "src" / "app.py").write_text("VALUE = 2\n")

    with pytest.raises(GitSafetyError, match="current branch does not match contract"):
        automation.commit(["src/app.py"], "feat: update value")


@pytest.mark.skipif(os.name == "nt", reason="fake gh executable is POSIX-only")
def test_pr_uses_gh_without_shell(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source, _ = repositories(tmp_path)
    worktree = tmp_path / "worktree"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    gh = bin_dir / "gh"
    gh.write_text("#!/bin/sh\nprintf '%s\\n' 'https://github.test/pr/1'\n")
    gh.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    automation = GitAutomation(git_contract(source, worktree), "target")
    automation.prepare_worktree()

    assert automation.create_pr("Title", "Body") == "https://github.test/pr/1"
```

- [ ] **Step 2: Run tests and verify Git automation is missing**

Run: `uv run pytest "tests/test_git_automation.py" -q`

Expected: FAIL during collection because `loop_engineering.git_automation` does not exist.

- [ ] **Step 3: Implement exact-target Git automation**

```python
# src/loop_engineering/git_automation.py
import subprocess
from collections.abc import Sequence
from pathlib import Path

from loop_engineering.models.contract import LoopContract, RepositoryTarget
from loop_engineering.paths import is_allowed_path


class GitSafetyError(RuntimeError):
    pass


def _run(argv: list[str], *, cwd: Path) -> str:
    result = subprocess.run(
        argv,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        shell=False,
    )
    if result.returncode:
        operation = argv[1] if len(argv) > 1 else "command"
        raise GitSafetyError(
            f"Git {operation} failed with exit code {result.returncode}"
        )
    return result.stdout.strip()


class GitAutomation:
    def __init__(self, contract: LoopContract, repository_id: str) -> None:
        self.contract = contract
        repository = next(
            (
                item
                for item in contract.repositories
                if item.id == repository_id
            ),
            None,
        )
        policy = next(
            (
                item
                for item in contract.git_policy.targets
                if item.repository_id == repository_id
            ),
            None,
        )
        if repository is None or policy is None:
            raise GitSafetyError("repository is not authorized for Git automation")
        self.repository: RepositoryTarget = repository
        self.policy = policy
        self.source = self.repository.path.resolve()
        source_root = Path(
            _run(["git", "rev-parse", "--show-toplevel"], cwd=self.source)
        ).resolve()
        if source_root != self.source:
            raise GitSafetyError("repository path is not the Git root")

    @property
    def worktree(self) -> Path:
        if not self.policy.worktree_path:
            raise GitSafetyError("worktree_path is not authorized")
        return self.policy.worktree_path.resolve()

    def prepare_worktree(self) -> Path:
        if not self.policy.create_worktree or not self.policy.branch:
            raise GitSafetyError("worktree creation is not authorized")
        if self.worktree.exists():
            raise GitSafetyError("worktree target already exists")
        _run(
            [
                "git",
                "worktree",
                "add",
                "-b",
                self.policy.branch,
                str(self.worktree),
                self.repository.base_branch,
            ],
            cwd=self.source,
        )
        return self.worktree

    def _validate_paths(self, paths: Sequence[str]) -> list[str]:
        if not paths:
            raise GitSafetyError("at least one exact path is required")
        validated: list[str] = []
        allowed = tuple(self.repository.allowed_paths)
        for value in paths:
            candidate = (self.worktree / value).resolve()
            if not candidate.is_relative_to(self.worktree):
                raise GitSafetyError("path escapes worktree")
            normalized = candidate.relative_to(self.worktree).as_posix()
            if not is_allowed_path(normalized, list(allowed)):
                raise GitSafetyError(f"{normalized} is outside allowed paths")
            validated.append(normalized)
        return validated

    def _assert_exact_worktree(self) -> None:
        root = Path(
            _run(["git", "rev-parse", "--show-toplevel"], cwd=self.worktree)
        ).resolve()
        if root != self.worktree:
            raise GitSafetyError("Git root does not match authorized worktree")
        branch = _run(["git", "branch", "--show-current"], cwd=self.worktree)
        if branch != self.policy.branch:
            raise GitSafetyError("current branch does not match contract")

    def commit(self, paths: Sequence[str], message: str) -> str:
        if not self.policy.commit:
            raise GitSafetyError("commit is not authorized")
        self._assert_exact_worktree()
        validated = self._validate_paths(paths)
        staged = _run(["git", "diff", "--cached", "--name-only"], cwd=self.worktree)
        if staged:
            raise GitSafetyError("index already contains staged paths")
        _run(["git", "add", "--", *validated], cwd=self.worktree)
        _run(["git", "commit", "-m", message], cwd=self.worktree)
        return _run(["git", "rev-parse", "HEAD"], cwd=self.worktree)

    def push(self) -> None:
        if not self.policy.push or not self.policy.remote or not self.policy.branch:
            raise GitSafetyError("push is not authorized")
        self._assert_exact_worktree()
        _run(
            ["git", "push", "-u", "--", self.policy.remote, self.policy.branch],
            cwd=self.worktree,
        )

    def create_pr(self, title: str, body: str) -> str:
        if not self.policy.create_pr or not self.policy.pr_target:
            raise GitSafetyError("PR creation is not authorized")
        self._assert_exact_worktree()
        return _run(
            [
                "gh",
                "pr",
                "create",
                "--base",
                self.policy.pr_target,
                "--head",
                self.policy.branch or "",
                "--title",
                title,
                "--body",
                body,
            ],
            cwd=self.worktree,
        )
```

- [ ] **Step 4: Run Git integration and quality checks**

Run: `uv run pytest "tests/test_git_automation.py" -q`

Expected: all tests pass without network access.

Run: `uv run ruff check "src/loop_engineering/git_automation.py" "tests/test_git_automation.py"`

Expected: `All checks passed!`

- [ ] **Step 5: Commit the Git-delivery slice**

```bash
git add "src/loop_engineering/git_automation.py" "tests/test_git_automation.py"
git commit -m "feat: automate authorized Git delivery"
```

### Task 8: Project Initialization and Core CLI

**Files:**
- Create: `src/loop_engineering/project.py`
- Create: `src/loop_engineering/cli.py`
- Create: `tests/test_project.py`
- Create: `tests/test_cli.py`
- Create: `templates/project.yaml`
- Modify: `src/loop_engineering/ledger.py`

**Interfaces:**
- Produces: `ProjectConfig`, `initialize_project(root, update_gitignore=False)`
- Produces: `main(argv=None)->int`
- Produces: approval-enforced transitions and authoritative `RunStore.complete(...)`
- CLI groups: `project`, `contract`, `schema`, `run`, `evidence`, `budget`,
  `completion`, `gate`, `scope`, `git`
- Project initialization never copies Core rules and never selects `autonomous`.

- [ ] **Step 1: Write project initialization and CLI contract tests**

```python
# tests/test_project.py
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from loop_engineering.project import ProjectConfig, initialize_project


def test_project_init_creates_minimal_config_without_mode(tmp_path: Path) -> None:
    config = initialize_project(tmp_path)
    path = tmp_path / ".loop-engineering" / "project.yaml"
    raw = yaml.safe_load(path.read_text())

    assert config == ProjectConfig.model_validate(raw)
    assert raw == {
        "protocol_constraint": ">=0.1,<0.2",
        "run_root": ".loop-runs",
        "instruction_files": ["AGENTS.md", "CLAUDE.md"],
    }
    assert "mode" not in raw


def test_project_init_updates_gitignore_only_when_explicit(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text("dist/\n")
    initialize_project(tmp_path, update_gitignore=True)
    assert (tmp_path / ".gitignore").read_text() == "dist/\n.loop-runs/\n"


def test_project_init_refuses_to_overwrite_existing_config(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    with pytest.raises(FileExistsError):
        initialize_project(tmp_path)


def test_project_config_rejects_incompatible_protocol_constraint() -> None:
    with pytest.raises(ValidationError):
        ProjectConfig(protocol_constraint=">=1,<2")


def test_project_config_rejects_instruction_path_escape() -> None:
    with pytest.raises(ValidationError, match="unsafe relative path"):
        ProjectConfig(instruction_files=["../../secret.txt"])
```

```python
# tests/test_cli.py
import json
from pathlib import Path

import yaml

from loop_engineering.cli import main
from tests.factories import valid_contract_data


def test_cli_validates_contract_and_exports_schemas(
    tmp_path: Path, capsys
) -> None:
    contract = tmp_path / "contract.yaml"
    contract.write_text(yaml.safe_dump(valid_contract_data(), sort_keys=False))

    assert main(["contract", "validate", str(contract)]) == 0
    assert json.loads(capsys.readouterr().out)["valid"] is True

    schemas = tmp_path / "schemas"
    assert main(["schema", "export", str(schemas)]) == 0
    assert sorted(path.name for path in schemas.iterdir()) == [
        "loop-contract.schema.json",
        "loop-event.schema.json",
        "loop-state.schema.json",
    ]


def test_cli_validation_error_does_not_echo_secret_input(
    tmp_path: Path,
    capsys,
) -> None:
    data = valid_contract_data()
    data["validation_commands"][0]["argv"] = ["curl", "--token", "secret-value"]
    contract = tmp_path / "contract.yaml"
    contract.write_text(yaml.safe_dump(data, sort_keys=False))

    assert main(["contract", "validate", str(contract)]) == 2
    error = json.loads(capsys.readouterr().err)
    assert "secret-value" not in json.dumps(error)
    assert "inline secret flags" in error["message"]


def test_cli_creates_and_reads_run(tmp_path: Path, capsys) -> None:
    contract_data = valid_contract_data()
    contract_data["repositories"][0]["path"] = str(tmp_path)
    contract = tmp_path / "contract.yaml"
    contract.write_text(yaml.safe_dump(contract_data, sort_keys=False))

    assert main(["run", "create", str(contract), "--project", str(tmp_path)]) == 0
    run_dir = tmp_path / ".loop-runs" / "loop-example-001"
    capsys.readouterr()
    assert main(["run", "status", str(run_dir)]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "intake"


def test_cli_result_updates_progress_and_strategy_counters(
    tmp_path: Path,
    capsys,
) -> None:
    data = valid_contract_data()
    data["repositories"][0]["path"] = str(tmp_path)
    contract = tmp_path / "contract.yaml"
    contract.write_text(yaml.safe_dump(data, sort_keys=False))
    assert main(["run", "create", str(contract), "--project", str(tmp_path)]) == 0
    run_dir = tmp_path / ".loop-runs" / data["loop_id"]
    capsys.readouterr()

    assert main(
        [
            "run",
            "intent",
            str(run_dir),
            "--actor",
            "maker",
            "--summary",
            "attempt",
        ]
    ) == 0
    action_id = json.loads(capsys.readouterr().out)["action_id"]
    assert main(
        [
            "run",
            "result",
            str(run_dir),
            action_id,
            "--actor",
            "maker",
            "--summary",
            "no progress",
            "--progress",
            "no",
            "--same-strategy",
            "yes",
        ]
    ) == 0
    capsys.readouterr()

    assert main(["run", "status", str(run_dir)]) == 0
    status = json.loads(capsys.readouterr().out)
    assert status["no_progress_cycles"] == 1
    assert status["same_strategy_retries"] == 1


def test_cli_requires_contract_approval_before_planning(
    tmp_path: Path,
    capsys,
) -> None:
    data = valid_contract_data()
    data["repositories"][0]["path"] = str(tmp_path)
    contract = tmp_path / "contract.yaml"
    contract.write_text(yaml.safe_dump(data, sort_keys=False))
    assert main(["run", "create", str(contract), "--project", str(tmp_path)]) == 0
    run_dir = tmp_path / ".loop-runs" / data["loop_id"]
    for target in ("discovering", "contract_drafting", "awaiting_approval"):
        assert main(
            [
                "run",
                "transition",
                str(run_dir),
                target,
                "--actor",
                "maker",
                "--reason",
                target,
            ]
        ) == 0
    capsys.readouterr()

    planning = [
        "run",
        "transition",
        str(run_dir),
        "planning",
        "--actor",
        "maker",
        "--reason",
        "approved plan",
    ]
    assert main(planning) == 2
    assert "contract approval" in json.loads(capsys.readouterr().err)["message"]
    assert main(
        [
            "run",
            "approval",
            str(run_dir),
            "--actor",
            "user",
            "--gate",
            "contract_approval",
            "--decision",
            "approve",
            "--summary",
            "approved",
        ]
    ) == 0
    capsys.readouterr()
    assert main(planning) == 0


def test_cli_gate_check_returns_pause_for_production(tmp_path: Path, capsys) -> None:
    contract = tmp_path / "contract.yaml"
    contract.write_text(yaml.safe_dump(valid_contract_data(), sort_keys=False))
    request = tmp_path / "request.json"
    request.write_text(
        json.dumps({"kind": "production_access", "target": "production"}),
        encoding="utf-8",
    )

    assert main(["gate", "check", str(contract), str(request)]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["outcome"] == "pause"
    assert output["confirmation"].startswith("⚠️ 危险操作检测！")


def test_cli_replaces_only_next_contract_version_while_awaiting(
    tmp_path: Path,
    capsys,
) -> None:
    data = valid_contract_data()
    data["repositories"][0]["path"] = str(tmp_path)
    first = tmp_path / "contract-v1.yaml"
    first.write_text(yaml.safe_dump(data, sort_keys=False))
    assert main(["run", "create", str(first), "--project", str(tmp_path)]) == 0
    run_dir = tmp_path / ".loop-runs" / data["loop_id"]
    for target in ("discovering", "contract_drafting", "awaiting_approval"):
        assert main(
            [
                "run",
                "transition",
                str(run_dir),
                target,
                "--actor",
                "maker",
                "--reason",
                target,
            ]
        ) == 0
    assert main(
        [
            "run",
            "approval",
            str(run_dir),
            "--actor",
            "user",
            "--gate",
            "final_acceptance",
            "--decision",
            "approve",
            "--summary",
            "version one only",
        ]
    ) == 0
    data["contract_version"] = 2
    second = tmp_path / "contract-v2.yaml"
    second.write_text(yaml.safe_dump(data, sort_keys=False))
    capsys.readouterr()

    assert main(
        [
            "run",
            "revise",
            str(run_dir),
            str(second),
            "--actor",
            "user",
            "--summary",
            "approved revision",
        ]
    ) == 0
    assert json.loads(capsys.readouterr().out)["contract_version"] == 2
    assert main(["run", "status", str(run_dir)]) == 0
    status = json.loads(capsys.readouterr().out)
    assert status["approvals"] == {"contract_revision": True}
```

- [ ] **Step 2: Run tests and verify project/CLI modules are missing**

Run: `uv run pytest "tests/test_project.py" "tests/test_cli.py" -q`

Expected: FAIL during collection because `loop_engineering.project` and `cli` do not exist.

- [ ] **Step 3: Implement minimal target-project configuration**

```python
# src/loop_engineering/project.py
from pathlib import Path
from typing import Literal

import yaml
from pydantic import Field, field_validator

from loop_engineering.models.contract import StrictModel
from loop_engineering.paths import normalized_relative


class ProjectConfig(StrictModel):
    protocol_constraint: Literal[">=0.1,<0.2"] = ">=0.1,<0.2"
    run_root: Literal[".loop-runs"] = ".loop-runs"
    instruction_files: list[str] = Field(
        default_factory=lambda: ["AGENTS.md", "CLAUDE.md"]
    )

    @field_validator("instruction_files")
    @classmethod
    def validate_instruction_files(cls, values: list[str]) -> list[str]:
        for value in values:
            normalized_relative(value)
        return values


def initialize_project(
    root: Path,
    *,
    update_gitignore: bool = False,
) -> ProjectConfig:
    root = root.resolve()
    if not root.is_dir():
        raise NotADirectoryError(root)
    directory = root / ".loop-engineering"
    directory.mkdir(exist_ok=True)
    path = directory / "project.yaml"
    if path.exists():
        raise FileExistsError(path)
    config = ProjectConfig()
    path.write_text(
        yaml.safe_dump(config.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )
    if update_gitignore:
        gitignore = root / ".gitignore"
        existing = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
        lines = existing.splitlines()
        if ".loop-runs/" not in lines:
            prefix = existing if not existing or existing.endswith("\n") else existing + "\n"
            gitignore.write_text(prefix + ".loop-runs/\n", encoding="utf-8")
    return config
```

Create `templates/project.yaml` with exactly:

```yaml
protocol_constraint: ">=0.1,<0.2"
run_root: ".loop-runs"
instruction_files:
  - "AGENTS.md"
  - "CLAUDE.md"
```

- [ ] **Step 4: Add transition recording to the run store**

First add `CheckerVerdict` to the existing `loop_engineering.models.run` import in
`src/loop_engineering/ledger.py`:

```python
from loop_engineering.models.run import (
    CheckerVerdict,
    EventKind,
    LoopEvent,
    LoopState,
    LoopStatus,
)
```

Add to `RunStore` in `src/loop_engineering/ledger.py`:

```python
def _record_transition(
    self,
    *,
    actor: str,
    target: LoopStatus,
    reason: str,
) -> LoopState:
    from loop_engineering.state_machine import transition

    previous = self.load_state()
    updated = transition(previous, target, reason)
    event = self.append_event(
        actor=actor,
        kind=EventKind.TRANSITION,
        summary=reason,
        from_status=previous.status,
        to_status=target,
        payload={"from": previous.status.value, "to": target.value},
    )
    updated = updated.model_copy(update={"last_event_sequence": event.sequence})
    self.save_state(updated)
    return updated


def record_transition(
    self,
    *,
    actor: str,
    target: LoopStatus,
    reason: str,
) -> LoopState:
    previous = self.load_state()
    if target is LoopStatus.DONE:
        raise ValueError("use RunStore.complete for DONE")
    if previous.status is LoopStatus.AWAITING_APPROVAL and target in {
        LoopStatus.DESIGNING,
        LoopStatus.PLANNING,
    }:
        approvals = self.summary()["approvals"]
        approved = approvals.get("contract_approval") or approvals.get(
            "contract_revision"
        )
        if not approved:
            raise ValueError("contract approval is required before planning")
    return self._record_transition(actor=actor, target=target, reason=reason)


def complete(
    self,
    *,
    actor: str,
    reason: str,
) -> LoopState:
    import hashlib

    from loop_engineering.evidence import (
        DoneEvaluator,
        evaluate_scope,
        git_fingerprint,
    )
    from loop_engineering.models.evidence import CompletionContext, EvidenceRecord

    contract = LoopContract.model_validate(
        yaml.safe_load(self.contract_path.read_text(encoding="utf-8"))
    )
    state = self.load_state()
    summary = self.summary()
    approvals = summary["approvals"]
    required_gates = set(contract.human_gates)
    if approvals.get("contract_revision"):
        required_gates.discard("contract_approval")
    gates_clear = (
        not summary["pending_intents"]
        and state.status is LoopStatus.DECIDING
        and all(approvals.get(gate) is True for gate in required_gates)
    )
    checker = (
        CheckerVerdict(summary["checker_verdict"])
        if summary["checker_verdict"]
        else None
    )
    evidence: list[EvidenceRecord] = []
    git_operations: dict[str, set[str]] = {}
    evidence_root = self.evidence_dir.resolve()
    for event in self.events():
        if (
            event.contract_version != state.contract_version
            or event.kind is not EventKind.RESULT
        ):
            continue
        raw_evidence = event.payload.get("evidence")
        if isinstance(raw_evidence, dict):
            record = EvidenceRecord.model_validate(raw_evidence)
            if record.contract_version != state.contract_version:
                raise ValueError("evidence contract version does not match run")
            for filename, expected_hash in (
                (record.stdout_file, record.stdout_sha256),
                (record.stderr_file, record.stderr_sha256),
            ):
                path = (evidence_root / filename).resolve()
                if not path.is_relative_to(evidence_root) or not path.is_file():
                    raise ValueError("evidence file is missing or outside run directory")
                if hashlib.sha256(path.read_bytes()).hexdigest() != expected_hash:
                    raise ValueError("evidence file hash does not match ledger")
            evidence.append(record)
        git_result = event.payload.get("git")
        if isinstance(git_result, dict) and git_result.get("success") is True:
            repository_id = git_result.get("repository_id")
            operation = git_result.get("operation")
            if isinstance(repository_id, str) and isinstance(operation, str):
                git_operations.setdefault(repository_id, set()).add(operation)
    git_delivered: dict[str, bool] = {}
    for target in contract.git_policy.targets:
        required: set[str] = set()
        if target.push:
            required.add("push")
        if target.create_pr:
            required.add("create_pr")
        git_delivered[target.repository_id] = required <= git_operations.get(
            target.repository_id,
            set(),
        )
    authoritative = CompletionContext(
        evidence=evidence,
        current_fingerprints={
            repository.id: git_fingerprint(repository.path)
            for repository in contract.repositories
        },
        checker_verdict=checker,
        human_accepted=approvals.get("final_acceptance") is True,
        git_delivered=git_delivered,
        scope_valid=evaluate_scope(contract).valid,
        gates_clear=gates_clear,
        contract_current=True,
    )
    evaluation = DoneEvaluator(contract).evaluate(authoritative)
    if not evaluation.done:
        raise ValueError("DONE requirements failed: " + "; ".join(evaluation.reasons))
    return self._record_transition(actor=actor, target=LoopStatus.DONE, reason=reason)


def record_approval(
    self,
    *,
    actor: str,
    gate: str,
    approved: bool,
    summary: str,
) -> LoopEvent:
    return self.append_event(
        actor=actor,
        kind=EventKind.APPROVAL,
        summary=summary,
        payload={"gate": gate, "approved": approved},
    )


def record_checker(
    self,
    *,
    actor: str,
    verdict: CheckerVerdict,
    findings: list[str],
) -> LoopEvent:
    event = self.append_event(
        actor=actor,
        kind=EventKind.CHECKER,
        summary=f"checker verdict: {verdict.value}",
        payload={"verdict": verdict.value, "findings": findings},
    )
    if verdict is CheckerVerdict.REVISE:
        state = self.load_state()
        self.save_state(
            state.model_copy(
                update={"checker_revisions_used": state.checker_revisions_used + 1}
            )
        )
    return event


def replace_contract(
    self,
    revised: LoopContract,
    *,
    actor: str,
    summary: str,
) -> LoopState:
    current = LoopContract.model_validate(
        yaml.safe_load(self.contract_path.read_text(encoding="utf-8"))
    )
    state = self.load_state()
    if state.status is not LoopStatus.AWAITING_APPROVAL:
        raise ValueError("contract replacement requires awaiting_approval")
    if revised.loop_id != current.loop_id:
        raise ValueError("revised contract must retain loop_id")
    if revised.contract_version != current.contract_version + 1:
        raise ValueError("revised contract version must increment by one")
    _atomic_write(
        self.contract_path,
        yaml.safe_dump(revised.model_dump(mode="json"), sort_keys=False),
    )
    updated = state.model_copy(update={"contract_version": revised.contract_version})
    self.save_state(updated)
    event = self.record_approval(
        actor=actor,
        gate="contract_revision",
        approved=True,
        summary=summary,
    )
    updated = updated.model_copy(update={"last_event_sequence": event.sequence})
    self.save_state(updated)
    return updated


def summary(self) -> dict[str, Any]:
    events = self.events()
    state = self.load_state()
    approvals: dict[str, bool] = {}
    latest_checker: str | None = None
    for event in events:
        if event.contract_version != state.contract_version:
            continue
        if event.kind is EventKind.APPROVAL:
            approvals[str(event.payload["gate"])] = bool(event.payload["approved"])
        elif event.kind is EventKind.CHECKER:
            latest_checker = str(event.payload["verdict"])
    return {
        **state.model_dump(mode="json"),
        "pending_intents": [
            event.action_id for event in self.pending_intents() if event.action_id
        ],
        "approvals": approvals,
        "checker_verdict": latest_checker,
    }
```

- [ ] **Step 5: Implement the CLI as a thin adapter over Core APIs**

```python
# src/loop_engineering/cli.py
import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from pydantic import ValidationError

from loop_engineering import __version__
from loop_engineering.contract import export_schemas, load_contract
from loop_engineering.evidence import DoneEvaluator, ValidationRunner, evaluate_scope
from loop_engineering.git_automation import GitAutomation
from loop_engineering.ledger import RunStore
from loop_engineering.models.evidence import CompletionContext
from loop_engineering.models.run import CheckerVerdict, LoopStatus
from loop_engineering.policy import ActionRequest, GateOutcome, GatePolicy, render_confirmation
from loop_engineering.project import initialize_project
from loop_engineering.redaction import redact
from loop_engineering.state_machine import BudgetCondition, budget_status


def _json(value: object, *, stream=sys.stdout) -> None:
    print(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False),
        file=stream,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="loop-engineering")
    parser.add_argument("--version", action="version", version=__version__)
    groups = parser.add_subparsers(dest="group", required=True)

    project = groups.add_parser("project")
    project_commands = project.add_subparsers(dest="command", required=True)
    project_init = project_commands.add_parser("init")
    project_init.add_argument("--root", type=Path, default=Path.cwd())
    project_init.add_argument("--update-gitignore", action="store_true")

    contract = groups.add_parser("contract")
    contract_commands = contract.add_subparsers(dest="command", required=True)
    contract_validate = contract_commands.add_parser("validate")
    contract_validate.add_argument("path", type=Path)

    schema = groups.add_parser("schema")
    schema_commands = schema.add_subparsers(dest="command", required=True)
    schema_export = schema_commands.add_parser("export")
    schema_export.add_argument("output", type=Path)

    run = groups.add_parser("run")
    run_commands = run.add_subparsers(dest="command", required=True)
    run_create = run_commands.add_parser("create")
    run_create.add_argument("contract", type=Path)
    run_create.add_argument("--project", type=Path, required=True)
    run_status = run_commands.add_parser("status")
    run_status.add_argument("run_dir", type=Path)
    run_events = run_commands.add_parser("events")
    run_events.add_argument("run_dir", type=Path)
    run_transition = run_commands.add_parser("transition")
    run_transition.add_argument("run_dir", type=Path)
    run_transition.add_argument("target", choices=[status.value for status in LoopStatus])
    run_transition.add_argument("--actor", required=True)
    run_transition.add_argument("--reason", required=True)
    run_complete = run_commands.add_parser("complete")
    run_complete.add_argument("run_dir", type=Path)
    run_complete.add_argument("--actor", required=True)
    run_complete.add_argument("--reason", required=True)
    run_intent = run_commands.add_parser("intent")
    run_intent.add_argument("run_dir", type=Path)
    run_intent.add_argument("--actor", required=True)
    run_intent.add_argument("--summary", required=True)
    run_intent.add_argument("--payload-json", default="{}")
    run_result = run_commands.add_parser("result")
    run_result.add_argument("run_dir", type=Path)
    run_result.add_argument("action_id")
    run_result.add_argument("--actor", required=True)
    run_result.add_argument("--summary", required=True)
    run_result.add_argument("--payload-json", default="{}")
    run_result.add_argument("--progress", choices=["yes", "no", "unknown"], default="unknown")
    run_result.add_argument(
        "--same-strategy",
        choices=["yes", "no", "unknown"],
        default="unknown",
    )
    run_approval = run_commands.add_parser("approval")
    run_approval.add_argument("run_dir", type=Path)
    run_approval.add_argument("--actor", required=True)
    run_approval.add_argument("--gate", required=True)
    run_approval.add_argument("--decision", choices=["approve", "reject"], required=True)
    run_approval.add_argument("--summary", required=True)
    run_checker = run_commands.add_parser("checker")
    run_checker.add_argument("run_dir", type=Path)
    run_checker.add_argument("--actor", required=True)
    run_checker.add_argument(
        "--verdict",
        choices=[verdict.value for verdict in CheckerVerdict],
        required=True,
    )
    run_checker.add_argument("--findings-json", default="[]")
    run_revise = run_commands.add_parser("revise")
    run_revise.add_argument("run_dir", type=Path)
    run_revise.add_argument("contract", type=Path)
    run_revise.add_argument("--actor", required=True)
    run_revise.add_argument("--summary", required=True)

    evidence = groups.add_parser("evidence")
    evidence_commands = evidence.add_subparsers(dest="command", required=True)
    evidence_run = evidence_commands.add_parser("run")
    evidence_run.add_argument("run_dir", type=Path)
    evidence_run.add_argument("command_id")

    budget = groups.add_parser("budget")
    budget_commands = budget.add_subparsers(dest="command", required=True)
    budget_check = budget_commands.add_parser("check")
    budget_check.add_argument("run_dir", type=Path)

    completion = groups.add_parser("completion")
    completion_commands = completion.add_subparsers(dest="command", required=True)
    completion_evaluate = completion_commands.add_parser("evaluate")
    completion_evaluate.add_argument("contract", type=Path)
    completion_evaluate.add_argument("context", type=Path)

    gate = groups.add_parser("gate")
    gate_commands = gate.add_subparsers(dest="command", required=True)
    gate_check = gate_commands.add_parser("check")
    gate_check.add_argument("contract", type=Path)
    gate_check.add_argument("request", type=Path)

    scope = groups.add_parser("scope")
    scope_commands = scope.add_subparsers(dest="command", required=True)
    scope_check = scope_commands.add_parser("check")
    scope_check.add_argument("contract", type=Path)

    git = groups.add_parser("git")
    git_commands = git.add_subparsers(dest="command", required=True)
    for command in ("prepare", "push"):
        child = git_commands.add_parser(command)
        child.add_argument("run_dir", type=Path)
        child.add_argument("repository_id")
    git_commit = git_commands.add_parser("commit")
    git_commit.add_argument("run_dir", type=Path)
    git_commit.add_argument("repository_id")
    git_commit.add_argument("--message", required=True)
    git_commit.add_argument("--path", action="append", required=True)
    git_pr = git_commands.add_parser("pr")
    git_pr.add_argument("run_dir", type=Path)
    git_pr.add_argument("repository_id")
    git_pr.add_argument("--title", required=True)
    git_pr.add_argument("--body-file", type=Path, required=True)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if (args.group, args.command) == ("project", "init"):
            config = initialize_project(
                args.root,
                update_gitignore=args.update_gitignore,
            )
            _json(config.model_dump(mode="json"))
        elif (args.group, args.command) == ("contract", "validate"):
            contract = load_contract(args.path)
            _json({"valid": True, "loop_id": contract.loop_id})
        elif (args.group, args.command) == ("schema", "export"):
            _json({"schemas": [str(path) for path in export_schemas(args.output)]})
        elif (args.group, args.command) == ("run", "create"):
            store = RunStore.create(args.project, load_contract(args.contract))
            _json({"run_dir": str(store.run_dir)})
        elif (args.group, args.command) == ("run", "status"):
            _json(RunStore.open(args.run_dir).summary())
        elif (args.group, args.command) == ("run", "events"):
            _json(
                [
                    event.model_dump(mode="json")
                    for event in RunStore.open(args.run_dir).events()
                ]
            )
        elif (args.group, args.command) == ("run", "transition"):
            state = RunStore.open(args.run_dir).record_transition(
                actor=args.actor,
                target=LoopStatus(args.target),
                reason=args.reason,
            )
            _json(state.model_dump(mode="json"))
        elif (args.group, args.command) == ("run", "complete"):
            state = RunStore.open(args.run_dir).complete(
                actor=args.actor,
                reason=args.reason,
            )
            _json(state.model_dump(mode="json"))
        elif (args.group, args.command) == ("run", "intent"):
            action_id = RunStore.open(args.run_dir).record_intent(
                actor=args.actor,
                summary=args.summary,
                payload=json.loads(args.payload_json),
            )
            _json({"action_id": action_id})
        elif (args.group, args.command) == ("run", "result"):
            event = RunStore.open(args.run_dir).record_result(
                action_id=args.action_id,
                actor=args.actor,
                summary=args.summary,
                payload=json.loads(args.payload_json),
                made_progress=(
                    None if args.progress == "unknown" else args.progress == "yes"
                ),
                same_strategy=(
                    None
                    if args.same_strategy == "unknown"
                    else args.same_strategy == "yes"
                ),
            )
            _json(event.model_dump(mode="json"))
        elif (args.group, args.command) == ("run", "approval"):
            event = RunStore.open(args.run_dir).record_approval(
                actor=args.actor,
                gate=args.gate,
                approved=args.decision == "approve",
                summary=args.summary,
            )
            _json(event.model_dump(mode="json"))
        elif (args.group, args.command) == ("run", "checker"):
            event = RunStore.open(args.run_dir).record_checker(
                actor=args.actor,
                verdict=CheckerVerdict(args.verdict),
                findings=json.loads(args.findings_json),
            )
            _json(event.model_dump(mode="json"))
        elif (args.group, args.command) == ("run", "revise"):
            state = RunStore.open(args.run_dir).replace_contract(
                load_contract(args.contract),
                actor=args.actor,
                summary=args.summary,
            )
            _json(state.model_dump(mode="json"))
        elif (args.group, args.command) == ("evidence", "run"):
            store = RunStore.open(args.run_dir)
            record = ValidationRunner(load_contract(store.contract_path), store).run(
                args.command_id
            )
            _json(record.model_dump(mode="json"))
        elif (args.group, args.command) == ("budget", "check"):
            store = RunStore.open(args.run_dir)
            result = budget_status(
                load_contract(store.contract_path),
                store.load_state(),
            )
            _json(result.model_dump(mode="json"))
            if result.condition is BudgetCondition.EXHAUSTED:
                return 4
            if result.condition is BudgetCondition.DIAGNOSIS_REQUIRED:
                return 5
            return 0
        elif (args.group, args.command) == ("completion", "evaluate"):
            context = CompletionContext.model_validate_json(
                args.context.read_text(encoding="utf-8")
            )
            result = DoneEvaluator(load_contract(args.contract)).evaluate(context)
            _json(result.model_dump(mode="json"))
            return 0 if result.done else 3
        elif (args.group, args.command) == ("gate", "check"):
            request = ActionRequest.model_validate_json(
                args.request.read_text(encoding="utf-8")
            )
            decision = GatePolicy(load_contract(args.contract)).evaluate(request)
            output = decision.model_dump(mode="json")
            if decision.outcome is GateOutcome.PAUSE:
                output["confirmation"] = render_confirmation(request, decision)
            _json(output)
        elif (args.group, args.command) == ("scope", "check"):
            result = evaluate_scope(load_contract(args.contract))
            _json(result.model_dump(mode="json"))
            return 0 if result.valid else 6
        elif args.group == "git":
            store = RunStore.open(args.run_dir)
            automation = GitAutomation(
                load_contract(store.contract_path),
                args.repository_id,
            )
            if args.command == "prepare":
                _json({"worktree": str(automation.prepare_worktree())})
            elif args.command == "commit":
                _json({"commit": automation.commit(args.path, args.message)})
            elif args.command == "push":
                automation.push()
                _json({"pushed": True})
            elif args.command == "pr":
                _json(
                    {
                        "url": automation.create_pr(
                            args.title,
                            args.body_file.read_text(encoding="utf-8"),
                        )
                    }
                )
            else:
                raise AssertionError("unreachable Git command")
        else:
            raise AssertionError("unreachable command")
    except Exception as error:
        if isinstance(error, ValidationError):
            message = "; ".join(
                f"{'.'.join(str(part) for part in item['loc'])}: {item['msg']}"
                for item in error.errors(include_url=False, include_input=False)
            )
        else:
            message = str(redact(str(error)))
        _json(
            {"error": type(error).__name__, "message": message},
            stream=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

- [ ] **Step 6: Run CLI, project and regression checks**

Run: `uv run pytest "tests/test_project.py" "tests/test_cli.py" -q`

Expected: all tests pass.

Run: `uv run loop-engineering --version`

Expected: `0.1.0`.

Run: `uv run ruff check "src" "tests"`

Expected: `All checks passed!`

- [ ] **Step 7: Commit the project/CLI slice**

```bash
git add "src/loop_engineering/project.py" "src/loop_engineering/cli.py" "src/loop_engineering/ledger.py" "tests/test_project.py" "tests/test_cli.py" "templates/project.yaml"
git commit -m "feat: add Loop project and run CLI"
```

### Task 9: Normative Protocol, Codex Skill and Cross-Project Adoption

**Files:**
- Create: `PROTOCOL.md`
- Modify: `README.md`
- Create: `adapters/codex/SKILL.md`
- Create: `docs/adoption.md`
- Create: `templates/final-report.md`
- Create: `tests/test_adapter_contract.py`

**Interfaces:**
- Consumes: CLI commands from Task 8 and all Core invariants.
- Produces: Codex skill named `loop-engineering`.
- Produces: complete manual and automated onboarding steps for another project.
- Guarantees: skill does not claim unavailable commands and never bypasses a human gate.

- [ ] **Step 1: Write a static contract test for the Codex Skill**

```python
# tests/test_adapter_contract.py
from pathlib import Path

import yaml


def test_codex_skill_declares_required_loop_contract() -> None:
    path = Path("adapters/codex/SKILL.md")
    text = path.read_text(encoding="utf-8")
    _, frontmatter, body = text.split("---", 2)
    metadata = yaml.safe_load(frontmatter)

    assert metadata["name"] == "loop-engineering"
    assert "state-changing" in metadata["description"]
    assert "Compatible Core: >=0.1,<0.2" in body
    for required in (
        "collaborative",
        "autonomous",
        "Loop Contract",
        "Maker",
        "Checker",
        "BUDGET_EXHAUSTED",
        "loop-engineering contract validate",
        "loop-engineering run create",
        "loop-engineering evidence run",
        "loop-engineering budget check",
        "loop-engineering gate check",
        "loop-engineering completion evaluate",
        "loop-engineering run complete",
        "loop-engineering scope check",
        "KISS",
        "append-only",
        "不得自动合并或部署",
    ):
        assert required in body


def test_adoption_guide_has_manual_and_installed_paths() -> None:
    text = Path("docs/adoption.md").read_text(encoding="utf-8")
    assert "立即可用：人工引用规范" in text
    assert "实现完成后：CLI + Codex Skill" in text
    assert "loop-engineering project init" in text
    assert "$loop-engineering" in text
```

- [ ] **Step 2: Run the test and verify adapter documents are missing**

Run: `uv run pytest "tests/test_adapter_contract.py" -q`

Expected: FAIL because `adapters/codex/SKILL.md` does not exist.

- [ ] **Step 3: Write the normative protocol**

Create `PROTOCOL.md` with this exact normative structure and language:

```markdown
# Loop Engineering Core Protocol 0.1.0

## Normative terms

MUST, MUST NOT, SHOULD and MAY are requirement levels. A conforming adapter MUST
enforce every MUST/MUST NOT rule and MUST reject incompatible protocol versions.

## Admission

- Read-only questions MAY use investigate-verify-report without a run.
- Every state-changing task MUST create a Loop Contract.
- Mode MUST be collaborative or autonomous, MUST NOT be inherited, and defaults to collaborative.
- Autonomous execution MUST NOT start before explicit contract approval.

## Contract

The contract MUST identify objective, repositories, allowed paths, scope,
acceptance criteria, evidence commands, risk, permissions, Git policy, budgets,
human gates, assumptions and stop conditions. Objective, scope, acceptance,
dangerous permissions, repository targets, Git targets or budget expansion MUST
create a new contract version and pause execution.

Rule priority is: platform safety and the latest explicit user instruction; the
approved Loop Contract; applicable `AGENTS.md`; repository architecture/testing
rules; then Core defaults. A new higher-priority instruction that conflicts with
the contract MUST pause execution and revise the contract before mutation.

## Loop

The legal lifecycle is intake -> discovering -> contract_drafting ->
awaiting_approval -> designing/planning -> executing -> verifying -> checking ->
deciding. Deciding MAY return to planning/executing or enter paused, done,
blocked or budget_exhausted. Done, blocked and budget_exhausted are immutable;
continuation creates a child run.

Each execution iteration MUST select one unmet criterion, record an intent,
perform the smallest scoped action, observe real feedback, record the result,
capture evidence, invoke Checker when required, and decide the next state.

## Evidence and verification

- Every acceptance criterion MUST have fresh evidence for the current fingerprint.
- Bug fixes SHOULD preserve before-fail and after-pass evidence.
- Validation MUST use argv execution with shell disabled.
- Tests MUST NOT be removed, weakened, skipped or hidden to claim success.
- Medium/high risk MUST receive independent Checker ACCEPT.
- Collaborative runs and all high-risk runs MUST receive final human acceptance.

## Failure, recovery and budgets

- The same failed strategy MAY be retried at most once.
- Two consecutive iterations without new evidence or material progress MUST return
  to diagnosis before another state-changing attempt.
- Interrupted intents MUST be reconciled against worktrees, refs, remotes and
  external state before retrying.
- Iteration, time and Checker-revision limits are contract data and MUST be enforced.
- A contract contradiction pauses; missing external authority/state blocks; only a
  reached contract or global limit becomes budget_exhausted.

## Persistence

Each run MUST persist its approved contract, atomic state snapshot, append-only
JSONL events, evidence files and final report under `.loop-runs/<loop_id>/`.
Events MUST include monotonic intent/result pairs, transitions, approvals, Checker
verdicts and external side-effect identifiers. Runtime data MUST be ignored by Git
by default and MUST NOT contain secrets or full model reasoning.

## Safety

- The adapter MUST resolve and boundary-check every path.
- Secrets, tokens, sensitive responses and full model reasoning MUST NOT be persisted.
- Unmatched intent events MUST be reconciled against real external state before retry.
- Force-push, history rewriting, reset --hard, automatic merge and automatic deployment are forbidden.
- Production and sensitive-data operations always require a fresh human gate.
- Database changes require a forward plan, compatibility analysis and recovery strategy.
- Unresolved variables, broad globs and workspace-root destructive targets are forbidden.
- User changes of unknown origin MUST NOT be overwritten, reverted or deleted.
- Every approval, rejection and permission change MUST be appended to the run ledger.

## Git and cross-repository delivery

Git automation MUST re-check the exact repository, worktree, base branch, target
branch, remote and allowed paths immediately before mutation. It MUST stage only
explicit approved paths and MUST preserve unrelated dirty user work. Multi-repository
runs MUST follow the acyclic contract dependency order, use one branch and PR per
repository, and disclose prerequisite PRs. DONE means ready for human merge, never
merged or deployed.

## Engineering quality

- Read existing code, tests and local instructions before writing.
- Apply KISS and YAGNI; implement only the smallest accepted behavior.
- Apply DRY only to material repetition in scope; do not speculate with abstractions.
- Preserve SOLID responsibility, dependency and interface boundaries.
- Do not perform unrelated refactors, bulk formatting or dependency upgrades.
- Match the repository's comment language and explain reasons or constraints.
- A new dependency requires necessity, alternatives and authorization evidence.

## Termination

DONE means all criteria have fresh evidence, required Checker/human gates passed,
the diff remains in scope, and approved Git/PR delivery completed. BLOCKED is only
for missing authority, input or external state. BUDGET_EXHAUSTED is only for a
contract or global limit. Difficulty alone is not a terminal reason.
```

- [ ] **Step 4: Write the Codex Skill workflow**

Create `adapters/codex/SKILL.md` with:

```markdown
---
name: loop-engineering
description: Use for every state-changing engineering task when the user wants a collaborative or autonomous evidence-gated coding loop.
---

# Loop Engineering for Codex

Compatible Core: >=0.1,<0.2

Read `PROTOCOL.md`, the target project's `.loop-engineering/project.yaml`,
every existing configured instruction file, all applicable `AGENTS.md`, and the
approved Loop Contract before modifying state.

Resolve `PROTOCOL.md` from the LoopEngineering repository containing this Skill.
If it is absent or its version does not satisfy `>=0.1,<0.2`, stop instead of
silently falling back.

## Hard gate

Do not edit files, install dependencies, create Git refs, commit, push, open a PR,
or call an external write API until the Loop Contract has been shown to the user
and explicitly approved. The contract's exact preauthorization may cover later
Git actions. New targets or permissions require a revised approval.

The sole preapproval write is an adapter-owned contract draft in a newly created
temporary directory for schema validation. It must not touch the target project and
is removed after the approved contract is persisted.

## Intake

1. Classify the request as read-only or state-changing.
2. For state-changing work, ask for `collaborative` or `autonomous` unless supplied.
3. Default to `collaborative`; never reuse the previous task's mode.
4. Inspect the repository, instructions, tests, recent commits and dirty state read-only.
5. Draft `contract.yaml` from the Core template with exact repositories, paths,
   acceptance criteria, argv validation, budget, permissions and Git targets. Keep
   the unapproved draft in an ephemeral temporary directory, not the target project.
6. Run `loop-engineering contract validate "<contract-path>"`.
7. Present a compact Loop Contract summary and wait for approval.
8. After approval, run
   `loop-engineering run create "<contract-path>" --project "<project-root>"`,
   retain the created `intake` snapshot, record the discovering/drafting/awaiting
   transitions and the approval event with `loop-engineering run approval`, then
   transition into designing or planning.

## Maker loop

For each unmet acceptance criterion:

1. Run `loop-engineering budget check "<run-dir>"`. An exhausted result transitions
   to BUDGET_EXHAUSTED. A diagnosis-required result returns to planning and requires
   a new causal hypothesis before another action. Otherwise choose one smallest
   verifiable increment.
2. Serialize the exact ActionRequest and run
   `loop-engineering gate check "<contract-path>" "<request-json>"`.
   A `pause` decision returns the complete professional confirmation text; show
   it verbatim and wait for an explicit “是”“确认” or “继续”. Record the human
   approval with `loop-engineering run approval "<run-dir>" --actor user --gate
   dangerous_action --decision approve --summary "approved exact action"`; only an
   approval continues. Use `--decision reject` for rejection. Record a policy `deny`
   as rejected and never execute it.
3. Immediately before every approved external state change, run
   `loop-engineering run intent` with the exact action and target.
4. Make the change without touching unrelated user work.
5. Run `loop-engineering run result` immediately after observing real state,
   marking whether new evidence/progress occurred and whether the strategy was reused.
   Git results use payload shape
   `{"git":{"repository_id":"target","operation":"push","success":true,
   "commit_sha":"<sha>","pr_url":"<url-or-empty>"}}`; record `create_pr` as a
   separate successful operation. Completion derives per-repository delivery only
   from these current-contract result events, never from prose.
6. Run `loop-engineering evidence run "<run-dir>" "<VAL-ID>"`.
7. Do not repeat the same failed strategy more than once.
8. For multiple repositories, follow the contract's acyclic `depends_on` order,
   create one branch/PR per repository, and list prerequisite PRs in each dependent PR.

## Checker

- Low risk: Maker self-checks against the contract and raw evidence.
- Medium/high risk: dispatch a fresh independent Checker context.
- Checker reads the contract, actual diff and raw evidence, then returns only
  `ACCEPT`, `REVISE` or `BLOCK` with findings and evidence.
- Record the verdict and findings with `loop-engineering run checker`.
- Checker never edits production code. `REVISE` returns to Maker and consumes a revision.
- If an independent Checker is unavailable, medium/high work cannot become DONE.

## Control modes

- `collaborative`: pause at contract, nontrivial design, plan, new dangerous action
  and final acceptance.
- `autonomous`: continue inside the approved contract until DONE, BLOCKED,
  BUDGET_EXHAUSTED or a hard human gate.
- The user may downgrade to collaborative at any time. Upgrading requires explicit approval.
- A material target, scope, evidence, dangerous permission or budget change pauses the
  run, increments `contract_version`, re-enters contract_drafting/awaiting_approval,
  and invokes `loop-engineering run revise` only after explicit approval.
- Record every collaborative design, plan and final decision with
  `loop-engineering run approval "<run-dir>" --actor user --gate "<gate>"
  --decision approve --summary "explicit user approval"`; use `--decision reject`
  for rejection, which never permits forward transition.

## Completion

Do not claim DONE from prose. Build the strict CompletionContext and run
`loop-engineering completion evaluate "<contract-path>" "<context-json>"`.
Only a zero exit code permits calling `loop-engineering run complete "<run-dir>"
--actor maker --reason "all DONE requirements passed"`. That authoritative command
re-derives evidence records and hashes, current fingerprints, scope, Git delivery,
approvals, pending intents and Checker status before transitioning. Verify every
acceptance criterion has fresh evidence and approved Git/PR delivery completed. Use the
`loop-engineering git` subcommands only after a matching gate decision and emit the
final report from `templates/final-report.md`.

Set `scope_valid` in CompletionContext only from
`loop-engineering scope check "<contract-path>"`; do not infer it from Maker prose.
Derive `checker_verdict`, `human_accepted`, `gates_clear` and
`contract_current` from `loop-engineering run status "<run-dir>"`: unresolved
intent IDs, a paused state, or a required contract gate without an approval event make
`gates_clear=false`, and contract versions must match.
Populate evidence only from validator result events returned by
`loop-engineering run events "<run-dir>"`.

不得自动合并或部署。不得强推、改写历史、执行 `git reset --hard`、泄露秘密，
或通过删除/弱化测试制造成功。
```

- [ ] **Step 5: Write the cross-project adoption guide requested by the user**

Create `docs/adoption.md` with these exact steps:

````markdown
# 在其他项目中使用 Loop Engineering

## 立即可用：人工引用规范

1. 在任务中提供规范地址：
   `https://github.com/MRongM/LoopEngineering/blob/master/docs/superpowers/specs/2026-07-30-loop-engineering-protocol-design.md`。
2. 明确控制模式：`collaborative` 或 `autonomous`。
3. 提供目标仓库、目标、验收标准和期望的 Git 权限。
4. 要求 Agent 先只读调查并起草 Loop Contract。
5. 审阅目标、范围、证据命令、预算、危险权限和 Git 目标。
6. 明确批准后再允许 Agent 修改代码。
7. 最终只接受包含测试证据、Checker 结论和 Git/PR 状态的报告。

可直接使用以下任务模板：

```text
请读取 Loop Engineering 规范：
https://github.com/MRongM/LoopEngineering/blob/master/docs/superpowers/specs/2026-07-30-loop-engineering-protocol-design.md

控制模式：autonomous
目标仓库：/work/acme-orders
目标：实现一个明确、可验证的目标
验收标准：
- 可重复验证的行为一
- 可重复验证的行为二
Git 权限：允许创建隔离分支、原子提交、推送和 PR；禁止自动合并与部署

先只读调查并起草 Loop Contract，等待我明确批准后再执行。
```

## 实现完成后：CLI + Codex Skill

### 0. 检查前置条件

- Python 3.12–3.14。
- `uv` 与 Git 可用。
- 只有创建 GitHub PR 时才需要已认证的 `gh` CLI。
- 本地已检出 LoopEngineering；以下 Unix 示例路径为 `/opt/LoopEngineering`，
  目标项目示例路径为 `/work/acme-orders`，请替换为自己的绝对路径。

### 1. 安装 CLI

开发检出：

```bash
uv tool install --editable "/opt/LoopEngineering"
```

发布 `v0.1.0` 标签后：

```bash
uv tool install "git+https://github.com/MRongM/LoopEngineering.git@v0.1.0"
```

验证：

```bash
loop-engineering --version
```

预期输出：`0.1.0`。

### 2. 安装 Codex Skill

将仓库内 `adapters/codex` 链接到 Codex Skills 目录。目标路径必须由用户明确指定：

```bash
mkdir -p "/Users/alice/.codex/skills"
ln -s "/opt/LoopEngineering/adapters/codex" "/Users/alice/.codex/skills/loop-engineering"
```

如果目标已存在，先检查其来源，不要覆盖。创建新 Codex 会话以重新发现 Skill。

Windows PowerShell：

```powershell
New-Item -ItemType Directory -Force -Path "C:/Users/Alice/.codex/skills"
New-Item -ItemType SymbolicLink -Path "C:/Users/Alice/.codex/skills/loop-engineering" -Target "C:/Tools/LoopEngineering/adapters/codex"
```

### 3. 初始化目标项目

```bash
loop-engineering project init --root "/work/acme-orders" --update-gitignore
```

该命令只创建 `.loop-engineering/project.yaml`，并按显式参数把
`.loop-runs/` 加入 `.gitignore`；不会选择自动模式，也不会复制 Core。

### 4. 添加项目入口约束

在项目根 `AGENTS.md` 中加入：

```markdown
For every state-changing engineering task, invoke $loop-engineering.
Require an approved Loop Contract before mutation and evidence before DONE.
```

### 5. 发起任务

```text
$loop-engineering
控制模式：autonomous
目标：修复订单重复提交问题
验收：先复现失败，再证明修复；相关回归测试通过
Git：允许创建分支、提交、推送和 PR
```

### 6. 批准并观察

Agent 必须先展示 Loop Contract。批准后，运行状态位于：
`/work/acme-orders/.loop-runs/loop-example-001/`。自动模式只在终态或安全门禁暂停。

### 7. 验收交付

检查 `final-report.md`、测试证据、Checker 结论、提交和 PR。合并与部署仍由人工执行。
````

- [ ] **Step 6: Add README and final-report contract**

Replace the bootstrap `README.md` with:

````markdown
# Loop Engineering

Loop Engineering 0.1.0 provides evidence-gated, recoverable execution loops for
coding agents. The Core is tool-independent; the first adapter targets Codex.

## Use it now

Without installing code, reference the approved design in your task and require an
approved Loop Contract before any mutation:

- [Design specification](docs/superpowers/specs/2026-07-30-loop-engineering-protocol-design.md)
- [Cross-project adoption guide](docs/adoption.md)

## Install the implementation

```bash
uv tool install --editable "/opt/LoopEngineering"
loop-engineering --version
```

Link `adapters/codex` into an explicitly chosen Codex Skills directory, initialize
the target project, then invoke `$loop-engineering`. Full commands for Unix and
Windows are in `docs/adoption.md`.

## Safety boundary

The first release has no scheduler, daemon, automatic merge, automatic deployment,
force-push, history rewrite or implicit production access. Runtime state under
`.loop-runs/` is local and ignored by default.

## Development

```bash
uv sync --dev
uv run pytest -q
uv run ruff check "src" "tests"
uv build
```
````

Create `templates/final-report.md` with exactly:

```markdown
# Loop Final Report

## Terminal state

## Contract results

## Changed files and repositories

## Validation evidence

## Checker and human gates

## Git branches, commits and pull requests

## Budget and recovery events

## Known limitations and checks not run

## KISS, YAGNI, DRY and SOLID

## Required human follow-up
```

- [ ] **Step 7: Run adapter, documentation and regression checks**

Run: `uv run pytest "tests/test_adapter_contract.py" -q`

Expected: all tests pass.

Run: `uv run ruff check "src" "tests"`

Expected: `All checks passed!`

Run: `uv run pytest -q`

Expected: the full suite passes.

- [ ] **Step 8: Commit protocol, adapter and adoption docs**

```bash
git add "PROTOCOL.md" "README.md" "adapters/codex/SKILL.md" "docs/adoption.md" "templates/final-report.md" "tests/test_adapter_contract.py"
git commit -m "feat: add Codex Loop adapter and adoption guide"
```

### Task 10: End-to-End Dry Run and Release Gate

**Files:**
- Create: `tests/e2e/test_loop_dry_run.py`
- Create: `tests/e2e/test_risk_gates.py`
- Create: `tests/test_protocol_coverage.py`
- Modify: `README.md`
- Modify: `schemas/loop-contract.schema.json`
- Modify: `schemas/loop-state.schema.json`
- Modify: `schemas/loop-event.schema.json`

**Interfaces:**
- Exercises: project init -> contract validation -> run creation -> state transitions -> evidence -> Checker decision -> completion evaluation.
- Produces: a network-free local release gate for protocol `0.1.0`.

- [ ] **Step 1: Write an end-to-end low-risk dry-run test**

```python
# tests/e2e/test_loop_dry_run.py
import subprocess
from pathlib import Path

import yaml

from loop_engineering.cli import main
from loop_engineering.contract import load_contract
from loop_engineering.evidence import (
    DoneEvaluator,
    ValidationRunner,
    evaluate_scope,
    git_fingerprint,
)
from loop_engineering.ledger import RunStore
from loop_engineering.models.evidence import CompletionContext
from loop_engineering.models.run import LoopStatus
from loop_engineering.project import initialize_project
from tests.factories import valid_contract_data


def git(*argv: str, cwd: Path) -> None:
    subprocess.run(["git", *argv], cwd=cwd, check=True, capture_output=True)


def test_low_risk_loop_reaches_done_only_after_fresh_evidence(tmp_path: Path) -> None:
    project = tmp_path / "consumer"
    project.mkdir()
    git("init", "-b", "master", cwd=project)
    git("config", "user.email", "test@example.com", cwd=project)
    git("config", "user.name", "Test", cwd=project)
    (project / "tests").mkdir()
    (project / "tests" / "test_value.py").write_text(
        "def test_value():\n    assert 2 + 2 == 4\n",
        encoding="utf-8",
    )
    initialize_project(project, update_gitignore=True)
    git("add", ".", cwd=project)
    git("commit", "-m", "initial", cwd=project)

    data = valid_contract_data()
    data["mode"] = "autonomous"
    data["human_gates"] = ["contract_approval"]
    data["repositories"][0]["path"] = str(project)
    data["validation_commands"][0]["argv"] = [
        "python",
        "-m",
        "pytest",
        "tests/test_value.py",
        "-q",
    ]
    contract_path = tmp_path / "contract.yaml"
    contract_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    contract = load_contract(contract_path)
    store = RunStore.create(project, contract)

    for target in (
        LoopStatus.DISCOVERING,
        LoopStatus.CONTRACT_DRAFTING,
        LoopStatus.AWAITING_APPROVAL,
    ):
        store.record_transition(actor="maker", target=target, reason=target.value)
    store.record_approval(
        actor="user",
        gate="contract_approval",
        approved=True,
        summary="approved autonomous dry run",
    )
    for target in (
        LoopStatus.PLANNING,
        LoopStatus.EXECUTING,
        LoopStatus.VERIFYING,
    ):
        store.record_transition(actor="maker", target=target, reason=target.value)

    evidence = ValidationRunner(contract, store).run("VAL-1")
    store.record_transition(
        actor="maker",
        target=LoopStatus.DECIDING,
        reason="validation evidence recorded",
    )
    context = CompletionContext(
        evidence=[evidence],
        current_fingerprints={"target": git_fingerprint(project)},
        checker_verdict=None,
        human_accepted=False,
        git_delivered={"target": True},
        scope_valid=evaluate_scope(contract).valid,
        gates_clear=True,
        contract_current=True,
    )
    evaluation = DoneEvaluator(contract).evaluate(context)

    assert evaluation.done is True
    assert main(
        [
            "run",
            "complete",
            str(store.run_dir),
            "--actor",
            "maker",
            "--reason",
            "evidence complete",
        ]
    ) == 0
    assert store.load_state().status is LoopStatus.DONE
```

- [ ] **Step 2: Write integrated medium/high-risk gate scenarios**

```python
# tests/e2e/test_risk_gates.py
from datetime import datetime, timezone

from loop_engineering.evidence import DoneEvaluator
from loop_engineering.models.contract import LoopContract
from loop_engineering.models.evidence import CompletionContext, EvidenceRecord
from loop_engineering.models.run import CheckerVerdict
from tests.factories import valid_contract_data


def scenario(
    risk: str,
    *,
    checker: CheckerVerdict | None,
    human: bool,
) -> tuple[LoopContract, CompletionContext]:
    data = valid_contract_data()
    data["mode"] = "autonomous"
    data["risk_level"] = risk
    data["human_gates"] = (
        ["contract_approval", "final_acceptance"]
        if risk == "high"
        else ["contract_approval"]
    )
    data["budget"]["max_checker_revisions"] = {"low": 0, "medium": 2, "high": 3}[risk]
    contract = LoopContract.model_validate(data)
    now = datetime(2026, 7, 30, tzinfo=timezone.utc)
    evidence = EvidenceRecord(
        evidence_id="E-risk",
        contract_version=contract.contract_version,
        command_id="VAL-1",
        repository_id="target",
        criterion_ids=["AC-1"],
        started_at=now,
        ended_at=now,
        exit_code=0,
        passed=True,
        code_fingerprint="current",
        stdout_file="E-risk.stdout.txt",
        stderr_file="E-risk.stderr.txt",
        stdout_sha256="0" * 64,
        stderr_sha256="0" * 64,
    )
    context = CompletionContext(
        evidence=[evidence],
        current_fingerprints={"target": "current"},
        checker_verdict=checker,
        human_accepted=human,
        git_delivered={"target": True},
        scope_valid=True,
        gates_clear=True,
        contract_current=True,
    )
    return contract, context


def test_medium_risk_rejects_revise_and_accepts_checker_accept() -> None:
    contract, revise = scenario(
        "medium",
        checker=CheckerVerdict.REVISE,
        human=False,
    )
    assert DoneEvaluator(contract).evaluate(revise).done is False
    _, accepted = scenario(
        "medium",
        checker=CheckerVerdict.ACCEPT,
        human=False,
    )
    assert DoneEvaluator(contract).evaluate(accepted).done is True


def test_high_risk_requires_checker_and_human() -> None:
    contract, missing_human = scenario(
        "high",
        checker=CheckerVerdict.ACCEPT,
        human=False,
    )
    assert DoneEvaluator(contract).evaluate(missing_human).reasons == [
        "human final acceptance is missing"
    ]
    _, accepted = scenario(
        "high",
        checker=CheckerVerdict.ACCEPT,
        human=True,
    )
    assert DoneEvaluator(contract).evaluate(accepted).done is True
```

- [ ] **Step 3: Write a protocol-to-test coverage guard**

```python
# tests/test_protocol_coverage.py
from pathlib import Path

from loop_engineering.contract import export_schemas


def test_protocol_invariants_have_named_test_modules() -> None:
    required = {
        "contract": "tests/test_contract.py",
        "state": "tests/test_state_machine.py",
        "ledger": "tests/test_ledger.py",
        "evidence": "tests/test_evidence.py",
        "safety": "tests/test_policy.py",
        "Git": "tests/test_git_automation.py",
        "adapter": "tests/test_adapter_contract.py",
        "dry run": "tests/e2e/test_loop_dry_run.py",
        "risk gates": "tests/e2e/test_risk_gates.py",
    }
    missing = [name for name, path in required.items() if not Path(path).is_file()]
    assert missing == []


def test_forbidden_capabilities_are_absent_from_cli() -> None:
    cli = Path("src/loop_engineering/cli.py").read_text(encoding="utf-8")
    for forbidden in ("force-push", "reset --hard", " merge ", " deploy "):
        assert forbidden not in cli


def test_committed_schemas_match_models(tmp_path: Path) -> None:
    generated = export_schemas(tmp_path)
    for path in generated:
        assert path.read_bytes() == Path("schemas", path.name).read_bytes()
```

- [ ] **Step 4: Run the dry run and fix only failures inside approved scope**

Run: `uv run pytest "tests/e2e/test_loop_dry_run.py" "tests/e2e/test_risk_gates.py" "tests/test_protocol_coverage.py" -q`

Expected: all tests pass without network, remote Git writes or production access.

- [ ] **Step 5: Regenerate versioned schemas and verify no drift**

Run: `uv run loop-engineering schema export "schemas"`

Expected: three schema paths are printed.

Run: `uv run pytest "tests/test_protocol_coverage.py::test_committed_schemas_match_models" -q`

Expected: PASS, proving the committed schemas exactly match the final models.

- [ ] **Step 6: Execute the complete release gate**

Run: `uv run pytest -q`

Expected: all unit, integration, security, adapter and end-to-end tests pass.

Run: `uv run ruff check "src" "tests"`

Expected: `All checks passed!`

Run: `uv run python -m compileall -q "src"`

Expected: exit 0 with no output.

Run: `uv build`

Expected: source and wheel artifacts are created under `dist/`.

Run: `uv run loop-engineering --version`

Expected: `0.1.0`.

- [ ] **Step 7: Add an evidence-accurate support matrix to README**

Append this exact support table:

```markdown
## Support status

| Capability | Status |
|---|---|
| Python 3.14 on macOS | Verified by the local release suite |
| Python 3.12–3.13 | Declared compatible; CI is required before claiming verified execution |
| Linux Core CLI | Designed and documented; Linux CI is required before claiming verified execution |
| Windows Core path/subprocess APIs | Designed and documented; Windows CI is required before claiming verified execution |
| Git worktree/commit/push | Verified against a local bare remote |
| GitHub PR creation | Requires an authenticated `gh` CLI |
| Scheduler or daemon | Not included |
| Automatic merge/deployment/production access | Forbidden |
```

- [ ] **Step 8: Commit the end-to-end release gate**

```bash
git add "tests/e2e/test_loop_dry_run.py" "tests/e2e/test_risk_gates.py" "tests/test_protocol_coverage.py" "README.md" "schemas"
git commit -m "test: verify Loop Engineering end to end"
```

## Specification Coverage Map

| Approved design section | Implemented and verified by |
|---|---|
| 1–4 Background, goals, non-goals and principles | Global Constraints; Tasks 1, 5, 9 and 10 |
| 5 Core/adapter architecture | File and Responsibility Map; Tasks 1, 8 and 9 |
| 6 Admission and control modes | Tasks 2, 8, 9 and risk-gate tests in Task 10 |
| 7 Loop Contract, versions and Git preauthorization | Tasks 2, 4, 6 and 7 |
| 8 State machine and iteration lifecycle | Tasks 3, 4, 8 and the dry run in Task 10 |
| 9 Risk, Maker and Checker | Tasks 2, 3, 4, 9 and Task 10 risk scenarios |
| 10 Evidence and DONE definition | Task 5 plus Task 10 freshness and completion tests |
| 11 Failure recovery and budgets | Tasks 3, 4, 8 and the Codex loop in Task 9 |
| 12 Persistence model | Task 4 plus run inspection commands in Task 8 |
| 13 Git and cross-repository delivery | Tasks 2, 5, 6, 7 and 10 |
| 14 Codex interaction and final report | Task 9 |
| 15 Code-generation quality and rule precedence | Tasks 1 and 9; full release gate in Task 10 |
| 16 Safety gates | Tasks 2, 4, 6, 7 and 9 |
| 17 File layout and ownership | File and Responsibility Map; declared file lists in every task |
| 18 Test strategy and release threshold | Focused TDD checks in Tasks 1–9; release gate in Task 10 |
| 19 Recommended implementation order | Tasks 1–10 in dependency order |
| 20 Design acceptance criteria | Plan Completion Criteria and Task 10 |
| 21 Confirmed decisions | Global Constraints, Stable Public Interfaces and Tasks 2–10 |

## Plan Completion Criteria

Implementation is complete only when:

1. Every task commit exists in order and contains only its declared files.
2. `uv run pytest -q`, Ruff, compileall and `uv build` pass from a clean checkout.
3. Generated schemas match the committed models.
4. The dry run reaches DONE only after fresh evidence.
5. Medium/high risk cannot reach DONE without Checker ACCEPT.
6. High risk cannot reach DONE without human acceptance.
7. Unmatched intents are detected before retries.
8. Exact Git targets work against a local bare remote without force/history operations.
9. Another project can follow `docs/adoption.md` without copying Core rules.
10. The final diff contains no scheduler, daemon, automatic merge, deployment or production access.
