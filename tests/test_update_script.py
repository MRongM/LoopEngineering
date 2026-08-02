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
