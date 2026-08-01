import re
from pathlib import Path

import yaml

SKILL_PATH = Path("adapters/codex/SKILL.md")


def skill_parts() -> tuple[dict[str, object], str]:
    text = SKILL_PATH.read_text(encoding="utf-8")
    prefix, frontmatter, body = text.split("---", 2)
    assert prefix == ""
    return yaml.safe_load(frontmatter), body


def test_codex_skill_exposes_one_first_release_identity() -> None:
    metadata, body = skill_parts()

    assert metadata["name"] == "loop-engine"
    assert "Core Protocol: 0.1.0" in body
    assert "`protocol_version: 0.1.0`" in body
    assert "`mode: autonomous`" in body
    for obsolete in ("Compatible Core:", "protocol_constraint", "legacy contract"):
        assert obsolete.casefold() not in body.casefold()


def test_repository_gitignore_has_no_obsolete_loop_runtime_root() -> None:
    text = Path(".gitignore").read_text(encoding="utf-8")

    assert ".loop-runs/" not in text


def test_codex_skill_forms_one_execution_closed_contract() -> None:
    _, body = skill_parts()

    for required in (
        "Ready-to-execute Loop Contract",
        "execution_plan",
        "design_decisions",
        "actions",
        "one pre-execution approval",
        "Use exactly one human gate: `contract_approval`",
        "contract_sha256",
        "accepted_risk_ids",
        "required_gate=contract_revision",
        "`git_worktree`",
        "`<branch>@<resolved-absolute-worktree-path>`",
    ):
        assert required in body

    for obsolete in (
        "design_approval",
        "plan_approval",
    ):
        assert obsolete not in body


def test_codex_skill_continues_without_routine_interruptions_after_approval() -> None:
    _, body = skill_parts()

    for required in (
        "Batch every unresolved pre-execution decision into the complete summary",
        "After approval, do not ask for routine confirmations",
        "Accumulate non-blocking questions and report them with the final result",
        "Risk level alone is not a pause boundary.",
        "otherwise return to diagnosis with the exact finding",
    ):
        assert required in body


def test_codex_skill_pauses_only_at_hard_boundaries() -> None:
    _, body = skill_parts()

    for required in (
        "## Hard pause and stop boundaries",
        "complete contract revision",
        "current bound approval is missing, stale or mismatched",
        "pending intent cannot be reconciled",
        "platform or external authentication hard gate",
        "necessary authority or input is unavailable",
        "required independent Checker is unavailable",
        "user cancels",
        "authoritative budget or terminal state",
        "Permanent-deny operations remain denied",
    ):
        assert required in body


def test_codex_skill_runs_the_autonomous_decision_loop() -> None:
    _, body = skill_parts()

    for required in (
        "## Autonomous decision loop",
        "`designing -> planning -> executing -> verifying -> checking -> deciding`",
        "one unmet acceptance criterion",
        "next smallest action",
        "Fresh evidence and material progress",
        "Two consecutive iterations without new evidence or material progress",
        "Checker `REVISE`",
        "Checker `BLOCK`",
        "Checker `ACCEPT` plus every current DONE fact",
        "BUDGET_EXHAUSTED",
    ):
        assert required in body


def test_codex_skill_uses_one_project_local_control_directory() -> None:
    _, body = skill_parts()

    for required in (
        "`.loop-engine/project.yaml`",
        "`.loop-engine/drafts/<loop-id>/contract.yaml`",
        "`.loop-engine/runs/<loop-id>/`",
        "`.loop-engine/cache/`",
        "never create another Loop-owned top-level path",
        "Use resolved absolute paths for every `repositories[].path`",
    ):
        assert required in body
def test_codex_skill_requires_isolated_validation_and_fresh_evidence() -> None:
    _, body = skill_parts()

    for required in (
        "workspace_policy: isolated",
        "disposable Git snapshot",
        "`.loop-engine/cache/`",
        "current code fingerprint",
        "fresh validator evidence",
        "current scope result",
        "required Checker `ACCEPT`",
        "no unresolved intent",
        "Never use prose, stale evidence or Maker confidence as completion evidence.",
    ):
        assert required in body


def test_codex_skill_keeps_goal_continuation_bound_to_the_run() -> None:
    _, body = skill_parts()

    for required in (
        "Task-scoped continuation",
        "Every newly approved Codex Loop task uses Goal binding by default.",
        "`$loop-engine goal-bridge/v1`",
        "`create_goal`",
        "`get_goal`",
        "`update_goal`",
        "Revalidate the current contract authorization binding",
        "Reconcile every pending intent",
        "Do not set `token_budget` unless the user explicitly supplies it",
    ):
        assert required.casefold() in body.casefold()


def test_codex_skill_uses_only_the_loop_engine_cli() -> None:
    _, body = skill_parts()

    for group in (
        "project",
        "contract",
        "run",
        "evidence",
        "budget",
        "completion",
        "gate",
        "scope",
        "git",
    ):
        assert f"loop-engine {group}" in body

    obsolete_command = re.compile(
        r"\b(?:loop-engineering|loop-agent)\s+"
        r"(?:project|contract|run|evidence|budget|completion|gate|scope|git)\b"
    )
    assert obsolete_command.search(body) is None


def test_docs_install_into_the_loop_engine_skill_directory() -> None:
    for path in (Path("README.md"), Path("docs/adoption.md")):
        text = path.read_text(encoding="utf-8")
        assert "skills/loop-engine" in text
        assert "skills/loop-engineering" not in text


def test_active_docs_describe_only_the_first_release() -> None:
    active = (
        Path("README.md"),
        Path("PROTOCOL.md"),
        Path("docs/adoption.md"),
        Path("docs/release-identity.md"),
        SKILL_PATH,
    )
    for path in active:
        text = path.read_text(encoding="utf-8")
        assert "0.1.0" in text, path


def test_codex_implicit_invocation_is_eligibility_not_task_authorization() -> None:
    metadata = yaml.safe_load(
        Path("adapters/codex/agents/openai.yaml").read_text(encoding="utf-8")
    )
    _, body = skill_parts()

    assert metadata == {"policy": {"allow_implicit_invocation": True}}
    assert "Only explicit `$loop-engine` may start a new Loop task." in body
    assert (
        "`allow_implicit_invocation: true` is eligibility, not authorization." in body
    )
