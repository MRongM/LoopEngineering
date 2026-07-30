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
