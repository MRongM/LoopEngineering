# Roadmap: Loop Engineering

## Overview

本里程碑以横向分层方式把 Loop Engineering 从 0.2.0 演进为 Autonomous-only 0.3.0。先冻结协议、兼容性和安全不变量，再替换唯一 CLI 入口及其生命周期，随后收敛 Codex Adapter 与 `$loop-engine` 的自主决策循环，最后统一文档、兼容性说明和跨层发布证据。各阶段按顺序执行，避免 Adapter 或文档先于 Core 合同语义漂移。

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Protocol 0.3 Contract** - 建立 Autonomous-only 协议、兼容边界和不变安全门禁 (completed 2026-07-31)
- [x] **Phase 2: CLI and Lifecycle** - 将唯一执行入口切换为 `loop-engine` 并贯通安装生命周期 (completed 2026-07-31)
- [x] **Phase 3: Autonomous Codex Skill** - 移除模式分支并实现一次批准后的自主决策与续跑闭环 (completed 2026-07-31)
- [x] **Phase 4: Release Convergence** - 统一面向用户的命名、兼容性文档和完整发布证据 (completed 2026-07-31)

## Phase Details

### Phase 1: Protocol 0.3 Contract

**Goal**: Core 以可验证且不削弱安全门禁的方式只接受 Autonomous，并明确旧合同兼容边界
**Depends on**: Nothing (first phase)
**Requirements**: [CORE-01, CORE-02, CORE-03, CORE-05, CORE-06, SAFE-01, SAFE-02, SAFE-03, TEST-01]
**Success Criteria** (what must be TRUE):

  1. 用户创建省略 `mode` 的 0.3.0 合同时，合同可通过校验并明确解析为 `autonomous`。
  2. 用户提交任何协议版本的 collaborative 合同或尝试恢复 collaborative Run 时，会收到确定性拒绝，系统不会静默迁移它。
  3. 用户仍可读取 0.1.0/0.2.0 autonomous 合同，且这些合同继续执行其原有风险授权和最终门禁语义。
  4. 合同批准绑定、预算、Checker、新鲜证据、范围检查和永久禁止项在 0.3.0 下仍被强制执行。
  5. 协议、严格模型、通用模板和生成 JSON Schema 对 0.3.0 语义保持一致并可确定性重建。

**Plans**: 2 plans
Plans:
**Wave 1**

- [x] 01-01: 以 TDD 建立 0.3 设计、合同模型、模板与 Schema 的 Autonomous-only 语义

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-02: 以 TDD 扩展账本授权、风险策略和完成 Gate 的 0.3 安全语义

### Phase 2: CLI and Lifecycle

**Goal**: 安装后的 Agent Shell 只暴露 `loop-engine`，同时保持完整命令能力和正确的包生命周期
**Depends on**: Phase 1
**Requirements**: [CLI-01, CLI-02, LIFE-01]
**Success Criteria** (what must be TRUE):

  1. 用户安装 Python 分发包后只能调用 `loop-engine`，且现有命令组和参数能力完整可用。
  2. 用户环境中不会由该包注册 `loop-engineering` 或 `loop-agent` 可执行别名。
  3. 用户通过生命周期管理器执行安装、状态检查、更新和卸载时，管理器始终区分 `loop-engineering` 分发包与 `loop-engine` 可执行入口，并正确验证或移除后者。

**Plans**: 2 plans
Plans:
**Wave 1**

- [x] 02-01: 以失败测试锁定唯一命令表面，并切换 Python console script 入口

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 02-02: 更新生命周期管理器并验证安装、状态、更新和卸载闭环

### Phase 3: Autonomous Codex Skill

**Goal**: `$loop-engine` 在一次合同批准后可以基于证据自主决策、执行、修正和可靠续跑
**Depends on**: Phase 2
**Requirements**: [CORE-04, AUTO-01, AUTO-02, AUTO-03, AUTO-04, AUTO-05]
**Success Criteria** (what must be TRUE):

  1. 用户启动 `$loop-engine` 新任务时不再看到模式选择，生成的合同始终采用 Autonomous。
  2. 用户完成一次完整合同批准后，Skill 能自主推进设计、计划、执行、验证、Checker、修正和下一步决策。
  3. Skill 根据测试、命令反馈和 Checker 证据选择下一最小动作，只在已定义的硬边界出现时暂停。
  4. 用户跨 turn 继续任务时，Skill 会重新校验 Goal、Run、账本、授权、预算和未决 intent，不依赖对话记忆或“最新 Run”猜测。
  5. Adapter 中不存在 collaborative 的选择、展示、降级或专属执行路径。

**Plans**: 2 plans
Plans:
**Wave 1**

- [x] 03-01: 以 Adapter 契约测试移除 collaborative 表面并锁定 Goal/Run 续跑绑定

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 03-02: 实现一次批准后的自主决策循环、最小动作选择和精确暂停边界

### Phase 4: Release Convergence

**Goal**: 所有用户入口、文档和验证证据共同证明 0.3.0 可以一致发布
**Depends on**: Phase 3
**Requirements**: [CLI-03, NAME-01, TEST-02]
**Success Criteria** (what must be TRUE):

  1. 用户在 Adapter、README、接入指南、示例和测试中看到的执行命令全部是 `loop-engine`。
  2. 用户可以从兼容性说明明确得知：产品、仓库和 Python 包仍叫 Loop Engineering / `loop-engineering`，Skill 触发词仍为 `$loop-engine`，且没有 CLI 别名或 collaborative 迁移路径。
  3. 维护者可以用新鲜证据证明协议、CLI、生命周期、Adapter、全量测试、Ruff、构建及 `git diff --check` 全部通过。

**Plans**: 2 plans

Plans:

**Wave 1**

- [x] 04-01: 同步 README、接入指南、示例、兼容性说明和命名残留检查

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 04-02: 执行跨层回归、静态检查、构建与最终发布证据验证

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Protocol 0.3 Contract | 2/2 | Complete   | 2026-07-31 |
| 2. CLI and Lifecycle | 2/2 | Complete    | 2026-07-31 |
| 3. Autonomous Codex Skill | 2/2 | Complete    | 2026-07-31 |
| 4. Release Convergence | 2/2 | Complete    | 2026-07-31 |
