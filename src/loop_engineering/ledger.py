import json
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from filelock import FileLock

from loop_engineering.layout import (
    CONTROL_DIR_NAME,
    RUNS_DIR_NAME,
    cache_root,
    runs_root,
)
from loop_engineering.models.contract import LoopContract
from loop_engineering.models.run import (
    CheckerVerdict,
    ContractAuthorization,
    EventKind,
    LoopEvent,
    LoopState,
    LoopStatus,
)
from loop_engineering.project import ensure_project
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
        run_dir = run_dir.resolve()
        if (
            run_dir.parent.name != RUNS_DIR_NAME
            or run_dir.parent.parent.name != CONTROL_DIR_NAME
        ):
            raise ValueError(
                "run directory must be inside the canonical .loop-engine/runs directory"
            )
        project_root = run_dir.parent.parent.parent
        if run_dir.parent != runs_root(project_root):
            raise ValueError(
                "run directory must be inside the canonical .loop-engine/runs directory"
            )
        self.run_dir = run_dir
        self.contract_path = run_dir / "contract.yaml"
        self.state_path = run_dir / "state.json"
        self.events_path = run_dir / "events.jsonl"
        self.evidence_dir = run_dir / "evidence"
        self.lock = FileLock(str(run_dir / ".ledger.lock"))
        self.project_root = project_root
        self.cache_dir = cache_root(self.project_root) / "runs" / run_dir.name

    @classmethod
    def create(cls, project_root: Path, contract: LoopContract) -> "RunStore":
        project_root = project_root.resolve()
        ensure_project(project_root)
        run_dir = runs_root(project_root) / contract.loop_id
        run_dir.mkdir(parents=True, exist_ok=False)
        store = cls(run_dir)
        store.evidence_dir.mkdir()
        _atomic_write(
            store.contract_path,
            yaml.safe_dump(contract.model_dump(mode="json"), sort_keys=False),
        )
        now = datetime.now(UTC)
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
        state = LoopState.model_validate(state.model_dump(mode="python"))
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
                timestamp=datetime.now(UTC),
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
        if self.pending_intents():
            raise ValueError("pending intent must be reconciled before a new action")
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
        pending = {event.action_id for event in self.pending_intents() if event.action_id}
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
            updates["no_progress_cycles"] = 0 if made_progress else state.no_progress_cycles + 1
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
        if target is LoopStatus.DONE:
            raise ValueError("use RunStore.complete for DONE")
        if target in {
            LoopStatus.DESIGNING,
            LoopStatus.PLANNING,
            LoopStatus.EXECUTING,
            LoopStatus.VERIFYING,
            LoopStatus.CHECKING,
            LoopStatus.DECIDING,
        }:
            summary = self.summary()
            approvals = summary["approvals"]
            approved = approvals.get("contract_approval") or approvals.get(
                "contract_revision"
            )
            if not approved:
                raise ValueError("contract approval is required before planning")
            if not summary["contract_authorized"]:
                raise ValueError(
                    "current contract approval does not match the persisted contract"
                )
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
            and summary["contract_authorized"]
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
                        raise ValueError(
                            "evidence file is missing or outside run directory"
                        )
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
            git_delivered=git_delivered,
            scope_valid=evaluate_scope(contract).valid,
            gates_clear=gates_clear,
            contract_current=True,
        )
        evaluation = DoneEvaluator(contract).evaluate(authoritative)
        if not evaluation.done:
            raise ValueError(
                "DONE requirements failed: " + "; ".join(evaluation.reasons)
            )
        return self._record_transition(
            actor=actor,
            target=LoopStatus.DONE,
            reason=reason,
        )

    def _record_approval_event(
        self,
        *,
        actor: str,
        gate: str,
        approved: bool,
        summary: str,
    ) -> LoopEvent:
        payload: dict[str, Any] = {"gate": gate, "approved": approved}
        if approved and gate in {"contract_approval", "contract_revision"}:
            from loop_engineering.contract import contract_fingerprint

            contract = LoopContract.model_validate(
                yaml.safe_load(self.contract_path.read_text(encoding="utf-8"))
            )
            payload.update(
                {
                    "protocol_version": contract.protocol_version,
                    "contract_version": contract.contract_version,
                    "contract_sha256": contract_fingerprint(contract),
                    "accepted_risk_ids": sorted(
                        operation.risk_id
                        for operation in contract.authorized_operations
                    ),
                }
            )
        return self.append_event(
            actor=actor,
            kind=EventKind.APPROVAL,
            summary=summary,
            payload=payload,
        )

    def record_approval(
        self,
        *,
        actor: str,
        gate: str,
        approved: bool,
        summary: str,
    ) -> LoopEvent:
        if gate != "contract_approval":
            raise ValueError("public approval accepts only contract_approval")
        if self.load_state().status is not LoopStatus.AWAITING_APPROVAL:
            raise ValueError("contract approval requires awaiting_approval")
        return self._record_approval_event(
            actor=actor,
            gate=gate,
            approved=approved,
            summary=summary,
        )

    def current_contract_authorization(self) -> ContractAuthorization | None:
        from loop_engineering.contract import contract_fingerprint

        contract = LoopContract.model_validate(
            yaml.safe_load(self.contract_path.read_text(encoding="utf-8"))
        )
        latest: LoopEvent | None = None
        for event in self.events():
            if (
                event.contract_version == contract.contract_version
                and event.kind is EventKind.APPROVAL
                and event.payload.get("gate")
                in {"contract_approval", "contract_revision"}
            ):
                latest = event
        if latest is None or latest.payload.get("approved") is not True:
            return None
        try:
            authorization = ContractAuthorization.model_validate(
                {
                    "protocol_version": latest.payload["protocol_version"],
                    "contract_version": latest.payload["contract_version"],
                    "contract_sha256": latest.payload["contract_sha256"],
                    "accepted_risk_ids": latest.payload["accepted_risk_ids"],
                }
            )
        except (KeyError, ValueError):
            return None
        expected_risk_ids = sorted(
            operation.risk_id
            for operation in contract.authorized_operations
        )
        if (
            authorization.protocol_version != contract.protocol_version
            or authorization.contract_version != contract.contract_version
            or authorization.contract_sha256 != contract_fingerprint(contract)
            or authorization.accepted_risk_ids != expected_risk_ids
        ):
            return None
        return authorization

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
                    update={
                        "checker_revisions_used": state.checker_revisions_used + 1
                    }
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
        updated = state.model_copy(
            update={"contract_version": revised.contract_version}
        )
        self.save_state(updated)
        event = self._record_approval_event(
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
            "contract_authorized": self.current_contract_authorization() is not None,
            "checker_verdict": latest_checker,
        }
