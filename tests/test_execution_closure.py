import pytest
from pydantic import ValidationError

from loop_engineering.contract import contract_fingerprint
from loop_engineering.models.contract import LoopContract
from tests.factories import valid_contract_data


def first_contract_data() -> dict:
    return valid_contract_data()


def test_first_release_is_the_only_supported_protocol_version() -> None:
    contract = LoopContract.model_validate(first_contract_data())

    assert contract.protocol_version == "0.1.0"
    data = first_contract_data()
    data["protocol_version"] = "9.9.9"
    with pytest.raises(ValidationError, match="protocol_version"):
        LoopContract.model_validate(data)


def test_first_release_requires_an_execution_closed_plan() -> None:
    data = first_contract_data()
    data.pop("execution_plan")

    with pytest.raises(ValidationError, match="execution_plan"):
        LoopContract.model_validate(data)


def test_first_release_requires_isolated_validation() -> None:
    data = first_contract_data()
    data["validation_commands"][0]["workspace_policy"] = "clean"

    with pytest.raises(ValidationError, match="workspace_policy"):
        LoopContract.model_validate(data)


def test_first_release_accepts_an_execution_closed_contract() -> None:
    contract = LoopContract.model_validate(first_contract_data())

    assert contract.protocol_version == "0.1.0"
    assert [action.target for action in contract.execution_plan.actions] == [
        "src/",
        "tests/",
    ]


def test_execution_plan_is_bound_into_the_approved_contract_hash() -> None:
    original = LoopContract.model_validate(first_contract_data())
    revised_data = first_contract_data()
    revised_data["execution_plan"]["design_decisions"].append(
        "Keep validation side effects inside the project control root."
    )
    revised = LoopContract.model_validate(revised_data)

    assert contract_fingerprint(original) != contract_fingerprint(revised)


def test_first_release_rejects_a_planned_action_that_would_pause_after_approval() -> None:
    data = first_contract_data()
    data["execution_plan"]["actions"].append(
        {
            "kind": "file_delete",
            "repository_id": "target",
            "target": "tests/generated.log",
            "impact": "Deletes a generated file",
            "risk": "The wrong file may be removed",
            "recovery": "Regenerate the file",
            "evidence": "The validation workspace must remain clean",
        }
    )

    with pytest.raises(ValidationError, match="execution plan is not closed"):
        LoopContract.model_validate(data)


def test_first_release_budget_covers_one_full_validation_pass() -> None:
    data = first_contract_data()
    data["validation_commands"][0]["timeout_seconds"] = 1800
    data["budget"]["max_minutes"] = 20

    with pytest.raises(ValidationError, match="validation timeout budget"):
        LoopContract.model_validate(data)


def test_first_release_contract_has_no_routine_post_approval_human_gate() -> None:
    data = first_contract_data()
    data["human_gates"].append("plan_approval")

    with pytest.raises(ValidationError, match="contract_approval"):
        LoopContract.model_validate(data)
