import json
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from loop_engineering.ledger import LedgerCorruption, RunStore
from loop_engineering.models.contract import LoopContract
from loop_engineering.models.run import ContractAuthorization, EventKind, LoopStatus
from tests.factories import autonomous_risk_contract_data, valid_contract_data


def create_store(tmp_path: Path) -> RunStore:
    contract = LoopContract.model_validate(valid_contract_data())
    return RunStore.create(tmp_path, contract)


def create_risk_store(tmp_path: Path) -> RunStore:
    data = autonomous_risk_contract_data()
    data["repositories"][0]["path"] = str(tmp_path)
    contract = LoopContract.model_validate(data)
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


def test_v020_contract_approval_binds_version_hash_and_risk_ids(
    tmp_path: Path,
) -> None:
    store = create_risk_store(tmp_path)

    event = store.record_approval(
        actor="user",
        gate="contract_approval",
        approved=True,
        summary="accepted all disclosed risks",
    )

    assert event.payload["protocol_version"] == "0.2.0"
    assert event.payload["contract_version"] == 1
    assert len(event.payload["contract_sha256"]) == 64
    assert event.payload["accepted_risk_ids"] == ["RISK-1"]
    authorization = store.current_contract_authorization()
    assert authorization is not None
    assert authorization.contract_sha256 == event.payload["contract_sha256"]
    assert authorization.accepted_risk_ids == ["RISK-1"]


def test_v020_rejected_or_tampered_contract_has_no_authorization(
    tmp_path: Path,
) -> None:
    rejected = create_risk_store(tmp_path / "rejected")
    rejected.record_approval(
        actor="user",
        gate="contract_approval",
        approved=False,
        summary="risk not accepted",
    )
    assert rejected.current_contract_authorization() is None

    tampered = create_risk_store(tmp_path / "tampered")
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


def test_legacy_contract_approval_payload_remains_unbound(tmp_path: Path) -> None:
    contract = LoopContract.model_validate(
        valid_contract_data(protocol_version="0.1.0")
    )
    store = RunStore.create(tmp_path, contract)

    event = store.record_approval(
        actor="user",
        gate="contract_approval",
        approved=True,
        summary="legacy approval",
    )

    assert event.payload == {"gate": "contract_approval", "approved": True}
    assert store.current_contract_authorization() is None


def test_contract_authorization_rejects_noncanonical_risk_id() -> None:
    with pytest.raises(ValidationError, match="RISK-<positive-number>"):
        ContractAuthorization(
            protocol_version="0.2.0",
            contract_version=1,
            contract_sha256="0" * 64,
            accepted_risk_ids=["RISK-0"],
        )


def test_tampered_v020_contract_cannot_leave_awaiting_approval(
    tmp_path: Path,
) -> None:
    store = create_risk_store(tmp_path)
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


def test_contract_revision_cannot_downgrade_v020_protocol(tmp_path: Path) -> None:
    store = create_risk_store(tmp_path)
    for target in (
        LoopStatus.DISCOVERING,
        LoopStatus.CONTRACT_DRAFTING,
        LoopStatus.AWAITING_APPROVAL,
    ):
        store.record_transition(actor="maker", target=target, reason=target.value)
    revised_data = valid_contract_data(protocol_version="0.1.0")
    revised_data["loop_id"] = "loop-example-001"
    revised_data["contract_version"] = 2
    revised = LoopContract.model_validate(revised_data)

    with pytest.raises(ValueError, match="protocol downgrade"):
        store.replace_contract(
            revised,
            actor="user",
            summary="must not downgrade safety semantics",
        )
