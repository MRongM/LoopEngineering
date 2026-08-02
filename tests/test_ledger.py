import json
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from loop_engineering.ledger import LedgerCorruption, RunStore
from loop_engineering.models.action import ActionRequest
from loop_engineering.models.contract import LoopContract
from loop_engineering.models.run import ContractAuthorization, EventKind, LoopStatus
from tests.factories import autonomous_risk_contract_data, valid_contract_data


def create_store(tmp_path: Path) -> RunStore:
    contract = LoopContract.model_validate(valid_contract_data())
    return RunStore.create(tmp_path, contract)


def create_risk_store(tmp_path: Path) -> RunStore:
    tmp_path.mkdir(parents=True, exist_ok=True)
    data = autonomous_risk_contract_data()
    data["repositories"][0]["path"] = str(tmp_path)
    return RunStore.create(tmp_path, LoopContract.model_validate(data))


def create_platform_store(tmp_path: Path) -> tuple[RunStore, ActionRequest]:
    target = f"codex-goal:create:{tmp_path.resolve()}/.loop-engine/runs/loop-example-001"
    data = valid_contract_data()
    data["repositories"][0]["path"] = str(tmp_path.resolve())
    data["risk_level"] = "medium"
    data["budget"]["max_checker_revisions"] = 2
    data["authorized_operations"] = [
        {
            "risk_id": "RISK-1",
            "kind": "platform_state",
            "repository_id": None,
            "target": target,
            "risk_level": "medium",
            "impact": "Creates the approved bound Goal",
            "worst_case": "The host may retain an unwanted Goal",
            "recovery": "Pause and reconcile the exact Goal state",
            "evidence": "The host result identifies the bound Goal",
        }
    ]
    data["execution_plan"]["actions"].append(
        {
            "kind": "platform_state",
            "repository_id": None,
            "target": target,
            "impact": "Creates the approved bound Goal",
            "risk": "The host state changes",
            "recovery": "Pause and reconcile the exact Goal state",
            "evidence": "The host result identifies the bound Goal",
        }
    )
    return (
        RunStore.create(tmp_path, LoopContract.model_validate(data)),
        ActionRequest(kind="platform_state", target=target),
    )


def move_to_awaiting_approval(store: RunStore) -> None:
    for target in (
        LoopStatus.DISCOVERING,
        LoopStatus.CONTRACT_DRAFTING,
        LoopStatus.AWAITING_APPROVAL,
    ):
        store.record_transition(actor="maker", target=target, reason=target.value)


def approve_for_execution(store: RunStore) -> None:
    move_to_awaiting_approval(store)
    store.record_approval(
        actor="user",
        gate="contract_approval",
        approved=True,
        summary="approved exact action plan",
    )
    for target in (LoopStatus.PLANNING, LoopStatus.EXECUTING):
        store.record_transition(actor="maker", target=target, reason=target.value)


def planned_write(target: str = "src/app.py") -> ActionRequest:
    return ActionRequest(
        kind="file_write",
        repository_id="target",
        target=target,
    )


def test_events_are_monotonic_and_secrets_are_redacted(tmp_path: Path) -> None:
    store = create_store(tmp_path)
    approve_for_execution(store)
    action_id = store.record_action_intent(
        actor="maker",
        summary="call validator",
        request=planned_write(),
        payload={"Authorization": "Bearer secret-token"},
    )
    store.record_result(
        action_id=action_id,
        actor="maker",
        summary="validator passed",
        payload={"token": "hidden"},
    )

    events = store.events()
    assert [event.sequence for event in events] == list(range(1, len(events) + 1))
    assert [event.kind for event in events[-2:]] == [EventKind.INTENT, EventKind.RESULT]
    assert events[-2].payload["Authorization"] == "[REDACTED]"
    assert events[-1].payload["token"] == "[REDACTED]"
    assert store.pending_intents() == []


def test_run_store_uses_the_single_project_control_root(tmp_path: Path) -> None:
    store = create_store(tmp_path)

    assert store.run_dir == (
        tmp_path.resolve() / ".loop-engine" / "runs" / "loop-example-001"
    )
    assert (tmp_path / ".loop-engine" / "project.yaml").is_file()


def test_run_store_rejects_a_noncanonical_run_directory(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="canonical .loop-engine/runs directory"):
        RunStore(tmp_path / "runs" / "loop-example-001")


def test_unmatched_intent_is_reported_for_reconciliation(tmp_path: Path) -> None:
    store = create_store(tmp_path)
    approve_for_execution(store)
    action_id = store.record_action_intent(
        actor="maker",
        summary="write",
        request=planned_write(),
        payload={},
    )

    assert [event.action_id for event in store.pending_intents()] == [action_id]


def test_new_intent_is_rejected_until_the_previous_one_is_reconciled(
    tmp_path: Path,
) -> None:
    store = create_store(tmp_path)
    approve_for_execution(store)
    store.record_action_intent(
        actor="maker",
        summary="first action",
        request=planned_write(),
        payload={},
    )

    with pytest.raises(ValueError, match="pending intent"):
        store.record_action_intent(
            actor="maker",
            summary="second action",
            request=planned_write("tests/test_app.py"),
            payload={},
        )


def test_half_written_tail_is_detected(tmp_path: Path) -> None:
    store = create_store(tmp_path)
    approve_for_execution(store)
    store.record_action_intent(
        actor="maker",
        summary="write",
        request=planned_write(),
        payload={},
    )
    with store.events_path.open("ab") as handle:
        handle.write(b'{"sequence":2')

    with pytest.raises(LedgerCorruption, match="partial tail"):
        store.events()


def test_state_snapshot_is_valid_json(tmp_path: Path) -> None:
    store = create_store(tmp_path)
    state = store.load_state()
    store.save_state(state.model_copy(update={"last_event_sequence": 7}))

    assert json.loads(store.state_path.read_text())["last_event_sequence"] == 7


def test_state_save_revalidates_model_copy_invariants(tmp_path: Path) -> None:
    store = create_store(tmp_path)
    state = store.load_state().model_copy(
        update={
            "status": LoopStatus.EXECUTING,
            "paused_at": store.load_state().started_at,
        }
    )

    with pytest.raises(ValidationError, match="paused_at"):
        store.save_state(state)


def test_open_detects_contract_state_version_mismatch(tmp_path: Path) -> None:
    store = create_store(tmp_path)
    state = store.load_state().model_copy(update={"contract_version": 2})
    store.save_state(state)

    with pytest.raises(LedgerCorruption, match="contract and state snapshot disagree"):
        RunStore.open(store.run_dir)


def test_open_rejects_a_persisted_collaborative_run(tmp_path: Path) -> None:
    store = create_store(tmp_path)
    raw = yaml.safe_load(store.contract_path.read_text(encoding="utf-8"))
    raw["mode"] = "collaborative"
    store.contract_path.write_text(
        yaml.safe_dump(raw, sort_keys=False),
        encoding="utf-8",
    )

    with pytest.raises(ValidationError, match="collaborative control mode is unsupported"):
        RunStore.open(store.run_dir)


def test_result_updates_progress_and_strategy_counters(tmp_path: Path) -> None:
    store = create_store(tmp_path)
    approve_for_execution(store)
    action_id = store.record_action_intent(
        actor="maker",
        summary="attempt",
        request=planned_write(),
        payload={},
    )
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
    approve_for_execution(store)
    action_id = store.record_action_intent(
        actor="maker",
        summary="attempt",
        request=planned_write(),
        payload={},
    )
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


def test_action_intent_requires_current_contract_approval(tmp_path: Path) -> None:
    store = create_store(tmp_path)

    with pytest.raises(PermissionError, match="contract approval"):
        store.record_action_intent(
            actor="maker",
            summary="too early",
            request=planned_write(),
            payload={},
        )

    assert store.events() == []


def test_action_intent_requires_the_executing_state(tmp_path: Path) -> None:
    store = create_store(tmp_path)
    move_to_awaiting_approval(store)
    store.record_approval(
        actor="user",
        gate="contract_approval",
        approved=True,
        summary="approved exact action plan",
    )
    store.record_transition(
        actor="maker",
        target=LoopStatus.PLANNING,
        reason="plan approved work",
    )

    with pytest.raises(ValueError, match="executing state"):
        store.record_action_intent(
            actor="maker",
            summary="wrong state",
            request=planned_write(),
            payload={},
        )


def test_platform_action_intent_cannot_mutate_while_paused(tmp_path: Path) -> None:
    store, request = create_platform_store(tmp_path)
    move_to_awaiting_approval(store)
    store.record_approval(
        actor="user",
        gate="contract_approval",
        approved=True,
        summary="approved exact platform action",
    )
    store.record_transition(
        actor="maker",
        target=LoopStatus.PLANNING,
        reason="plan approved work",
    )
    store.record_transition(
        actor="maker",
        target=LoopStatus.PAUSED,
        reason="host hard gate",
    )

    with pytest.raises(ValueError, match="executing state"):
        store.record_action_intent(
            actor="maker",
            summary="must not bypass pause",
            request=request,
            payload={},
        )


def test_action_intent_rejects_unplanned_request(tmp_path: Path) -> None:
    store = create_store(tmp_path)
    approve_for_execution(store)

    with pytest.raises(PermissionError, match="outside the approved execution plan"):
        store.record_action_intent(
            actor="maker",
            summary="unplanned write",
            request=planned_write("docs/unsafe.md"),
            payload={},
        )


def test_action_intent_rejects_exhausted_budget(tmp_path: Path) -> None:
    store = create_store(tmp_path)
    approve_for_execution(store)
    contract = LoopContract.model_validate(valid_contract_data())
    store.save_state(
        store.load_state().model_copy(
            update={"iterations_used": contract.budget.max_iterations}
        )
    )

    with pytest.raises(ValueError, match="budget is exhausted"):
        store.record_action_intent(
            actor="maker",
            summary="over budget",
            request=planned_write(),
            payload={},
        )


def test_action_intent_persists_the_exact_checked_request(tmp_path: Path) -> None:
    store = create_store(tmp_path)
    approve_for_execution(store)
    request = planned_write()

    store.record_action_intent(
        actor="maker",
        summary="checked write",
        request=request,
        payload={"path_count": 1},
    )

    intent = store.events()[-1]
    assert intent.payload == {
        "path_count": 1,
        "request": request.model_dump(mode="json"),
    }


@pytest.mark.parametrize("reserved", ["git", "evidence"])
def test_generic_result_cannot_claim_authoritative_payloads(
    tmp_path: Path,
    reserved: str,
) -> None:
    store = create_store(tmp_path)
    approve_for_execution(store)
    action_id = store.record_action_intent(
        actor="maker",
        summary="checked write",
        request=planned_write(),
        payload={},
    )

    with pytest.raises(ValueError, match="reserved result payload"):
        store.record_result(
            action_id=action_id,
            actor="maker",
            summary="forged authority",
            payload={reserved: {"success": True}},
        )

    assert [event.action_id for event in store.pending_intents()] == [action_id]


def test_contract_approval_binds_version_hash_and_risk_ids(tmp_path: Path) -> None:
    store = create_risk_store(tmp_path)
    move_to_awaiting_approval(store)

    event = store.record_approval(
        actor="user",
        gate="contract_approval",
        approved=True,
        summary="accepted all disclosed risks",
    )

    assert event.payload["protocol_version"] == "0.1.0"
    assert event.payload["contract_version"] == 1
    assert len(event.payload["contract_sha256"]) == 64
    assert event.payload["accepted_risk_ids"] == ["RISK-1"]
    authorization = store.current_contract_authorization()
    assert authorization is not None
    assert authorization.contract_sha256 == event.payload["contract_sha256"]
    assert authorization.accepted_risk_ids == ["RISK-1"]


def test_rejected_or_tampered_contract_has_no_authorization(tmp_path: Path) -> None:
    rejected = create_risk_store(tmp_path / "rejected")
    move_to_awaiting_approval(rejected)
    rejected.record_approval(
        actor="user",
        gate="contract_approval",
        approved=False,
        summary="risk not accepted",
    )
    assert rejected.current_contract_authorization() is None

    tampered = create_risk_store(tmp_path / "tampered")
    move_to_awaiting_approval(tampered)
    tampered.record_approval(
        actor="user",
        gate="contract_approval",
        approved=True,
        summary="accepted original contract",
    )
    raw = yaml.safe_load(tampered.contract_path.read_text(encoding="utf-8"))
    raw["objective"] = "A different objective"
    tampered.contract_path.write_text(
        yaml.safe_dump(raw, sort_keys=False),
        encoding="utf-8",
    )

    assert tampered.current_contract_authorization() is None


def test_contract_authorization_rejects_noncanonical_risk_id() -> None:
    with pytest.raises(ValidationError, match="RISK-<positive-number>"):
        ContractAuthorization(
            protocol_version="0.1.0",
            contract_version=1,
            contract_sha256="0" * 64,
            accepted_risk_ids=["RISK-0"],
        )


def test_contract_approval_requires_awaiting_approval(tmp_path: Path) -> None:
    store = create_store(tmp_path)

    with pytest.raises(ValueError, match="awaiting_approval"):
        store.record_approval(
            actor="user",
            gate="contract_approval",
            approved=True,
            summary="too early",
        )


def test_public_approval_api_rejects_every_other_gate(tmp_path: Path) -> None:
    store = create_store(tmp_path)
    move_to_awaiting_approval(store)

    with pytest.raises(ValueError, match="only contract_approval"):
        store.record_approval(
            actor="user",
            gate="contract_revision",
            approved=True,
            summary="must use contract replacement",
        )


def test_pause_before_approval_cannot_resume_into_execution_flow(
    tmp_path: Path,
) -> None:
    store = create_store(tmp_path)
    move_to_awaiting_approval(store)
    store.record_transition(
        actor="maker",
        target=LoopStatus.PAUSED,
        reason="waiting for user",
    )

    with pytest.raises(ValueError, match="contract approval"):
        store.record_transition(
            actor="maker",
            target=LoopStatus.PLANNING,
            reason="must not bypass approval through pause",
        )


def test_tampered_contract_cannot_leave_awaiting_approval(tmp_path: Path) -> None:
    store = create_risk_store(tmp_path)
    move_to_awaiting_approval(store)
    store.record_approval(
        actor="user",
        gate="contract_approval",
        approved=True,
        summary="accepted original risks",
    )
    raw = yaml.safe_load(store.contract_path.read_text(encoding="utf-8"))
    raw["objective"] = "Tampered after approval"
    store.contract_path.write_text(
        yaml.safe_dump(raw, sort_keys=False),
        encoding="utf-8",
    )

    assert store.summary()["contract_authorized"] is False
    with pytest.raises(ValueError, match="current contract approval"):
        store.record_transition(
            actor="maker",
            target=LoopStatus.PLANNING,
            reason="must not use stale approval",
        )


def test_contract_revision_stays_on_first_protocol_and_gets_fresh_binding(
    tmp_path: Path,
) -> None:
    store = create_store(tmp_path)
    move_to_awaiting_approval(store)
    revised_data = valid_contract_data()
    revised_data["contract_version"] = 2
    revised_data["objective"] = "A clarified first-release objective"

    state = store.replace_contract(
        LoopContract.model_validate(revised_data),
        actor="user",
        summary="approve revised contract",
    )

    authorization = store.current_contract_authorization()
    assert state.contract_version == 2
    assert authorization is not None
    assert authorization.protocol_version == "0.1.0"
    assert authorization.contract_version == 2
