from pathlib import Path
from typing import Literal

import yaml
from pydantic import Field, field_validator

from loop_engineering.layout import (
    CACHE_DIR_NAME,
    CONTROL_DIR_NAME,
    DRAFTS_DIR_NAME,
    INTERNAL_GITIGNORE,
    RUNS_DIR_NAME,
    control_root,
    project_config_path,
)
from loop_engineering.models.base import StrictModel
from loop_engineering.paths import normalized_relative


class ProjectConfig(StrictModel):
    protocol_version: Literal["0.1.0"] = "0.1.0"
    instruction_files: list[str] = Field(
        default_factory=lambda: ["AGENTS.md", "CLAUDE.md"]
    )

    @field_validator("instruction_files")
    @classmethod
    def validate_instruction_files(cls, values: list[str]) -> list[str]:
        for value in values:
            normalized_relative(value)
        return values


def _is_link_like(path: Path) -> bool:
    return path.is_symlink() or path.is_junction()


def _reject_link(path: Path) -> None:
    if _is_link_like(path):
        raise ValueError(f"linked control path is forbidden: {path}")


def _validate_control_layout(root: Path) -> None:
    directory = control_root(root)
    _reject_link(directory)
    if not directory.is_dir():
        raise NotADirectoryError(directory)
    gitignore = directory / ".gitignore"
    config = project_config_path(root)
    for path in (gitignore, config):
        _reject_link(path)
        if not path.is_file():
            raise FileNotFoundError(path)
    if gitignore.read_text(encoding="utf-8") != INTERNAL_GITIGNORE:
        raise ValueError("project control .gitignore does not match the required policy")
    for name in (DRAFTS_DIR_NAME, RUNS_DIR_NAME, CACHE_DIR_NAME):
        path = directory / name
        _reject_link(path)
        if not path.is_dir():
            raise NotADirectoryError(path)


def initialize_project(
    root: Path,
) -> ProjectConfig:
    root = root.resolve()
    if not root.is_dir():
        raise NotADirectoryError(root)
    path = project_config_path(root)
    if path.exists():
        raise FileExistsError(path)
    conflicts = sorted(
        path.name
        for path in root.iterdir()
        if path.name.startswith(".loop-") and path.name != CONTROL_DIR_NAME
    )
    if conflicts:
        raise ValueError(
            "conflicting Loop-owned directory requires explicit cleanup: "
            + ", ".join(conflicts)
        )
    directory = control_root(root)
    _reject_link(directory)
    directory.mkdir(exist_ok=True)
    internal_gitignore = directory / ".gitignore"
    _reject_link(internal_gitignore)
    if internal_gitignore.exists():
        if internal_gitignore.read_text(encoding="utf-8") != INTERNAL_GITIGNORE:
            raise FileExistsError(internal_gitignore)
    else:
        internal_gitignore.write_text(INTERNAL_GITIGNORE, encoding="utf-8")
    for name in (DRAFTS_DIR_NAME, RUNS_DIR_NAME, CACHE_DIR_NAME):
        runtime_directory = directory / name
        _reject_link(runtime_directory)
        runtime_directory.mkdir(exist_ok=True)
    config = ProjectConfig()
    _reject_link(path)
    path.write_text(
        yaml.safe_dump(config.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )
    return config


def load_project_config(root: Path) -> ProjectConfig:
    root = root.resolve()
    _validate_control_layout(root)
    path = project_config_path(root)
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return ProjectConfig.model_validate(raw)


def ensure_project(root: Path) -> ProjectConfig:
    path = project_config_path(root)
    if path.is_file():
        return load_project_config(root)
    return initialize_project(root)
