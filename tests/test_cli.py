import json
from pathlib import Path

import pytest
import yaml

from loop_engineering.cli import main
from loop_engineering.ledger import RunStore
from loop_engineering.models.contract import LoopContract
from loop_engineering.models.run import LoopStatus
from loop_engineering.project import initialize_project
from tests.factories import autonomous_risk_contract_data, valid_contract_data


def test_cli_help_uses_unique_name_and_keeps_every_command_group(capsys) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--help"])

    assert exit_info.value.code == 0
    help_text = capsys.readouterr().out
    assert help_text.startswith("usage: loop-engine ")
    for group in (
        "project",
        "contract",
        "schema",
        "run",
        "evidence",
        "budget",
        "completion",
        "gate",
        "scope",
        "git",
        "watch",
    ):
        assert group in help_text


def test_cli_watch_discovers_project_and_filters_terminal_runs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys,
) -> None:
    project = tmp_path / "project"
    nested = project / "src" / "feature"
    nested.mkdir(parents=True)
    initialize_project(project)
    active_data = valid_contract_data()
    active_data["loop_id"] = "loop-active"
    active_data["repositories"][0]["path"] = str(project)
    RunStore.create(project, LoopContract.model_validate(active_data))
    terminal_data = valid_contract_data()
    terminal_data["loop_id"] = "loop-terminal"
    terminal_data["repositories"][0]["path"] = str(project)
    terminal = RunStore.create(project, LoopContract.model_validate(terminal_data))
    terminal.save_state(
        terminal.load_state().model_copy(update={"status": LoopStatus.DONE})
    )
    monkeypatch.chdir(nested)

    assert main(["watch"]) == 0
    active_output = capsys.readouterr().out
    assert "loop-active" in active_output
    assert "loop-terminal" not in active_output

    assert main(["watch", "--all"]) == 0
    all_output = capsys.readouterr().out
    assert "loop-active" in all_output
    assert "loop-terminal" in all_output


def test_cli_watch_rejects_a_run_directory_argument(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["watch", str(tmp_path)])

    assert exit_info.value.code == 2


def test_run_command_group_does_not_expose_watch(capsys) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["run", "--help"])

    assert exit_info.value.code == 0
    assert "watch" not in capsys.readouterr().out


def test_cli_validates_contract_and_exports_schemas(tmp_path: Path, capsys) -> None:
    contract = tmp_path / "contract.yaml"
    contract.write_text(yaml.safe_dump(valid_contract_data(), sort_keys=False))

    assert main(["contract", "validate", str(contract)]) == 0
    assert json.loads(capsys.readouterr().out)["valid"] is True

    schemas = tmp_path / "schemas"
    assert main(["schema", "export", str(schemas)]) == 0
    assert sorted(path.name for path in schemas.iterdir()) == [
        "loop-contract.schema.json",
        "loop-event.schema.json",
        "loop-state.schema.json",
    ]


def test_cli_validation_error_does_not_echo_secret_input(
    tmp_path: Path,
    capsys,
) -> None:
    data = valid_contract_data()
    data["validation_commands"][0]["argv"] = ["curl", "--token", "secret-value"]
    contract = tmp_path / "contract.yaml"
    contract.write_text(yaml.safe_dump(data, sort_keys=False))

    assert main(["contract", "validate", str(contract)]) == 2
    error = json.loads(capsys.readouterr().err)
    assert "secret-value" not in json.dumps(error)
    assert "inline secret flags" in error["message"]


def test_cli_creates_and_reads_run(tmp_path: Path, capsys) -> None:
    contract_data = valid_contract_data()
    contract_data["repositories"][0]["path"] = str(tmp_path)
    contract = tmp_path / "contract.yaml"
    contract.write_text(yaml.safe_dump(contract_data, sort_keys=False))

    assert main(["run", "create", str(contract), "--project", str(tmp_path)]) == 0
    run_dir = tmp_path / ".loop-runs" / "loop-example-001"
    capsys.readouterr()
    assert main(["run", "status", str(run_dir)]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "intake"


def test_cli_result_updates_progress_and_strategy_counters(
    tmp_path: Path,
    capsys,
) -> None:
    data = valid_contract_data()
    data["repositories"][0]["path"] = str(tmp_path)
    contract = tmp_path / "contract.yaml"
    contract.write_text(yaml.safe_dump(data, sort_keys=False))
    assert main(["run", "create", str(contract), "--project", str(tmp_path)]) == 0
    run_dir = tmp_path / ".loop-runs" / data["loop_id"]
    capsys.readouterr()

    assert main(
        [
            "run",
            "intent",
            str(run_dir),
            "--actor",
            "maker",
            "--summary",
            "attempt",
        ]
    ) == 0
    action_id = json.loads(capsys.readouterr().out)["action_id"]
    assert main(
        [
            "run",
            "result",
            str(run_dir),
            action_id,
            "--actor",
            "maker",
            "--summary",
            "no progress",
            "--progress",
            "no",
            "--same-strategy",
            "yes",
        ]
    ) == 0
    capsys.readouterr()

    assert main(["run", "status", str(run_dir)]) == 0
    status = json.loads(capsys.readouterr().out)
    assert status["no_progress_cycles"] == 1
    assert status["same_strategy_retries"] == 1


def test_cli_requires_contract_approval_before_planning(
    tmp_path: Path,
    capsys,
) -> None:
    data = valid_contract_data()
    data["repositories"][0]["path"] = str(tmp_path)
    contract = tmp_path / "contract.yaml"
    contract.write_text(yaml.safe_dump(data, sort_keys=False))
    assert main(["run", "create", str(contract), "--project", str(tmp_path)]) == 0
    run_dir = tmp_path / ".loop-runs" / data["loop_id"]
    for target in ("discovering", "contract_drafting", "awaiting_approval"):
        assert main(
            [
                "run",
                "transition",
                str(run_dir),
                target,
                "--actor",
                "maker",
                "--reason",
                target,
            ]
        ) == 0
    capsys.readouterr()

    planning = [
        "run",
        "transition",
        str(run_dir),
        "planning",
        "--actor",
        "maker",
        "--reason",
        "approved plan",
    ]
    assert main(planning) == 2
    assert "contract approval" in json.loads(capsys.readouterr().err)["message"]
    assert main(
        [
            "run",
            "approval",
            str(run_dir),
            "--actor",
            "user",
            "--gate",
            "contract_approval",
            "--decision",
            "approve",
            "--summary",
            "approved",
        ]
    ) == 0
    capsys.readouterr()
    assert main(planning) == 0


def test_cli_gate_check_requires_bound_approval_for_v030_production(
    tmp_path: Path,
    capsys,
) -> None:
    contract = tmp_path / "contract.yaml"
    contract.write_text(yaml.safe_dump(valid_contract_data(), sort_keys=False))
    request = tmp_path / "request.json"
    request.write_text(
        json.dumps({"kind": "production_access", "target": "production"}),
        encoding="utf-8",
    )

    assert main(["gate", "check", str(contract), str(request)]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["outcome"] == "pause"
    assert output["required_gate"] == "contract_approval"
    assert "confirmation" not in output


def test_cli_gate_check_returns_confirmation_for_legacy_production(
    tmp_path: Path,
    capsys,
) -> None:
    contract = tmp_path / "contract.yaml"
    contract.write_text(
        yaml.safe_dump(
            valid_contract_data(protocol_version="0.1.0"),
            sort_keys=False,
        )
    )
    request = tmp_path / "request.json"
    request.write_text(
        json.dumps({"kind": "production_access", "target": "production"}),
        encoding="utf-8",
    )

    assert main(["gate", "check", str(contract), str(request)]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["outcome"] == "pause"
    assert output["required_gate"] == "dangerous_action"
    assert output["confirmation"].startswith("⚠️ 危险操作检测！")


def test_cli_gate_check_uses_bound_run_authorization_for_autonomous_risk(
    tmp_path: Path,
    capsys,
) -> None:
    data = autonomous_risk_contract_data()
    data["repositories"][0]["path"] = str(tmp_path)
    contract = tmp_path / "contract.yaml"
    contract.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    request = tmp_path / "request.json"
    request.write_text(
        json.dumps(
            {
                "kind": "production_access",
                "repository_id": "target",
                "target": "production/customer-index",
            }
        ),
        encoding="utf-8",
    )
    assert main(["run", "create", str(contract), "--project", str(tmp_path)]) == 0
    run_dir = tmp_path / ".loop-runs" / data["loop_id"]
    assert main(
        [
            "run",
            "approval",
            str(run_dir),
            "--actor",
            "user",
            "--gate",
            "contract_approval",
            "--decision",
            "approve",
            "--summary",
            "accepted disclosed production risk",
        ]
    ) == 0
    capsys.readouterr()

    assert main(["gate", "check", str(run_dir), str(request)]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["outcome"] == "allow"
    assert output["required_gate"] is None
    assert "confirmation" not in output


def test_cli_direct_bound_contract_cannot_prove_risk_approval(
    tmp_path: Path,
    capsys,
) -> None:
    data = autonomous_risk_contract_data()
    contract = tmp_path / "contract.yaml"
    contract.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    request = tmp_path / "request.json"
    request.write_text(
        json.dumps(
            {
                "kind": "production_access",
                "repository_id": "target",
                "target": "production/customer-index",
            }
        ),
        encoding="utf-8",
    )

    assert main(["gate", "check", str(contract), str(request)]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["outcome"] == "pause"
    assert output["required_gate"] == "contract_approval"
    assert "confirmation" not in output


def test_cli_replaces_only_next_contract_version_while_awaiting(
    tmp_path: Path,
    capsys,
) -> None:
    data = valid_contract_data()
    data["repositories"][0]["path"] = str(tmp_path)
    first = tmp_path / "contract-v1.yaml"
    first.write_text(yaml.safe_dump(data, sort_keys=False))
    assert main(["run", "create", str(first), "--project", str(tmp_path)]) == 0
    run_dir = tmp_path / ".loop-runs" / data["loop_id"]
    for target in ("discovering", "contract_drafting", "awaiting_approval"):
        assert main(
            [
                "run",
                "transition",
                str(run_dir),
                target,
                "--actor",
                "maker",
                "--reason",
                target,
            ]
        ) == 0
    assert main(
        [
            "run",
            "approval",
            str(run_dir),
            "--actor",
            "user",
            "--gate",
            "final_acceptance",
            "--decision",
            "approve",
            "--summary",
            "version one only",
        ]
    ) == 0
    data["contract_version"] = 2
    second = tmp_path / "contract-v2.yaml"
    second.write_text(yaml.safe_dump(data, sort_keys=False))
    capsys.readouterr()

    assert main(
        [
            "run",
            "revise",
            str(run_dir),
            str(second),
            "--actor",
            "user",
            "--summary",
            "approved revision",
        ]
    ) == 0
    assert json.loads(capsys.readouterr().out)["contract_version"] == 2
    assert main(["run", "status", str(run_dir)]) == 0
    status = json.loads(capsys.readouterr().out)
    assert status["approvals"] == {"contract_revision": True}
