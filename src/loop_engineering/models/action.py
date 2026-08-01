from enum import StrEnum

from pydantic import Field, model_validator

from loop_engineering.models.base import StrictModel


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
    PLATFORM_STATE = "platform_state"
    GIT_WORKTREE = "git_worktree"
    GIT_COMMIT = "git_commit"
    GIT_PUSH = "git_push"
    CREATE_PR = "create_pr"
    FORCE_PUSH = "force_push"
    HISTORY_REWRITE = "history_rewrite"
    MERGE = "merge"
    DEPLOY = "deploy"


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
