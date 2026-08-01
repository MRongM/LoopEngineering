import os
import subprocess
from pathlib import Path

import pytest

from loop_engineering.cli import main
from loop_engineering.git_automation import GitAutomation, GitSafetyError
from loop_engineering.ledger import RunStore
from loop_engineering.models.contract import LoopContract
from loop_engineering.models.run import EventKind, LoopStatus
from tests.factories import valid_contract_data


def run(*argv: str, cwd: Path | None = None) -> str:
    result = subprocess.run(
        list(argv),
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        shell=False,
    )
    return result.stdout.strip()


def git_contract(
    repo: Path,
    worktree: Path,
    *,
    plan_worktree: bool = False,
) -> LoopContract:
    data = valid_contract_data()
    data["repositories"][0].update(
        {"path": str(repo), "allowed_paths": ["src/", "tests/"]}
    )
    data["git_policy"]["targets"][0].update(
        {
            "create_worktree": True,
            "commit": True,
            "push": True,
            "create_pr": True,
            "branch": "feat/loop-test",
            "remote": "origin",
            "pr_target": "master",
            "worktree_path": str(worktree),
        }
    )
    if plan_worktree:
        target = f"feat/loop-test@{worktree.resolve()}"
        data["authorized_operations"] = [
            {
                "risk_id": "RISK-1",
                "kind": "git_worktree",
                "repository_id": "target",
                "target": target,
                "risk_level": "low",
                "impact": "Creates the approved isolated Git worktree",
                "worst_case": "The worktree path may need manual cleanup",
                "recovery": "Remove the worktree through a separately approved action",
                "evidence": "The execution plan requires isolated implementation",
            }
        ]
        data["execution_plan"]["actions"].append(
            {
                "kind": "git_worktree",
                "repository_id": "target",
                "target": target,
                "impact": "Creates the approved isolated Git worktree",
                "risk": "A new branch and worktree are created",
                "recovery": "Remove them through a separately approved action",
                "evidence": "Git state proves the exact branch and worktree",
            }
        )
    return LoopContract.model_validate(data)


def approve_for_execution(store: RunStore) -> None:
    for target in (
        LoopStatus.DISCOVERING,
        LoopStatus.CONTRACT_DRAFTING,
        LoopStatus.AWAITING_APPROVAL,
    ):
        store.record_transition(actor="maker", target=target, reason=target.value)
    store.record_approval(
        actor="user",
        gate="contract_approval",
        approved=True,
        summary="approved exact Git plan",
    )
    for target in (LoopStatus.PLANNING, LoopStatus.EXECUTING):
        store.record_transition(actor="maker", target=target, reason=target.value)


def repositories(tmp_path: Path) -> tuple[Path, Path]:
    remote = tmp_path / "remote.git"
    source = tmp_path / "source"
    run("git", "init", "--bare", str(remote))
    run("git", "init", "-b", "master", str(source))
    run("git", "config", "user.email", "test@example.com", cwd=source)
    run("git", "config", "user.name", "Test", cwd=source)
    (source / "src").mkdir()
    (source / "tests").mkdir()
    (source / "src" / "app.py").write_text("VALUE = 1\n")
    (source / "tests" / ".gitkeep").write_text("")
    run("git", "add", ".", cwd=source)
    run("git", "commit", "-m", "initial", cwd=source)
    run("git", "remote", "add", "origin", str(remote), cwd=source)
    run("git", "push", "-u", "origin", "master", cwd=source)
    return source, remote


def test_worktree_commit_and_push_use_exact_contract_targets(tmp_path: Path) -> None:
    source, remote = repositories(tmp_path)
    worktree = tmp_path / "worktree"
    automation = GitAutomation(git_contract(source, worktree), "target")

    assert automation.prepare_worktree() == worktree.resolve()
    (worktree / "src" / "app.py").write_text("VALUE = 2\n")
    commit = automation.commit(["src/app.py"], "feat: update value")
    automation.push()

    assert len(commit) == 40
    assert (
        run(
            "git",
            "--git-dir",
            str(remote),
            "rev-parse",
            "refs/heads/feat/loop-test",
        )
        == commit
    )


def test_cli_git_prepare_rejects_missing_contract_authorization(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source, _ = repositories(tmp_path)
    worktree = tmp_path / "worktree"
    store = RunStore.create(source, git_contract(source, worktree))

    assert main(["git", "prepare", str(store.run_dir), "target"]) == 2
    assert not worktree.exists()
    assert "contract approval" in capsys.readouterr().err


def test_cli_git_prepare_uses_exact_plan_and_records_intent_result(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source, _ = repositories(tmp_path)
    worktree = tmp_path / "worktree"
    store = RunStore.create(
        source,
        git_contract(source, worktree, plan_worktree=True),
    )
    approve_for_execution(store)

    assert main(["git", "prepare", str(store.run_dir), "target"]) == 0
    assert worktree.is_dir()
    events = store.events()
    assert [event.kind for event in events[-2:]] == [EventKind.INTENT, EventKind.RESULT]
    assert events[-1].payload["git"] == {
        "operation": "prepare",
        "repository_id": "target",
        "success": True,
        "worktree": str(worktree.resolve()),
    }
    assert capsys.readouterr().err == ""


def test_cli_git_failure_closes_its_intent(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source, _ = repositories(tmp_path)
    worktree = tmp_path / "worktree"
    store = RunStore.create(
        source,
        git_contract(source, worktree, plan_worktree=True),
    )
    approve_for_execution(store)
    worktree.mkdir()

    assert main(["git", "prepare", str(store.run_dir), "target"]) == 2
    assert store.pending_intents() == []
    result = store.events()[-1]
    assert result.kind is EventKind.RESULT
    assert result.payload["git"] == {
        "error_type": "GitSafetyError",
        "operation": "prepare",
        "repository_id": "target",
        "success": False,
    }
    assert "worktree target already exists" in capsys.readouterr().err


def test_unknown_repository_id_is_not_authorized(tmp_path: Path) -> None:
    source, _ = repositories(tmp_path)
    with pytest.raises(GitSafetyError, match="repository is not authorized"):
        GitAutomation(git_contract(source, tmp_path / "worktree"), "missing")


def test_repository_path_must_be_the_exact_git_root(tmp_path: Path) -> None:
    source, _ = repositories(tmp_path)
    contract = git_contract(source, tmp_path / "worktree")
    contract = contract.model_copy(
        update={
            "repositories": [
                contract.repositories[0].model_copy(update={"path": source / "src"})
            ]
        }
    )
    with pytest.raises(GitSafetyError, match="repository path is not the Git root"):
        GitAutomation(contract, "target")


def test_commit_rejects_paths_outside_allowlist(tmp_path: Path) -> None:
    source, _ = repositories(tmp_path)
    worktree = tmp_path / "worktree"
    automation = GitAutomation(git_contract(source, worktree), "target")
    automation.prepare_worktree()
    (worktree / "secret.txt").write_text("do not stage\n")

    with pytest.raises(GitSafetyError, match="outside allowed paths"):
        automation.commit(["secret.txt"], "bad")


def test_prepare_worktree_does_not_touch_user_changes(tmp_path: Path) -> None:
    source, _ = repositories(tmp_path)
    (source / "local-notes.txt").write_text("user-owned\n")
    worktree = tmp_path / "worktree"

    GitAutomation(git_contract(source, worktree), "target").prepare_worktree()

    assert (source / "local-notes.txt").read_text() == "user-owned\n"
    assert "?? local-notes.txt" in run("git", "status", "--short", cwd=source)


def test_commit_refuses_previously_staged_content(tmp_path: Path) -> None:
    source, _ = repositories(tmp_path)
    worktree = tmp_path / "worktree"
    automation = GitAutomation(git_contract(source, worktree), "target")
    automation.prepare_worktree()
    (worktree / "tests" / "extra.py").write_text("VALUE = 3\n")
    run("git", "add", "tests/extra.py", cwd=worktree)
    (worktree / "src" / "app.py").write_text("VALUE = 2\n")

    with pytest.raises(GitSafetyError, match="index already contains staged paths"):
        automation.commit(["src/app.py"], "feat: update value")


def test_commit_refuses_a_different_checked_out_branch(tmp_path: Path) -> None:
    source, _ = repositories(tmp_path)
    worktree = tmp_path / "worktree"
    automation = GitAutomation(git_contract(source, worktree), "target")
    automation.prepare_worktree()
    run("git", "switch", "-c", "feat/other", cwd=worktree)
    (worktree / "src" / "app.py").write_text("VALUE = 2\n")

    with pytest.raises(GitSafetyError, match="current branch does not match contract"):
        automation.commit(["src/app.py"], "feat: update value")


@pytest.mark.skipif(os.name == "nt", reason="fake gh executable is POSIX-only")
def test_pr_uses_gh_without_shell(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, _ = repositories(tmp_path)
    worktree = tmp_path / "worktree"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    gh = bin_dir / "gh"
    gh.write_text("#!/bin/sh\nprintf '%s\\n' 'https://github.test/pr/1'\n")
    gh.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    automation = GitAutomation(git_contract(source, worktree), "target")
    automation.prepare_worktree()

    assert automation.create_pr("Title", "Body") == "https://github.test/pr/1"
