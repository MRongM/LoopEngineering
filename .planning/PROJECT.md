# Loop Engineering

## What This Is

Loop Engineering 是面向编码 Agent 的证据门控、可恢复执行协议与工具集。它通过严格合同、追加式账本、风险门禁、新鲜验证证据和独立 Checker，约束 Agent 在明确范围内持续执行，并以可审计事实而不是自然语言声明判定完成。

当前里程碑将 Core Protocol 演进到 0.3.0：删除 `collaborative` 并仅保留 `autonomous`，同时把 Agent 使用的 Shell CLI 入口统一为 `loop-engine`。

## Core Value

Agent 只能在明确批准且可验证的范围内自主执行，并且只有真实证据满足合同后才能完成。

## Requirements

### Validated

- ✓ 严格的版本化 Loop Contract、状态机与预算约束 — 现有 0.2.0 实现
- ✓ 原子状态快照、追加式 intent/result 账本与未决动作检测 — 现有 0.2.0 实现
- ✓ 合同版本、规范化 SHA-256 与风险 ID 绑定的 Autonomous 授权 — 现有 0.2.0 实现
- ✓ 新鲜证据、代码指纹、范围、Checker、Gate 与 Git 交付共同派生 `DONE` — 现有 0.2.0 实现
- ✓ Codex `$loop-engine` 显式启动与 Goal/Run 自然语言续跑 — 现有 Codex Adapter
- ✓ 受控的 worktree、commit、push 与 PR 自动化，永久禁止强推、历史改写、自动合并和部署 — 现有 0.2.0 实现
- ✓ Core Protocol 与 Python 包 0.3.0 只接受 Autonomous，且明确旧合同兼容边界 — Phase 1
- ✓ Agent Shell 只注册 `loop-engine`，生命周期仍按 `loop-engineering` 分发包安全管理 — Phase 2
- ✓ Codex `$loop-engine` 在一次合同批准后自主设计、计划、执行、验证、修正和可靠续跑 — Phase 3
- ✓ README、接入指南、兼容矩阵、构建产物和完整发布证据统一到 0.3.0 — Phase 4

### Active

- 无 — 当前里程碑的 21 项需求均已实现并通过阶段验证。

### Out of Scope

- 产品名、Python 包名或仓库名重命名 — 继续使用 `Loop Engineering` 与 `loop-engineering`
- Codex Skill 触发词重命名 — 继续使用 `$loop-engine`
- 为旧 CLI `loop-engineering` 或拟议的 `loop-agent` 保留兼容别名 — 0.3.0 只暴露 `loop-engine`
- 转换或恢复 collaborative 合同与 Run — 0.3.0 明确不兼容该模式
- 削弱合同批准、风险披露、Checker、证据、预算或永久禁止项 — 这些安全不变量保持不变
- 新增 scheduler、daemon、自动合并或自动部署 — 不属于本里程碑

## Context

- 当前实现为 Loop Engineering 0.3.0，使用 Python 3.12+、Pydantic strict models、PyYAML 与 filelock。
- Core 保持工具无关；Codex 专有行为位于 `adapters/codex/`。
- Core、通用模板和生成 Schema 已仅接受 `autonomous`；0.3 省略模式采用 Autonomous，legacy omission 与 collaborative Run 均拒绝。
- Python 分发包仍为 `loop-engineering`，唯一 Shell CLI 为 `loop-engine`；Adapter 和当前发布文档均已收敛，且不提供旧 CLI alias。
- 里程碑最终回归为 231 个测试通过；Ruff、Schema 重建、临时 sdist/wheel 构建、wheel entry point 和 `git diff --check` 均通过。

## Constraints

- **协议兼容性**：0.3.0 只接受 autonomous；旧 0.1.0/0.2.0 autonomous 合同可读取，collaborative 合同与 Run 明确不兼容。
- **迁移安全**：不得把 collaborative Run 静默转换为 autonomous；目标、权限、风险或合同版本变化仍需完整批准。
- **实现边界**：Core 不得引入 Codex 专有模型；Codex 行为继续留在 Adapter seam。
- **测试纪律**：生产代码前必须先有失败测试，并保留新鲜 RED→GREEN 证据；不得弱化测试、Gate 或 Schema。
- **子进程安全**：所有命令继续使用 argv 与 `shell=False`，不得拼接 Shell 命令执行用户数据。
- **Git 安全**：不得自动合并、部署、强推、改写历史或执行 `git reset --hard`；不得覆盖无关用户修改。
- **命名边界**：产品与包继续叫 Loop Engineering / `loop-engineering`；仅可执行命令改为 `loop-engine`。

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Core Protocol 0.3.0 仅支持 Autonomous | 提供无需模式分支的自主执行 Skill | ✓ Phase 1 验证 |
| collaborative 合同与 Run 不再兼容 | 用户明确选择彻底移除 collaborative 选项 | ✓ Phase 1 验证 |
| 旧 0.1.0/0.2.0 autonomous 合同仍可读取 | 只移除 collaborative，不扩大无关兼容性破坏 | ✓ Phase 1 验证 |
| `loop-engine` 成为唯一 Shell CLI 入口 | 统一 Skill 触发词与 Agent 执行命令的基础名称 | ✓ Phase 2 验证 |
| 产品名、包名和 `$loop-engine` 触发词保持不变 | 将变更限制在 Core 默认语义和执行命令，避免无关重命名 | ✓ Phase 4 身份矩阵与构建产物验证 |
| 一次完整合同批准后由 Skill 自主选择下一最小动作 | 实现无需 routine confirmation 的可恢复循环 | ✓ Phase 3 决策循环与续跑验证 |
| 安全 Gate、风险绑定、Checker 与证据规则不变 | Autonomous 缺省不能等同于弱化授权或完成标准 | ✓ Phase 1–4 跨层回归 |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `$gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `$gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-07-31 after Phase 4 verification*
