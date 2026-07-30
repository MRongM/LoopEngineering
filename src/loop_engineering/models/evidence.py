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
