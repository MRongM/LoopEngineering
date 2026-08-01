import hashlib
import os
import shutil
import subprocess
import uuid
from datetime import UTC, datetime
from pathlib import Path

from loop_engineering.layout import CONTROL_DIR_NAME
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
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        argv,
        cwd=cwd,
        check=False,
        capture_output=True,
        shell=False,
        timeout=timeout,
        env=env,
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
    diff = _git(
        ["diff", "--binary", "HEAD", "--", ".", f":(exclude){CONTROL_DIR_NAME}/**"],
        cwd=repository,
    )
    names = _git(
        [
            "ls-files",
            "--others",
            "--exclude-standard",
            f"--exclude={CONTROL_DIR_NAME}/**",
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
            [
                "diff",
                "--no-renames",
                "--name-only",
                f"{repository.base_branch}...HEAD",
                "--",
                ".",
                f":(exclude){CONTROL_DIR_NAME}/**",
            ],
            cwd=root,
        )
        working = _git(
            [
                "diff",
                "--no-renames",
                "--name-only",
                "HEAD",
                "--",
                ".",
                f":(exclude){CONTROL_DIR_NAME}/**",
            ],
            cwd=root,
        )
        untracked = _git(
            [
                "ls-files",
                "--others",
                "--exclude-standard",
                f"--exclude={CONTROL_DIR_NAME}/**",
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


def _working_paths(repository: Path) -> set[str]:
    working = _git(
        [
            "diff",
            "--no-renames",
            "--name-only",
            "HEAD",
            "--",
            ".",
            f":(exclude){CONTROL_DIR_NAME}/**",
        ],
        cwd=repository,
    )
    untracked = _git(
        [
            "ls-files",
            "--others",
            "--exclude-standard",
            f"--exclude={CONTROL_DIR_NAME}/**",
        ],
        cwd=repository,
    )
    return {
        line
        for line in (working + b"\n" + untracked).decode().splitlines()
        if line
    }


def _output_bytes(value: bytes | str | None) -> bytes:
    if value is None:
        return b""
    return value if isinstance(value, bytes) else value.encode("utf-8", errors="replace")


def _copy_validation_snapshot(repository: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    names = _git(
        ["ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=repository,
    ).split(b"\0")
    for raw_name in names:
        if not raw_name:
            continue
        name = os.fsdecode(raw_name)
        if name == CONTROL_DIR_NAME or name.startswith(f"{CONTROL_DIR_NAME}/"):
            continue
        source = repository / name
        target = destination / name
        if not target.resolve().is_relative_to(destination.resolve()):
            raise ValueError(f"validation snapshot path escapes repository: {name}")
        if not source.exists() and not source.is_symlink():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_symlink():
            link_target = os.readlink(source)
            resolved_link = (source.parent / link_target).resolve()
            if Path(link_target).is_absolute() or not resolved_link.is_relative_to(
                repository
            ):
                raise ValueError(
                    f"validation snapshot symlink escapes repository: {name}"
                )
            target.symlink_to(
                link_target,
                target_is_directory=resolved_link.is_dir(),
            )
        elif source.is_file():
            shutil.copy2(source, target)

    init = _run(["git", "init", "-q", "-b", "loop-validation"], cwd=destination)
    if init.returncode != 0:
        raise RuntimeError(
            f"validation snapshot command failed with exit code {init.returncode}"
        )
    hooks = destination / ".git" / "disabled-hooks"
    hooks.mkdir()
    for argv in (
        ["git", "add", "--all"],
        [
            "git",
            "-c",
            "user.name=Loop Engine",
            "-c",
            "user.email=loop-engine@invalid.local",
            "-c",
            f"core.hooksPath={hooks}",
            "commit",
            "-q",
            "--no-gpg-sign",
            "--no-verify",
            "-m",
            "validation snapshot",
        ],
    ):
        result = _run(argv, cwd=destination)
        if result.returncode != 0:
            raise RuntimeError(
                f"validation snapshot command failed with exit code {result.returncode}"
            )


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
        if not cwd.is_dir():
            raise NotADirectoryError(cwd)
        validation_cache = (
            self.store.cache_dir
            / "validation"
            / command.id
            / uuid.uuid4().hex
        )
        execution_root = validation_cache / "workspace"
        execution_cwd = (execution_root / command.cwd).resolve()
        if not execution_cwd.is_relative_to(execution_root):
            raise ValueError("validation cwd is outside execution workspace")
        environment = os.environ.copy()
        environment.update(
            {
                "TMPDIR": str(validation_cache / "tmp"),
                "TMP": str(validation_cache / "tmp"),
                "TEMP": str(validation_cache / "tmp"),
                "XDG_CACHE_HOME": str(validation_cache / "xdg"),
                "LOOP_ENGINE_CACHE_DIR": str(validation_cache),
            }
        )
        before_fingerprint = git_fingerprint(repository_root)
        before_paths = _working_paths(repository_root)
        action_id = self.store.record_intent(
            actor="validator",
            summary=f"run {command.id}",
            payload={
                "argv": command.argv,
                "cwd": str(cwd),
                "execution_cwd": str(execution_cwd),
                "cache_dir": str(validation_cache),
            },
        )
        started = datetime.now(UTC)
        exit_code: int
        stdout = b""
        stderr = b""
        error_type: str | None = None
        timed_out = False
        try:
            validation_cache.mkdir(parents=True, exist_ok=True)
            _copy_validation_snapshot(repository_root, execution_root)
            if git_fingerprint(repository_root) != before_fingerprint:
                raise RuntimeError(
                    "source repository changed while validation snapshot was created"
                )
            execution_cwd.mkdir(parents=True, exist_ok=True)
            (validation_cache / "tmp").mkdir(parents=True, exist_ok=True)
            (validation_cache / "xdg").mkdir(parents=True, exist_ok=True)
        except (OSError, RuntimeError, ValueError) as error:
            exit_code = 126
            stderr = f"{type(error).__name__}: {error}\n".encode(
                "utf-8",
                errors="replace",
            )
            error_type = type(error).__name__
        else:
            try:
                result = _run(
                    command.argv,
                    cwd=execution_cwd,
                    timeout=command.timeout_seconds,
                    env=environment,
                )
                exit_code = result.returncode
                stdout = result.stdout
                stderr = result.stderr
            except subprocess.TimeoutExpired as error:
                exit_code = 124
                stdout = _output_bytes(error.stdout)
                stderr = _output_bytes(error.stderr) + (
                    f"\nvalidation timed out after {command.timeout_seconds} seconds\n".encode()
                )
                error_type = type(error).__name__
                timed_out = True
            except OSError as error:
                exit_code = 127
                stderr = f"{type(error).__name__}: {error}\n".encode(
                    "utf-8",
                    errors="replace",
                )
                error_type = type(error).__name__
        ended = datetime.now(UTC)
        try:
            after_fingerprint = git_fingerprint(repository_root)
            after_paths = _working_paths(repository_root)
            workspace_clean = before_fingerprint == after_fingerprint
            workspace_changes = [] if workspace_clean else sorted(
                before_paths | after_paths
            )
            if not workspace_clean and not workspace_changes:
                workspace_changes = ["<git-head-or-content-changed>"]
        except (OSError, RuntimeError, ValueError) as error:
            after_fingerprint = before_fingerprint
            workspace_clean = False
            workspace_changes = ["<workspace-state-unavailable>"]
            if error_type is None:
                error_type = type(error).__name__
            stderr += f"\nworkspace inspection failed: {error}\n".encode(
                "utf-8",
                errors="replace",
            )
        if not workspace_clean:
            stderr += (
                "\nvalidation changed the repository workspace: "
                + ", ".join(workspace_changes)
                + "\n"
            ).encode("utf-8")
        evidence_id = f"E-{uuid.uuid4().hex}"
        stdout_file = f"{evidence_id}.stdout.txt"
        stderr_file = f"{evidence_id}.stderr.txt"
        stdout_text = str(redact(stdout.decode(errors="replace")))
        stderr_text = str(redact(stderr.decode(errors="replace")))
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
            exit_code=exit_code,
            passed=exit_code == 0 and workspace_clean and error_type is None,
            code_fingerprint=after_fingerprint,
            stdout_file=stdout_file,
            stderr_file=stderr_file,
            stdout_sha256=hashlib.sha256(stdout_text.encode()).hexdigest(),
            stderr_sha256=hashlib.sha256(stderr_text.encode()).hexdigest(),
            workspace_clean=workspace_clean,
            workspace_changes=workspace_changes,
            error_type=error_type,
            timed_out=timed_out,
        )
        self.store.record_result(
            action_id=action_id,
            actor="validator",
            summary=f"{command.id} exit={exit_code}",
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
