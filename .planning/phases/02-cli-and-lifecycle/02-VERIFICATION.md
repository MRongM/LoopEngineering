---
phase: 02-cli-and-lifecycle
verified: 2026-07-31T15:20:56Z
status: passed
score: 3/3 must-haves verified
requirements_verified: 3/3
decision_coverage:
  honored: 5
  total: 5
  not_honored: []
---

# Phase 2: CLI and Lifecycle Verification Report

**Phase Goal:** 安装后的 Agent Shell 只暴露 `loop-engine`，同时保持完整命令能力和正确的包生命周期
**Verified:** 2026-07-31T15:20:56Z
**Status:** passed

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | 安装后的包只提供 `loop-engine`，且十个现有命令组保持完整 | ✓ VERIFIED | `[project.scripts]` 只有 `loop-engine`；真实 `uv run loop-engine --help` 显示 project、contract、schema、run、evidence、budget、completion、gate、scope、git 十组命令。 |
| 2 | 包不注册 `loop-engineering` 或 `loop-agent` executable | ✓ VERIFIED | 元数据精确映射测试通过；`.venv/bin` 实际扫描只发现 `.venv/bin/loop-engine`。 |
| 3 | 生命周期管理器区分分发包和 executable，并正确验证安装、更新和卸载 | ✓ VERIFIED | 47 个生命周期测试覆盖 Protocol 0.3 marker、uv argv、版本探测、旧别名拒绝、更新重校验、卸载缺失确认及删除保留路径。 |

**Score:** 3/3 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `pyproject.toml` | 唯一 `loop-engine` console script | ✓ EXISTS + SUBSTANTIVE + WIRED | 分发包仍为 `loop-engineering` 0.3.0，脚本映射严格等于 `{loop-engine: loop_engineering.cli:main}`。 |
| `src/loop_engineering/cli.py` | 新 argparse 程序名及完整命令组 | ✓ EXISTS + SUBSTANTIVE + WIRED | parser 使用 `prog="loop-engine"`，复用原有 `main` 和全部子命令实现。 |
| `adapters/codex/scripts/manage.py` | 分发包/入口分离的安全生命周期 | ✓ EXISTS + SUBSTANTIVE + WIRED | 独立身份常量、0.3 checkout 校验、安装探测和卸载缺失验证均由 `main` 路径调用。 |
| `tests/test_codex_installer.py` | 生命周期成功与失败关闭矩阵 | ✓ EXISTS + SUBSTANTIVE | 47 项覆盖 install/update/uninstall、旧 alias、错误版本、元数据、Git/path/dirty state 与恢复保留。 |

**Artifacts:** 4/4 verified

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `pyproject.toml` | `cli.main` | console script mapping | ✓ WIRED | `uv run loop-engine --version` 实际输出 `0.3.0`。 |
| `manage.py` | `pyproject.toml` | exact project name/version/scripts metadata | ✓ WIRED | `_validate_checkout` 在任何 uv 调用之前强制精确映射。 |
| `manage.py` | `loop-engine` executable | `shutil.which` and argv `--version` probe | ✓ WIRED | install/update 之后调用 `_verify_installed_cli`，uninstall 删除 checkout 前调用 `_verify_uninstalled_cli`。 |

**Wiring:** 3/3 connections verified

## Requirements Coverage

| Requirement | Status | Evidence |
|-------------|--------|----------|
| CLI-01: 唯一入口为 `loop-engine` 且命令能力完整 | ✓ SATISFIED | 包元数据、真实 `--version`/`--help`、完整命令组测试。 |
| CLI-02: 不注册旧 CLI alias | ✓ SATISFIED | exact scripts 断言、legacy metadata 负向测试、`.venv/bin` 实际扫描。 |
| LIFE-01: 生命周期管理包名并验证/移除新入口 | ✓ SATISFIED | 分离常量、精确 uv argv、post-install/update probe、post-uninstall absence gate 和 47 项套件。 |

**Coverage:** 3/3 requirements satisfied

## Decision Coverage

Phase 2 CONTEXT 中五项决策全部落实：唯一脚本映射、argparse 名称、身份常量分离、
安装/更新/卸载后的 executable 状态验证，以及本阶段只同步生命周期相关 Skill 命令。
未添加 shim、符号链接、兼容 alias 或新的删除捷径。

## Behavioral Verification

| Check | Result | Detail |
|-------|--------|--------|
| Lifecycle suite | ✓ 47 passed | `tests/test_codex_installer.py`。 |
| Phase integration suite | ✓ 62 passed | 生命周期与 Adapter 契约联合运行。 |
| Full regression suite | ✓ 225 passed, 0 failed | Protocol 0.3、CLI、生命周期及 Phase 1 回归全部通过。 |
| Static analysis | ✓ | focused/full Ruff 均为 `All checks passed!`。 |
| Runtime version | ✓ | `uv run loop-engine --version` → `0.3.0`。 |
| Runtime command surface | ✓ | `uv run loop-engine --help` 显示十个命令组。 |
| Installed scripts | ✓ | `.venv/bin` 只存在 `loop-engine`。 |
| Schema drift | ✓ none | GSD schema-drift gate 返回 `drift_detected: false`。 |
| Diff integrity | ✓ | `git diff --check` 无输出。 |

## Test Quality Audit

| Test Area | Linked Requirements | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|---------------------|--------|---------|----------|-----------------|---------|
| Package/CLI metadata | CLI-01/02 | Yes | 0 | No | Exact value + runtime behavior | ✓ STRONG |
| Install/update lifecycle | LIFE-01 | Yes | 0 | No | Ordered argv + observable executable state | ✓ STRONG |
| Uninstall safety/recovery | LIFE-01 | Yes | 0 | No | Failure-path behavior + filesystem retention | ✓ STRONG |

The tests assert external command arguments and observable results while keeping subprocess execution
behind a controlled test boundary. No test was removed, skipped or weakened to obtain GREEN.

## Anti-Patterns Found

None. No `shell=True`, `os.system`, TODO/FIXME/XXX/HACK marker, compatibility shim,
automatic merge/deployment or destructive Git addition exists in the Phase 2 implementation scope.

## Human Verification Required

N/A — package metadata, CLI output and lifecycle behavior are fully programmatically verifiable;
the managed lifecycle itself remains a user-operated bootstrap action and was not run globally.

## Scope Boundaries for Later Phases

- Phase 3 removes remaining collaborative choices and branches from the Codex Skill and implements the autonomous decision loop.
- Phase 4 replaces remaining user-facing `loop-engineering` command references in README, adoption guides, examples and compatibility notes.

These are explicit later-phase deliverables rather than Phase 2 gaps.

## Gaps Summary

**No gaps found.** Phase goal achieved and ready to proceed.

## Verification Metadata

**Verification approach:** Goal-backward from ROADMAP success criteria and both plan must-haves
**Automated checks:** 225 full tests plus focused lifecycle, runtime, static and structural gates
**Human checks required:** 0
**Total verification time:** 3 min

---
*Verified: 2026-07-31T15:20:56Z*
*Verifier: Codex inline fallback (subagent execution intentionally disabled)*
