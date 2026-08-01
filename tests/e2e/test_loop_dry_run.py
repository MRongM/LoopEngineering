import subprocess
import sys
from pathlib import Path

import yaml

from loop_engineering.cli import main
from loop_engineering.contract import load_contract
from loop_engineering.evidence import (
    DoneEvaluator,
    ValidationRunner,
    evaluate_scope,
    git_fingerprint,
)
from loop_engineering.ledger import RunStore
from loop_engineering.models.evidence import CompletionContext
from loop_engineering.models.run import LoopStatus
from loop_engineering.project import initialize_project
from tests.factories import valid_contract_data


def git(*argv: str, cwd: Path) -> None:
    subprocess.run(
        ["git", *argv],
        cwd=cwd,
        check=True,
        capture_output=True,
        shell=False,
    )


def test_low_risk_loop_reaches_done_only_after_fresh_evidence(tmp_path: Path) -> None:
    project = tmp_path / "consumer"
    project.mkdir()
    git("init", "-b", "master", cwd=project)
    git("config", "user.email", "test@example.com", cwd=project)
    git("config", "user.name", "Test", cwd=project)
    (project / "tests").mkdir()
    (project / "tests" / "test_value.py").write_text(
        "def test_value():\n    assert 2 + 2 == 4\n",
        encoding="utf-8",
    )
    initialize_project(project)
    git("add", ".", cwd=project)
    git("commit", "-m", "initial", cwd=project)

    data = valid_contract_data()
    data["mode"] = "autonomous"
    data["human_gates"] = ["contract_approval"]
    data["repositories"][0]["path"] = str(project)
    data["validation_commands"][0]["argv"] = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_value.py",
        "-q",
    ]
    contract_path = tmp_path / "contract.yaml"
    contract_path.write_text(
        yaml.safe_dump(data, sort_keys=False),
        encoding="utf-8",
    )
    contract = load_contract(contract_path)
    store = RunStore.create(project, contract)

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
        summary="approved autonomous dry run",
    )
    for target in (
        LoopStatus.PLANNING,
        LoopStatus.EXECUTING,
        LoopStatus.VERIFYING,
    ):
        store.record_transition(actor="maker", target=target, reason=target.value)

    evidence = ValidationRunner(contract, store).run("VAL-1")
    store.record_transition(
        actor="maker",
        target=LoopStatus.DECIDING,
        reason="validation evidence recorded",
    )
    context = CompletionContext(
        evidence=[evidence],
        current_fingerprints={"target": git_fingerprint(project)},
        checker_verdict=None,
        git_delivered={"target": True},
        scope_valid=evaluate_scope(contract).valid,
        gates_clear=True,
        contract_current=True,
    )
    evaluation = DoneEvaluator(contract).evaluate(context)

    assert evaluation.done is True
    assert main(
        [
            "run",
            "complete",
            str(store.run_dir),
            "--actor",
            "maker",
            "--reason",
            "evidence complete",
        ]
    ) == 0
    assert store.load_state().status is LoopStatus.DONE
