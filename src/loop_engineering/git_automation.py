import subprocess
from collections.abc import Sequence
from pathlib import Path

from loop_engineering.models.contract import LoopContract, RepositoryTarget
from loop_engineering.paths import is_allowed_path


class GitSafetyError(RuntimeError):
    pass


def _run(argv: list[str], *, cwd: Path) -> str:
    result = subprocess.run(
        argv,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        shell=False,
    )
    if result.returncode:
        operation = argv[1] if len(argv) > 1 else "command"
        raise GitSafetyError(
            f"Git {operation} failed with exit code {result.returncode}"
        )
    return result.stdout.strip()


class GitAutomation:
    def __init__(self, contract: LoopContract, repository_id: str) -> None:
        self.contract = contract
        repository = next(
            (
                item
                for item in contract.repositories
                if item.id == repository_id
            ),
            None,
        )
        policy = next(
            (
                item
                for item in contract.git_policy.targets
                if item.repository_id == repository_id
            ),
            None,
        )
        if repository is None or policy is None:
            raise GitSafetyError("repository is not authorized for Git automation")
        self.repository: RepositoryTarget = repository
        self.policy = policy
        self.source = self.repository.path.resolve()
        source_root = Path(
            _run(["git", "rev-parse", "--show-toplevel"], cwd=self.source)
        ).resolve()
        if source_root != self.source:
            raise GitSafetyError("repository path is not the Git root")

    @property
    def worktree(self) -> Path:
        if not self.policy.worktree_path:
            raise GitSafetyError("worktree_path is not authorized")
        return self.policy.worktree_path.resolve()

    def prepare_worktree(self) -> Path:
        if not self.policy.create_worktree or not self.policy.branch:
            raise GitSafetyError("worktree creation is not authorized")
        if self.worktree.exists():
            raise GitSafetyError("worktree target already exists")
        _run(
            [
                "git",
                "worktree",
                "add",
                "-b",
                self.policy.branch,
                str(self.worktree),
                self.repository.base_branch,
            ],
            cwd=self.source,
        )
        return self.worktree

    def _validate_paths(self, paths: Sequence[str]) -> list[str]:
        if not paths:
            raise GitSafetyError("at least one exact path is required")
        validated: list[str] = []
        for value in paths:
            candidate = (self.worktree / value).resolve()
            if not candidate.is_relative_to(self.worktree):
                raise GitSafetyError("path escapes worktree")
            normalized = candidate.relative_to(self.worktree).as_posix()
            if not is_allowed_path(normalized, self.repository.allowed_paths):
                raise GitSafetyError(f"{normalized} is outside allowed paths")
            validated.append(normalized)
        return validated

    def _assert_exact_worktree(self) -> None:
        root = Path(
            _run(["git", "rev-parse", "--show-toplevel"], cwd=self.worktree)
        ).resolve()
        if root != self.worktree:
            raise GitSafetyError("Git root does not match authorized worktree")
        branch = _run(["git", "branch", "--show-current"], cwd=self.worktree)
        if branch != self.policy.branch:
            raise GitSafetyError("current branch does not match contract")

    def commit(self, paths: Sequence[str], message: str) -> str:
        if not self.policy.commit:
            raise GitSafetyError("commit is not authorized")
        self._assert_exact_worktree()
        validated = self._validate_paths(paths)
        staged = _run(["git", "diff", "--cached", "--name-only"], cwd=self.worktree)
        if staged:
            raise GitSafetyError("index already contains staged paths")
        _run(["git", "add", "--", *validated], cwd=self.worktree)
        _run(["git", "commit", "-m", message], cwd=self.worktree)
        return _run(["git", "rev-parse", "HEAD"], cwd=self.worktree)

    def push(self) -> None:
        if not self.policy.push or not self.policy.remote or not self.policy.branch:
            raise GitSafetyError("push is not authorized")
        self._assert_exact_worktree()
        _run(
            ["git", "push", "-u", "--", self.policy.remote, self.policy.branch],
            cwd=self.worktree,
        )

    def create_pr(self, title: str, body: str) -> str:
        if not self.policy.create_pr or not self.policy.pr_target:
            raise GitSafetyError("PR creation is not authorized")
        self._assert_exact_worktree()
        return _run(
            [
                "gh",
                "pr",
                "create",
                "--base",
                self.policy.pr_target,
                "--head",
                self.policy.branch or "",
                "--title",
                title,
                "--body",
                body,
            ],
            cwd=self.worktree,
        )
