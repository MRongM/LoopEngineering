from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

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
    now = datetime(2026, 7, 30, tzinfo=UTC)
    return LoopState(
        loop_id="loop-example-001",
        contract_version=1,
        status=status,
        started_at=now,
        updated_at=now,
        paused_at=now
        if status in {LoopStatus.AWAITING_APPROVAL, LoopStatus.PAUSED}
        else None,
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
            "updated_at": datetime(2026, 7, 30, 1, tzinfo=UTC),
        }
    )
    now = current.started_at + timedelta(minutes=contract.budget.max_minutes)

    result = budget_status(contract, current, now=now)

    assert result.condition is BudgetCondition.EXHAUSTED
    assert set(result.reasons) == {"iteration limit reached", "time limit reached"}


def test_same_strategy_retry_limit_is_one() -> None:
    current = state(LoopStatus.DECIDING).model_copy(update={"same_strategy_retries": 1})
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
    current = state(LoopStatus.DECIDING).model_copy(update={"checker_revisions_used": 2})

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


def test_awaiting_approval_and_paused_time_do_not_consume_execution_budget() -> None:
    contract = LoopContract.model_validate(valid_contract_data())
    started = state(LoopStatus.CONTRACT_DRAFTING)
    awaiting = transition(
        started,
        LoopStatus.AWAITING_APPROVAL,
        "present contract",
        now=started.started_at + timedelta(minutes=1),
    )

    while_waiting = budget_status(
        contract,
        awaiting,
        now=started.started_at + timedelta(hours=2),
    )
    resumed = transition(
        awaiting,
        LoopStatus.PLANNING,
        "contract approved",
        now=started.started_at + timedelta(hours=2),
    )
    after_active_work = budget_status(
        contract,
        resumed,
        now=started.started_at + timedelta(hours=2, minutes=28),
    )

    assert while_waiting.condition is BudgetCondition.AVAILABLE
    assert resumed.paused_seconds == pytest.approx(119 * 60)
    assert resumed.paused_at is None
    assert after_active_work.condition is BudgetCondition.AVAILABLE


def test_persisted_state_cannot_freeze_an_executing_time_budget() -> None:
    now = datetime(2026, 7, 30, tzinfo=UTC)

    with pytest.raises(ValidationError, match="paused_at"):
        LoopState(
            loop_id="loop-example-001",
            contract_version=1,
            status=LoopStatus.EXECUTING,
            started_at=now,
            updated_at=now,
            paused_at=now,
        )


def test_persisted_nonexecuting_state_requires_a_pause_timestamp() -> None:
    now = datetime(2026, 7, 30, tzinfo=UTC)

    with pytest.raises(ValidationError, match="paused_at"):
        LoopState(
            loop_id="loop-example-001",
            contract_version=1,
            status=LoopStatus.PAUSED,
            started_at=now,
            updated_at=now,
        )
