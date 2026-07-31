import subprocess
import sys
from pathlib import Path

from loop_engineering.evidence import (
    DoneEvaluator,
    ValidationRunner,
    evaluate_scope,
    git_fingerprint,
)
from loop_engineering.ledger import RunStore
from loop_engineering.models.contract import LoopContract
from loop_engineering.models.evidence import CompletionContext
from loop_engineering.models.run import CheckerVerdict
from loop_engineering.paths import is_allowed_path
from tests.factories import valid_contract_data


def run(*argv: str, cwd: Path | None = None) -> None:
    subprocess.run(argv, cwd=cwd, check=True, capture_output=True, shell=False)


def init_git_repo(path: Path) -> None:
    run("git", "init", "-b", "master", str(path))
    run("git", "-C", str(path), "config", "user.email", "test@example.com")
    run("git", "-C", str(path), "config", "user.name", "Test")
    (path / "tests").mkdir()
    (path / "tests" / "test_example.py").write_text("def test_ok():\n    assert True\n")
    (path / ".gitignore").write_text(".loop-runs/\n")
    run("git", "-C", str(path), "add", ".")
    run("git", "-C", str(path), "commit", "-m", "initial")


def test_validation_uses_argv_and_records_redacted_output(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    init_git_repo(project)
    data = valid_contract_data()
    data["repositories"][0]["path"] = str(project)
    data["validation_commands"][0]["argv"] = [
        sys.executable,
        "-c",
        "print('token=secret-value')",
    ]
    contract = LoopContract.model_validate(data)
    store = RunStore.create(project, contract)

    evidence = ValidationRunner(contract, store).run("VAL-1")

    stdout = (store.evidence_dir / evidence.stdout_file).read_text()
    assert evidence.passed is True
    assert evidence.shell is False
    assert "[REDACTED]" in stdout
    assert "secret-value" not in stdout


def test_validation_rejects_cwd_escape(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    init_git_repo(project)
    data = valid_contract_data()
    data["repositories"][0]["path"] = str(project)
    data["validation_commands"][0]["cwd"] = "../"
    contract = LoopContract.model_validate(data)
    store = RunStore.create(project, contract)

    try:
        ValidationRunner(contract, store).run("VAL-1")
    except ValueError as error:
        assert "outside repository" in str(error)
    else:
        raise AssertionError("cwd escape was accepted")


def test_done_rejects_stale_or_missing_evidence(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    init_git_repo(project)
    data = valid_contract_data()
    data["repositories"][0]["path"] = str(project)
    contract = LoopContract.model_validate(data)

    evaluation = DoneEvaluator(contract).evaluate(
        CompletionContext(
            evidence=[],
            current_fingerprints={"target": git_fingerprint(project)},
            checker_verdict=None,
            human_accepted=True,
            git_delivered={"target": True},
            scope_valid=True,
            gates_clear=True,
            contract_current=True,
        )
    )

    assert evaluation.done is False
    assert evaluation.reasons == ["AC-1 lacks fresh evidence VAL-1"]


def test_scope_evaluation_reports_out_of_scope_files(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    init_git_repo(project)
    data = valid_contract_data()
    data["repositories"][0]["path"] = str(project)
    contract = LoopContract.model_validate(data)
    (project / "outside.txt").write_text("not approved\n")

    result = evaluate_scope(contract)

    assert result.valid is False
    assert result.violations == ["target:outside.txt"]


def test_scope_evaluation_includes_commits_since_base_branch(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    init_git_repo(project)
    run("git", "-C", str(project), "checkout", "-b", "feat/scope")
    (project / "outside.txt").write_text("committed but not approved\n")
    run("git", "-C", str(project), "add", "outside.txt")
    run("git", "-C", str(project), "commit", "-m", "outside scope")
    data = valid_contract_data()
    data["repositories"][0]["path"] = str(project)
    contract = LoopContract.model_validate(data)

    result = evaluate_scope(contract)

    assert result.valid is False
    assert result.violations == ["target:outside.txt"]


def test_repository_root_can_be_an_explicit_allowed_boundary() -> None:
    assert is_allowed_path("README.md", ["."]) is True
    assert is_allowed_path("../secret.txt", ["."]) is False


def test_fingerprint_requires_the_exact_git_root(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    init_git_repo(project)

    try:
        git_fingerprint(project / "tests")
    except ValueError as error:
        assert "exact Git root" in str(error)
    else:
        raise AssertionError("repository subdirectory was accepted as a Git root")


def test_medium_risk_requires_checker_accept() -> None:
    data = valid_contract_data()
    data["mode"] = "autonomous"
    data["human_gates"] = ["contract_approval"]
    data["risk_level"] = "medium"
    data["budget"]["max_checker_revisions"] = 2
    contract = LoopContract.model_validate(data)

    evaluation = DoneEvaluator(contract).evaluate(
        CompletionContext(
            evidence=[],
            current_fingerprints={},
            checker_verdict=CheckerVerdict.REVISE,
            human_accepted=False,
            git_delivered={"target": True},
            scope_valid=True,
            gates_clear=True,
            contract_current=True,
        )
    )

    assert "checker has not accepted" in evaluation.reasons


def test_done_rejects_scope_drift_unresolved_gate_and_stale_contract() -> None:
    contract = LoopContract.model_validate(valid_contract_data())

    evaluation = DoneEvaluator(contract).evaluate(
        CompletionContext(
            evidence=[],
            current_fingerprints={},
            checker_verdict=None,
            human_accepted=False,
            git_delivered={"target": True},
            scope_valid=False,
            gates_clear=False,
            contract_current=False,
        )
    )

    assert "actual diff is outside approved scope" in evaluation.reasons
    assert "a required gate is unresolved" in evaluation.reasons
    assert "evidence belongs to a stale contract version" in evaluation.reasons


def test_explicit_final_acceptance_gate_remains_enforced() -> None:
    data = valid_contract_data()
    data["human_gates"].append("final_acceptance")
    contract = LoopContract.model_validate(data)

    evaluation = DoneEvaluator(contract).evaluate(
        CompletionContext(
            evidence=[],
            current_fingerprints={},
            checker_verdict=None,
            human_accepted=False,
            git_delivered={"target": True},
            scope_valid=True,
            gates_clear=True,
            contract_current=True,
        )
    )

    assert "human final acceptance is missing" in evaluation.reasons
