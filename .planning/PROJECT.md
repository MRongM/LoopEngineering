# Loop Engineering

## What This Is

Loop Engineering 是面向编码 Agent 的证据门控、可恢复执行协议与工具集。它通过严格合同、追加式账本、风险门禁、新鲜验证证据和独立 Checker，约束 Agent 在明确范围内持续执行，并以可审计事实而不是自然语言声明判定完成。

当前里程碑将 Core Protocol 演进到 0.3.0：新合同默认采用 `autonomous`，同时把 Agent 使用的 Shell CLI 入口统一为 `loop-agent`。

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

### Active

- [ ] 发布 Core Protocol 与 Python 包 0.3.0，使 0.3.0 合同省略 `mode` 时默认解析为 `autonomous`
- [ ] 保留 0.1.0/0.2.0 缺省 `mode` 的 `collaborative` 语义，禁止现有 Run 静默迁移
- [ ] 将 Agent 执行用的 Shell CLI 入口从 `loop-engineering` 完整替换为 `loop-agent`，不保留旧命令别名
- [ ] 同步协议、模型、模板、生成 Schema、Codex Adapter、生命周期管理器、README、接入文档与兼容性说明
- [ ] 通过测试先行和完整验证证明模式解析、CLI 安装生命周期、旧协议兼容性及安全门禁未回归

### Out of Scope

- 产品名、Python 包名或仓库名重命名 — 继续使用 `Loop Engineering` 与 `loop-engineering`
- Codex Skill 触发词重命名 — 继续使用 `$loop-engine`
- 为旧 CLI `loop-engineering` 保留兼容别名 — 0.3.0 只暴露 `loop-agent`
- 将活动的 0.1.0/0.2.0 Run 自动升级到 0.3.0 — 迁移必须显式创建并批准新合同版本
- 削弱合同批准、风险披露、Checker、证据、预算或永久禁止项 — 这些安全不变量保持不变
- 新增 scheduler、daemon、自动合并或自动部署 — 不属于本里程碑

## Context

- 当前实现为 Loop Engineering 0.2.0，使用 Python 3.12+、Pydantic strict models、PyYAML 与 filelock。
- Core 保持工具无关；Codex 专有行为位于 `adapters/codex/`。
- 当前批准设计让 Codex Adapter 在省略模式时采用 `autonomous`，但 Core、通用模板和 JSON Schema 仍默认 `collaborative`。
- 本里程碑明确取代“Core 默认继续 collaborative”以及“拒绝协议级 Autonomous 默认”的旧局部决策，并通过协议 0.3.0 隔离兼容语义。
- 当前 Shell CLI 入口为 `loop-engineering`，Adapter 与文档也使用该命令；用户要求统一改为 `loop-agent`。
- 0.2.0 本地基线验证为 181 个测试通过且 Ruff 无告警；0.3.0 必须保留或提升该验证水平。

## Constraints

- **协议兼容性**：0.1.0/0.2.0 缺省模式必须继续是 `collaborative`；0.3.0 才能缺省为 `autonomous`。
- **迁移安全**：活动旧 Run 不得静默升级；目标、权限、风险或合同版本变化仍需完整批准。
- **实现边界**：Core 不得引入 Codex 专有模型；Codex 行为继续留在 Adapter seam。
- **测试纪律**：生产代码前必须先有失败测试，并保留新鲜 RED→GREEN 证据；不得弱化测试、Gate 或 Schema。
- **子进程安全**：所有命令继续使用 argv 与 `shell=False`，不得拼接 Shell 命令执行用户数据。
- **Git 安全**：不得自动合并、部署、强推、改写历史或执行 `git reset --hard`；不得覆盖无关用户修改。
- **命名边界**：产品与包继续叫 Loop Engineering / `loop-engineering`；仅可执行命令改为 `loop-agent`。

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 通过 Core Protocol 0.3.0 引入 Autonomous 缺省值 | 避免静默改变 0.1.0/0.2.0 合同的安全语义 | — Pending |
| 旧协议省略 `mode` 时继续解析为 `collaborative` | 保持现有合同和 Run 的行为兼容性 | — Pending |
| `loop-agent` 成为唯一 Shell CLI 入口 | 明确区分 Agent 执行命令与产品/包名称 | — Pending |
| 产品名、包名和 `$loop-engine` 触发词保持不变 | 将变更限制在 Core 默认语义和执行命令，避免无关重命名 | — Pending |
| 安全 Gate、风险绑定、Checker 与证据规则不变 | Autonomous 缺省不能等同于弱化授权或完成标准 | — Pending |

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
*Last updated: 2026-07-31 after initialization*
