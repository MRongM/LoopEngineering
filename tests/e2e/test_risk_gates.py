from datetime import UTC, datetime

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
    data["budget"]["max_checker_revisions"] = {
        "low": 0,
        "medium": 2,
        "high": 3,
    }[risk]
    contract = LoopContract.model_validate(data)
    now = datetime(2026, 7, 30, tzinfo=UTC)
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
