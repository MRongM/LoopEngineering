from pathlib import Path

import yaml


def test_codex_skill_declares_required_loop_contract() -> None:
    path = Path("adapters/codex/SKILL.md")
    text = path.read_text(encoding="utf-8")
    _, frontmatter, body = text.split("---", 2)
    metadata = yaml.safe_load(frontmatter)

    assert metadata["name"] == "loop-engineering"
    assert "state-changing" in metadata["description"]
    assert "install or uninstall" in metadata["description"]
    assert "Compatible Core: >=0.2,<0.3" in body
    for required in (
        "collaborative",
        "autonomous",
        "Loop Contract",
        "Maker",
        "Checker",
        "BUDGET_EXHAUSTED",
        "loop-engineering contract validate",
        "loop-engineering run create",
        "loop-engineering evidence run",
        "loop-engineering budget check",
        "loop-engineering gate check",
        "loop-engineering completion evaluate",
        "loop-engineering run complete",
        "loop-engineering scope check",
        "KISS",
        "append-only",
        "Adapter lifecycle",
        "scripts/manage.py",
        "--codex-home",
        "--yes",
        "user-operated",
        "https://github.com/MRongM/LoopEngineering.git",
        "--branch master",
        "loop-engineering --version",
        "PowerShell",
        "py -3.12",
        "不得自动合并或部署",
    ):
        assert required in body
    assert 'mkdir -p "$codex_home/skills" && \\' in body
    assert 'install --codex-home "$codex_home" && \\' in body
    assert 'throw "Loop Engineering install failed"' in body


def test_adoption_guide_has_manual_and_installed_paths() -> None:
    text = Path("docs/adoption.md").read_text(encoding="utf-8")
    assert "立即可用：人工引用规范" in text
    assert "托管安装与卸载：CLI + Codex Skill" in text
    assert "loop-engineering project init" in text
    assert "$loop-engineering" in text
    assert "manage.py\" install --codex-home" in text
    assert "manage.py\" uninstall --codex-home" in text
    assert "py -3.12" in text
    assert 'mkdir -p "$codex_home/skills" && \\' in text
    assert 'throw "Loop Engineering install failed"' in text
    assert "ln -s" not in text


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
        " && loop-engineering --version"
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


def test_codex_skill_uses_one_default_pre_execution_approval() -> None:
    text = Path("adapters/codex/SKILL.md").read_text(encoding="utf-8")
    _, _, body = text.split("---", 2)

    for required in (
        "Ready-to-execute Loop Contract",
        "without a separate mode prompt",
        "one pre-execution approval",
        "key design decisions and the minimal implementation plan",
        "without another approval",
        "do not add `design_approval` or `plan_approval` by default",
        "final acceptance before DONE",
        "Autonomous `0.2.0` does not add `final_acceptance` based on risk level",
    ):
        assert required in body

    for obsolete in (
        "ask for `collaborative` or `autonomous` unless supplied",
        "`collaborative`: pause at contract, nontrivial design, plan",
        "Record every collaborative design, plan and final decision",
        "Low/medium-risk autonomous work may reach DONE without final acceptance",
    ):
        assert obsolete not in body


def test_codex_skill_bundles_autonomous_risk_acceptance() -> None:
    text = Path("adapters/codex/SKILL.md").read_text(encoding="utf-8")
    _, _, body = text.split("---", 2)

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


def test_protocol_v020_defines_bound_autonomous_risk_acceptance() -> None:
    protocol = Path("PROTOCOL.md").read_text(encoding="utf-8")
    design = Path(
        "docs/superpowers/specs/2026-07-31-autonomous-single-risk-acceptance-design.md"
    ).read_text(encoding="utf-8")

    for required in (
        "Loop Engineering Core Protocol 0.2.0",
        "contract_sha256",
        "accepted_risk_ids",
        "contract_revision",
        "Production and sensitive-data operations",
        "Autonomous 0.2.0",
    ):
        assert required in protocol
    assert "Production and sensitive-data operations always require a fresh human gate" not in protocol
    assert "用户已批准" in design
