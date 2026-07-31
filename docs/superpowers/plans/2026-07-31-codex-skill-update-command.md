# Codex Skill Update Command Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. The user selected inline execution; do not dispatch implementation subagents. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a fail-closed `manage.py update` command that fast-forwards the exact managed Loop Engineering Codex Skill checkout from official `origin/master` and reinstalls the CLI from that updated checkout.

**Architecture:** Keep all Codex-specific lifecycle behavior in `adapters/codex/scripts/manage.py`. Reuse existing checkout, clean-state, executable, and argv subprocess helpers; add only source validation and update orchestration. Tests stub every Git and uv subprocess, so development validation never updates a real Skill or uses the network.

**Tech Stack:** Python 3.12+, standard-library `argparse`/`pathlib`/`subprocess`, pytest 9, Ruff, Markdown documentation.

## Global Constraints

- Read `PROTOCOL.md` and `docs/superpowers/specs/2026-07-31-codex-skill-update-command-design.md` before changing behavior.
- Add failing tests and preserve observed RED output before production changes.
- Every subprocess uses an argv list with `shell=False`; never add shell command strings.
- Do not weaken existing lifecycle validation, tests, schemas, or gates.
- Do not add dependencies, automatic updates, deletion/reclone, rollback, merge, deployment, force-push, history rewrite, or production access.
- Modify only the paths authorized by `.loop-runs/loop-codex-skill-update/contract.yaml`.
- Do not create a branch or commit; the user did not authorize Git mutations.
- Record each write intent/result and fresh validation evidence in the current Loop ledger.

## File Structure

| File | Responsibility |
|---|---|
| `adapters/codex/scripts/manage.py` | Parse lifecycle commands, validate the managed checkout and source, perform fast-forward update, reinstall CLI |
| `tests/test_codex_installer.py` | Behavioral and fail-closed tests using only temporary paths and stubbed subprocesses |
| `adapters/codex/SKILL.md` | Codex-facing lifecycle workflow and safety boundary |
| `README.md` | Copy-paste Unix/PowerShell update entrypoint for users |
| `docs/adoption.md` | Detailed managed lifecycle adoption instructions |
| `tests/test_adapter_contract.py` | Static contract tying all three documentation surfaces together |

---

### Task 1: Drive the managed update behavior with failing tests

**Files:**

- Modify: `tests/test_codex_installer.py`
- Modify: `adapters/codex/scripts/manage.py`

**Interfaces:**

- Consumes: existing `_validate_checkout(codex_home: Path) -> Path`, `_ensure_clean(repository: Path) -> None`, `_run(argv: list[str]) -> CompletedProcess[str]`, and `_executable(name: str) -> str`.
- Produces: `OFFICIAL_REPOSITORY`, `MANAGED_BRANCH`, `_ensure_update_source(repository: Path) -> None`, `_update(codex_home: Path, repository: Path) -> None`, and `update --codex-home PATH`.

- [ ] **Step 1: Extend the subprocess stub and add all update tests before production code**

Add `Callable` and the canonical test URL:

```python
from collections.abc import Callable

OFFICIAL_REPOSITORY = "https://github.com/MRongM/LoopEngineering.git"
```

Extend `_stub_commands` with these keyword parameters:

```python
git_branch: str = "master\n",
git_remote: str = f"{OFFICIAL_REPOSITORY}\n",
git_pull_returncode: int = 0,
git_pull_stderr: str = "",
after_pull: Callable[[], None] | None = None,
```

Handle the new exact Git commands inside its stubbed `run` function:

```python
elif "symbolic-ref" in argv:
    returncode = 0 if git_branch else 1
    return subprocess.CompletedProcess(
        argv, returncode, stdout=git_branch, stderr=""
    )
elif "get-url" in argv:
    return subprocess.CompletedProcess(argv, 0, stdout=git_remote, stderr="")
elif "pull" in argv:
    if git_pull_returncode == 0 and after_pull is not None:
        after_pull()
    return subprocess.CompletedProcess(
        argv,
        git_pull_returncode,
        stdout="",
        stderr=git_pull_stderr,
    )
```

Rename the help test and require the new parser surface:

```python
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
```

Add the successful exact-argv behavior:

```python
def test_update_fast_forwards_official_master_and_reinstalls_cli(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    codex_home, repository, script = _checkout(tmp_path)
    manager = _load_manager(script, monkeypatch)
    calls = _stub_commands(manager, monkeypatch)

    assert manager.main(["update", "--codex-home", str(codex_home)]) == 0

    argv_calls = [argv for argv, _ in calls]
    clean = [
        [
            "/tools/git", "-C", str(repository), "status", "--porcelain=v1",
            "--untracked-files=all", "--ignored=matching",
        ],
        [
            "/tools/git", "-C", str(repository), "for-each-ref",
            "--format=%(refname:short)", "refs/heads", "refs/stash",
        ],
        [
            "/tools/git", "-C", str(repository), "rev-list", "--all",
            "--not", "--remotes",
        ],
        [
            "/tools/git", "-C", str(repository), "symbolic-ref", "--quiet",
            "--short", "HEAD",
        ],
        [
            "/tools/git", "-C", str(repository), "remote", "get-url", "--all",
            "origin",
        ],
    ]
    assert argv_calls == [
        *clean,
        [
            "/tools/git", "-C", str(repository), "pull", "--ff-only",
            "origin", "master",
        ],
        *clean,
        [
            "/tools/uv", "tool", "install", "--reinstall", str(repository),
        ],
    ]
```

Add fail-closed precondition coverage:

```python
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
```

Add Git, post-update validation, and uv failure coverage:

```python
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
        (repository / "PROTOCOL.md").write_text("# unexpected protocol\n", encoding="utf-8")

    calls = _stub_commands(manager, monkeypatch, after_pull=invalidate_protocol_marker)

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
        "/tools/uv", "tool", "install", "--reinstall", str(repository),
    ]
    assert "updated Skill checkout was retained" in capsys.readouterr().err
    assert repository.exists()
```

- [ ] **Step 2: Run the focused tests and preserve RED evidence**

Run:

```bash
".venv/bin/python" -m pytest "tests/test_codex_installer.py" -q
```

Expected: existing install/uninstall tests pass; new update tests fail because argparse does not expose `update` and no update orchestration exists. Record the exact counts and reason in the Loop ledger before editing `manage.py`.

- [ ] **Step 3: Implement only the behavior required by the failing tests**

Add constants beside `TOOL_NAME`:

```python
OFFICIAL_REPOSITORY = "https://github.com/MRongM/LoopEngineering.git"
MANAGED_BRANCH = "master"
```

Update the exception docstring because an update may safely preserve a fast-forwarded
checkout when the later CLI reinstall fails:

```python
class LifecycleError(RuntimeError):
    """The requested lifecycle action could not be completed safely."""
```

Update the parser description and add `update` between install and uninstall:

```python
parser = argparse.ArgumentParser(
    description="Install, update, or uninstall the Loop Engineering Codex Skill and CLI."
)
# Existing install parser remains unchanged.
update = commands.add_parser(
    "update",
    help="Fast-forward the managed Skill checkout and reinstall its CLI.",
)
update.add_argument("--codex-home", type=Path)
```

Generalize `_install` without changing existing install argv:

```python
def _install(repository: Path, *, reinstall: bool = False) -> None:
    argv = [_executable("uv"), "tool", "install"]
    if reinstall:
        argv.append("--reinstall")
    argv.append(str(repository))
    result = _run(argv)
    if result.returncode != 0:
        retained = "the updated Skill checkout was retained" if reinstall else "the Skill checkout was retained"
        raise LifecycleError(f"uv tool install failed; {retained}")
    action = "Reinstalled" if reinstall else "Installed"
    print(f"{action} {TOOL_NAME} CLI from {repository}")
```

Add exact branch and origin validation:

```python
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
```

Add update orchestration:

```python
def _update(codex_home: Path, repository: Path) -> None:
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
        raise LifecycleError("Git fast-forward update failed; the CLI was not reinstalled")

    repository = _validate_checkout(codex_home)
    _ensure_clean(repository)
    _ensure_update_source(repository)
    _install(repository, reinstall=True)
    print(f"Updated {TOOL_NAME} Skill checkout at {repository}")
```

Route the command without weakening uninstall confirmation:

```python
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
```

- [ ] **Step 4: Run the installer tests and preserve GREEN evidence**

Run:

```bash
".venv/bin/python" -m pytest "tests/test_codex_installer.py" -q
```

Expected: all installer tests pass with no network access and no warnings.

---

### Task 2: Drive consistent user documentation with a failing contract test

**Files:**

- Modify: `tests/test_adapter_contract.py`
- Modify: `adapters/codex/SKILL.md`
- Modify: `README.md`
- Modify: `docs/adoption.md`

**Interfaces:**

- Consumes: the exact `manage.py update --codex-home` interface from Task 1.
- Produces: matching Unix and PowerShell instructions and static assertions across all user-facing surfaces.

- [ ] **Step 1: Add documentation assertions before changing documentation**

In `test_codex_skill_declares_required_loop_contract`, replace the existing
`"install or uninstall"` metadata assertion and require update-aware body markers:

```python
assert "install, update, or uninstall" in metadata["description"]
for required in (
    "update --codex-home",
    "uv tool install --reinstall",
    "git pull --ff-only",
    "official origin/master",
):
    assert required in body
```

In `test_adoption_guide_has_manual_and_installed_paths`, require:

```python
assert "托管安装、更新与卸载：CLI + Codex Skill" in text
assert 'manage.py" update --codex-home' in text
assert "git pull --ff-only" in text
assert "uv tool install --reinstall" in text
```

Add a README update-contract test:

```python
def test_readme_documents_one_line_fail_closed_update() -> None:
    text = Path("README.md").read_text(encoding="utf-8")
    update = (
        'codex_home="${CODEX_HOME:-$HOME/.codex}";'
        ' skill_dir="$codex_home/skills/loop-engineering";'
        ' python3 "$skill_dir/adapters/codex/scripts/manage.py" update'
        ' --codex-home "$codex_home"'
        ' && loop-engineering --version'
    )

    assert update in text
    assert "fast-forward-only" in text
    assert "updated Skill checkout" in text
    assert "rm -rf" not in text
```

- [ ] **Step 2: Run the contract test and preserve RED evidence**

Run:

```bash
".venv/bin/python" -m pytest "tests/test_adapter_contract.py" -q
```

Expected: failures identify missing update commands and safety wording in the Skill, README, and adoption guide.

- [ ] **Step 3: Update the Codex Skill lifecycle section**

Change frontmatter to include `install, update, or uninstall`. In `Adapter lifecycle`, document the Unix and PowerShell update commands exactly as approved in the design. State that update:

- is user-operated rather than a Maker-loop action;
- requires the official `origin/master`, a clean managed checkout, and fast-forward-only Git history;
- revalidates after Git and uses `uv tool install --reinstall`;
- retains the updated checkout on CLI reinstall failure;
- requires a new Codex session after success.

Do not alter the Loop intake, Maker/Checker, gate, or completion semantics.

- [ ] **Step 4: Add the README update entrypoint**

Insert `## Update in Codex` between installation and uninstallation. Add this exact Unix one-line command:

```bash
codex_home="${CODEX_HOME:-$HOME/.codex}"; skill_dir="$codex_home/skills/loop-engineering"; python3 "$skill_dir/adapters/codex/scripts/manage.py" update --codex-home "$codex_home" && loop-engineering --version
```

Add the corresponding PowerShell commands from the design. Explain fast-forward-only behavior, official source/branch validation, clean-state refusal, partial CLI failure recovery, and the new-session requirement.

- [ ] **Step 5: Extend the adoption guide**

Rename the lifecycle heading to `托管安装、更新与卸载：CLI + Codex Skill`. Add update examples for Unix and PowerShell using the same variables and exact manager invocation as README. Explain that the manager performs `git pull --ff-only origin master`, then `uv tool install --reinstall` only after post-update validation.

- [ ] **Step 6: Run the adapter contract tests and preserve GREEN evidence**

Run:

```bash
".venv/bin/python" -m pytest "tests/test_adapter_contract.py" -q
```

Expected: all adapter documentation contract tests pass.

---

### Task 3: Verify scope, quality, and protocol completion

**Files:**

- Verify only: all authorized files and `.loop-runs/loop-codex-skill-update/`

**Interfaces:**

- Consumes: Tasks 1–2 final working tree.
- Produces: fresh evidence for `AC-1` through `AC-4`, independent medium-risk Checker verdict, and final acceptance handoff.

- [ ] **Step 1: Run focused validation through the Loop evidence runner**

Run:

```bash
".venv/bin/loop-engineering" evidence run ".loop-runs/loop-codex-skill-update" "VAL-1"
".venv/bin/loop-engineering" evidence run ".loop-runs/loop-codex-skill-update" "VAL-2"
```

Expected: both evidence records report exit code 0 against the current fingerprint.

- [ ] **Step 2: Run complete tests and lint through the evidence runner**

Run:

```bash
".venv/bin/loop-engineering" evidence run ".loop-runs/loop-codex-skill-update" "VAL-3"
".venv/bin/loop-engineering" evidence run ".loop-runs/loop-codex-skill-update" "VAL-4"
```

Expected: the complete suite and Ruff both exit 0 with no new warnings.

- [ ] **Step 3: Run non-mutating diff and scope checks**

Run:

```bash
git diff --check
git status --short
".venv/bin/loop-engineering" scope check ".loop-runs/loop-codex-skill-update/contract.yaml"
```

Expected: diff check exits 0; status lists only authorized files; scope check reports valid.

- [ ] **Step 4: Obtain the required independent medium-risk Checker verdict**

Provide a fresh read-only reviewer with the approved contract, design, actual diff, RED/GREEN results, and raw evidence. The reviewer must check source trust, fail-closed ordering, partial failure semantics, exact argv/`shell=False`, tests, documentation consistency, and scope. Record only `ACCEPT`, `REVISE`, or `BLOCK` in the Loop ledger. The reviewer must not edit files.

- [ ] **Step 5: Evaluate completion and leave only final human acceptance**

Transition through verifying/checking/deciding, build CompletionContext only from current evidence, scope output, ledger events, and Checker verdict, then run `completion evaluate`. Because the approved contract explicitly retains `final_acceptance`, stop before DONE and present the evidence-backed result to the user. Do not commit or push.
