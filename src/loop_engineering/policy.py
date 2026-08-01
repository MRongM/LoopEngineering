from enum import StrEnum

from loop_engineering.contract import contract_fingerprint
from loop_engineering.models.action import ActionKind, ActionRequest
from loop_engineering.models.base import StrictModel
from loop_engineering.models.contract import LoopContract
from loop_engineering.models.run import ContractAuthorization
from loop_engineering.paths import is_allowed_path


class GateOutcome(StrEnum):
    ALLOW = "allow"
    PAUSE = "pause"
    DENY = "deny"


class GateRequirement(StrEnum):
    CONTRACT_APPROVAL = "contract_approval"
    CONTRACT_REVISION = "contract_revision"


class GateDecision(StrictModel):
    outcome: GateOutcome
    reason: str
    requires_confirmation: bool = False
    required_gate: GateRequirement | None = None


class GatePolicy:
    def __init__(
        self,
        contract: LoopContract,
        authorization: ContractAuthorization | None = None,
    ) -> None:
        self.contract = contract
        self.authorization = authorization

    def _pause(
        self,
        reason: str,
        required_gate: GateRequirement,
    ) -> GateDecision:
        return GateDecision(
            outcome=GateOutcome.PAUSE,
            reason=reason,
            requires_confirmation=True,
            required_gate=required_gate,
        )

    def _scope_pause(self, reason: str) -> GateDecision:
        return self._pause(reason, GateRequirement.CONTRACT_REVISION)

    def _authorization_matches_contract(self) -> bool:
        if self.authorization is None:
            return False
        expected_risk_ids = sorted(
            operation.risk_id
            for operation in self.contract.authorized_operations
        )
        return (
            self.authorization.protocol_version == self.contract.protocol_version
            and self.authorization.contract_version == self.contract.contract_version
            and self.authorization.contract_sha256
            == contract_fingerprint(self.contract)
            and self.authorization.accepted_risk_ids == expected_risk_ids
        )

    def _risk_is_accepted(self, risk_id: str | None) -> bool:
        return bool(
            risk_id
            and self._authorization_matches_contract()
            and self.authorization
            and risk_id in self.authorization.accepted_risk_ids
        )

    def _is_planned(self, request: ActionRequest) -> bool:
        plan = self.contract.execution_plan
        file_kinds = {
            ActionKind.FILE_WRITE,
            ActionKind.BATCH_WRITE,
            ActionKind.FILE_DELETE,
            ActionKind.BATCH_MOVE,
        }
        for planned in plan.actions:
            if (
                planned.kind is not request.kind
                or planned.repository_id != request.repository_id
            ):
                continue
            if planned.target == request.target:
                return True
            if request.kind in file_kinds and is_allowed_path(
                request.target,
                [planned.target],
            ):
                return True
        return False

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
        if not self._authorization_matches_contract():
            return self._pause(
                "current contract approval is missing or stale",
                GateRequirement.CONTRACT_APPROVAL,
            )
        if not self._is_planned(request):
            return self._scope_pause(
                "operation is outside the approved execution plan"
            )
        exact = next(
            (
                operation
                for operation in self.contract.authorized_operations
                if operation.kind is request.kind
                and operation.repository_id == request.repository_id
                and operation.target == request.target
            ),
            None,
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
                and is_allowed_path(request.target, repository.allowed_paths)
            )
            if not target_allowed:
                return self._scope_pause(
                    "target is outside approved repository paths"
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
            ActionKind.GIT_WORKTREE: bool(
                git_target
                and git_target.create_worktree
                and git_target.branch
                and git_target.worktree_path
                and request.target
                == f"{git_target.branch}@{git_target.worktree_path.resolve()}"
            ),
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
            if not allowed:
                return self._scope_pause("Git action is not preauthorized")
            if exact is None:
                return self._scope_pause(
                    "Git action lacks a disclosed exact risk grant"
                )
            if not self._risk_is_accepted(exact.risk_id):
                return self._pause(
                    "current contract risk acceptance is missing or stale",
                    GateRequirement.CONTRACT_APPROVAL,
                )
            return GateDecision(
                outcome=GateOutcome.ALLOW,
                reason="Git action matches approved contract and risk grant",
            )

        if request.kind in {
            ActionKind.PRODUCTION_ACCESS,
            ActionKind.SENSITIVE_DATA,
        }:
            if exact is None:
                return self._scope_pause(
                    "operation is outside the approved risk grant"
                )
            if not getattr(self.contract.permissions, request.kind.value):
                return self._scope_pause(
                    f"contract permission {request.kind.value} is false"
                )
            if not self._risk_is_accepted(exact.risk_id):
                return self._pause(
                    "current contract risk acceptance is missing or stale",
                    GateRequirement.CONTRACT_APPROVAL,
                )
            return GateDecision(
                outcome=GateOutcome.ALLOW,
                reason="exact high-risk operation is accepted by the current contract",
            )

        if exact is not None:
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
                return self._scope_pause(
                    f"contract permission {permission_field} is false"
                )
            if not self._risk_is_accepted(exact.risk_id):
                return self._pause(
                    "current contract risk acceptance is missing or stale",
                    GateRequirement.CONTRACT_APPROVAL,
                )
            return GateDecision(
                outcome=GateOutcome.ALLOW,
                reason="exact operation is accepted by the current contract",
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
            ActionKind.PLATFORM_STATE,
        }
        if request.kind in dangerous:
            return self._scope_pause(
                "dangerous operation needs an exact risk grant"
            )
        return GateDecision(
            outcome=GateOutcome.ALLOW,
            reason="low-risk scoped action",
        )
