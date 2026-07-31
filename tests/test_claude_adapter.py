import json
from pathlib import Path

import yaml

PLUGIN_MANIFEST = Path(".claude-plugin/plugin.json")
MARKETPLACE_MANIFEST = Path(".claude-plugin/marketplace.json")
SKILL = Path("adapters/claude/SKILL.md")
DESIGN = Path("docs/superpowers/specs/2026-07-31-claude-adapter-design.md")


def _skill_parts() -> tuple[dict[str, object], str]:
    text = SKILL.read_text(encoding="utf-8")
    prefix, frontmatter, body = text.split("---", 2)
    assert prefix == ""
    metadata = yaml.safe_load(frontmatter)
    assert isinstance(metadata, dict)
    return metadata, body


def test_repository_is_a_native_claude_marketplace_and_plugin() -> None:
    plugin = json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))
    marketplace = json.loads(MARKETPLACE_MANIFEST.read_text(encoding="utf-8"))

    assert plugin["name"] == "loop-engineering"
    assert plugin["version"] == "0.2.0"
    assert plugin["skills"] == ["./adapters/claude/"]
    assert not {"agents", "commands", "hooks"} & plugin.keys()

    assert marketplace["name"] == "loop-engineering"
    assert marketplace["plugins"] == [
        {
            "name": "loop-engineering",
            "source": "./",
            "description": "Evidence-gated Loop Engineering workflows for Claude Code",
        }
    ]


def test_claude_skill_is_manual_only_and_resolves_the_authoritative_protocol() -> None:
    metadata, body = _skill_parts()

    assert metadata["name"] == "loop-engine"
    assert metadata["disable-model-invocation"] is True
    assert "allowed-tools" not in metadata
    for required in (
        "Compatible Core: >=0.2,<0.3",
        "current user message explicitly invokes `/loop-engineering:loop-engine`",
        "Every later user message that should continue this Skill must invoke it again",
        "`${CLAUDE_PLUGIN_ROOT}/PROTOCOL.md`",
        "reply with `/loop-engineering:loop-engine confirm`",
    ):
        assert required in body
    assert "$loop-engine" not in body
    assert "Codex" not in body


def test_claude_skill_preserves_the_core_workflow_and_safety_contract() -> None:
    _, body = _skill_parts()

    for required in (
        "`.loop-runs/.drafts/<loop-id>/contract.yaml`",
        "contract_approval",
        "Autonomous Risk Acceptance",
        "loop-engineering budget check",
        "loop-engineering gate check",
        "required_gate=contract_revision",
        "loop-engineering run intent",
        "loop-engineering run result",
        "loop-engineering evidence run",
        "fresh independent Checker",
        "loop-engineering completion evaluate",
        "loop-engineering scope check",
        "force-push, history rewriting, reset --hard, automatic merge and automatic deployment",
    ):
        assert required in body


def test_claude_lifecycle_is_user_operated_through_native_commands() -> None:
    _, skill = _skill_parts()
    readme = Path("README.md").read_text(encoding="utf-8")
    adoption = Path("docs/adoption.md").read_text(encoding="utf-8")
    commands = (
        'uv tool install "git+https://github.com/MRongM/LoopEngineering.git@master"',
        "claude plugin marketplace add MRongM/LoopEngineering",
        "claude plugin install loop-engineering@loop-engineering --scope user",
        "claude plugin marketplace update loop-engineering",
        "claude plugin update loop-engineering@loop-engineering --scope user",
        "claude plugin uninstall loop-engineering@loop-engineering --scope user",
        "uv tool uninstall loop-engineering",
    )

    for command in commands:
        assert command in skill
        assert command in readme
        assert command in adoption
    assert "never run lifecycle commands on the user's behalf" in skill


def test_claude_design_and_repository_docs_define_the_adapter_boundary() -> None:
    design = DESIGN.read_text(encoding="utf-8")
    agents = Path("AGENTS.md").read_text(encoding="utf-8")
    context = Path("CONTEXT.md").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")

    for required in (
        "状态：用户已通过 Loop Contract 批准",
        "Claude Code 原生 Plugin/Marketplace",
        "disable-model-invocation",
        "Core 保持工具无关",
        "不新增自定义生命周期管理器",
        "先增加失败测试",
    ):
        assert required in design
    assert "Host-specific behavior belongs in its matching `adapters/<host>/` directory." in agents
    assert "Claude Code Skill 激活" in context
    assert "`/loop-engineering:loop-engine`" in context
    assert "Codex and Claude Code adapters" in readme
