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
