import hashlib
import json
from pathlib import Path

import yaml

from loop_engineering.models.contract import LoopContract
from loop_engineering.models.run import LoopEvent, LoopState


def contract_fingerprint(contract: LoopContract) -> str:
    canonical = json.dumps(
        contract.model_dump(mode="json"),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def load_contract(path: Path) -> LoopContract:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError("contract root must be a mapping")
    base = path.resolve().parent
    for repository in raw.get("repositories", []):
        repository_path = Path(repository["path"])
        if not repository_path.is_absolute():
            repository["path"] = str((base / repository_path).resolve())
    for target in raw.get("git_policy", {}).get("targets", []):
        if target.get("worktree_path"):
            worktree_path = Path(target["worktree_path"])
            if not worktree_path.is_absolute():
                target["worktree_path"] = str((base / worktree_path).resolve())
    return LoopContract.model_validate(raw)


def write_contract_schema(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    schema = LoopContract.model_json_schema()
    path.write_text(
        json.dumps(schema, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path


def export_schemas(output_dir: Path) -> tuple[Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    models = (
        ("loop-contract.schema.json", LoopContract),
        ("loop-state.schema.json", LoopState),
        ("loop-event.schema.json", LoopEvent),
    )
    paths: list[Path] = []
    for filename, model in models:
        path = output_dir / filename
        path.write_text(
            json.dumps(
                model.model_json_schema(),
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        paths.append(path)
    return paths[0], paths[1], paths[2]
