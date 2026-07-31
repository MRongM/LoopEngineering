import json
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from loop_engineering.contract import load_contract, write_contract_schema
from loop_engineering.models.contract import LoopContract
from tests.factories import autonomous_risk_contract_data, valid_contract_data


def test_valid_contract_is_strict_and_defaults_to_collaborative(tmp_path: Path) -> None:
    data = valid_contract_data()
    data.pop("mode")
    path = tmp_path / "contract.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    contract = load_contract(path)

    assert contract.mode.value == "collaborative"
    assert contract.protocol_version == "0.2.0"


def test_legacy_contract_remains_valid_without_risk_disclosures() -> None:
    data = valid_contract_data(protocol_version="0.1.0")
    data["authorized_operations"] = [
        {
            "kind": "file_delete",
            "repository_id": "target",
            "target": "tmp/generated.txt",
        }
    ]

    contract = LoopContract.model_validate(data)

    assert contract.protocol_version == "0.1.0"
    assert contract.authorized_operations[0].kind == "file_delete"


def test_autonomous_v020_accepts_disclosed_high_risk_without_final_gate() -> None:
    contract = LoopContract.model_validate(autonomous_risk_contract_data())

    assert contract.human_gates == ["contract_approval"]
    assert contract.authorized_operations[0].risk_id == "RISK-1"


@pytest.mark.parametrize(
    "missing",
    ["risk_id", "risk_level", "impact", "worst_case", "recovery", "evidence"],
)
def test_v020_authorized_operation_requires_complete_risk_disclosure(
    missing: str,
) -> None:
    data = autonomous_risk_contract_data()
    data["authorized_operations"][0].pop(missing)

    with pytest.raises(ValidationError, match="risk disclosure"):
        LoopContract.model_validate(data)


def test_v020_risk_ids_must_be_unique() -> None:
    data = autonomous_risk_contract_data()
    data["authorized_operations"].append(data["authorized_operations"][0].copy())

    with pytest.raises(ValidationError, match="risk ids must be unique"):
        LoopContract.model_validate(data)


@pytest.mark.parametrize("kind", ["production_access", "sensitive_data"])
def test_v020_production_and_sensitive_risks_must_be_high(kind: str) -> None:
    data = autonomous_risk_contract_data(kind)
    data["authorized_operations"][0]["risk_level"] = "medium"

    with pytest.raises(ValidationError, match="must be high risk"):
        LoopContract.model_validate(data)


def test_v020_sensitive_operation_requires_matching_permission() -> None:
    data = autonomous_risk_contract_data("sensitive_data")
    data["permissions"]["sensitive_data"] = False

    with pytest.raises(ValidationError, match="permission sensitive_data is false"):
        LoopContract.model_validate(data)


@pytest.mark.parametrize(
    ("kind", "permission"),
    [
        ("network", "network"),
        ("dependency_change", "dependency_changes"),
        ("global_package", "dependency_changes"),
        ("database_change", "database_changes"),
    ],
)
def test_v020_authorized_operation_requires_category_permission(
    kind: str,
    permission: str,
) -> None:
    data = autonomous_risk_contract_data(kind)
    data["permissions"][permission] = False

    with pytest.raises(ValidationError, match=f"permission {permission} is false"):
        LoopContract.model_validate(data)


def test_v020_contract_risk_cannot_understate_operation_risk() -> None:
    data = autonomous_risk_contract_data()
    data["risk_level"] = "medium"
    data["budget"]["max_checker_revisions"] = 2

    with pytest.raises(ValidationError, match="contract risk level understates"):
        LoopContract.model_validate(data)


@pytest.mark.parametrize(
    "target",
    ["production/*", "${PRODUCTION_TARGET}", "$PRODUCTION_TARGET", "[", "/"],
)
def test_v020_authorized_operation_requires_resolved_exact_target(
    target: str,
) -> None:
    data = autonomous_risk_contract_data()
    data["authorized_operations"][0]["target"] = target

    with pytest.raises(ValidationError, match="resolved exact target"):
        LoopContract.model_validate(data)


def test_v020_high_risk_autonomous_requires_a_high_risk_disclosure() -> None:
    data = valid_contract_data()
    data["mode"] = "autonomous"
    data["risk_level"] = "high"
    data["human_gates"] = ["contract_approval"]
    data["budget"]["max_checker_revisions"] = 3

    with pytest.raises(ValidationError, match="high-risk autonomous contract"):
        LoopContract.model_validate(data)


def test_legacy_high_risk_autonomous_contract_still_requires_final_gate() -> None:
    data = valid_contract_data(protocol_version="0.1.0")
    data["mode"] = "autonomous"
    data["risk_level"] = "high"
    data["human_gates"] = ["contract_approval"]
    data["budget"]["max_checker_revisions"] = 3

    with pytest.raises(ValidationError, match="requires final_acceptance"):
        LoopContract.model_validate(data)


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
