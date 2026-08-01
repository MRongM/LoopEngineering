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
ENTRY_WORD_BUDGET = 2113


def read_skill_body() -> str:
    _, _, body = SKILL_PATH.read_text(encoding="utf-8").split("---", 2)
    return body


def read_adapter_protocol() -> str:
    parts = [read_skill_body()]
    parts.extend(
        path.read_text(encoding="utf-8")
        for path in REFERENCE_PATHS
        if path.is_file()
    )
    return "\n".join(parts)


def test_codex_skill_uses_bounded_progressive_disclosure() -> None:
    body = read_skill_body()

    assert len(body.split()) <= ENTRY_WORD_BUDGET
    for path in REFERENCE_PATHS:
        route = path.relative_to(SKILL_PATH.parent)
        assert path.is_file(), path
        assert f"`{route.as_posix()}`" in body
        assert f"`{path.as_posix()}`" not in body
        assert (SKILL_PATH.parent / route).is_file()

    assert "Read each required reference directly from this routing table" in body
    assert "git clone --depth 1" not in body
    assert "git clone --depth 1" in REFERENCE_PATHS[3].read_text(encoding="utf-8")


def test_codex_skill_keeps_the_safety_kernel_inline() -> None:
    body = read_skill_body()

    for required in (
        "Only explicit `$loop-engine` may start a new Loop task.",
        "Compatible Core: >=0.3,<0.4",
        "Do not mutate before the complete Loop Contract is explicitly approved.",
        "Never scan `.loop-runs/` for a newest Draft or Run.",
        "Never use prose as evidence of `DONE`.",
        "force-push, history rewriting, `git reset --hard`, automatic merge and automatic deployment",
    ):
        assert required in body


def test_codex_skill_declares_required_loop_contract() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    _, frontmatter, body = text.split("---", 2)
    protocol = read_adapter_protocol()
    metadata = yaml.safe_load(frontmatter)

    assert set(metadata) == {"name", "description"}
    assert metadata["name"] == "loop-engine"
    assert metadata["description"] == (
        "Run evidence-gated Loop Engineering workflows and manage the Codex adapter lifecycle."
    )
    assert not metadata["description"].startswith("Use when")
    assert "Compatible Core: >=0.3,<0.4" in body
    for required in (
        "autonomous",
        "Loop Contract",
        "Maker",
        "Checker",
        "BUDGET_EXHAUSTED",
        "loop-engine contract validate",
        "loop-engine run create",
        "loop-engine evidence run",
        "loop-engine budget check",
        "loop-engine gate check",
        "loop-engine completion evaluate",
        "loop-engine run complete",
        "loop-engine scope check",
        "KISS",
        "append-only",
        "Adapter lifecycle",
        "scripts/manage.py",
        "--codex-home",
        "--yes",
        "user-operated",
        "https://github.com/MRongM/LoopEngineering.git",
        "--branch master",
        "loop-engine --version",
        "PowerShell",
        "py -3.12",
        "不得自动合并或部署",
    ):
        assert required in protocol
    assert 'mkdir -p "$codex_home/skills" && \\' in protocol
    assert 'install --codex-home "$codex_home" && \\' in protocol
    assert 'throw "Loop Engineering install failed"' in protocol
    assert "collaborative" not in protocol.casefold()


def test_codex_skill_is_autonomous_only() -> None:
    body = read_adapter_protocol()

    for required in (
        "`protocol_version: 0.3.0`",
        "`mode: autonomous`",
        "Do not ask the user to choose a control mode.",
        "Reject incompatible mode input",
        "## Autonomous execution",
        "The Adapter has no alternate control-mode path.",
    ):
        assert required in body

    for obsolete in (
        "collaborative",
        "Resolve the mode from the current request",
        "The user may downgrade",
        "Upgrading requires explicit approval",
        "## Control modes",
    ):
        assert obsolete.casefold() not in body.casefold()

    for group in (
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
        assert f"loop-engineering {group}" not in body


def test_codex_skill_runs_the_autonomous_decision_loop() -> None:
    body = read_adapter_protocol()

    for required in (
        "## Autonomous decision loop",
        "`designing -> planning -> executing -> verifying -> checking -> deciding`",
        "one unmet acceptance criterion",
        "next smallest action",
        "Fresh evidence and material progress",
        "A test or command failure with new information",
        "Two consecutive iterations without new evidence or material progress",
        "Checker `REVISE`",
        "Checker `BLOCK`",
        "Checker `ACCEPT` plus every current DONE fact",
        "The same failed strategy may be attempted at most once",
        "BUDGET_EXHAUSTED",
    ):
        assert required in body


def test_codex_skill_pauses_only_at_hard_boundaries() -> None:
    body = read_adapter_protocol()

    for required in (
        "## Hard pause and stop boundaries",
        "complete contract revision",
        "current bound approval is missing, stale or mismatched",
        "Goal/Run binding is missing, ambiguous, stale or unrelated",
        "pending intent cannot be reconciled",
        "platform or external authentication hard gate",
        "necessary authority or input is unavailable",
        "required independent Checker is unavailable",
        "user cancels",
        "authoritative budget or terminal state",
        "Risk level alone is not a pause boundary.",
        "Permanent-deny operations remain denied",
        "otherwise return to diagnosis with the exact finding",
    ):
        assert required in body

    assert "otherwise pause with the exact finding" not in body


def test_codex_skill_completion_requires_fresh_evidence() -> None:
    body = read_adapter_protocol()

    for required in (
        "current code fingerprint",
        "fresh validator evidence",
        "current scope result",
        "required Checker `ACCEPT`",
        "current contract authorization",
        "no unresolved intent",
        "Never use prose, stale evidence or Maker confidence as completion evidence.",
        '`loop-engine completion evaluate "<contract-path>" "<context-json>"`',
    ):
        assert required in body


def test_codex_skill_enables_task_scoped_implicit_selection() -> None:
    metadata = yaml.safe_load(
        Path("adapters/codex/agents/openai.yaml").read_text(encoding="utf-8")
    )

    assert metadata == {"policy": {"allow_implicit_invocation": True}}


def test_adoption_guide_has_manual_and_installed_paths() -> None:
    text = Path("docs/adoption.md").read_text(encoding="utf-8")
    assert "立即可用：人工引用规范" in text
    assert "托管安装与卸载：CLI + Codex Skill" in text
    assert "loop-engine project init" in text
    assert "$loop-engine" in text
    assert "$loop-engineering" not in text
    assert "manage.py\" install --codex-home" in text
    assert "manage.py\" uninstall --codex-home" in text
    assert "py -3.12" in text
    assert 'mkdir -p "$codex_home/skills" && \\' in text
    assert 'throw "Loop Engineering install failed"' in text
    assert "ln -s" not in text


def test_project_watch_is_documented_as_a_read_only_dashboard() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    adoption = Path("docs/adoption.md").read_text(encoding="utf-8")

    for text in (readme, adoption):
        assert "loop-engine watch" in text
        assert "loop-engine watch --all" in text
        assert "loop-engine run watch" not in text

    for required in (
        "从当前目录向上查找",
        "不接受 Run 目录参数",
        "严格只读",
        "非终态和暂停",
        "终态历史",
        "非 TTY",
    ):
        assert required in adoption


def test_current_release_docs_use_only_loop_engine_commands() -> None:
    active_paths = (
        Path("README.md"),
        Path("docs/adoption.md"),
        Path("docs/compatibility.md"),
        Path("CONTEXT.md"),
        Path("docs/adr/0001-require-manual-skill-invocation.md"),
        Path("adapters/codex/SKILL.md"),
        *REFERENCE_PATHS,
    )
    legacy_command = re.compile(
        r"\b(?:loop-engineering|loop-agent)\s+"
        r"(?:--version|--help|project|contract|schema|run|evidence|budget|completion|gate|scope|git)\b"
    )

    active_docs = {path: path.read_text(encoding="utf-8") for path in active_paths}
    for path, text in active_docs.items():
        assert legacy_command.search(text) is None, path

    assert "loop-engine --version" in active_docs[Path("README.md")]
    assert "loop-engine --version" in active_docs[Path("docs/adoption.md")]
    assert "loop-engine project init" in active_docs[Path("docs/adoption.md")]


def test_compatibility_guide_defines_030_identity_and_migration_boundaries() -> None:
    text = Path("docs/compatibility.md").read_text(encoding="utf-8")

    for required in (
        "Loop Engineering 0.3.0",
        "Python 分发包",
        "`loop-engineering`",
        "托管 checkout",
        "`$loop-engine`",
        "唯一 Shell CLI",
        "`loop-engine`",
        "`loop-agent`",
        "不提供 CLI alias",
        "0.1.0/0.2.0",
        "显式 `mode: autonomous`",
        "省略 `mode`",
        "`mode: collaborative`",
        "不提供自动迁移",
        "历史审计记录",
        "不是当前执行指南",
    ):
        assert required in text


def test_codex_skill_requires_the_short_trigger_only_for_new_tasks() -> None:
    skill = Path("adapters/codex/SKILL.md").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")
    adoption = Path("docs/adoption.md").read_text(encoding="utf-8")
    normalized_readme = " ".join(readme.split())

    for text in (skill, readme, adoption):
        assert "$loop-engine" in text
        assert "$loop-engineering" not in text

    for required in (
        "Only explicit `$loop-engine` may start a new Loop task.",
        "`allow_implicit_invocation: true` is eligibility, not authorization.",
        "After a task is uniquely bound, later user messages may continue it in natural language.",
        "Never use implicit selection to start or adopt a task.",
    ):
        assert required in skill

    for obsolete in (
        "Every later user message that should continue this Skill must invoke",
        "Whenever this Skill pauses, require the user's reply to begin with",
    ):
        assert obsolete not in skill

    assert "Only a new task starts with `$loop-engine`" in normalized_readme
    assert "只有新任务的首条消息需要 `$loop-engine`" in adoption


def test_codex_skill_supports_task_scoped_goal_bound_continuation() -> None:
    skill = read_adapter_protocol()
    normalized_skill = " ".join(skill.split()).casefold()
    context = Path("CONTEXT.md").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")
    adoption = Path("docs/adoption.md").read_text(encoding="utf-8")
    manual_adr = Path("docs/adr/0001-require-manual-skill-invocation.md").read_text(
        encoding="utf-8"
    )
    goal_adr = Path("docs/adr/0002-bind-codex-goal-autocontinuation.md").read_text(
        encoding="utf-8"
    )

    for required in (
        "Task-scoped continuation",
        "Pending Draft binding",
        "Every newly approved Codex Loop task uses Goal binding by default.",
        "natural-language clarification, approval, revision, pause recovery, cancellation and feedback",
        "Do not scan `.loop-runs/`",
        "`$loop-engine goal-bridge/v1`",
        "`create_goal`",
        "`get_goal`",
        "`update_goal`",
        "`platform_state`",
        "`loop-engine run events`",
        "`loop-engine run status`",
        "Revalidate the current contract authorization binding",
        "`protocol_version`",
        "`contract_version`",
        "`contract_sha256`",
        "complete `accepted_risk_ids`",
        "Reconcile every pending intent",
        "`loop-engine budget check`",
        "Do not set `token_budget` unless the user explicitly supplies it",
        "unrelated active Goal",
        "authoritative Loop `DONE`",
        "Do not call `update_goal` with `blocked`",
        "`user_cancelled:`",
    ):
        assert required.casefold() in normalized_skill

    assert "任务级续跑（Task-scoped Continuation）" in context
    assert "0002-bind-codex-goal-autocontinuation.md" in manual_adr
    assert "Only a new Loop task requires explicit invocation" in goal_adr
    assert "Codex task-scoped continuation" in readme
    assert "Codex 任务级自然语言续跑" in adoption
    assert "Goal Token 预算" in adoption

    for text in (skill, context, readme, adoption):
        assert "Goal automatically grants Loop approval" not in text

    assert "Optional Codex Goal auto-continuation" not in readme
    assert "可选：Codex Goal 自动续跑" not in adoption


def test_codex_skill_accepts_natural_language_approval_without_a_fixed_phrase() -> None:
    body = read_adapter_protocol()

    for required in (
        "Accept one unambiguous natural-language approval of the latest complete summary.",
        "Do not require a fixed confirmation subcommand or trigger prefix.",
        "Questions, partial decisions, conditional replies, stale references and unrelated messages are not approvals.",
    ):
        assert required in body

    for obsolete in (
        "Ask the user to reply with `$loop-engine confirm`",
        "Accept any unambiguous approval in a user message that begins with `$loop-engine`",
    ):
        assert obsolete not in body


def test_readme_documents_one_line_managed_install() -> None:
    text = Path("README.md").read_text(encoding="utf-8")
    normalized = " ".join(text.split())
    install = (
        'codex_home="${CODEX_HOME:-$HOME/.codex}";'
        ' skill_dir="$codex_home/skills/loop-engineering";'
        ' mkdir -p "$codex_home/skills"'
        ' && git clone --depth 1 --branch master'
        ' "https://github.com/MRongM/LoopEngineering.git" "$skill_dir"'
        ' && python3 "$skill_dir/adapters/codex/scripts/manage.py"'
        ' install --codex-home "$codex_home"'
        " && loop-engine --version"
    )

    assert install in text
    assert "installs the CLI through the checked-in lifecycle manager" in normalized
    assert 'uv run ruff check "src" "tests" "adapters/codex/scripts"' in text
    assert 'throw "Loop Engineering install failed"' in text
    assert "ln -s" not in text


def test_readme_documents_one_line_fail_closed_uninstall() -> None:
    text = Path("README.md").read_text(encoding="utf-8")
    uninstall = (
        'codex_home="${CODEX_HOME:-$HOME/.codex}";'
        ' skill_dir="$codex_home/skills/loop-engineering";'
        ' python3 "$skill_dir/adapters/codex/scripts/manage.py" uninstall'
        ' --codex-home "$codex_home" --yes'
    )

    assert uninstall in text
    assert "refuses dirty or symlinked checkouts" in text
    assert "command rm" not in text
    assert "rm -rf" not in text


def test_codex_skill_uses_one_autonomous_pre_execution_approval() -> None:
    body = read_adapter_protocol()

    for required in (
        "Ready-to-execute Loop Contract",
        "without a separate mode prompt",
        "one pre-execution approval",
        "key design decisions and the minimal implementation plan",
        "without another approval",
        "do not add `design_approval` or `plan_approval` by default",
        "Do not add `final_acceptance` by default",
        "Risk level alone never creates another human gate",
    ):
        assert required in body

    for obsolete in (
        "ask for `collaborative` or `autonomous` unless supplied",
        "`collaborative`: pause at contract, nontrivial design, plan",
        "Record every collaborative design, plan and final decision",
        "Low/medium-risk autonomous work may reach DONE without final acceptance",
        "final acceptance before DONE",
    ):
        assert obsolete.casefold() not in body.casefold()


def test_codex_skill_defaults_every_new_task_to_autonomous() -> None:
    body = read_adapter_protocol()

    for required in (
        "Set `protocol_version: 0.3.0` and `mode: autonomous` for every new task.",
        "Do not ask the user to choose a control mode.",
        "Reject incompatible mode input",
        "| New task | Set Autonomous Protocol 0.3 in the complete contract |",
    ):
        assert required in body

    for obsolete in (
        "otherwise set `collaborative` without a separate mode prompt",
        "| Mode omitted | Select `collaborative` and disclose it in the complete summary |",
        "Resolve an omitted mode to `collaborative` and disclose it in the summary",
        "Use an explicit `collaborative`",
        "| Mode omitted |",
    ):
        assert obsolete.casefold() not in body.casefold()


def test_current_compatibility_supersedes_historical_mode_defaults() -> None:
    current = Path(
        "docs/superpowers/specs/2026-07-31-codex-autonomous-default-design.md"
    ).read_text(encoding="utf-8")
    protocol_design = Path(
        "docs/superpowers/specs/2026-07-30-loop-engineering-protocol-design.md"
    ).read_text(encoding="utf-8")
    approval_design = Path(
        "docs/superpowers/specs/2026-07-31-single-execution-approval-design.md"
    ).read_text(encoding="utf-8")
    adoption = Path("docs/adoption.md").read_text(encoding="utf-8")
    compatibility = Path("docs/compatibility.md").read_text(encoding="utf-8")

    assert "- 状态：用户已批准" in current
    for legacy_design in (protocol_design, approval_design):
        assert "2026-07-31-codex-autonomous-default-design.md" in legacy_design
    assert "新合同固定使用 `mode: autonomous`" in adoption
    assert "0.3.0 省略 `mode` 时解析为 `autonomous`" in compatibility
    assert "旧版本省略 `mode` 时拒绝读取" in compatibility


def test_codex_skill_keeps_control_files_inside_target_project() -> None:
    body = read_adapter_protocol()
    adoption = Path("docs/adoption.md").read_text(encoding="utf-8")

    for required in (
        "`.loop-runs/.drafts/<loop-id>/contract.yaml`",
        "`<run-dir>/inputs/`",
        "Perform every adapter-owned preparatory write inside the target project",
        "Use resolved absolute paths for every `repositories[].path`",
        "Never create adapter-owned control files outside the target project",
    ):
        assert required in body

    for obsolete in (
        "newly created\ntemporary directory",
        "not the target project",
    ):
        assert obsolete not in body

    assert "`.loop-runs/` 中" in adoption
    assert "系统临时目录" in adoption
    assert "所有预备阶段文件" in adoption
    assert "绝对路径" in adoption


def test_codex_skill_bundles_autonomous_risk_acceptance() -> None:
    body = read_adapter_protocol()

    for required in (
        "Autonomous Risk Acceptance",
        "List every planned dangerous, production, sensitive-data and Git mutation",
        "risk_id",
        "worst_case",
        'gate check "<run-dir>" "<request-json>"',
        "required_gate=contract_revision",
        "one revised complete-summary approval",
        "do not record `dangerous_action`",
        "production_access",
        "sensitive_data",
        "platform or external-service hard gate",
        "force-push, history rewriting, reset --hard, automatic merge and automatic deployment",
    ):
        assert required in body

    for obsolete in (
        'gate check "<contract-path>" "<request-json>"',
        "high-risk work still requires it",
        "Keep emergent-danger and final-acceptance gates distinct",
        "loop-engineering gate check",
    ):
        assert obsolete not in body


def test_protocol_design_uses_one_default_pre_execution_approval() -> None:
    text = Path(
        "docs/superpowers/specs/2026-07-30-loop-engineering-protocol-design.md"
    ).read_text(encoding="utf-8")

    for required in (
        "模式由 Adapter 解析，不要求用户为每个正式任务单独选择",
        "同一次执行授权",
        "关键设计决策与最小实施计划",
        "批准后，Agent 默认连续通过设计和计划阶段",
        "`design_approval` 或 `plan_approval`",
        "Autonomous `0.2.0` 不因风险等级自动增加最终人工验收",
        "精确列明且已在契约批准中接受的生产或敏感数据操作不再暂停",
        "解析并披露控制模式",
        "所有 `collaborative` 运行已通过人工最终验收门",
        "显式指定则采用，否则默认 `collaborative`，不单独询问",
    ):
        assert required in text

    for obsolete in (
        "每个正式任务必须显式选择",
        "`collaborative` 默认在以下节点等待确认",
        "用户在每个任务开始前选择协作执行或自动托管",
        "要求用户选择控制模式",
        "高风险任务仍需最终人工验收",
        "需要访问生产环境或传输敏感数据",
        "所有 `collaborative` 运行和高风险任务已通过人工最终验收门",
    ):
        assert obsolete not in text


def test_protocol_v030_defines_bound_autonomous_risk_acceptance() -> None:
    protocol = Path("PROTOCOL.md").read_text(encoding="utf-8")
    design = Path(
        "docs/superpowers/specs/2026-07-31-autonomous-single-risk-acceptance-design.md"
    ).read_text(encoding="utf-8")

    for required in (
        "Loop Engineering Core Protocol 0.3.0",
        "contract_sha256",
        "accepted_risk_ids",
        "contract_revision",
        "Production and sensitive-data operations",
        "Autonomous 0.2.0/0.3.0",
    ):
        assert required in protocol
    assert "Production and sensitive-data operations always require a fresh human gate" not in protocol
    assert "用户已批准" in design
