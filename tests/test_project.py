from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from loop_engineering.project import (
    ProjectConfig,
    initialize_project,
    load_project_config,
)


def test_project_init_creates_minimal_config_without_mode(tmp_path: Path) -> None:
    config = initialize_project(tmp_path)
    path = tmp_path / ".loop-engine" / "project.yaml"
    raw = yaml.safe_load(path.read_text())

    assert config == ProjectConfig.model_validate(raw)
    assert raw == {
        "protocol_version": "0.1.0",
        "instruction_files": ["AGENTS.md", "CLAUDE.md"],
    }
    assert "mode" not in raw


def test_project_init_contains_all_loop_owned_state_and_ignores_runtime_data(
    tmp_path: Path,
) -> None:
    (tmp_path / ".gitignore").write_text("dist/\n")
    initialize_project(tmp_path)

    control_root = tmp_path / ".loop-engine"
    assert (tmp_path / ".gitignore").read_text() == "dist/\n"
    assert (control_root / ".gitignore").read_text() == (
        "*\n!.gitignore\n!project.yaml\n"
    )
    assert {
        path.name for path in control_root.iterdir() if path.is_dir()
    } == {"drafts", "runs", "cache"}


def test_project_init_refuses_to_overwrite_existing_config(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    with pytest.raises(FileExistsError):
        initialize_project(tmp_path)


def test_project_init_rejects_a_linked_control_root(tmp_path: Path) -> None:
    external = tmp_path / "external"
    external.mkdir()
    try:
        (tmp_path / ".loop-engine").symlink_to(
            external,
            target_is_directory=True,
        )
    except OSError as error:
        pytest.skip(f"directory symlinks are unavailable: {error}")

    with pytest.raises(ValueError, match="linked control path"):
        initialize_project(tmp_path)

    assert not (external / "project.yaml").exists()


def test_project_load_rejects_a_linked_runtime_directory(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    cache = tmp_path / ".loop-engine" / "cache"
    cache.rmdir()
    external = tmp_path / "external-cache"
    external.mkdir()
    try:
        cache.symlink_to(external, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"directory symlinks are unavailable: {error}")

    with pytest.raises(ValueError, match="linked control path"):
        load_project_config(tmp_path)


def test_project_config_rejects_another_protocol_version() -> None:
    with pytest.raises(ValidationError):
        ProjectConfig(protocol_version="9.9.9")


def test_project_config_rejects_a_protocol_constraint_field() -> None:
    with pytest.raises(ValidationError):
        ProjectConfig(protocol_constraint="any-range")


def test_project_template_uses_the_exact_first_release() -> None:
    raw = yaml.safe_load(Path("templates/project.yaml").read_text(encoding="utf-8"))

    config = ProjectConfig.model_validate(raw)

    assert config.protocol_version == "0.1.0"


def test_project_config_rejects_instruction_path_escape() -> None:
    with pytest.raises(ValidationError, match="unsafe relative path"):
        ProjectConfig(instruction_files=["../../secret.txt"])
