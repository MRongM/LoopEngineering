from collections.abc import Callable
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from uuid import uuid4

import pytest

MANAGER = Path("adapters/codex/scripts/manage.py")
OFFICIAL_REPOSITORY = "https://github.com/MRongM/LoopEngineering.git"


def _checkout(
    tmp_path: Path,
    *,
    canonical: bool = True,
) -> tuple[Path, Path, Path]:
    codex_home = tmp_path / "codex-home"
    repository = (
        codex_home / "skills" / "loop-engineering"
        if canonical
        else tmp_path / "somewhere-else" / "loop-engineering"
    )
    script = repository / "adapters" / "codex" / "scripts" / "manage.py"
    script.parent.mkdir(parents=True)
    shutil.copy2(MANAGER, script)
    (repository / "PROTOCOL.md").write_text(
        "# Loop Engineering Core Protocol 0.2.0\n",
        encoding="utf-8",
    )
    (repository / "adapters" / "codex" / "SKILL.md").write_text(
        "---\nname: loop-engineering\n---\n\nCompatible Core: >=0.2,<0.3\n",
        encoding="utf-8",
    )
    (repository / "pyproject.toml").write_text(
        '[project]\nname = "loop-engineering"\n',
        encoding="utf-8",
    )
    (repository / ".git").mkdir()
    return codex_home, repository, script


def _load_manager(script: Path, monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    name = f"loop_engineering_codex_manager_{uuid4().hex}"
    spec = importlib.util.spec_from_file_location(name, script)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, name, module)
    spec.loader.exec_module(module)
    return module


def _stub_commands(
    manager: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    *,
    git_stdout: str = "",
    git_refs: str = "master\n",
    git_local_commits: str = "",
    git_branch: str = "master\n",
    git_remote: str = f"{OFFICIAL_REPOSITORY}\n",
    git_pull_returncode: int = 0,
    git_pull_stderr: str = "",
    after_pull: Callable[[], None] | None = None,
    uv_returncode: int = 0,
    uv_stderr: str = "",
) -> list[tuple[list[str], dict[str, object]]]:
    calls: list[tuple[list[str], dict[str, object]]] = []
    executables = {"git": "/tools/git", "uv": "/tools/uv"}
    monkeypatch.setattr(manager.shutil, "which", executables.get)

    def run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append((argv, kwargs))
        assert kwargs == {
            "capture_output": True,
            "check": False,
            "shell": False,
            "text": True,
        }
        if argv[0] == executables["git"]:
            returncode = 0
            stderr = ""
            if "status" in argv:
                stdout = git_stdout
            elif "for-each-ref" in argv:
                stdout = git_refs
            elif "rev-list" in argv:
                stdout = git_local_commits
            elif "symbolic-ref" in argv:
                stdout = git_branch
                returncode = 0 if git_branch else 1
            elif "get-url" in argv:
                stdout = git_remote
            elif "pull" in argv:
                stdout = ""
                returncode = git_pull_returncode
                stderr = git_pull_stderr
                if returncode == 0 and after_pull is not None:
                    after_pull()
            else:
                raise AssertionError(f"unexpected Git argv: {argv}")
            return subprocess.CompletedProcess(
                argv,
                returncode,
                stdout=stdout,
                stderr=stderr,
            )
        if argv[0] == executables["uv"]:
            return subprocess.CompletedProcess(
                argv,
                uv_returncode,
                stdout="",
                stderr=uv_stderr,
            )
        raise AssertionError(f"unexpected executable: {argv[0]}")

    monkeypatch.setattr(manager.subprocess, "run", run)
    return calls


def test_lifecycle_manager_exposes_install_update_and_uninstall_commands() -> None:
    result = subprocess.run(
        [sys.executable, str(MANAGER), "--help"],
        check=False,
        capture_output=True,
        text=True,
        shell=False,
    )

    assert result.returncode == 0
    assert "{install,update,uninstall}" in result.stdout


def test_install_uses_exact_uv_argv_without_a_shell(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    codex_home, repository, script = _checkout(tmp_path)
    manager = _load_manager(script, monkeypatch)
    calls = _stub_commands(manager, monkeypatch)

    assert manager.main(["install", "--codex-home", str(codex_home)]) == 0
    assert calls == [
        (
            ["/tools/uv", "tool", "install", str(repository)],
            {
                "capture_output": True,
                "check": False,
                "shell": False,
                "text": True,
            },
        )
    ]


@pytest.mark.parametrize("failure", ["wrong-path", "missing-marker"])
def test_install_rejects_an_unmanaged_checkout_before_running_uv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
) -> None:
    codex_home, repository, script = _checkout(
        tmp_path,
        canonical=failure != "wrong-path",
    )
    if failure == "missing-marker":
        (repository / "PROTOCOL.md").unlink()
    manager = _load_manager(script, monkeypatch)
    calls = _stub_commands(manager, monkeypatch)

    assert manager.main(["install", "--codex-home", str(codex_home)]) == 2
    assert calls == []
    assert repository.exists()


@pytest.mark.parametrize("link_level", ["checkout", "skills-parent"])
def test_install_rejects_linked_managed_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    link_level: str,
) -> None:
    codex_home, repository, script = _checkout(tmp_path, canonical=False)
    codex_home.mkdir()
    try:
        if link_level == "checkout":
            skills = codex_home / "skills"
            skills.mkdir()
            (skills / "loop-engineering").symlink_to(repository, target_is_directory=True)
        else:
            (codex_home / "skills").symlink_to(repository.parent, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"directory links are unavailable: {error}")
    manager = _load_manager(script, monkeypatch)
    calls = _stub_commands(manager, monkeypatch)

    assert manager.main(["install", "--codex-home", str(codex_home)]) == 2
    assert calls == []
    assert repository.exists()


def test_update_fast_forwards_official_master_and_reinstalls_cli(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    codex_home, repository, script = _checkout(tmp_path)
    manager = _load_manager(script, monkeypatch)
    calls = _stub_commands(manager, monkeypatch)

    assert manager.main(["update", "--codex-home", str(codex_home)]) == 0

    clean_commands = [
        [
            "/tools/git",
            "-C",
            str(repository),
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--ignored=matching",
        ],
        [
            "/tools/git",
            "-C",
            str(repository),
            "for-each-ref",
            "--format=%(refname:short)",
            "refs/heads",
            "refs/stash",
        ],
        [
            "/tools/git",
            "-C",
            str(repository),
            "rev-list",
            "--all",
            "--not",
            "--remotes",
        ],
        [
            "/tools/git",
            "-C",
            str(repository),
            "symbolic-ref",
            "--quiet",
            "--short",
            "HEAD",
        ],
        [
            "/tools/git",
            "-C",
            str(repository),
            "remote",
            "get-url",
            "--all",
            "origin",
        ],
    ]
    assert [argv for argv, _ in calls] == [
        *clean_commands,
        [
            "/tools/git",
            "-C",
            str(repository),
            "pull",
            "--ff-only",
            "origin",
            "master",
        ],
        *clean_commands,
        ["/tools/uv", "tool", "install", "--reinstall", str(repository)],
    ]


@pytest.mark.parametrize(
    ("git_branch", "git_remote"),
    [
        ("feature/local\n", f"{OFFICIAL_REPOSITORY}\n"),
        ("", f"{OFFICIAL_REPOSITORY}\n"),
        ("master\n", "https://example.invalid/LoopEngineering.git\n"),
        (
            "master\n",
            f"{OFFICIAL_REPOSITORY}\nhttps://example.invalid/mirror.git\n",
        ),
    ],
)
def test_update_rejects_an_unmanaged_branch_or_origin_before_pull(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    git_branch: str,
    git_remote: str,
) -> None:
    codex_home, repository, script = _checkout(tmp_path)
    manager = _load_manager(script, monkeypatch)
    calls = _stub_commands(
        manager,
        monkeypatch,
        git_branch=git_branch,
        git_remote=git_remote,
    )

    assert manager.main(["update", "--codex-home", str(codex_home)]) == 2
    assert not any("pull" in argv for argv, _ in calls)
    assert not any(argv[0] == "/tools/uv" for argv, _ in calls)
    assert repository.exists()


def test_update_rejects_a_dirty_checkout_before_pull(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    codex_home, repository, script = _checkout(tmp_path)
    manager = _load_manager(script, monkeypatch)
    calls = _stub_commands(manager, monkeypatch, git_stdout=" M README.md\n")

    assert manager.main(["update", "--codex-home", str(codex_home)]) == 2
    assert len(calls) == 1
    assert repository.exists()


@pytest.mark.parametrize(
    ("git_refs", "git_local_commits"),
    [
        ("master\nfeature/local\n", ""),
        ("master\nstash\n", ""),
        ("master\n", "deadbeef\n"),
    ],
)
def test_update_preserves_local_git_state_not_shown_by_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    git_refs: str,
    git_local_commits: str,
) -> None:
    codex_home, repository, script = _checkout(tmp_path)
    manager = _load_manager(script, monkeypatch)
    calls = _stub_commands(
        manager,
        monkeypatch,
        git_refs=git_refs,
        git_local_commits=git_local_commits,
    )

    assert manager.main(["update", "--codex-home", str(codex_home)]) == 2
    assert not any("pull" in argv for argv, _ in calls)
    assert repository.exists()


def test_update_does_not_reinstall_cli_when_fast_forward_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    codex_home, repository, script = _checkout(tmp_path)
    manager = _load_manager(script, monkeypatch)
    calls = _stub_commands(
        manager,
        monkeypatch,
        git_pull_returncode=1,
        git_pull_stderr="fatal: Not possible to fast-forward\n",
    )

    assert manager.main(["update", "--codex-home", str(codex_home)]) == 2
    assert not any(argv[0] == "/tools/uv" for argv, _ in calls)
    assert repository.exists()


def test_update_revalidates_markers_before_reinstalling_cli(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    codex_home, repository, script = _checkout(tmp_path)
    manager = _load_manager(script, monkeypatch)

    def invalidate_protocol_marker() -> None:
        (repository / "PROTOCOL.md").write_text(
            "# unexpected protocol\n",
            encoding="utf-8",
        )

    calls = _stub_commands(
        manager,
        monkeypatch,
        after_pull=invalidate_protocol_marker,
    )

    assert manager.main(["update", "--codex-home", str(codex_home)]) == 2
    assert not any(argv[0] == "/tools/uv" for argv, _ in calls)
    assert repository.exists()


def test_update_retains_the_updated_checkout_when_uv_reinstall_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    codex_home, repository, script = _checkout(tmp_path)
    manager = _load_manager(script, monkeypatch)
    calls = _stub_commands(
        manager,
        monkeypatch,
        uv_returncode=1,
        uv_stderr="error: permission denied\n",
    )

    assert manager.main(["update", "--codex-home", str(codex_home)]) == 2
    assert calls[-1][0] == [
        "/tools/uv",
        "tool",
        "install",
        "--reinstall",
        str(repository),
    ]
    assert "updated Skill checkout was retained" in capsys.readouterr().err
    assert repository.exists()


def test_uninstall_requires_explicit_yes_before_running_commands(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    codex_home, repository, script = _checkout(tmp_path)
    manager = _load_manager(script, monkeypatch)
    calls = _stub_commands(manager, monkeypatch)

    assert manager.main(["uninstall", "--codex-home", str(codex_home)]) == 3
    assert calls == []
    assert repository.exists()


def test_uninstall_refuses_a_dirty_checkout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    codex_home, repository, script = _checkout(tmp_path)
    manager = _load_manager(script, monkeypatch)
    calls = _stub_commands(manager, monkeypatch, git_stdout=" M README.md\n")
    monkeypatch.chdir(tmp_path)

    assert manager.main(["uninstall", "--codex-home", str(codex_home), "--yes"]) == 2
    assert len(calls) == 1
    assert repository.exists()


@pytest.mark.parametrize(
    ("git_refs", "git_local_commits"),
    [
        ("master\nfeature/local\n", ""),
        ("master\nstash\n", ""),
        ("master\n", "deadbeef\n"),
    ],
)
def test_uninstall_preserves_local_git_state_not_shown_by_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    git_refs: str,
    git_local_commits: str,
) -> None:
    codex_home, repository, script = _checkout(tmp_path)
    manager = _load_manager(script, monkeypatch)
    _stub_commands(
        manager,
        monkeypatch,
        git_refs=git_refs,
        git_local_commits=git_local_commits,
    )
    monkeypatch.chdir(tmp_path)

    assert manager.main(["uninstall", "--codex-home", str(codex_home), "--yes"]) == 2
    assert repository.exists()


def test_uninstall_refuses_to_remove_the_current_working_tree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    codex_home, repository, script = _checkout(tmp_path)
    manager = _load_manager(script, monkeypatch)
    calls = _stub_commands(manager, monkeypatch)
    monkeypatch.chdir(repository / "adapters")

    assert manager.main(["uninstall", "--codex-home", str(codex_home), "--yes"]) == 2
    assert calls == []
    assert repository.exists()


def test_uninstall_keeps_the_skill_when_uv_fails_unexpectedly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    codex_home, repository, script = _checkout(tmp_path)
    manager = _load_manager(script, monkeypatch)
    calls = _stub_commands(
        manager,
        monkeypatch,
        uv_returncode=2,
        uv_stderr="error: permission denied\n",
    )
    monkeypatch.chdir(tmp_path)

    assert manager.main(["uninstall", "--codex-home", str(codex_home), "--yes"]) == 2
    assert calls[-1][0] == ["/tools/uv", "tool", "uninstall", "loop-engineering"]
    assert repository.exists()


def test_uninstall_reports_directory_removal_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    codex_home, repository, script = _checkout(tmp_path)
    manager = _load_manager(script, monkeypatch)
    _stub_commands(manager, monkeypatch)

    def fail_removal(_path: Path) -> None:
        raise OSError("directory is busy")

    monkeypatch.setattr(manager.shutil, "rmtree", fail_removal)
    monkeypatch.chdir(tmp_path)

    assert manager.main(["uninstall", "--codex-home", str(codex_home), "--yes"]) == 2
    assert "could not remove" in capsys.readouterr().err
    assert repository.exists()


@pytest.mark.parametrize(
    ("uv_returncode", "uv_stderr"),
    [
        (0, ""),
        (2, "error: `loop-engineering` is not installed\n"),
    ],
)
def test_uninstall_removes_only_the_validated_checkout_after_cli_is_absent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    uv_returncode: int,
    uv_stderr: str,
) -> None:
    codex_home, repository, script = _checkout(tmp_path)
    sibling = codex_home / "skills" / "keep-me"
    sibling.mkdir()
    manager = _load_manager(script, monkeypatch)
    calls = _stub_commands(
        manager,
        monkeypatch,
        uv_returncode=uv_returncode,
        uv_stderr=uv_stderr,
    )
    monkeypatch.chdir(tmp_path)

    assert manager.main(["uninstall", "--codex-home", str(codex_home), "--yes"]) == 0
    assert not repository.exists()
    assert sibling.is_dir()
    assert calls[-1][0][0] == "/tools/git"
