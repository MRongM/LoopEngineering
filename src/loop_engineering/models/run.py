import re
from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import Field, field_validator

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


class ContractAuthorization(StrictModel):
    protocol_version: Literal["0.2.0"]
    contract_version: int = Field(ge=1)
    contract_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    accepted_risk_ids: list[str]

    @field_validator("accepted_risk_ids")
    @classmethod
    def validate_risk_ids(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("accepted risk ids must be unique")
        if any(not re.fullmatch(r"RISK-[1-9][0-9]*", value) for value in values):
            raise ValueError("accepted risk ids must use RISK-<positive-number>")
        return values


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
