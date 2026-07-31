---
status: resolved
trigger: "解决安装卡死的问题"
created: 2026-08-01
updated: 2026-08-01
---

# Install Silent Hang

## Symptoms

- expected: 克隆完成后，生命周期安装命令持续显示安装进度，并最终提供可用的 `loop-engine` 0.3.0 可执行入口。
- actual: 克隆完成后终端长期无输出，`loop-engine` 尚未出现，表现为安装卡死。
- errors: 新安装过程没有错误输出；此前更新曾因旧 checkout 标记不一致而失败，重新克隆后该标记错误已消失。
- reproduction: `python3 adapters/codex/scripts/manage.py install --codex-home <codex-home>` 在内部调用 `uv tool install <checkout>`。
- timeline: 2026-08-01 安装 Core 0.3.0 的 `master` checkout 时出现。

## Current Focus

- hypothesis: confirmed — 生命周期管理器静默捕获长时间 uv 安装输出，且没有终止边界。
- test: patched manager 在隔离的 managed checkout、uv cache/tool/bin 中执行完整安装。
- expecting: 安装阶段立即显示状态及 uv 实时进度，在超时路径保留 checkout，成功后 `loop-engine --version` 返回 `0.3.0`。
- next_action: none
- reasoning_checkpoint: 根因、修复和发布产物均已通过新鲜证据验证。
- tdd_checkpoint: GREEN confirmed — focused 2/2, lifecycle 48/48, full suite 232/232.

## Evidence

- timestamp: 2026-08-01
  observation: 现有 `_run` 固定使用 `capture_output=True`，`_install` 直接调用它，未设置 `timeout`。
  implication: uv 的进度和错误均在子进程结束前不可见，且真实挂起没有终止边界。
- timestamp: 2026-08-01
  observation: 原安装缓存中已生成 0.3.0 wheel，并继续写入 Pydantic、PyYAML、filelock 等依赖。
  implication: 用户看到无输出时安装曾有实际进展，并非卡在仓库验证或 wheel 构建。
- timestamp: 2026-08-01
  observation: 隔离的全新 uv cache/tool/bin 安装约 30 秒完成，实时输出覆盖依赖解析、下载、构建和安装，最终 `loop-engine --version` 返回 `0.3.0`。
  implication: 相同安装 argv 能正常完成；生命周期包装层的静默行为是可复现差异。
- timestamp: 2026-08-01
  observation: 两个聚焦回归测试均失败，显示实际 kwargs 为 `capture_output=True` 且没有 `timeout`。
  implication: RED 证据直接覆盖用户可见进度和有界等待两个缺失行为。
- timestamp: 2026-08-01
  observation: patched manager 的隔离端到端安装实时显示解析、下载、构建和安装，退出码为 0，最终版本为 `0.3.0`。
  implication: 原始用户路径已通过管理器本身验证，不仅是单元测试或直接 uv 调用。
- timestamp: 2026-08-01
  observation: 完整回归 232 passed，Ruff、`py_compile`、`git diff --check` 和 sdist/wheel 构建均成功。
  implication: 修复没有破坏生命周期安全、CLI 身份或发布产物。

## Eliminated

- hypothesis: fresh checkout 的 Core/Skill/pyproject 版本标记仍不一致。
  evidence: fresh `master` checkout 的协议、Skill 兼容范围、包版本和唯一 CLI 均为 0.3.0/`loop-engine`。
- hypothesis: 删除 CLI console-script 可以消除依赖安装等待。
  evidence: console-script 仅是分发元数据入口；依赖来自 Core 包，不由 CLI 名称产生。

## Resolution

- root_cause: `_run` 固定 `capture_output=True`，而 `_install` 未设置 timeout；因此 uv 在慢网络或首次下载时有实际进展但终端完全静默，也无法区分慢任务与真正挂起。
- fix: 安装/重装前立即 flush 状态；仅对 `uv tool install` 继承 stdout/stderr；设置 600 秒 timeout；超时转换为明确 LifecycleError 并保留 Skill checkout。
- verification: RED 2 failed → GREEN 2 passed；生命周期 48 passed；全量 232 passed；隔离 manager install exit 0 并报告 0.3.0；Ruff/语法/差异/构建均通过。
- files_changed: `adapters/codex/scripts/manage.py`, `tests/test_codex_installer.py`, `.planning/debug/install-silent-hang.md`
