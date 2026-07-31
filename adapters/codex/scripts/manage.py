import argparse
import os
import shutil
import subprocess
import sys
import tomllib
from collections.abc import Sequence
from pathlib import Path

TOOL_NAME = "loop-engineering"
PROTOCOL_HEADER = "# Loop Engineering Core Protocol 0.1.0"
CORE_COMPATIBILITY = "Compatible Core: >=0.1,<0.2"
ERROR = 2
CONFIRMATION_REQUIRED = 3


class LifecycleError(RuntimeError):
    """The requested lifecycle action failed without changing the Skill checkout."""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Install or uninstall the Loop Engineering Codex Skill and CLI."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    install = commands.add_parser("install", help="Install the CLI from this Skill checkout.")
    install.add_argument("--codex-home", type=Path)
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
    expected = codex_home / "skills" / TOOL_NAME
    for managed_path in (codex_home, expected.parent, expected):
        if _is_link_like(managed_path):
            raise LifecycleError("managed lifecycle commands do not operate through links")
    repository = _repository_root()
    if repository != expected.resolve():
        raise LifecycleError(f"Skill checkout must be the exact managed path: {expected}")
    if not repository.is_dir() or not (repository / ".git").exists():
        raise LifecycleError("Skill checkout is not a Git repository")

    protocol = repository / "PROTOCOL.md"
    skill = repository / "adapters" / "codex" / "SKILL.md"
    project = repository / "pyproject.toml"
    try:
        protocol_header = protocol.read_text(encoding="utf-8").splitlines()[0]
        skill_text = skill.read_text(encoding="utf-8")
        project_data = tomllib.loads(project.read_text(encoding="utf-8"))
    except (IndexError, OSError, tomllib.TOMLDecodeError) as error:
        raise LifecycleError("Skill checkout markers are missing or invalid") from error
    if protocol_header != PROTOCOL_HEADER:
        raise LifecycleError("Skill checkout protocol marker does not match")
    if "name: loop-engineering" not in skill_text or CORE_COMPATIBILITY not in skill_text:
        raise LifecycleError("Skill checkout adapter marker does not match")
    if project_data.get("project", {}).get("name") != TOOL_NAME:
        raise LifecycleError("Skill checkout package marker does not match")
    return repository


def _executable(name: str) -> str:
    executable = shutil.which(name)
    if executable is None:
        raise LifecycleError(f"required executable is not available: {name}")
    return executable


def _run(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        capture_output=True,
        check=False,
        shell=False,
        text=True,
    )


def _install(repository: Path) -> None:
    result = _run([_executable("uv"), "tool", "install", str(repository)])
    if result.returncode != 0:
        raise LifecycleError("uv tool install failed; the Skill checkout was retained")
    print(f"Installed {TOOL_NAME} CLI from {repository}")


def _ensure_outside(repository: Path) -> None:
    current = Path.cwd().resolve()
    if current == repository or repository in current.parents:
        raise LifecycleError("change to a directory outside the Skill checkout before uninstalling")


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
    if refs.stdout.splitlines() != ["master"]:
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


def _already_uninstalled(result: subprocess.CompletedProcess[str]) -> bool:
    output_lines = [
        line.strip()
        for output in (result.stdout, result.stderr)
        for line in output.splitlines()
        if line.strip()
    ]
    return result.returncode == 2 and output_lines == [
        "error: `loop-engineering` is not installed"
    ]


def _uninstall(codex_home: Path, repository: Path) -> None:
    _ensure_outside(repository)
    _ensure_clean(repository)
    result = _run([_executable("uv"), "tool", "uninstall", TOOL_NAME])
    if result.returncode != 0 and not _already_uninstalled(result):
        raise LifecycleError("uv tool uninstall failed; the Skill checkout was retained")

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
    print(f"Uninstalled {TOOL_NAME} CLI and removed {repository}")


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        codex_home = _codex_home(args.codex_home)
        repository = _validate_checkout(codex_home)
        if args.command == "install":
            _install(repository)
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
