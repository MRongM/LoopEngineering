---
status: resolved
trigger: "确认自主决策并使用 inline 方式修复运行时 Gate/intent 绕过、Checker 身份与新鲜度、行为测试覆盖及 ADR 版本残留。"
created: 2026-08-01
updated: 2026-08-01
---

# Runtime Gate and Checker Binding

## Symptoms

- expected: 每个可执行动作和验证入口都在当前合同批准、正确状态、预算与 Gate 边界内；
  中高风险 Checker `ACCEPT` 必须绑定当前源码与验证事实后才能参与 `DONE`。
- actual: 通用 `run intent`/`run result` 与 `evidence run` 可绕过部分运行时前置条件；
  Checker 事件仅记录可自由填写的 actor、verdict 和 findings，完成重建无法证明其独立性
  或新鲜度。
- errors: 当前测试全部通过，但缺少这些负向行为用例，因此属于规范审计发现而非已有测试失败。
- timeline: 2026-08-01 首版执行闭合完成后进行 Skill/Protocol 一致性复审时发现。
- reproduction: 在未批准或错误状态的 Run 上直接调用通用 intent/验证入口；或在源码和证据
  变化前记录 Checker `ACCEPT`，随后观察当前实现只读取同合同版本的最新 verdict。
- user boundary: inline、自主决策；不创建分支、worktree、commit、push、PR；需要新增权限的
  事项留到最终报告。

## Current Focus

- hypothesis: 已确认。Core 缺少统一动作准入和事实绑定的 Checker attestation，使部分 Skill
  MUST 约束仅依赖 Adapter 守约。
- test: 已完成 Action/Result、Validation、Checker、Adapter 契约和状态边界的 RED→GREEN。
- expecting: 受检入口拒绝未批准、错误状态、超预算、计划外或伪造权威事实；旧 Checker
  `ACCEPT` 在任何后续变更后失效。
- next_action: 无；保留未提交工作树供用户审阅。
- reasoning_checkpoint: 目标是封闭 Core 自身可控制的入口；宿主原始工具拦截仍明确属于
  Adapter/宿主信任边界，不在 Core 中引入 Codex 专有类型。
- tdd_checkpoint: 所有计划内 RED 均已复现，最终全量 GREEN 为 264 passed。

## Evidence

- timestamp: 2026-08-01
  observation: 基线全量测试 239 passed，Adapter 定向测试 16 passed，Ruff 与 diff check 通过。
  implication: 修复必须以新增负向测试提供 RED，不能把既有 GREEN 当作缺口不存在的证据。
- timestamp: 2026-08-01
  observation: Action/Result 定向 RED 为 15 failed, 37 passed；失败由缺少
    `record_action_intent`、CLI 未接收 request 文件且通用 result 未拒绝权威 payload 引起。
  implication: 新测试准确命中计划中的入口与 provenance 缺口，不是环境或导入错误。
- timestamp: 2026-08-01
  observation: Action/Result GREEN 为 52 passed；Validation RED 为 4 failed, 16 passed，
    修复后 GREEN 为 20 passed。
  implication: Core 已拒绝未批准、错误状态、超预算或合同不匹配的验证，并隔离权威结果来源。
- timestamp: 2026-08-01
  observation: Checker 定向 RED 为 6 failed, 33 passed；失败由缺少 host Checker ID、
    attestation 事实字段和 CLI 新接口引起。
  implication: Checker 测试命中身份/新鲜度缺口，进入最小生产实现。
- timestamp: 2026-08-01
  observation: Checker/watch 修复后聚焦回归 51 passed；Adapter 文档契约 RED 为
    4 failed, 15 passed，分别命中 request-bound 入口、Checker 绑定、宿主信任边界和 ADR
    `0.3` 残留。
  implication: 运行时实现保持 GREEN，文档更新由可复现的失败契约驱动。
- timestamp: 2026-08-01
  observation: 全量回归达到 260 passed；随后自审新增状态/身份边界测试得到
    4 failed, 51 passed，命中暂停中的 platform action、跨合同 Checker ID 复用、Checker
    修订预算耗尽和 Checker actor/ID 不一致。
  implication: 聚焦 RED 证明边角条件此前仍可绕过，需要在最终发布验证前收紧。

## Eliminated

- hypothesis: 仅修改 Skill 文案即可修复。
  evidence: Git 专用入口已在 Core 内强制 Gate/状态/intent-result，而通用入口没有同等检查。
  reason: 问题包含可执行控制流差异，不是纯文档漂移。

## Resolution

- root_cause: Core 将 Gate 检查与通用 intent 记录分离，验证入口未重验运行授权；Checker
  verdict 未绑定合同、源码、证据和账本时点。Codex Skill 也没有明确宿主工具无法由 Core
  拦截的信任边界。
- fix: 新增 request-bound `record_action_intent`、专用 Git/证据结果、验证前置检查和严格
  `CheckerAttestation`；完成判定只消费当前 attestation。暂停平台变更、跨合同 Checker ID
  复用、预算耗尽和 actor/ID 不一致均失败关闭。Protocol、Skill、接入文档和 ADR 已同步。
- verification: 全量 pytest `264 passed`；Ruff `All checks passed!`；`git diff --check`
  通过；三份 Schema 重建后逐字节一致；临时目录成功构建 `loop-engineering 0.1.0` sdist 和
  wheel，wheel 仅暴露 `loop-engine` console script。
- files_changed: `src/loop_engineering/{cli,evidence,ledger}.py`、
  `src/loop_engineering/models/run.py`、五个行为/契约测试模块、`PROTOCOL.md`、Codex Skill
  及两个 routed playbook、README、接入指南、ADR 0001、Requirements、计划与本记录。
