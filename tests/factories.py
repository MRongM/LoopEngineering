from pathlib import Path
from typing import Any


def valid_contract_data() -> dict[str, Any]:
    return {
        "loop_id": "loop-example-001",
        "contract_version": 1,
        "protocol_version": "0.1.0",
        "objective": "Add one verified example behavior",
        "mode": "collaborative",
        "repositories": [
            {
                "id": "target",
                "path": str(Path.cwd()),
                "base_branch": "master",
                "allowed_paths": ["src/", "tests/"],
                "depends_on": [],
            }
        ],
        "in_scope": ["Implement the approved behavior"],
        "out_of_scope": ["Deployment"],
        "acceptance_criteria": [
            {
                "id": "AC-1",
                "description": "Focused tests pass",
                "required_evidence": ["VAL-1"],
            }
        ],
        "validation_commands": [
            {
                "id": "VAL-1",
                "repository_id": "target",
                "cwd": ".",
                "argv": ["python", "-m", "pytest", "tests/test_example.py", "-q"],
                "criterion_ids": ["AC-1"],
                "timeout_seconds": 600,
            }
        ],
        "risk_level": "low",
        "permissions": {
            "network": False,
            "dependency_changes": False,
            "database_changes": False,
            "production_access": False,
            "sensitive_data": False,
        },
        "git_policy": {
            "targets": [
                {
                    "repository_id": "target",
                    "create_worktree": False,
                    "commit": False,
                    "push": False,
                    "create_pr": False,
                }
            ],
            "force_push": False,
            "history_rewrite": False,
            "merge": False,
            "deploy": False,
        },
        "budget": {
            "max_iterations": 3,
            "max_minutes": 30,
            "max_checker_revisions": 0,
            "max_same_strategy_retries": 1,
        },
        "human_gates": ["contract_approval", "final_acceptance"],
        "assumptions": ["The repository uses Python"],
        "stop_conditions": ["done", "blocked", "budget_exhausted"],
    }
