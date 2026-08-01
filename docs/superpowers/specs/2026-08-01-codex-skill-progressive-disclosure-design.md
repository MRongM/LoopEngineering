# Codex Skill 渐进披露设计

- 状态：已由 Loop Contract v1 批准
- 日期：2026-08-01
- 适用范围：`adapters/codex/` 与 Adapter 契约测试
- 协议基线：Loop Engineering Core Protocol 0.3.0

## 1. 目标

将 Codex `$loop-engine` Skill 从单一长文档重构为一个始终加载的安全内核和四个按阶段
读取的 playbook。重构必须降低常驻上下文、让职责边界可见且可测试，同时保持当前
Protocol 0.3.0 的准入、授权、Goal/Run、Gate、Checker、预算与权威完成语义。

当前基线为 409 行、3251 词、24062 字节。入口重构后不得超过 2113 词，即常驻词数
至少降低 35%。引用文档的总长度不是成功指标；成功取决于每个任务只加载当前阶段所需
的指令，并且任何关键安全规则都不会因条件路由而变得不可见。

## 2. 审计结论与排序

### 2.1 已确认事实

- Core Protocol、严格模型、CLI 和账本已经提供确定性的合同、Gate、证据和完成能力，
  当前里程碑审计为 21/21 requirements、4/4 phases 和 5/5 flows 通过。
- `SKILL.md` 同时承担任务准入、Goal 生命周期、包生命周期、合同 Intake、Maker 循环、
  Checker、暂停边界和完成协议，属于多个独立变化轴的单文件聚合。
- `tests/test_adapter_contract.py` 有 548 行，能够锁定大量正向和负向词面，但多数断言
  默认全部规范必须位于入口文件中，阻止安全的渐进披露，并不能证明入口已正确路由。
- Core CLI 已提供精确的 `run`、`gate`、`budget`、`evidence`、`scope` 和 `completion`
  命令面。本轮没有证据支持新增 Core 命令或数据模型。
- 目标仓库没有 `.loop-engineering/project.yaml`，但 `run create --project` 使用显式项目根
  即可建立 Run。配置准入是否应由 Core 强制属于独立产品决策，不应夹带进本次重构。

### 2.2 优先级

| 优先级 | 机会 | 收益 | 风险 | 本轮决策 |
|---|---|---|---|---|
| P0 | 保持安全内核始终可见 | 防止准入、授权或 DONE 语义被条件加载 | 低 | 必须完成 |
| P1 | 按阶段拆分 playbook | 显著降低常驻上下文并明确职责 | 中 | 本轮实现 |
| P1 | 测试入口路由与组合语义 | 防止引用缺失或错误迁移 | 低 | 本轮实现 |
| P2 | 统一精确 CLI 配方 | 降低 Agent 猜测参数的概率 | 低 | 随 playbook 完成 |
| P3 | 项目初始化/配置准入收敛 | 消除配置存在性歧义 | 中 | 后续独立设计 |
| P3 | Core 辅助的 resume snapshot | 减少多命令续跑编排 | 高 | 有使用证据后再做 |
| P4 | 真实宿主 Goal 场景测试 | 覆盖 Codex 平台集成 | 高 | 依赖平台测试能力 |

## 3. 方案比较

### 方案 A：原文件内压缩

删除重复句、合并表格并调整顺序。实现风险最低，但多个职责仍一起变化，所有任务仍需
加载完整生命周期和执行协议，测试也继续把“存在某句话”误当成“阶段路由正确”。

### 方案 B：安全内核加渐进披露 playbook

入口只保留触发准入、协议兼容、变更前硬门、读取前置条件、路由规则和永久禁止项。
其余规则按阶段拆成四个入口直接引用的文档。测试分别验证安全内核、路由图、引用存在性、
组合语义和词数预算。

这是推荐并获批的方案。它用文档边界解决当前文档职责问题，不扩展 Core，不引入依赖，
也不改变现有外部行为。

### 方案 C：新增 Core/CLI 编排命令

新增 preflight 或 resume snapshot 命令，自动聚合状态、授权、预算和未决 intent。它可能
进一步降低 Agent 编排错误，但会修改 Core/CLI、测试和兼容表面，当前没有运行数据证明
收益足以承担范围和兼容成本，因此留到后续阶段。

## 4. 目标架构

```text
adapters/codex/SKILL.md
├── 始终可见：准入、兼容、硬门、路由、永久禁止项
├── references/intake-contract.md   新任务、Pending Draft、合同与修订
├── references/goal-bridge.md       Goal 创建、续跑、取消与完成
├── references/execution-loop.md    Maker、Checker、预算、证据与 DONE
└── references/lifecycle.md         安装、更新、卸载与项目初始化参考
```

### 4.1 `SKILL.md`：安全内核与路由器

入口承担以下且仅以下职责：

1. 只有显式 `$loop-engine` 可以启动新任务；自然语言只能继续唯一绑定的 Draft 或 Run。
2. 新任务固定使用 Protocol 0.3.0 Autonomous。
3. 合同批准前只有目标项目内的合同草案可以写入。
4. 在任何修改前读取 Core Protocol、项目配置、配置的指令文件、`AGENTS.md` 和当前合同。
5. 根据当前阶段强制读取一个或多个直接引用文档；缺失、不可读或不适用时 fail closed。
6. 永久禁止强推、历史改写、`reset --hard`、自动合并、自动部署及伪造完成。

入口不重复安装命令、完整 Goal 算法、Maker 步骤或 CompletionContext 字段清单。

### 4.2 `intake-contract.md`：执行授权

负责 Pending Draft 绑定、只读 Intake、合同字段、风险披露、校验、完整摘要顺序、一次
执行前批准、Run 创建和合同修订。它不得包含 Goal 工具调用或代码实施循环。

### 4.3 `goal-bridge.md`：宿主绑定

负责 canonical objective、`get_goal`/`create_goal`/`update_goal`、Goal create/complete
Gate、intent/result、跨 turn 续跑、取消和终态映射。它不得重新定义合同审批或 Core DONE。

### 4.4 `execution-loop.md`：证据循环

负责预算检查、ActionRequest、Gate、intent/result、RED→GREEN、evidence、Checker、暂停边界、
CompletionContext、scope check 和权威 `run complete`。它不得包含生命周期安装命令。

### 4.5 `lifecycle.md`：用户操作的生命周期

负责安装、更新、卸载、项目初始化和平台差异。安装与删除继续是用户操作，不得被 Maker
循环代执行；管理器的 fail-closed 条件和会话重启要求保持不变。

## 5. 路由契约

| 当前任务/阶段 | 必须读取 |
|---|---|
| 新任务或 Pending Draft | `references/intake-contract.md` |
| 已批准 Run 的 Goal 创建或任意续跑 | `references/goal-bridge.md` |
| designing 至 deciding、验证或完成 | `references/execution-loop.md` |
| 安装、更新、状态、卸载或项目初始化 | `references/lifecycle.md` |

一个阶段可能要求多个文档。例如初次批准后的执行同时需要 Goal bridge 和 execution loop。
这些路径必须以 `SKILL.md` 所在目录为解析基准，而不是目标项目的工作目录。入口必须使用
强制措辞并直接列出路径；不得通过引用文档再跳转到第二层 playbook 引用。

## 6. 错误处理和安全保持

- 引用文件缺失、不可读或路由不明确时停止，不凭记忆继续。
- 安全内核与引用冲突时，以 Core Protocol、当前用户指令和获批合同的优先级处理并暂停
  合同修订，不静默选择宽松解释。
- 路由仅决定读取哪些说明，不授予 Intake、审批、权限、预算或完成权。
- Goal objective 仍只是指针；Run 账本仍是授权与完成事实来源。
- 所有 Action 仍先预算、Gate 和 intent，后修改与 result；中高风险仍需独立 Checker。
- 不把拆分后的重复减少解释为可以删除永久禁止项、绑定字段或新鲜证据要求。

## 7. 测试设计

`tests/test_adapter_contract.py` 增加集中读取辅助函数：

- `read_skill_body()` 只返回入口正文，用于始终可见规则和词数预算。
- `read_adapter_protocol()` 按固定顺序组合入口和四个引用，用于完整语义回归。
- `REFERENCE_PATHS` 是唯一的期望引用清单，测试每个文件存在且被入口直接引用。

测试遵循以下分层：

1. 新增测试先在当前单文件实现上失败：引用不存在、路由缺失、入口超过 2113 词。
2. 安全内核测试继续只检查入口，确保关键规则没有被错误下沉。
3. 现有详细语义断言改为读取组合语料，但不删除其 required/obsolete 项。
4. 新增边界断言，确保生命周期命令不再常驻入口，同时仍存在于组合语料。
5. 定向测试通过后运行全量测试、Ruff 与 `git diff --check`。

## 8. 实施边界

本轮只修改 Adapter 文档结构及其契约测试。README、adoption、ADR 和 Core 对外行为不变，
因为用户可见语义没有变化。不得创建新依赖、生成脚本框架或为未知的未来适配器预留抽象。

GSD quick 采用 inline 适配：当前主代理写计划、执行和状态摘要。项目指令与获批合同明确
禁止未经请求的 Git 操作，因此跳过 GSD 默认的分支、worktree、实现子代理和提交步骤。
独立 Checker 只做只读审查，不参与实现。

## 9. 分阶段演进路线

### 当前切片：渐进披露

完成安全内核、四个 playbook、测试路由和上下文预算。这是一个可独立验证且不改变 Core
的最小交付。

### 后续候选：项目 preflight

单独决定 `.loop-engineering/project.yaml` 是否为 Run 的强制前置条件，以及缺失时由用户
还是 Adapter 初始化。该决策需要 Core、CLI、adoption 和迁移兼容性共同设计。

### 后续候选：恢复快照

在收集真实失败样本后，评估只读 `resume snapshot` 命令是否应聚合合同授权、状态、预算、
未决 intent 和证据新鲜度。只有证明多命令编排是主要故障源时才扩展 Core。

### 后续候选：宿主场景验证

如果 Codex 提供可隔离的 Goal 测试接口，再增加真实 create/reconcile/complete 场景；仓库测试
继续禁止伪造宿主成功证据。

## 10. 完成条件

入口词数达到预算，四个引用及路由测试通过，全部既有语义断言和全量回归保持通过，独立
Checker 接受实际差异，并由 Loop 的新鲜证据、scope check 和权威完成命令共同判定 DONE。
