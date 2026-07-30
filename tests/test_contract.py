import json
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from loop_engineering.contract import load_contract, write_contract_schema
from loop_engineering.models.contract import LoopContract
from tests.factories import valid_contract_data


def test_valid_contract_is_strict_and_defaults_to_collaborative(tmp_path: Path) -> None:
    data = valid_contract_data()
    data.pop("mode")
    path = tmp_path / "contract.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    contract = load_contract(path)

    assert contract.mode.value == "collaborative"
    assert contract.protocol_version == "0.1.0"


def test_contract_rejects_unknown_fields() -> None:
    data = valid_contract_data()
    data["unapproved"] = True

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        LoopContract.model_validate(data)


@pytest.mark.parametrize("field", ["force_push", "history_rewrite", "merge", "deploy"])
def test_contract_can_never_enable_forbidden_git_actions(field: str) -> None:
    data = valid_contract_data()
    data["git_policy"][field] = True

    with pytest.raises(ValidationError):
        LoopContract.model_validate(data)


def test_push_requires_exact_branch_and_remote() -> None:
    data = valid_contract_data()
    data["git_policy"]["targets"][0]["push"] = True

    with pytest.raises(ValidationError, match="branch and remote"):
        LoopContract.model_validate(data)


@pytest.mark.parametrize(
    ("field", "value"),
    [("branch", "--force"), ("remote", "--force"), ("pr_target", "main:admin")],
)
def test_git_targets_reject_option_like_or_refspec_values(field: str, value: str) -> None:
    data = valid_contract_data()
    data["git_policy"]["targets"][0].update(
        {"commit": True, "branch": "feat/safe", "worktree_path": "worktree"}
    )
    data["git_policy"]["targets"][0][field] = value

    with pytest.raises(ValidationError):
        LoopContract.model_validate(data)


def test_pr_requires_push_and_exact_target_branch() -> None:
    data = valid_contract_data()
    data["git_policy"]["targets"][0].update(
        {"create_pr": True, "branch": "feat/example", "remote": "origin"}
    )

    with pytest.raises(ValidationError, match="create_pr requires push and pr_target"):
        LoopContract.model_validate(data)


def test_cross_repository_dependency_graph_must_be_acyclic() -> None:
    data = valid_contract_data()
    first = data["repositories"][0]
    first["depends_on"] = ["shared"]
    data["repositories"].append(
        {
            "id": "shared",
            "path": str(Path.cwd()),
            "base_branch": "master",
            "allowed_paths": ["src/"],
            "depends_on": ["target"],
        }
    )

    with pytest.raises(ValidationError, match="contains a cycle"):
        LoopContract.model_validate(data)


def test_network_validation_requires_network_permission() -> None:
    data = valid_contract_data()
    data["validation_commands"][0]["requires_network"] = True

    with pytest.raises(ValidationError, match="requires unapproved network"):
        LoopContract.model_validate(data)


def test_collaborative_contract_requires_final_acceptance_gate() -> None:
    data = valid_contract_data()
    data["human_gates"] = ["contract_approval"]

    with pytest.raises(ValidationError, match="requires final_acceptance"):
        LoopContract.model_validate(data)


def test_every_contract_requires_one_contract_approval_gate() -> None:
    data = valid_contract_data()
    data["mode"] = "autonomous"
    data["human_gates"] = ["final_acceptance"]

    with pytest.raises(ValidationError, match="requires contract_approval"):
        LoopContract.model_validate(data)


def test_validation_command_rejects_inline_secret_flags() -> None:
    data = valid_contract_data()
    data["validation_commands"][0]["argv"] = ["curl", "--token", "secret"]

    with pytest.raises(ValidationError, match="inline secret flags"):
        LoopContract.model_validate(data)


@pytest.mark.parametrize(
    "boundary",
    ["../src", "/system", "C:\\system", "src/*.py", "$PROJECT_ROOT/src"],
)
def test_contract_rejects_unsafe_allowed_path_boundaries(boundary: str) -> None:
    data = valid_contract_data()
    data["repositories"][0]["allowed_paths"] = [boundary]

    with pytest.raises(ValidationError, match="unsafe relative path"):
        LoopContract.model_validate(data)


def test_schema_export_is_deterministic(tmp_path: Path) -> None:
    first = write_contract_schema(tmp_path / "first.json")
    second = write_contract_schema(tmp_path / "second.json")

    assert json.loads(first.read_text()) == json.loads(second.read_text())
    assert json.loads(first.read_text())["title"] == "LoopContract"
