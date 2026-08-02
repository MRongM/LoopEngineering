# Loop Skill Intake Spec/Plan 提示设计

- 状态：用户已批准条件提示策略
- 日期：2026-08-02
- 适用范围：Codex Adapter Intake 文案与契约测试

## 目标

每个显式启动的新 `$loop-engine` Intake 都向用户说明：现有 spec 或 plan 可以作为
Loop Contract 的来源材料。已提供文档时确认将读取并映射；未提供时只提示该选项，
继续根据当前请求起草，不等待额外输入。

## 方案比较

### A. 写入常驻 `SKILL.md`

不采用。它能最早暴露提示，但会扩大所有阶段都加载的安全内核，而该行为只属于 Intake。

### B. 写入 `references/intake-contract.md`

采用。显式新任务必须读取该 playbook，提示与契约起草职责一致，并保持现有渐进披露边界。

### C. 只补 README 或 adoption 文档

不采用。它能帮助安装前发现能力，但不能约束 Skill 在实际 Intake 中告知用户。

## 行为契约

在新 Intake 开始时，Adapter 必须只提示一次：

- 请求已经引用或提供 spec/plan 时，确认会读取它们并映射到契约草稿。
- 请求没有 spec/plan 时，告知用户可以提供文档路径或内容，但该选项非阻塞；继续使用
  当前请求和仓库事实起草契约。
- spec/plan 只是来源材料，不构成合同批准，也不能替代必需契约字段、仓库事实或适用指令。

该提示不是新的问题、审批门或暂停条件，不改变唯一 `contract_approval` 语义。

## 测试策略

1. 先在 `tests/test_adapter_contract.py` 增加组合语料断言，要求 Intake 明确包含上述三项行为。
2. 运行聚焦测试并保留因提示缺失产生的 RED。
3. 仅修改 `adapters/codex/references/intake-contract.md`，运行聚焦 GREEN。
4. 运行完整 pytest、Ruff 与 `git diff --check`，确认 Core、Schema 和 CLI 无变化。

## 范围外

- 不增加 `contract generate` CLI、解析器或新的契约 Schema 字段。
- 不规定 spec/plan 文件格式，不实现来源追踪或冲突自动解决。
- 不修改 Core Protocol、审批、Gate、预算或执行状态机。
- 不创建分支、提交、推送、PR、合并或部署。

## 完成条件

- 新 Intake 会根据 spec/plan 是否已提供给出对应的单次提示。
- 未提供文档时提示不阻塞契约起草。
- spec/plan 不会被误当作批准或完整契约。
- 聚焦和全量质量门通过，并记录新鲜 RED→GREEN 证据。
