from enum import StrEnum

from pydantic import Field, model_validator

from loop_engineering.models.contract import LoopContract, StrictModel
from loop_engineering.paths import is_allowed_path


class ActionKind(StrEnum):
    FILE_WRITE = "file_write"
    BATCH_WRITE = "batch_write"
    FILE_DELETE = "file_delete"
    BATCH_MOVE = "batch_move"
    DEPENDENCY_CHANGE = "dependency_change"
    GLOBAL_PACKAGE = "global_package"
    DATABASE_CHANGE = "database_change"
    SYSTEM_CONFIG = "system_config"
    PERMISSION_CHANGE = "permission_change"
    NETWORK = "network"
    SENSITIVE_DATA = "sensitive_data"
    PRODUCTION_ACCESS = "production_access"
    GIT_COMMIT = "git_commit"
    GIT_PUSH = "git_push"
    CREATE_PR = "create_pr"
    FORCE_PUSH = "force_push"
    HISTORY_REWRITE = "history_rewrite"
    MERGE = "merge"
    DEPLOY = "deploy"


class GateOutcome(StrEnum):
    ALLOW = "allow"
    PAUSE = "pause"
    DENY = "deny"


class ActionRequest(StrictModel):
    kind: ActionKind
    target: str = Field(min_length=1)
    repository_id: str | None = None
    impact: str = "External state will change"
    risk: str = "The change may be difficult to recover"
    recovery: str = "Use a forward fix or an approved revert"
    evidence: str = "The approved Loop Contract requires this action"
    forward_plan: str | None = None
    compatibility_analysis: str | None = None

    @model_validator(mode="after")
    def require_database_safety_details(self) -> "ActionRequest":
        if self.kind is ActionKind.DATABASE_CHANGE and not (
            self.forward_plan
            and self.compatibility_analysis
            and self.recovery != "Use a forward fix or an approved revert"
        ):
            raise ValueError(
                "database change requires forward plan, compatibility analysis and recovery"
            )
        return self


class GateDecision(StrictModel):
    outcome: GateOutcome
    reason: str
    requires_confirmation: bool = False


class GatePolicy:
    def __init__(self, contract: LoopContract) -> None:
        self.contract = contract

    def evaluate(self, request: ActionRequest) -> GateDecision:
        if request.kind in {
            ActionKind.FORCE_PUSH,
            ActionKind.HISTORY_REWRITE,
            ActionKind.MERGE,
            ActionKind.DEPLOY,
        }:
            return GateDecision(
                outcome=GateOutcome.DENY,
                reason="operation is forbidden",
            )
        if request.kind in {
            ActionKind.PRODUCTION_ACCESS,
            ActionKind.SENSITIVE_DATA,
        }:
            return GateDecision(
                outcome=GateOutcome.PAUSE,
                reason="operation always requires a fresh human gate",
                requires_confirmation=True,
            )

        exact = any(
            operation.kind == request.kind.value
            and operation.repository_id == request.repository_id
            and operation.target == request.target
            for operation in self.contract.authorized_operations
        )
        if request.kind in {
            ActionKind.FILE_WRITE,
            ActionKind.BATCH_WRITE,
            ActionKind.FILE_DELETE,
            ActionKind.BATCH_MOVE,
        }:
            repository = next(
                (
                    item
                    for item in self.contract.repositories
                    if item.id == request.repository_id
                ),
                None,
            )
            target_allowed = bool(
                repository
                and (
                    is_allowed_path(request.target, repository.allowed_paths)
                    or (exact and is_allowed_path(request.target, ["."]))
                )
            )
            if not target_allowed:
                return GateDecision(
                    outcome=GateOutcome.PAUSE,
                    reason="target is outside approved repository paths",
                    requires_confirmation=True,
                )

        git_target = next(
            (
                target
                for target in self.contract.git_policy.targets
                if target.repository_id == request.repository_id
            ),
            None,
        )
        git_flags = {
            ActionKind.GIT_COMMIT: bool(
                git_target and git_target.commit and request.target == git_target.branch
            ),
            ActionKind.GIT_PUSH: bool(
                git_target
                and git_target.push
                and request.target == f"{git_target.remote}/{git_target.branch}"
            ),
            ActionKind.CREATE_PR: bool(
                git_target
                and git_target.create_pr
                and request.target == f"{git_target.branch}->{git_target.pr_target}"
            ),
        }
        if request.kind in git_flags:
            allowed = git_flags[request.kind]
            return GateDecision(
                outcome=GateOutcome.ALLOW if allowed else GateOutcome.PAUSE,
                reason=(
                    "Git action matches contract"
                    if allowed
                    else "Git action is not preauthorized"
                ),
                requires_confirmation=not allowed,
            )

        if exact:
            permission_fields = {
                ActionKind.DEPENDENCY_CHANGE: "dependency_changes",
                ActionKind.GLOBAL_PACKAGE: "dependency_changes",
                ActionKind.DATABASE_CHANGE: "database_changes",
                ActionKind.NETWORK: "network",
            }
            permission_field = permission_fields.get(request.kind)
            if permission_field and not getattr(
                self.contract.permissions,
                permission_field,
            ):
                return GateDecision(
                    outcome=GateOutcome.PAUSE,
                    reason=f"contract permission {permission_field} is false",
                    requires_confirmation=True,
                )
            return GateDecision(
                outcome=GateOutcome.ALLOW,
                reason="exact operation is preauthorized",
            )

        dangerous = {
            ActionKind.BATCH_WRITE,
            ActionKind.FILE_DELETE,
            ActionKind.BATCH_MOVE,
            ActionKind.DEPENDENCY_CHANGE,
            ActionKind.GLOBAL_PACKAGE,
            ActionKind.DATABASE_CHANGE,
            ActionKind.NETWORK,
            ActionKind.SYSTEM_CONFIG,
            ActionKind.PERMISSION_CHANGE,
        }
        if request.kind in dangerous:
            return GateDecision(
                outcome=GateOutcome.PAUSE,
                reason="dangerous operation needs exact approval",
                requires_confirmation=True,
            )
        return GateDecision(
            outcome=GateOutcome.ALLOW,
            reason="low-risk scoped action",
        )


def render_confirmation(request: ActionRequest, decision: GateDecision) -> str:
    database_details = ""
    if request.kind is ActionKind.DATABASE_CHANGE:
        database_details = (
            f"前向方案：{request.forward_plan}\n"
            f"兼容性分析：{request.compatibility_analysis}\n"
        )
    return (
        "⚠️ 危险操作检测！\n"
        f"操作类型：{request.kind.value}\n"
        f"精确目标：{request.target}\n"
        f"影响范围：{request.impact}\n"
        f"风险评估：{request.risk}\n"
        f"恢复方案：{request.recovery}\n"
        f"{database_details}"
        f"当前证据：{request.evidence}；策略判定：{decision.reason}\n\n"
        "请确认是否继续？[需要明确的“是”“确认”“继续”]"
    )
