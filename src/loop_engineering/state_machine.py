from datetime import UTC, datetime
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
    timestamp = now or datetime.now(UTC)
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
    current = now or datetime.now(UTC)
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
