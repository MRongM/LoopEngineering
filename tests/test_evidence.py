import subprocess
import sys
from pathlib import Path

import pytest

import loop_engineering.evidence as evidence_module
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
    (path / ".gitignore").write_text("__pycache__/\n")
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


def test_validation_spawn_failure_records_a_closed_failed_result(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    init_git_repo(project)
    data = valid_contract_data()
    data["repositories"][0]["path"] = str(project)
    data["validation_commands"][0]["argv"] = [
        "loop-engine-command-that-does-not-exist"
    ]
    contract = LoopContract.model_validate(data)
    store = RunStore.create(project, contract)

    evidence = ValidationRunner(contract, store).run("VAL-1")

    assert evidence.passed is False
    assert evidence.exit_code == 127
    assert evidence.error_type == "FileNotFoundError"
    assert store.pending_intents() == []


def test_validation_rejects_a_successful_command_that_mutates_the_workspace(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    init_git_repo(project)
    data = valid_contract_data()
    data["repositories"][0]["path"] = str(project)
    data["validation_commands"][0]["argv"] = [
        sys.executable,
        "-c",
        (
            "from pathlib import Path; "
            f"Path({str(project / 'generated.log')!r}).write_text('generated')"
        ),
    ]
    contract = LoopContract.model_validate(data)
    store = RunStore.create(project, contract)

    evidence = ValidationRunner(contract, store).run("VAL-1")

    assert evidence.exit_code == 0
    assert evidence.passed is False
    assert evidence.workspace_clean is False
    assert evidence.workspace_changes == ["generated.log"]
    assert store.pending_intents() == []


def test_validation_runs_in_an_isolated_control_root_snapshot(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    init_git_repo(project)
    data = valid_contract_data()
    data["repositories"][0]["path"] = str(project)
    data["validation_commands"][0]["argv"] = [
        sys.executable,
        "-c",
        "from pathlib import Path; Path('generated.log').write_text('generated')",
    ]
    contract = LoopContract.model_validate(data)
    store = RunStore.create(project, contract)

    evidence = ValidationRunner(contract, store).run("VAL-1")

    assert evidence.passed is True
    assert evidence.workspace_clean is True
    assert not (project / "generated.log").exists()
    assert list(store.cache_dir.rglob("generated.log"))


def test_validation_fails_when_source_changes_during_snapshot_creation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    init_git_repo(project)
    data = valid_contract_data()
    data["repositories"][0]["path"] = str(project)
    marker = project / "command-ran.txt"
    data["validation_commands"][0]["argv"] = [
        sys.executable,
        "-c",
        f"from pathlib import Path; Path({str(marker)!r}).write_text('ran')",
    ]
    contract = LoopContract.model_validate(data)
    store = RunStore.create(project, contract)
    original_copy = evidence_module._copy_validation_snapshot

    def copy_then_mutate_source(repository: Path, destination: Path) -> None:
        original_copy(repository, destination)
        (repository / "tests" / "test_example.py").write_text(
            "def test_changed():\n    assert True\n",
            encoding="utf-8",
        )

    monkeypatch.setattr(
        evidence_module,
        "_copy_validation_snapshot",
        copy_then_mutate_source,
    )

    evidence = ValidationRunner(contract, store).run("VAL-1")

    assert evidence.passed is False
    assert evidence.exit_code == 126
    assert evidence.workspace_clean is False
    assert not marker.exists()
    assert store.pending_intents() == []


def test_validation_rejects_a_snapshot_symlink_that_escapes_the_repository(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    init_git_repo(project)
    external = tmp_path / "external"
    external.mkdir()
    link = project / "external-link"
    try:
        link.symlink_to(external, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"symlinks are unavailable: {error}")
    data = valid_contract_data()
    data["repositories"][0]["path"] = str(project)
    data["validation_commands"][0]["argv"] = [
        sys.executable,
        "-c",
        "from pathlib import Path; Path('external-link/touched').write_text('unsafe')",
    ]
    contract = LoopContract.model_validate(data)
    store = RunStore.create(project, contract)

    evidence = ValidationRunner(contract, store).run("VAL-1")

    assert evidence.passed is False
    assert evidence.exit_code == 126
    assert evidence.error_type == "ValueError"
    assert not (external / "touched").exists()
    assert store.pending_intents() == []


def test_validation_routes_generic_temporary_and_cache_data_inside_control_root(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    init_git_repo(project)
    data = valid_contract_data()
    data["repositories"][0]["path"] = str(project)
    data["validation_commands"][0]["argv"] = [
        sys.executable,
        "-c",
        (
            "import os; from pathlib import Path; "
            "root = Path(os.environ['XDG_CACHE_HOME']); "
            "root.mkdir(parents=True, exist_ok=True); "
            "(root / 'cache.txt').write_text('cached')"
        ),
    ]
    contract = LoopContract.model_validate(data)
    store = RunStore.create(project, contract)

    evidence = ValidationRunner(contract, store).run("VAL-1")

    assert evidence.passed is True
    assert evidence.workspace_clean is True
    assert list((project / ".loop-engine" / "cache").rglob("cache.txt"))


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
            git_delivered={"target": True},
            scope_valid=False,
            gates_clear=False,
            contract_current=False,
        )
    )

    assert "actual diff is outside approved scope" in evaluation.reasons
    assert "a required gate is unresolved" in evaluation.reasons
    assert "evidence belongs to a stale contract version" in evaluation.reasons
