from pathlib import Path
from typing import Any


def valid_contract_data() -> dict[str, Any]:
    data: dict[str, Any] = {
        "loop_id": "loop-example-001",
        "contract_version": 1,
        "protocol_version": "0.1.0",
        "objective": "Add one verified example behavior",
        "mode": "autonomous",
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
        "human_gates": ["contract_approval"],
        "assumptions": ["The repository uses Python"],
        "stop_conditions": ["done", "blocked", "budget_exhausted"],
    }
    data["validation_commands"][0]["workspace_policy"] = "isolated"
    data["execution_plan"] = {
        "design_decisions": [
            "Keep Core tool-independent and persist the approved execution boundary."
        ],
        "actions": [
            {
                "kind": "file_write",
                "repository_id": "target",
                "target": "src/",
                "impact": "Changes implementation files in the approved source boundary",
                "risk": "A regression may be introduced",
                "recovery": "Restore affected files or apply a forward fix",
                "evidence": "VAL-1 verifies the acceptance criterion",
            },
            {
                "kind": "file_write",
                "repository_id": "target",
                "target": "tests/",
                "impact": "Changes tests in the approved test boundary",
                "risk": "A test may encode the wrong behavior",
                "recovery": "Correct the test against the approved contract",
                "evidence": "VAL-1 executes the focused tests",
            },
        ],
    }
    return data


def autonomous_risk_contract_data(
    kind: str = "production_access",
) -> dict[str, Any]:
    data = valid_contract_data()
    data["mode"] = "autonomous"
    data["risk_level"] = "high"
    data["human_gates"] = ["contract_approval"]
    data["budget"]["max_iterations"] = 10
    data["budget"]["max_minutes"] = 180
    data["budget"]["max_checker_revisions"] = 3
    if kind in {"production_access", "sensitive_data"}:
        data["permissions"][kind] = True
    data["authorized_operations"] = [
        {
            "risk_id": "RISK-1",
            "kind": kind,
            "repository_id": "target",
            "target": "production/customer-index",
            "risk_level": "high",
            "impact": "Reads the approved production index",
            "worst_case": "Sensitive records may be exposed",
            "recovery": "Stop access and rotate affected credentials",
            "evidence": "AC-1 requires production verification",
        }
    ]
    action: dict[str, Any] = {
        "kind": kind,
        "repository_id": "target",
        "target": "production/customer-index",
        "impact": "Reads or changes the approved production target",
        "risk": "Sensitive records or external state may be affected",
        "recovery": "Stop the operation and apply the disclosed recovery plan",
        "evidence": "AC-1 requires the exact approved operation",
    }
    if kind == "database_change":
        action.update(
            {
                "forward_plan": "apply the approved forward-only schema change",
                "compatibility_analysis": "the approved versions remain compatible",
                "recovery": "apply the approved compensating forward migration",
            }
        )
    data["execution_plan"]["actions"].append(action)
    return data
