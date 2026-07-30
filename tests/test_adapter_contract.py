from pathlib import Path

import yaml


def test_codex_skill_declares_required_loop_contract() -> None:
    path = Path("adapters/codex/SKILL.md")
    text = path.read_text(encoding="utf-8")
    _, frontmatter, body = text.split("---", 2)
    metadata = yaml.safe_load(frontmatter)

    assert metadata["name"] == "loop-engineering"
    assert "state-changing" in metadata["description"]
    assert "Compatible Core: >=0.1,<0.2" in body
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
        "不得自动合并或部署",
    ):
        assert required in body


def test_adoption_guide_has_manual_and_installed_paths() -> None:
    text = Path("docs/adoption.md").read_text(encoding="utf-8")
    assert "立即可用：人工引用规范" in text
    assert "实现完成后：CLI + Codex Skill" in text
    assert "loop-engineering project init" in text
    assert "$loop-engineering" in text


def test_readme_documents_one_line_direct_clone_install() -> None:
    text = Path("README.md").read_text(encoding="utf-8")
    install = (
        'mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"'
        ' && git clone --depth 1 --branch master'
        ' "https://github.com/MRongM/LoopEngineering.git"'
        ' "${CODEX_HOME:-$HOME/.codex}/skills/loop-engineering"'
        ' && uv tool install'
        ' "${CODEX_HOME:-$HOME/.codex}/skills/loop-engineering"'
    )

    assert install in text
    assert "Codex discovers `adapters/codex/SKILL.md` recursively" in text
    assert "ln -s" not in text


def test_readme_documents_guarded_one_line_uninstall() -> None:
    text = Path("README.md").read_text(encoding="utf-8")
    uninstall = (
        'skill_dir="${CODEX_HOME:-$HOME/.codex}/skills/loop-engineering";'
        ' test -f "$skill_dir/adapters/codex/SKILL.md"'
        ' && uv tool uninstall "loop-engineering"'
        ' && command rm -r -- "$skill_dir"'
    )

    assert uninstall in text
    assert "rm -rf" not in text
