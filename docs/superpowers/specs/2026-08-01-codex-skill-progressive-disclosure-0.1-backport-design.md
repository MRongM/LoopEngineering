# Codex Skill 渐进披露 0.1 回迁设计

- 状态：用户已批准迁移，并明确要求 Protocol 保持 `0.1.0`
- 日期：2026-08-01
- 来源优化：`feat/20260801-opt` / `5d4b983`
- 目标基线：`master` / `41cae1f`
- 适用范围：Codex Adapter 文档结构、契约测试与 GSD 任务记录

## 目标

把目标分支当前 3327 词的 `adapters/codex/SKILL.md` 重构为一个始终加载的安全内核和
四个按阶段读取的 playbook。入口不得超过 2113 词；组合语料必须保留目标分支现有的
Protocol `0.1.0` 执行闭合语义。

## 不变量

- `PROTOCOL.md`、Python 包版本和 Adapter 新任务协议号继续是 `0.1.0`。
- 唯一模式继续是 `autonomous`，唯一人工门继续是 `contract_approval`。
- 控制根继续是 `.loop-engine/`；不得引入 `.loop-runs/` 或 `.loop-engineering/`。
- 完整合同继续包含 `execution_plan.design_decisions` 和精确 `actions`。
- Goal 只作为 Run 指针；账本继续是授权、证据和完成的事实来源。
- 每个外部变更继续执行预算、Gate、intent、真实 result 和新鲜验证证据流程。
- 中高风险继续要求独立 Checker；DONE 继续由权威完成命令判定。
- 强推、历史改写、`git reset --hard`、自动合并和自动部署继续永久禁止。

## 方案

### A. 直接 cherry-pick 优化提交

拒绝。该提交基于旧的 0.3 文档面，包含 `Compatible Core: >=0.3,<0.4`、`.loop-runs/`
和旧兼容分支；直接迁移会违反首发 0.1 的身份与控制根。

### B. 以目标 0.1 原文为语义源进行结构回迁

采用。只复用安全内核、直接路由、四个职责文件和组合语料测试这一架构；所有正文从目标
`master` 当前 Skill 拆分，必要的交叉阶段摘要保留在入口，不从 0.3 playbook 复制行为。

### C. 只压缩单文件

不采用。它无法建立阶段职责边界，也不能验证引用存在性和直接路由，达不到已批准优化的
核心收益。

## 目标结构

```text
adapters/codex/SKILL.md
├── 始终可见：0.1 身份、准入、变更硬门、路由、永久禁止项
├── references/intake-contract.md
├── references/goal-bridge.md
├── references/execution-loop.md
└── references/lifecycle.md
```

- `intake-contract.md`：Pending Draft、合同字段、一次完整批准、Run 创建和修订。
- `goal-bridge.md`：Goal 创建、调和、续跑、取消和完成映射。
- `execution-loop.md`：预算、Gate、Maker、证据、Checker、暂停边界和权威完成。
- `lifecycle.md`：用户操作的安装、状态、更新、卸载和项目初始化。

引用路径必须直接出现在入口路由表中，以 `SKILL.md` 所在目录为解析基准。引用文档不得
形成第二层 playbook 路由。缺失、不可读、路由不明确或与 Core `0.1.0` 不兼容时 fail closed。

## 测试策略

1. 先增加 `REFERENCE_PATHS`、入口词数预算、直接路由和安全内核测试，并保留预期 RED。
2. `read_adapter_protocol()` 固定组合入口和四个引用；详细语义测试改读组合语料，正负断言
   不删除、不放宽。
3. 增加首发身份回归：组合语料必须包含 `0.1.0` 和 `.loop-engine/`，且不得包含 0.3
   兼容声明、`.loop-runs/` 或 `.loop-engineering/` 控制根。
4. 定向 Adapter 测试通过后运行全量 pytest、Ruff、`git diff --check` 和补丁适用性检查。

## 范围外

- 不修改 Core、Schema、模板、CLI、README、adoption 或 ADR 行为。
- 不新增依赖、兼容层、自动迁移或未来版本预留。
- 不创建分支、提交、推送、PR、合并或部署。

## 完成条件

- 入口不超过 2113 词并直接路由四个存在的引用。
- 目标 0.1 的所有既有 Adapter 语义断言与新增结构断言通过。
- 全量回归、Ruff 和差异检查通过。
- 生成的补丁包含所有未跟踪新文件，能在原始目标 `41cae1f` 的全新克隆中实际应用，
  且应用后的定向 Adapter 测试通过。
- `PROTOCOL.md` 和 `pyproject.toml` 无差异，组合 Adapter 语料没有 0.3 残留。
