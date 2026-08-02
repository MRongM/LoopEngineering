# Managed Update Script Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an executable root `update.sh` that safely updates the canonical Codex managed checkout through the existing lifecycle manager.

**Architecture:** Keep the Shell surface as a thin POSIX wrapper. It resolves the lifecycle manager from its own checkout, resolves `CODEX_HOME` exactly as the documented Unix flow does, and replaces itself with `python3 manage.py update`; the Python manager remains the single owner of Git, origin, checkout, reinstall, and version safety checks.

**Tech Stack:** POSIX `sh`, Python 3.12+, pytest, existing Codex lifecycle manager.

## Global Constraints

- The wrapper updates only `<CODEX_HOME>/skills/loop-engine`; it does not update arbitrary development repositories.
- Core remains tool-independent; Codex-specific update behavior stays in `adapters/codex/`.
- All paths and argv elements are quoted; Python subprocess code continues to use argv and `shell=False`.
- Do not duplicate or weaken the manager's clean-tree, official-origin, branch, fast-forward, marker, or CLI-version gates.
- Do not add dependencies, automatic merge, deployment, force-push, history rewrite, reset-hard, or production access.
- Execute inline; do not create subagents, branches, worktrees, commits, pushes, or pull requests.

---

### Task 1: Specify and implement the thin update wrapper

**Files:**
- Create: `tests/test_update_script.py`
- Create: `update.sh`

**Interfaces:**
- Consumes: `CODEX_HOME` when set, otherwise `$HOME/.codex`; `python3`; `adapters/codex/scripts/manage.py` in the same checkout.
- Produces: executable `update.sh` invoking `python3 <manager> update --codex-home <resolved-home>` and returning the manager's exact exit status.

- [x] **Step 1: Write the failing behavior tests**

```python
import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

UPDATE_SCRIPT = Path("update.sh")
FAKE_MANAGER = """import json
import os
import sys

print(json.dumps(sys.argv[1:]))
raise SystemExit(int(os.environ.get("TEST_MANAGER_EXIT", "0")))
"""


def _installed_script(tmp_path: Path, codex_home: Path) -> Path:
    assert UPDATE_SCRIPT.is_file(), "root update.sh is missing"
    repository = codex_home / "skills" / "loop-engine"
    manager = repository / "adapters" / "codex" / "scripts" / "manage.py"
    manager.parent.mkdir(parents=True)
    manager.write_text(FAKE_MANAGER, encoding="utf-8")
    script = repository / "update.sh"
    shutil.copy2(UPDATE_SCRIPT, script)
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    return script


@pytest.mark.parametrize("explicit_codex_home", [True, False])
def test_update_script_dispatches_exact_manager_argv_from_any_directory(
    tmp_path: Path,
    explicit_codex_home: bool,
) -> None:
    home = tmp_path / "home with spaces"
    codex_home = (
        tmp_path / "custom codex home"
        if explicit_codex_home
        else home / ".codex"
    )
    script = _installed_script(tmp_path, codex_home)
    outside = tmp_path / "outside checkout"
    outside.mkdir()
    environment = os.environ.copy()
    environment["HOME"] = str(home)
    if explicit_codex_home:
        environment["CODEX_HOME"] = str(codex_home)
    else:
        environment.pop("CODEX_HOME", None)

    result = subprocess.run(
        [str(script)],
        cwd=outside,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        shell=False,
    )

    assert result.returncode == 0
    assert json.loads(result.stdout) == ["update", "--codex-home", str(codex_home)]
    assert result.stderr == ""


def test_update_script_propagates_manager_failure(tmp_path: Path) -> None:
    codex_home = tmp_path / "codex home"
    script = _installed_script(tmp_path, codex_home)
    environment = os.environ.copy()
    environment["CODEX_HOME"] = str(codex_home)
    environment["TEST_MANAGER_EXIT"] = "7"

    result = subprocess.run(
        [str(script)],
        cwd=tmp_path,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        shell=False,
    )

    assert result.returncode == 7


def test_update_script_is_executable_posix_shell() -> None:
    assert UPDATE_SCRIPT.is_file(), "root update.sh is missing"
    assert os.access(UPDATE_SCRIPT, os.X_OK)
    result = subprocess.run(
        ["/bin/sh", "-n", str(UPDATE_SCRIPT)],
        check=False,
        capture_output=True,
        text=True,
        shell=False,
    )
    assert result.returncode == 0
    assert result.stderr == ""
```

- [x] **Step 2: Run the focused test and retain RED evidence**

Run: `uv run pytest -q tests/test_update_script.py`

Expected: four failed cases whose first assertion reports `root update.sh is missing`.

- [x] **Step 3: Add the minimal POSIX wrapper**

```sh
#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -P "$(dirname "$0")" && pwd)

if [ -n "${CODEX_HOME:-}" ]; then
    codex_home="$CODEX_HOME"
else
    codex_home="${HOME:?HOME must be set when CODEX_HOME is unset}/.codex"
fi

exec python3 \
    "$script_dir/adapters/codex/scripts/manage.py" \
    update \
    --codex-home \
    "$codex_home"
```

Make it executable with: `chmod 755 "update.sh"`.

- [x] **Step 4: Run focused GREEN verification**

Run: `uv run pytest -q tests/test_update_script.py`

Expected: `4 passed`.

Run: `/bin/sh -n "update.sh"`

Expected: exit code `0` with no output.

### Task 2: Document and verify the managed entrypoint

**Files:**
- Modify: `README.md:90`
- Test: `tests/test_update_script.py`

**Interfaces:**
- Consumes: the executable root `update.sh` from Task 1.
- Produces: a discoverable Unix update command without changing the existing one-line or PowerShell flows.

- [x] **Step 1: Add the checked-in wrapper to the Unix update documentation**

Insert before `### Unix one-line update`:

````markdown
### Unix update script

From the managed checkout root, run the checked-in wrapper:

```bash
./update.sh
```

The wrapper honors `CODEX_HOME` and otherwise uses `$HOME/.codex`. It can also be invoked by
absolute path from another working directory.
````

- [x] **Step 2: Run focused lifecycle regression tests**

Run: `uv run pytest -q tests/test_update_script.py tests/test_codex_installer.py`

Expected: all selected tests pass.

- [x] **Step 3: Run full fresh verification**

Run: `uv run pytest -q`

Expected: all tests pass with zero failures.

Run: `uv run ruff check "src" "tests" "adapters/codex/scripts"`

Expected: `All checks passed!`.

Run: `git diff --check`

Expected: exit code `0` with no whitespace errors.

- [x] **Step 4: Record GSD completion without Git mutation**

Write `.planning/quick/260802-d7i-update-sh-codex-checkout/260802-d7i-SUMMARY.md`, update
`.planning/STATE.md` with commit value `uncommitted`, and inspect `git status --short` plus
`git diff --stat`. Do not stage or commit any file.
