from pathlib import Path

import pytest
from pydantic import ValidationError

from loop_engineering.contract import contract_fingerprint
from loop_engineering.models.contract import LoopContract
from loop_engineering.models.run import ContractAuthorization
from loop_engineering.policy import (
    ActionKind,
    ActionRequest,
    GateOutcome,
    GatePolicy,
)
from tests.factories import autonomous_risk_contract_data, valid_contract_data


def approved_policy(data: dict) -> GatePolicy:
    contract = LoopContract.model_validate(data)
    authorization = ContractAuthorization(
        protocol_version=contract.protocol_version,
        contract_version=contract.contract_version,
        contract_sha256=contract_fingerprint(contract),
        accepted_risk_ids=sorted(
            operation.risk_id for operation in contract.authorized_operations
        ),
    )
    return GatePolicy(contract, authorization=authorization)


def risk_operation(kind: str, target: str, *, level: str = "low") -> dict:
    return {
        "risk_id": "RISK-1",
        "kind": kind,
        "repository_id": "target",
        "target": target,
        "risk_level": level,
        "impact": "Changes the exact approved target",
        "worst_case": "The target may require recovery",
        "recovery": "Apply the approved recovery procedure",
        "evidence": "The execution plan requires this exact action",
    }


def planned_action(kind: str, target: str, **extra: str) -> dict:
    action = {
        "kind": kind,
        "repository_id": "target",
        "target": target,
        "impact": "Changes the exact approved target",
        "risk": "The target may require recovery",
        "recovery": "Apply the approved recovery procedure",
        "evidence": "The execution plan requires this exact action",
    }
    action.update(extra)
    return action


def test_merge_deploy_force_and_history_rewrite_are_always_denied() -> None:
    contract = LoopContract.model_validate(valid_contract_data())
    for kind in (
        ActionKind.MERGE,
        ActionKind.DEPLOY,
        ActionKind.FORCE_PUSH,
        ActionKind.HISTORY_REWRITE,
    ):
        decision = GatePolicy(contract).evaluate(
            ActionRequest(kind=kind, repository_id="target", target="master")
        )
        assert decision.outcome is GateOutcome.DENY


def test_every_action_requires_the_current_bound_contract_approval() -> None:
    contract = LoopContract.model_validate(valid_contract_data())
    request = ActionRequest(
        kind=ActionKind.FILE_WRITE,
        repository_id="target",
        target="src/app.py",
    )

    missing = GatePolicy(contract).evaluate(request)
    accepted = approved_policy(valid_contract_data()).evaluate(request)

    assert missing.outcome is GateOutcome.PAUSE
    assert missing.required_gate == "contract_approval"
    assert accepted.outcome is GateOutcome.ALLOW


def test_stale_contract_hash_grants_no_authority() -> None:
    contract = LoopContract.model_validate(valid_contract_data())
    stale = ContractAuthorization(
        protocol_version="0.1.0",
        contract_version=1,
        contract_sha256="0" * 64,
        accepted_risk_ids=[],
    )

    decision = GatePolicy(contract, authorization=stale).evaluate(
        ActionRequest(
            kind=ActionKind.FILE_WRITE,
            repository_id="target",
            target="src/app.py",
        )
    )

    assert decision.outcome is GateOutcome.PAUSE
    assert decision.required_gate == "contract_approval"


@pytest.mark.parametrize("kind", [ActionKind.PRODUCTION_ACCESS, ActionKind.SENSITIVE_DATA])
def test_exact_approved_high_risk_operation_uses_the_bound_approval(
    kind: ActionKind,
) -> None:
    data = autonomous_risk_contract_data(kind.value)

    decision = approved_policy(data).evaluate(
        ActionRequest(
            kind=kind,
            repository_id="target",
            target="production/customer-index",
        )
    )

    assert decision.outcome is GateOutcome.ALLOW
    assert decision.requires_confirmation is False


def test_new_high_risk_target_requires_a_complete_contract_revision() -> None:
    decision = approved_policy(autonomous_risk_contract_data()).evaluate(
        ActionRequest(
            kind=ActionKind.PRODUCTION_ACCESS,
            repository_id="target",
            target="production/new-index",
        )
    )

    assert decision.outcome is GateOutcome.PAUSE
    assert decision.required_gate == "contract_revision"


def test_unplanned_risky_action_requires_a_complete_contract_revision() -> None:
    decision = approved_policy(valid_contract_data()).evaluate(
        ActionRequest(
            kind=ActionKind.FILE_DELETE,
            repository_id="target",
            target="tests/generated.log",
        )
    )

    assert decision.outcome is GateOutcome.PAUSE
    assert decision.required_gate == "contract_revision"


def test_exact_disclosed_delete_is_execution_closed_and_allowed() -> None:
    data = valid_contract_data()
    data["authorized_operations"] = [
        risk_operation("file_delete", "tests/generated.log")
    ]
    data["execution_plan"]["actions"].append(
        planned_action("file_delete", "tests/generated.log")
    )

    decision = approved_policy(data).evaluate(
        ActionRequest(
            kind=ActionKind.FILE_DELETE,
            repository_id="target",
            target="tests/generated.log",
        )
    )

    assert decision.outcome is GateOutcome.ALLOW


def test_exact_risk_grant_cannot_expand_repository_allowed_paths() -> None:
    data = valid_contract_data()
    data["authorized_operations"] = [
        risk_operation("file_delete", "config/production.yaml")
    ]
    data["execution_plan"]["actions"].append(
        planned_action("file_delete", "config/production.yaml")
    )

    with pytest.raises(ValidationError, match="outside approved repository paths"):
        LoopContract.model_validate(data)


def test_platform_state_requires_an_exact_plan_and_risk_grant() -> None:
    target = "codex-goal:create:/work/project/.loop-engine/runs/loop-example"
    data = valid_contract_data()
    operation = risk_operation("platform_state", target, level="medium")
    operation["repository_id"] = None
    data["authorized_operations"] = [operation]
    data["risk_level"] = "medium"
    data["budget"]["max_checker_revisions"] = 2
    action = planned_action("platform_state", target)
    action["repository_id"] = None
    data["execution_plan"]["actions"].append(action)

    exact = approved_policy(data).evaluate(
        ActionRequest(kind=ActionKind.PLATFORM_STATE, target=target)
    )
    changed = approved_policy(data).evaluate(
        ActionRequest(
            kind=ActionKind.PLATFORM_STATE,
            target="codex-goal:create:/work/project/.loop-engine/runs/loop-other",
        )
    )

    assert exact.outcome is GateOutcome.ALLOW
    assert changed.outcome is GateOutcome.PAUSE
    assert changed.required_gate == "contract_revision"


def test_file_target_outside_the_approved_plan_requires_revision() -> None:
    policy = approved_policy(valid_contract_data())
    for target in (
        "src_evil/payload.py",
        "../secret.txt",
        "C:\\secret.txt",
        "src/*.py",
        "$PROJECT_ROOT/src/app.py",
    ):
        decision = policy.evaluate(
            ActionRequest(
                kind=ActionKind.FILE_WRITE,
                repository_id="target",
                target=target,
            )
        )
        assert decision.outcome is GateOutcome.PAUSE
        assert decision.required_gate == "contract_revision"


def test_git_preapproval_matches_plan_repository_and_branch_exactly() -> None:
    data = valid_contract_data()
    data["git_policy"]["targets"][0].update(
        {
            "commit": True,
            "branch": "feat/exact",
            "worktree_path": str(Path.cwd() / "worktree"),
        }
    )
    data["authorized_operations"] = [risk_operation("git_commit", "feat/exact")]
    data["execution_plan"]["actions"].append(
        planned_action("git_commit", "feat/exact")
    )
    policy = approved_policy(data)

    exact = policy.evaluate(
        ActionRequest(
            kind=ActionKind.GIT_COMMIT,
            repository_id="target",
            target="feat/exact",
        )
    )
    changed = policy.evaluate(
        ActionRequest(
            kind=ActionKind.GIT_COMMIT,
            repository_id="target",
            target="feat/other",
        )
    )

    assert exact.outcome is GateOutcome.ALLOW
    assert changed.outcome is GateOutcome.PAUSE


def test_database_change_requires_forward_compatibility_and_recovery_details() -> None:
    with pytest.raises(ValidationError, match="database change requires"):
        ActionRequest(
            kind=ActionKind.DATABASE_CHANGE,
            repository_id="target",
            target="schema.users",
        )


def test_database_change_requires_permission_and_an_execution_closed_plan() -> None:
    data = valid_contract_data()
    data["risk_level"] = "medium"
    data["budget"]["max_checker_revisions"] = 2
    data["authorized_operations"] = [
        risk_operation("database_change", "schema.users", level="medium")
    ]
    data["execution_plan"]["actions"].append(
        planned_action(
            "database_change",
            "schema.users",
            forward_plan="add a nullable column",
            compatibility_analysis="old and new code accept null",
            recovery="apply a compensating forward migration",
        )
    )

    with pytest.raises(ValidationError, match="permission database_changes is false"):
        LoopContract.model_validate(data)

    data["permissions"]["database_changes"] = True
    decision = approved_policy(data).evaluate(
        ActionRequest(
            kind=ActionKind.DATABASE_CHANGE,
            repository_id="target",
            target="schema.users",
            forward_plan="add a nullable column",
            compatibility_analysis="old and new code accept null",
            recovery="apply a compensating forward migration",
        )
    )
    assert decision.outcome is GateOutcome.ALLOW
