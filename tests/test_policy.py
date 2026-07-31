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
    render_confirmation,
)
from tests.factories import autonomous_risk_contract_data, valid_contract_data


def policy(data: dict | None = None) -> GatePolicy:
    return GatePolicy(LoopContract.model_validate(data or valid_contract_data()))


def approved_policy(data: dict) -> GatePolicy:
    contract = LoopContract.model_validate(data)
    authorization = ContractAuthorization(
        protocol_version="0.2.0",
        contract_version=contract.contract_version,
        contract_sha256=contract_fingerprint(contract),
        accepted_risk_ids=sorted(
            operation.risk_id
            for operation in contract.authorized_operations
            if operation.risk_id is not None
        ),
    )
    return GatePolicy(contract, authorization=authorization)


def test_merge_deploy_force_and_history_rewrite_are_always_denied() -> None:
    for kind in (
        ActionKind.MERGE,
        ActionKind.DEPLOY,
        ActionKind.FORCE_PUSH,
        ActionKind.HISTORY_REWRITE,
    ):
        decision = policy().evaluate(
            ActionRequest(kind=kind, repository_id="target", target="master")
        )
        assert decision.outcome is GateOutcome.DENY


def test_legacy_production_and_sensitive_data_pause_for_fresh_human_gate() -> None:
    data = valid_contract_data(protocol_version="0.1.0")
    for kind in (ActionKind.PRODUCTION_ACCESS, ActionKind.SENSITIVE_DATA):
        decision = policy(data).evaluate(
            ActionRequest(kind=kind, target="production")
        )
        assert decision.outcome is GateOutcome.PAUSE
        assert decision.requires_confirmation is True
        assert decision.required_gate == "dangerous_action"


@pytest.mark.parametrize(
    "kind",
    [ActionKind.PRODUCTION_ACCESS, ActionKind.SENSITIVE_DATA],
)
def test_v020_autonomous_allows_exact_approved_high_risk_operation(
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
    assert decision.required_gate is None


def test_v020_autonomous_exact_risk_requires_current_contract_approval() -> None:
    data = autonomous_risk_contract_data()
    contract = LoopContract.model_validate(data)
    stale = ContractAuthorization(
        protocol_version="0.2.0",
        contract_version=contract.contract_version,
        contract_sha256="0" * 64,
        accepted_risk_ids=["RISK-1"],
    )
    request = ActionRequest(
        kind=ActionKind.PRODUCTION_ACCESS,
        repository_id="target",
        target="production/customer-index",
    )

    for candidate in (GatePolicy(contract), GatePolicy(contract, authorization=stale)):
        decision = candidate.evaluate(request)
        assert decision.outcome is GateOutcome.PAUSE
        assert decision.required_gate == "contract_approval"


def test_v020_autonomous_scoped_write_requires_bound_contract_approval() -> None:
    data = valid_contract_data()
    data["mode"] = "autonomous"
    data["human_gates"] = ["contract_approval"]
    request = ActionRequest(
        kind=ActionKind.FILE_WRITE,
        repository_id="target",
        target="src/app.py",
    )

    missing = GatePolicy(LoopContract.model_validate(data)).evaluate(request)
    accepted = approved_policy(data).evaluate(request)

    assert missing.outcome is GateOutcome.PAUSE
    assert missing.required_gate == "contract_approval"
    assert accepted.outcome is GateOutcome.ALLOW


def test_v020_autonomous_new_target_requires_complete_contract_revision() -> None:
    data = autonomous_risk_contract_data()
    decision = approved_policy(data).evaluate(
        ActionRequest(
            kind=ActionKind.PRODUCTION_ACCESS,
            repository_id="target",
            target="production/new-index",
        )
    )

    assert decision.outcome is GateOutcome.PAUSE
    assert decision.required_gate == "contract_revision"


def test_v020_autonomous_new_permission_requires_revision() -> None:
    data = autonomous_risk_contract_data("network")
    data["permissions"]["network"] = True
    decision = approved_policy(data).evaluate(
        ActionRequest(
            kind=ActionKind.DEPENDENCY_CHANGE,
            repository_id="target",
            target="dependencies/runtime-core",
        )
    )

    assert decision.outcome is GateOutcome.PAUSE
    assert decision.required_gate == "contract_revision"


def platform_state_contract_data() -> dict:
    data = valid_contract_data()
    data["mode"] = "autonomous"
    data["risk_level"] = "medium"
    data["human_gates"] = ["contract_approval"]
    data["authorized_operations"] = [
        {
            "risk_id": "RISK-1",
            "kind": "platform_state",
            "target": "codex-goal:create:/work/project/.loop-runs/loop-example",
            "risk_level": "medium",
            "impact": "Creates one explicitly requested host Goal",
            "worst_case": "The Goal consumes host continuation budget unexpectedly",
            "recovery": "The user pauses or cancels the Goal",
            "evidence": "The approved run requests cross-turn continuation",
        }
    ]
    return data


def test_platform_state_requires_an_exact_bound_risk_grant() -> None:
    target = "codex-goal:create:/work/project/.loop-runs/loop-example"
    exact = approved_policy(platform_state_contract_data()).evaluate(
        ActionRequest(kind=ActionKind.PLATFORM_STATE, target=target)
    )

    missing_data = platform_state_contract_data()
    missing_data["authorized_operations"] = []
    missing = approved_policy(missing_data).evaluate(
        ActionRequest(kind=ActionKind.PLATFORM_STATE, target=target)
    )

    changed = approved_policy(platform_state_contract_data()).evaluate(
        ActionRequest(
            kind=ActionKind.PLATFORM_STATE,
            target="codex-goal:create:/work/project/.loop-runs/loop-other",
        )
    )

    assert exact.outcome is GateOutcome.ALLOW
    for decision in (missing, changed):
        assert decision.outcome is GateOutcome.PAUSE
        assert decision.required_gate == "contract_revision"


def test_platform_state_rejects_a_stale_contract_approval() -> None:
    data = platform_state_contract_data()
    contract = LoopContract.model_validate(data)
    stale = ContractAuthorization(
        protocol_version="0.2.0",
        contract_version=contract.contract_version,
        contract_sha256="0" * 64,
        accepted_risk_ids=["RISK-1"],
    )

    decision = GatePolicy(contract, authorization=stale).evaluate(
        ActionRequest(
            kind=ActionKind.PLATFORM_STATE,
            target="codex-goal:create:/work/project/.loop-runs/loop-example",
        )
    )

    assert decision.outcome is GateOutcome.PAUSE
    assert decision.required_gate == "contract_approval"


def test_v020_collaborative_keeps_fresh_production_human_gate() -> None:
    data = autonomous_risk_contract_data()
    data["mode"] = "collaborative"
    data["human_gates"].append("final_acceptance")
    decision = approved_policy(data).evaluate(
        ActionRequest(
            kind=ActionKind.PRODUCTION_ACCESS,
            repository_id="target",
            target="production/customer-index",
        )
    )

    assert decision.outcome is GateOutcome.PAUSE
    assert decision.required_gate == "dangerous_action"


def test_system_permission_and_global_package_changes_pause() -> None:
    for kind in (
        ActionKind.SYSTEM_CONFIG,
        ActionKind.PERMISSION_CHANGE,
        ActionKind.GLOBAL_PACKAGE,
    ):
        decision = policy().evaluate(ActionRequest(kind=kind, target="/system"))
        assert decision.outcome is GateOutcome.PAUSE


def test_exact_authorized_operation_is_allowed() -> None:
    data = valid_contract_data(protocol_version="0.1.0")
    data["authorized_operations"] = [
        {
            "kind": "file_delete",
            "repository_id": "target",
            "target": "tmp/generated.txt",
        }
    ]
    decision = policy(data).evaluate(
        ActionRequest(
            kind=ActionKind.FILE_DELETE,
            repository_id="target",
            target="tmp/generated.txt",
        )
    )
    assert decision.outcome is GateOutcome.ALLOW


def test_exact_database_operation_also_requires_category_permission() -> None:
    data = valid_contract_data(protocol_version="0.1.0")
    data["authorized_operations"] = [
        {
            "kind": "database_change",
            "repository_id": "target",
            "target": "schema.users",
        }
    ]
    request = ActionRequest(
        kind=ActionKind.DATABASE_CHANGE,
        repository_id="target",
        target="schema.users",
        forward_plan="add nullable column",
        compatibility_analysis="both versions accept null",
        recovery="drop the unused column before rollout",
    )
    assert policy(data).evaluate(request).outcome is GateOutcome.PAUSE
    data["permissions"]["database_changes"] = True
    assert policy(data).evaluate(request).outcome is GateOutcome.ALLOW


def test_confirmation_contains_required_professional_warning_fields() -> None:
    request = ActionRequest(
        kind=ActionKind.DATABASE_CHANGE,
        repository_id="target",
        target="schema.users",
        forward_plan="add nullable column, then backfill",
        compatibility_analysis="old and new application versions accept null",
        recovery="drop only the unused nullable column before rollout",
    )
    decision = policy().evaluate(request)
    rendered = render_confirmation(request, decision)
    for label in (
        "⚠️ 危险操作检测！",
        "操作类型：",
        "精确目标：",
        "影响范围：",
        "风险评估：",
        "恢复方案：",
        "前向方案：",
        "兼容性分析：",
        "当前证据：",
        "请确认是否继续？",
    ):
        assert label in rendered


def test_file_target_outside_allowed_paths_requires_contract_revision() -> None:
    for target in (
        "src_evil/payload.py",
        "../secret.txt",
        "C:\\secret.txt",
        "src/*.py",
        "$PROJECT_ROOT/src/app.py",
    ):
        decision = policy().evaluate(
            ActionRequest(
                kind=ActionKind.FILE_WRITE,
                repository_id="target",
                target=target,
            )
        )
        assert decision.outcome is GateOutcome.PAUSE
        assert decision.requires_confirmation is True


def test_git_preapproval_matches_repository_and_branch_exactly() -> None:
    data = valid_contract_data(protocol_version="0.1.0")
    data["git_policy"]["targets"][0].update(
        {"commit": True, "branch": "feat/exact", "worktree_path": "worktree"}
    )
    exact = policy(data).evaluate(
        ActionRequest(
            kind=ActionKind.GIT_COMMIT,
            repository_id="target",
            target="feat/exact",
        )
    )
    changed = policy(data).evaluate(
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
