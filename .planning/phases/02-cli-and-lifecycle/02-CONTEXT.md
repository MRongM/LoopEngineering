# Phase 2: CLI and Lifecycle - Context

**Gathered:** 2026-07-31
**Status:** Ready for planning
**Mode:** Auto-generated under delegated autonomous decisions

<domain>
## Phase Boundary

把 Python 分发包提供的唯一 Agent Shell executable 从 `loop-engineering` 切换为
`loop-engine`，保持所有现有命令组和参数不变；同步 Codex 生命周期管理器，使安装、
更新与卸载继续按分发包名 `loop-engineering` 管理 uv tool，同时验证新的 executable。

</domain>

<decisions>
## Implementation Decisions

### the agent's Discretion
- `pyproject.toml` 只注册 `loop-engine = loop_engineering.cli:main`；不注册旧名或 `loop-agent`。
- argparse 的 `prog` 同步为 `loop-engine`，业务子命令实现保持原样。
- 生命周期代码使用独立常量区分分发包名、Skill checkout 名、Skill 触发词和 CLI 名，避免再次混用。
- 安装和更新成功后必须执行 `loop-engine --version`，并拒绝可发现的旧 CLI 别名；卸载仍调用 `uv tool uninstall loop-engineering`，然后确认 `loop-engine` 不再可发现。
- 生命周期 checkout marker 更新为 Protocol 0.3 和 `Compatible Core: >=0.3,<0.4`；本阶段仅同步 Adapter 的生命周期相关标记与安装验证命令，完整命令文档收敛仍由 Phase 4 负责。

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/loop_engineering/cli.py` 的一个 argparse parser 已提供全部命令组，入口改名无需复制命令实现。
- `adapters/codex/scripts/manage.py` 已集中封装 argv subprocess、checkout 校验、快速前移与安全删除。
- `tests/test_cli.py` 和 `tests/test_codex_installer.py` 已覆盖命令能力与生命周期失败关闭路径。

### Established Patterns
- 所有 subprocess 使用 argv 与 `shell=False`。
- 生命周期先验证精确 checkout/Git 边界，再执行 uv 或递归删除。
- 测试通过可控 `shutil.which` 和 `subprocess.run` 替身断言完整 argv 与失败恢复。

### Integration Points
- `[project.scripts]` 决定安装的 executable；`argparse.ArgumentParser(prog=...)` 决定帮助与错误表面。
- `uv tool install <repository>` 使用分发包元数据安装入口；`uv tool uninstall loop-engineering` 使用分发包名卸载。
- `adapters/codex/SKILL.md` 的兼容 marker 被生命周期管理器作为 checkout 身份校验的一部分。

</code_context>

<specifics>
## Specific Ideas

不增加 CLI shim、符号链接或兼容别名；不改 Python import package `loop_engineering`；
不放宽 checkout、Git、确认或删除门禁。

</specifics>

<deferred>
## Deferred Ideas

- Adapter 全文、README、adoption guide 和示例命令的统一替换属于 Phase 4。
- Adapter 的 Autonomous 决策循环属于 Phase 3。

</deferred>
