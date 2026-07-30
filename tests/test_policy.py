import pytest
from pydantic import ValidationError

from loop_engineering.models.contract import LoopContract
from loop_engineering.policy import (
    ActionKind,
    ActionRequest,
    GateOutcome,
    GatePolicy,
    render_confirmation,
)
from tests.factories import valid_contract_data


def policy(data: dict | None = None) -> GatePolicy:
    return GatePolicy(LoopContract.model_validate(data or valid_contract_data()))


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


def test_production_and_sensitive_data_always_pause_for_human() -> None:
    for kind in (ActionKind.PRODUCTION_ACCESS, ActionKind.SENSITIVE_DATA):
        decision = policy().evaluate(ActionRequest(kind=kind, target="production"))
        assert decision.outcome is GateOutcome.PAUSE
        assert decision.requires_confirmation is True


def test_system_permission_and_global_package_changes_pause() -> None:
    for kind in (
        ActionKind.SYSTEM_CONFIG,
        ActionKind.PERMISSION_CHANGE,
        ActionKind.GLOBAL_PACKAGE,
    ):
        decision = policy().evaluate(ActionRequest(kind=kind, target="/system"))
        assert decision.outcome is GateOutcome.PAUSE


def test_exact_authorized_operation_is_allowed() -> None:
    data = valid_contract_data()
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
    data = valid_contract_data()
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
    data = valid_contract_data()
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
