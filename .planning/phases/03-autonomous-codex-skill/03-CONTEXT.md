# Phase 3: Autonomous Codex Skill - Context

**Gathered:** 2026-07-31
**Status:** Ready for planning
**Mode:** Auto-generated from the approved 0.3 design and explicit autonomous inline authorization

<domain>
## Phase Boundary

收敛仓库内 Codex `$loop-engine` Skill 的运行协议：新任务固定生成 Autonomous 0.3
合同，不再提供或解释模式选项；一次完整合同批准后，Skill 基于真实命令、测试、
账本、证据和 Checker 结论持续选择下一最小动作，并在跨 turn 续跑时重新验证唯一
Goal/Run 绑定与全部授权状态。本阶段不修改 Core 模型、生命周期管理器或发布文档。

</domain>

<decisions>
## Implementation Decisions

### Autonomous-only admission

- **D-01:** 新 `$loop-engine` 任务固定写入 `protocol_version: 0.3.0` 与 `mode: autonomous`；不得询问、展示、接受或降级到其他控制模式。
- **D-02:** Adapter 正文不得保留 collaborative 的选择、说明、专属 Gate、最终验收或升级/降级路径。

### Goal/Run continuation

- **D-03:** 每次 host continuation 必须先用 canonical Goal marker 验证 loop ID 与绝对 Run 目录，再读取 `loop-engine run events`、`run status`、当前合同绑定、预算和未决 intent；不得依赖对话记忆或扫描“最新 Run”。

### Autonomous decision loop

- **D-04:** 一次完整合同批准覆盖合同内的设计、计划、普通执行和精确披露风险；之后按“一个未满足标准 → 一个最小可验证动作 → 真实反馈 → 证据 → Checker → 决策”循环推进。
- **D-05:** 下一步只由当前合同、状态、命令/测试反馈、证据新鲜度和 Checker 结论决定；失败时先形成新诊断，禁止重复无进展策略或用自然语言声明成功。
- **D-06:** 仅在合同扩展或批准失效、Goal/Run 绑定或未决 intent 无法对账、平台/外部认证硬门、缺少必要权限/输入/独立 Checker、用户取消以及真实预算终止时暂停；风险等级本身不增加确认。

### the agent's Discretion

- 调整 Skill 章节顺序和表格布局，以最少重复表达上述协议。
- 在既有 Adapter 契约测试中选择精确的正向与负向字符串/结构断言。

</decisions>

<canonical_refs>
## Canonical References

### Protocol and approved design

- `PROTOCOL.md` — 0.3 生命周期、证据、授权、失败恢复、预算和永久禁止项。
- `docs/superpowers/specs/2026-07-31-loop-engineering-0.3-autonomous-only-design.md` — Autonomous-only 取代决策及兼容边界。

### Project and prior phase

- `.planning/REQUIREMENTS.md` — CORE-04 与 AUTO-01..05 的验收范围。
- `.planning/phases/02-cli-and-lifecycle/02-02-SUMMARY.md` — 唯一 executable 已切换为 `loop-engine`。

</canonical_refs>

<specifics>
## Specific Ideas

- 将 `Control modes` 改为单一 `Autonomous execution`，把下一动作决策写成确定性表格。
- Runtime 示例和续跑命令必须使用 `loop-engine`；`loop-engineering` 仅可作为分发包、仓库或 checkout 名称出现。
- 保留 `$loop-engine goal-bridge/v1`、Goal intent/result 对账和权威 `DONE` 后才完成 Goal 的既有安全结构。

</specifics>

<deferred>
## Deferred Ideas

- README、adoption guide、ADR、历史设计与所有示例的全局命名清理属于 Phase 4。
- 不新增 scheduler、daemon、自动 merge/deploy 或新的 Core 命令。

</deferred>

---
*Phase: 03-autonomous-codex-skill*
*Context gathered: 2026-07-31 via approved autonomous decisions*
