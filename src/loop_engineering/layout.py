from pathlib import Path

CONTROL_DIR_NAME = ".loop-engine"
PROJECT_CONFIG_NAME = "project.yaml"
DRAFTS_DIR_NAME = "drafts"
RUNS_DIR_NAME = "runs"
CACHE_DIR_NAME = "cache"
INTERNAL_GITIGNORE = "*\n!.gitignore\n!project.yaml\n"
def control_root(project_root: Path) -> Path:
    return project_root.resolve() / CONTROL_DIR_NAME


def project_config_path(project_root: Path) -> Path:
    return control_root(project_root) / PROJECT_CONFIG_NAME


def drafts_root(project_root: Path) -> Path:
    return control_root(project_root) / DRAFTS_DIR_NAME


def runs_root(project_root: Path) -> Path:
    return control_root(project_root) / RUNS_DIR_NAME


def cache_root(project_root: Path) -> Path:
    return control_root(project_root) / CACHE_DIR_NAME
