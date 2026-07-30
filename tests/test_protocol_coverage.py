from pathlib import Path

from loop_engineering.contract import export_schemas


def test_protocol_invariants_have_named_test_modules() -> None:
    required = {
        "contract": "tests/test_contract.py",
        "state": "tests/test_state_machine.py",
        "ledger": "tests/test_ledger.py",
        "evidence": "tests/test_evidence.py",
        "safety": "tests/test_policy.py",
        "Git": "tests/test_git_automation.py",
        "adapter": "tests/test_adapter_contract.py",
        "dry run": "tests/e2e/test_loop_dry_run.py",
        "risk gates": "tests/e2e/test_risk_gates.py",
    }
    missing = [name for name, path in required.items() if not Path(path).is_file()]
    assert missing == []


def test_forbidden_capabilities_are_absent_from_cli() -> None:
    cli = Path("src/loop_engineering/cli.py").read_text(encoding="utf-8")
    for forbidden in ("force-push", "reset --hard", " merge ", " deploy "):
        assert forbidden not in cli


def test_committed_schemas_match_models(tmp_path: Path) -> None:
    generated = export_schemas(tmp_path)
    for path in generated:
        assert path.read_bytes() == Path("schemas", path.name).read_bytes()
