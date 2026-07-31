from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from loop_engineering.project import ProjectConfig, initialize_project


def test_project_init_creates_minimal_config_without_mode(tmp_path: Path) -> None:
    config = initialize_project(tmp_path)
    path = tmp_path / ".loop-engineering" / "project.yaml"
    raw = yaml.safe_load(path.read_text())

    assert config == ProjectConfig.model_validate(raw)
    assert raw == {
        "protocol_constraint": ">=0.3,<0.4",
        "run_root": ".loop-runs",
        "instruction_files": ["AGENTS.md", "CLAUDE.md"],
    }
    assert "mode" not in raw


def test_project_init_updates_gitignore_only_when_explicit(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text("dist/\n")
    initialize_project(tmp_path, update_gitignore=True)
    assert (tmp_path / ".gitignore").read_text() == "dist/\n.loop-runs/\n"


def test_project_init_refuses_to_overwrite_existing_config(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    with pytest.raises(FileExistsError):
        initialize_project(tmp_path)


def test_project_config_rejects_incompatible_protocol_constraint() -> None:
    with pytest.raises(ValidationError):
        ProjectConfig(protocol_constraint=">=1,<2")


def test_project_config_keeps_legacy_v020_constraint_readable() -> None:
    config = ProjectConfig(protocol_constraint=">=0.2,<0.3")

    assert config.protocol_constraint == ">=0.2,<0.3"


def test_project_template_uses_v030_constraint() -> None:
    raw = yaml.safe_load(Path("templates/project.yaml").read_text(encoding="utf-8"))

    config = ProjectConfig.model_validate(raw)

    assert config.protocol_constraint == ">=0.3,<0.4"


def test_project_config_rejects_instruction_path_escape() -> None:
    with pytest.raises(ValidationError, match="unsafe relative path"):
        ProjectConfig(instruction_files=["../../secret.txt"])
