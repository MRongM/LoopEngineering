import hashlib
import subprocess
import uuid
from datetime import UTC, datetime
from pathlib import Path

from loop_engineering.ledger import RunStore
from loop_engineering.models.contract import LoopContract, RiskLevel
from loop_engineering.models.evidence import (
    CompletionContext,
    CompletionEvaluation,
    EvidenceRecord,
    ScopeEvaluation,
)
from loop_engineering.models.run import CheckerVerdict
from loop_engineering.paths import is_allowed_path
from loop_engineering.redaction import redact


def _run(
    argv: list[str],
    *,
    cwd: Path,
    timeout: int = 60,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        argv,
        cwd=cwd,
        check=False,
        capture_output=True,
        shell=False,
        timeout=timeout,
    )


def _git(argv: list[str], *, cwd: Path) -> bytes:
    result = _run(["git", *argv], cwd=cwd)
    if result.returncode != 0:
        raise RuntimeError(f"git {argv[0]} failed with exit code {result.returncode}")
    return result.stdout


def _exact_git_root(repository: Path) -> Path:
    repository = repository.resolve()
    root = Path(
        _git(["rev-parse", "--show-toplevel"], cwd=repository).decode().strip()
    ).resolve()
    if root != repository:
        raise ValueError("repository path must be the exact Git root")
    return root


def git_fingerprint(repository: Path) -> str:
    repository = _exact_git_root(repository)
    head = _git(["rev-parse", "HEAD"], cwd=repository)
    diff = _git(["diff", "--binary", "HEAD"], cwd=repository)
    names = _git(
        [
            "ls-files",
            "--others",
            "--exclude-standard",
            "--exclude=.loop-runs/**",
        ],
        cwd=repository,
    ).decode().splitlines()
    untracked = bytearray()
    for name in sorted(names):
        candidate = (repository / name).resolve()
        untracked.extend(name.encode())
        untracked.extend(b"\0")
        if candidate.is_file() and candidate.is_relative_to(repository):
            untracked.extend(candidate.read_bytes())
        untracked.extend(b"\0")
    return hashlib.sha256(head + b"\0" + diff + b"\0" + bytes(untracked)).hexdigest()


def evaluate_scope(contract: LoopContract) -> ScopeEvaluation:
    violations: list[str] = []
    for repository in contract.repositories:
        root = _exact_git_root(repository.path)
        committed = _git(
            ["diff", "--no-renames", "--name-only", f"{repository.base_branch}...HEAD"],
            cwd=root,
        )
        working = _git(["diff", "--no-renames", "--name-only", "HEAD"], cwd=root)
        untracked = _git(
            [
                "ls-files",
                "--others",
                "--exclude-standard",
                "--exclude=.loop-runs/**",
            ],
            cwd=root,
        )
        changed = {
            line
            for line in (committed + b"\n" + working + b"\n" + untracked)
            .decode()
            .splitlines()
            if line
        }
        for path in sorted(changed):
            try:
                allowed = is_allowed_path(path, repository.allowed_paths)
            except ValueError:
                allowed = False
            if not allowed:
                violations.append(f"{repository.id}:{path}")
    return ScopeEvaluation(valid=not violations, violations=violations)


class ValidationRunner:
    def __init__(self, contract: LoopContract, store: RunStore) -> None:
        self.contract = contract
        self.store = store

    def run(self, command_id: str) -> EvidenceRecord:
        command = next(
            item for item in self.contract.validation_commands if item.id == command_id
        )
        repository = next(
            item for item in self.contract.repositories if item.id == command.repository_id
        )
        repository_root = _exact_git_root(repository.path)
        cwd = (repository_root / command.cwd).resolve()
        if not cwd.is_relative_to(repository_root):
            raise ValueError("validation cwd is outside repository")
        action_id = self.store.record_intent(
            actor="validator",
            summary=f"run {command.id}",
            payload={"argv": command.argv, "cwd": str(cwd)},
        )
        started = datetime.now(UTC)
        result = _run(command.argv, cwd=cwd, timeout=command.timeout_seconds)
        ended = datetime.now(UTC)
        evidence_id = f"E-{uuid.uuid4().hex}"
        stdout_file = f"{evidence_id}.stdout.txt"
        stderr_file = f"{evidence_id}.stderr.txt"
        stdout_text = str(redact(result.stdout.decode(errors="replace")))
        stderr_text = str(redact(result.stderr.decode(errors="replace")))
        self.store.evidence_dir.joinpath(stdout_file).write_text(stdout_text, encoding="utf-8")
        self.store.evidence_dir.joinpath(stderr_file).write_text(stderr_text, encoding="utf-8")
        evidence = EvidenceRecord(
            evidence_id=evidence_id,
            contract_version=self.store.load_state().contract_version,
            command_id=command.id,
            repository_id=repository.id,
            criterion_ids=command.criterion_ids,
            started_at=started,
            ended_at=ended,
            exit_code=result.returncode,
            passed=result.returncode == 0,
            code_fingerprint=git_fingerprint(repository_root),
            stdout_file=stdout_file,
            stderr_file=stderr_file,
            stdout_sha256=hashlib.sha256(stdout_text.encode()).hexdigest(),
            stderr_sha256=hashlib.sha256(stderr_text.encode()).hexdigest(),
        )
        self.store.record_result(
            action_id=action_id,
            actor="validator",
            summary=f"{command.id} exit={result.returncode}",
            payload={"evidence": evidence.model_dump(mode="json")},
        )
        return evidence


class DoneEvaluator:
    def __init__(self, contract: LoopContract) -> None:
        self.contract = contract

    def evaluate(self, context: CompletionContext) -> CompletionEvaluation:
        reasons: list[str] = []
        by_command = {record.command_id: record for record in context.evidence}
        for criterion in self.contract.acceptance_criteria:
            for required in criterion.required_evidence:
                evidence = by_command.get(required)
                expected_repository = next(
                    command.repository_id
                    for command in self.contract.validation_commands
                    if command.id == required
                )
                current = context.current_fingerprints.get(expected_repository)
                if (
                    not evidence
                    or not evidence.passed
                    or evidence.contract_version != self.contract.contract_version
                    or evidence.repository_id != expected_repository
                    or criterion.id not in evidence.criterion_ids
                    or evidence.code_fingerprint != current
                ):
                    reasons.append(f"{criterion.id} lacks fresh evidence {required}")
        if (
            self.contract.risk_level in {RiskLevel.MEDIUM, RiskLevel.HIGH}
            and context.checker_verdict is not CheckerVerdict.ACCEPT
        ):
            reasons.append("checker has not accepted")
        requires_human = "final_acceptance" in self.contract.human_gates
        if requires_human and not context.human_accepted:
            reasons.append("human final acceptance is missing")
        required_delivery = {
            target.repository_id
            for target in self.contract.git_policy.targets
            if target.push or target.create_pr
        }
        missing_delivery = sorted(
            repository_id
            for repository_id in required_delivery
            if not context.git_delivered.get(repository_id, False)
        )
        if missing_delivery:
            reasons.append("required Git delivery is incomplete: " + ", ".join(missing_delivery))
        if not context.scope_valid:
            reasons.append("actual diff is outside approved scope")
        if not context.gates_clear:
            reasons.append("a required gate is unresolved")
        if not context.contract_current:
            reasons.append("evidence belongs to a stale contract version")
        return CompletionEvaluation(done=not reasons, reasons=reasons)
