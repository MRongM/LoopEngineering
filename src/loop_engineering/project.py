from pathlib import Path
from typing import Literal

import yaml
from pydantic import Field, field_validator

from loop_engineering.models.contract import StrictModel
from loop_engineering.paths import normalized_relative


class ProjectConfig(StrictModel):
    protocol_constraint: Literal[">=0.2,<0.3", ">=0.3,<0.4"] = ">=0.3,<0.4"
    run_root: Literal[".loop-runs"] = ".loop-runs"
    instruction_files: list[str] = Field(
        default_factory=lambda: ["AGENTS.md", "CLAUDE.md"]
    )

    @field_validator("instruction_files")
    @classmethod
    def validate_instruction_files(cls, values: list[str]) -> list[str]:
        for value in values:
            normalized_relative(value)
        return values


def initialize_project(
    root: Path,
    *,
    update_gitignore: bool = False,
) -> ProjectConfig:
    root = root.resolve()
    if not root.is_dir():
        raise NotADirectoryError(root)
    directory = root / ".loop-engineering"
    directory.mkdir(exist_ok=True)
    path = directory / "project.yaml"
    if path.exists():
        raise FileExistsError(path)
    config = ProjectConfig()
    path.write_text(
        yaml.safe_dump(config.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )
    if update_gitignore:
        gitignore = root / ".gitignore"
        existing = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
        lines = existing.splitlines()
        if ".loop-runs/" not in lines:
            prefix = existing if not existing or existing.endswith("\n") else existing + "\n"
            gitignore.write_text(prefix + ".loop-runs/\n", encoding="utf-8")
    return config
