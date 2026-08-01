import argparse
import os
import shutil
import subprocess
import sys
import tomllib
from collections.abc import Sequence
from pathlib import Path

DISTRIBUTION_NAME = "loop-engineering"
SKILL_CHECKOUT_NAME = "loop-engine"
CODEX_SKILL_NAME = "loop-engine"
CLI_NAME = "loop-engine"
PACKAGE_VERSION = "0.1.0"
CODEX_INVOCATION_POLICY = "policy:\n  allow_implicit_invocation: true\n"
OFFICIAL_REPOSITORY = "https://github.com/MRongM/LoopEngineering.git"
MANAGED_BRANCH = "master"
PROTOCOL_HEADER = "# Loop Engineering Core Protocol 0.1.0"
CORE_PROTOCOL_MARKER = "Core Protocol: 0.1.0"
INSTALL_TIMEOUT_SECONDS = 600
ERROR = 2
CONFIRMATION_REQUIRED = 3


class LifecycleError(RuntimeError):
    """The requested lifecycle action could not be completed safely."""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Install, update, or uninstall the Loop Engineering Codex Skill and CLI."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    install = commands.add_parser("install", help="Install the CLI from this Skill checkout.")
    install.add_argument("--codex-home", type=Path)
    update = commands.add_parser(
        "update",
        help="Fast-forward the managed Skill checkout and reinstall its CLI.",
    )
    update.add_argument("--codex-home", type=Path)
    uninstall = commands.add_parser(
        "uninstall",
        help="Uninstall the CLI and remove this validated Skill checkout.",
    )
    uninstall.add_argument("--codex-home", type=Path)
    uninstall.add_argument(
        "--yes",
        action="store_true",
        help="Confirm removal of the validated Skill checkout.",
    )
    return parser


def _codex_home(explicit: Path | None) -> Path:
    configured = explicit or os.environ.get("CODEX_HOME")
    home = Path(configured).expanduser() if configured else Path.home() / ".codex"
    home = Path(os.path.abspath(home))
    if home == Path(home.anchor):
        raise LifecycleError("CODEX_HOME cannot be a filesystem root")
    return home


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _is_link_like(path: Path) -> bool:
    return path.is_symlink() or path.is_junction()


def _validate_checkout(codex_home: Path) -> Path:
    expected = codex_home / "skills" / SKILL_CHECKOUT_NAME
    for managed_path in (codex_home, expected.parent, expected):
        if _is_link_like(managed_path):
            raise LifecycleError("managed lifecycle commands do not operate through links")
    repository = _repository_root()
    if repository != expected.resolve():
        raise LifecycleError(f"Skill checkout must be the exact managed path: {expected}")
    git_dir = repository / ".git"
    if (
        not repository.is_dir()
        or not git_dir.is_dir()
        or _is_link_like(git_dir)
    ):
        raise LifecycleError("Skill checkout is not a Git repository")

    protocol = repository / "PROTOCOL.md"
    skill = repository / "adapters" / "codex" / "SKILL.md"
    invocation_policy = repository / "adapters" / "codex" / "agents" / "openai.yaml"
    project = repository / "pyproject.toml"
    try:
        protocol_header = protocol.read_text(encoding="utf-8").splitlines()[0]
        skill_text = skill.read_text(encoding="utf-8")
        invocation_policy_text = invocation_policy.read_text(encoding="utf-8")
        project_data = tomllib.loads(project.read_text(encoding="utf-8"))
    except (IndexError, OSError, tomllib.TOMLDecodeError) as error:
        raise LifecycleError("Skill checkout markers are missing or invalid") from error
    if protocol_header != PROTOCOL_HEADER:
        raise LifecycleError("Skill checkout protocol marker does not match")
    frontmatter_parts = skill_text.split("---", 2)
    if len(frontmatter_parts) != 3 or frontmatter_parts[0].strip():
        raise LifecycleError("Skill checkout adapter marker does not match")
    skill_frontmatter = frontmatter_parts[1].splitlines()
    if (
        f"name: {CODEX_SKILL_NAME}" not in skill_frontmatter
        or CORE_PROTOCOL_MARKER not in frontmatter_parts[2]
    ):
        raise LifecycleError("Skill checkout adapter marker does not match")
    if invocation_policy_text != CODEX_INVOCATION_POLICY:
        raise LifecycleError("Skill checkout invocation policy does not match")
    project_metadata = project_data.get("project", {})
    if (
        project_metadata.get("name") != DISTRIBUTION_NAME
        or project_metadata.get("version") != PACKAGE_VERSION
        or project_metadata.get("scripts")
        != {CLI_NAME: "loop_engineering.cli:main"}
    ):
        raise LifecycleError("Skill checkout package marker does not match")
    return repository


def _executable(name: str) -> str:
    executable = shutil.which(name)
    if executable is None:
        raise LifecycleError(f"required executable is not available: {name}")
    return executable


def _run(
    argv: list[str],
    *,
    capture_output: bool = True,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    run_options: dict[str, object] = {
        "capture_output": capture_output,
        "shell": False,
        "text": True,
    }
    if timeout is not None:
        run_options["timeout"] = timeout
    return subprocess.run(
        argv,
        check=False,
        **run_options,
    )


def _verify_installed_cli() -> None:
    result = _run([_executable(CLI_NAME), "--version"])
    if result.returncode != 0 or result.stdout.splitlines() != [PACKAGE_VERSION]:
        raise LifecycleError(
            f"installed {CLI_NAME} executable does not report {PACKAGE_VERSION}"
        )


def _verify_uninstalled_cli() -> None:
    if shutil.which(CLI_NAME) is not None:
        raise LifecycleError(f"CLI executable remains discoverable: {CLI_NAME}")


def _install(repository: Path, *, reinstall: bool = False) -> None:
    argv = [_executable("uv"), "tool", "install"]
    if reinstall:
        argv.append("--reinstall")
    argv.append(str(repository))
    retained = (
        "the updated Skill checkout was retained"
        if reinstall
        else "the Skill checkout was retained"
    )
    in_progress = "Reinstalling" if reinstall else "Installing"
    print(
        f"{in_progress} {CLI_NAME} executable from "
        f"{DISTRIBUTION_NAME} distribution at {repository}",
        flush=True,
    )
    try:
        result = _run(
            argv,
            capture_output=False,
            timeout=INSTALL_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as error:
        raise LifecycleError(
            f"uv tool install timed out after {INSTALL_TIMEOUT_SECONDS} seconds; "
            f"{retained}"
        ) from error
    if result.returncode != 0:
        raise LifecycleError(f"uv tool install failed; {retained}")
    _verify_installed_cli()
    action = "Reinstalled" if reinstall else "Installed"
    print(
        f"{action} {CLI_NAME} executable from "
        f"{DISTRIBUTION_NAME} distribution at {repository}"
    )


def _ensure_outside(repository: Path) -> None:
    current = Path.cwd().resolve()
    if current == repository or repository in current.parents:
        raise LifecycleError("change to a directory outside the Skill checkout before uninstalling")


def _ensure_git_boundary(repository: Path) -> None:
    git_dir = str(repository / ".git")
    resolved = _run(
        [
            _executable("git"),
            "-C",
            str(repository),
            "rev-parse",
            "--absolute-git-dir",
            "--path-format=absolute",
            "--git-common-dir",
        ]
    )
    if resolved.returncode != 0 or resolved.stdout.splitlines() != [git_dir, git_dir]:
        raise LifecycleError("Git metadata must remain inside the managed checkout")


def _ensure_clean(repository: Path) -> None:
    status = _run(
        [
            _executable("git"),
            "-C",
            str(repository),
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--ignored=matching",
        ]
    )
    if status.returncode != 0:
        raise LifecycleError("could not verify the Skill checkout with Git")
    if status.stdout.strip():
        raise LifecycleError("Skill checkout contains modified, untracked, or ignored files")

    refs = _run(
        [
            _executable("git"),
            "-C",
            str(repository),
            "for-each-ref",
            "--format=%(refname:short)",
            "refs/heads",
            "refs/stash",
        ]
    )
    if refs.returncode != 0:
        raise LifecycleError("could not verify local Git references")
    if refs.stdout.splitlines() != [MANAGED_BRANCH]:
        raise LifecycleError("Skill checkout contains local branches or stashed changes")

    local_commits = _run(
        [
            _executable("git"),
            "-C",
            str(repository),
            "rev-list",
            "--all",
            "--not",
            "--remotes",
        ]
    )
    if local_commits.returncode != 0:
        raise LifecycleError("could not verify local Git commits")
    if local_commits.stdout.strip():
        raise LifecycleError("Skill checkout contains commits not preserved by a remote")


def _ensure_update_source(repository: Path) -> None:
    branch = _run(
        [
            _executable("git"),
            "-C",
            str(repository),
            "symbolic-ref",
            "--quiet",
            "--short",
            "HEAD",
        ]
    )
    if branch.returncode != 0 or branch.stdout.splitlines() != [MANAGED_BRANCH]:
        raise LifecycleError(f"Skill checkout must be on {MANAGED_BRANCH}")

    origin = _run(
        [
            _executable("git"),
            "-C",
            str(repository),
            "remote",
            "get-url",
            "--all",
            "origin",
        ]
    )
    if origin.returncode != 0 or origin.stdout.splitlines() != [OFFICIAL_REPOSITORY]:
        raise LifecycleError(f"Skill checkout origin must be {OFFICIAL_REPOSITORY}")

    ahead = _run(
        [
            _executable("git"),
            "-C",
            str(repository),
            "rev-list",
            "--count",
            f"refs/remotes/origin/{MANAGED_BRANCH}..HEAD",
        ]
    )
    if ahead.returncode != 0 or ahead.stdout.splitlines() != ["0"]:
        raise LifecycleError(f"Skill checkout contains commits outside origin/{MANAGED_BRANCH}")


def _ensure_updated_head(repository: Path) -> None:
    revisions = _run(
        [
            _executable("git"),
            "-C",
            str(repository),
            "rev-parse",
            "HEAD",
            "FETCH_HEAD",
        ]
    )
    resolved = revisions.stdout.splitlines()
    if revisions.returncode != 0 or len(resolved) != 2 or resolved[0] != resolved[1]:
        raise LifecycleError(f"Skill checkout does not match fetched origin/{MANAGED_BRANCH}")


def _update(codex_home: Path, repository: Path) -> None:
    _ensure_git_boundary(repository)
    _ensure_clean(repository)
    _ensure_update_source(repository)
    result = _run(
        [
            _executable("git"),
            "-C",
            str(repository),
            "pull",
            "--ff-only",
            "origin",
            MANAGED_BRANCH,
        ]
    )
    if result.returncode != 0:
        raise LifecycleError(
            "Git fast-forward update failed; the CLI was not reinstalled"
        )

    repository = _validate_checkout(codex_home)
    _ensure_git_boundary(repository)
    _ensure_clean(repository)
    _ensure_update_source(repository)
    _ensure_updated_head(repository)
    _install(repository, reinstall=True)
    print(f"Updated {CODEX_SKILL_NAME} Skill checkout at {repository}")


def _already_uninstalled(result: subprocess.CompletedProcess[str]) -> bool:
    output_lines = [
        line.strip()
        for output in (result.stdout, result.stderr)
        for line in output.splitlines()
        if line.strip()
    ]
    return result.returncode == 2 and output_lines == [
        f"error: `{DISTRIBUTION_NAME}` is not installed"
    ]


def _uninstall(codex_home: Path, repository: Path) -> None:
    _ensure_outside(repository)
    _ensure_clean(repository)
    result = _run(
        [_executable("uv"), "tool", "uninstall", DISTRIBUTION_NAME]
    )
    if result.returncode != 0 and not _already_uninstalled(result):
        raise LifecycleError("uv tool uninstall failed; the Skill checkout was retained")
    _verify_uninstalled_cli()

    # Revalidate immediately before recursive removal so a changed target fails closed.
    repository = _validate_checkout(codex_home)
    _ensure_outside(repository)
    _ensure_clean(repository)
    try:
        shutil.rmtree(repository)
    except OSError as error:
        raise LifecycleError(
            f"CLI is absent, but could not remove the Skill checkout: {repository}"
        ) from error
    print(
        f"Uninstalled {DISTRIBUTION_NAME} distribution, removed {CLI_NAME} "
        f"executable, and removed {repository}"
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        codex_home = _codex_home(args.codex_home)
        repository = _validate_checkout(codex_home)
        if args.command == "install":
            _install(repository)
        elif args.command == "update":
            _update(codex_home, repository)
        elif not args.yes:
            print(
                f"Refusing to remove {repository} without explicit --yes confirmation.",
                file=sys.stderr,
            )
            return CONFIRMATION_REQUIRED
        else:
            _uninstall(codex_home, repository)
    except LifecycleError as error:
        print(f"error: {error}", file=sys.stderr)
        return ERROR
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
