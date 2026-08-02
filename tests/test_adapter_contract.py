import re
from pathlib import Path

import yaml

SKILL_PATH = Path("adapters/codex/SKILL.md")
REFERENCE_PATHS = (
    Path("adapters/codex/references/intake-contract.md"),
    Path("adapters/codex/references/goal-bridge.md"),
    Path("adapters/codex/references/execution-loop.md"),
    Path("adapters/codex/references/lifecycle.md"),
)
STAGE_ROUTES = (
    (
        "Explicit new task, Pending Draft, complete approval or contract revision",
        REFERENCE_PATHS[0],
    ),
    (
        "Goal creation, reconciliation, continuation, cancellation or Goal completion",
        REFERENCE_PATHS[1],
    ),
    (
        "Designing, planning, executing, verifying, checking, deciding or Loop completion",
        REFERENCE_PATHS[2],
    ),
    (
        "Installation, update, status, uninstall or project initialization",
        REFERENCE_PATHS[3],
    ),
)
ENTRY_WORD_BUDGET = 2113


def skill_parts() -> tuple[dict[str, object], str]:
    text = SKILL_PATH.read_text(encoding="utf-8")
    prefix, frontmatter, body = text.split("---", 2)
    assert prefix == ""
    return yaml.safe_load(frontmatter), body


def read_adapter_protocol() -> str:
    _, body = skill_parts()
    return "\n".join(
        [body]
        + [path.read_text(encoding="utf-8") for path in REFERENCE_PATHS if path.is_file()]
    )


def test_codex_skill_uses_bounded_progressive_disclosure() -> None:
    _, body = skill_parts()

    assert len(body.split()) <= ENTRY_WORD_BUDGET
    for path in REFERENCE_PATHS:
        route = path.relative_to(SKILL_PATH.parent)
        assert path.is_file(), path
        assert f"`{route.as_posix()}`" in body
        assert f"`{path.as_posix()}`" not in body
        assert "references/" not in path.read_text(encoding="utf-8")

    for stage, path in STAGE_ROUTES:
        route = path.relative_to(SKILL_PATH.parent)
        assert f"| {stage} | `{route.as_posix()}` |" in body

    assert "Read each required reference directly from this routing table" in body
    assert "git clone --depth 1" not in body
    assert "git clone --depth 1" in REFERENCE_PATHS[3].read_text(encoding="utf-8")


def test_codex_skill_keeps_the_first_release_safety_kernel_inline() -> None:
    _, body = skill_parts()

    for required in (
        "Only explicit `$loop-engine` may start a new Loop task.",
        "Core Protocol: 0.1.0",
        "Do not mutate before the complete Loop Contract is explicitly approved.",
        "Do not scan `.loop-engine/drafts/` or `.loop-engine/runs/` for the newest Draft or Run",
        "Never use prose as evidence of `DONE`.",
        "force-push, history rewriting, `git reset --hard`, automatic merge and automatic deployment",
    ):
        assert required in body


def test_codex_skill_composed_corpus_remains_first_release_only() -> None:
    protocol = read_adapter_protocol()

    assert "Core Protocol: 0.1.0" in protocol
    assert "`protocol_version: 0.1.0`" in protocol
    assert "`.loop-engine/`" in protocol
    for obsolete in (
        "Compatible Core:",
        ".loop-runs/",
        ".loop-engineering/",
    ):
        assert obsolete.casefold() not in protocol.casefold()

    assert re.search(r"\b0\.3(?:\.\d+)?\b", protocol) is None
    assert (
        re.search(
            r"required_gate\s*=\s*`?dangerous[-_]action`?",
            protocol,
            flags=re.IGNORECASE,
        )
        is None
    )


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
    body = read_adapter_protocol()

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


def test_codex_skill_tells_new_intake_users_about_spec_or_plan_sources() -> None:
    intake = " ".join(REFERENCE_PATHS[0].read_text(encoding="utf-8").split())

    for required in (
        "At the start of every explicit new Intake, tell the user once that they may provide an existing spec or plan as source material for the Loop Contract.",
        "If the request already names or includes a spec or plan, acknowledge that you will read it and map it into the contract draft.",
        "If neither is provided, mention the option without blocking Intake; continue from the current request and repository facts.",
        "Source material is not contract approval and does not replace required contract fields, repository facts or applicable instructions.",
    ):
        assert required in intake


def test_codex_skill_continues_without_routine_interruptions_after_approval() -> None:
    body = read_adapter_protocol()

    for required in (
        "Batch every unresolved pre-execution decision into the complete summary",
        "After approval, do not ask for routine confirmations",
        "Accumulate non-blocking questions and report them with the final result",
        "Risk level alone is not a pause boundary.",
        "otherwise return to diagnosis with the exact finding",
    ):
        assert required in body


def test_codex_skill_pauses_only_at_hard_boundaries() -> None:
    body = read_adapter_protocol()

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
    body = read_adapter_protocol()

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
    body = read_adapter_protocol()

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
    body = read_adapter_protocol()

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


def test_codex_skill_routes_mutations_through_checked_core_entrypoints() -> None:
    body = " ".join(read_adapter_protocol().split())

    for required in (
        'loop-engine run intent "<run-dir>" "<request-json>"',
        "exact checked `ActionRequest`",
        "Generic `loop-engine run result` cannot report Git or validator evidence.",
        "`loop-engine git` subcommands",
        "`loop-engine evidence run`",
    ):
        assert required in body


def test_codex_skill_requires_bound_fresh_checker_attestations() -> None:
    body = " ".join(read_adapter_protocol().split())

    for required in (
        '--checker-id "<host-checker-id>"',
        "Never invent or reuse a Checker ID.",
        "`contract_sha256`",
        "`source_fingerprints`",
        "`evidence_digests`",
        "`reviewed_through_sequence`",
        "Any later intent or result invalidates the attestation.",
    ):
        assert required in body


def test_codex_skill_states_the_cooperative_host_trust_boundary() -> None:
    body = " ".join(read_adapter_protocol().split())

    for required in (
        "cooperative enforcement protocol, not an adversarial sandbox",
        "Core cannot intercept raw host filesystem, shell or network tools",
        "route every external mutation through the checked Core entry points",
    ):
        assert required in body


def test_codex_skill_keeps_goal_continuation_bound_to_the_run() -> None:
    body = read_adapter_protocol()

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
    body = read_adapter_protocol()

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

    amended_adr = Path("docs/adr/0001-require-manual-skill-invocation.md").read_text(
        encoding="utf-8"
    )
    assert re.search(r"\b0\.3(?:\.\d+)?\b", amended_adr) is None


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
