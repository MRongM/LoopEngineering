# Codex Goal 任务级自然语言续跑最小强衔接设计

- 状态：Loop Contract v1 已批准；设计批准以 Run 账本中的 `design_approval` 事件为准
- 日期：2026-07-31
- 适用范围：Codex Adapter、生命周期管理器与通用 `platform_state` Gate
- 协议基线：Loop Engineering Core Protocol 0.2.0

## 1. 目标

Codex 中只有开始一个新的 Loop 任务时需要显式 `$loop-engine`。任务一旦在当前
对话中唯一绑定，用户后续可以用自然语言澄清、批准、修订、继续、暂停、取消或提供
反馈；跨 turn 的持久续跑默认由 Codex Goal 承载。

隐式选择 Skill 只允许 Adapter 检查当前 turn 是否属于已绑定任务，不授予新建任务、
扩大范围、绕过 Gate 或宣告完成的权限。Loop Run 仍是合同、权限、证据、预算、Checker
和 `DONE` 的唯一权威。

## 2. 非目标

- 不从任务语义、相似主题或普通自然语言隐式开始新的 Loop 任务。
- 不扫描 `.loop-runs/` 并按时间选择“最新” Draft 或 Run。
- 不接管无关 Goal，也不支持多个 Draft、Goal 或 Run 之间的猜测式选择。
- 不向 Core 合同、状态或持久化 Schema 添加 Codex 对话字段。
- 不同步或换算 Goal Token 预算与 Loop 工程预算。
- 不赋予 Goal 审批、权限扩展、Gate 判定或完成判定能力。
- 不在本次仓库实现中创建、更新或完成真实 Codex Goal，也不伪造宿主冒烟测试。

## 3. 职责边界

```text
显式 $loop-engine 启动
        │
        ▼
当前对话中的唯一 Pending Draft ── 自然语言澄清/批准
        │ 合同批准并创建 Run
        ▼
Codex Goal + Loop 账本绑定 ─────── 跨 turn 自然语言续跑
        │
        ▼
Loop Run
合同、Gate、事件、工程预算、证据、Checker、DONE
```

`allow_implicit_invocation: true` 只让宿主有资格在未出现触发词时选择 Codex Skill。
是否可以执行任何 Loop 动作，仍由 Adapter 的任务绑定准入规则决定。Codex 专有流程位于
`adapters/codex/`；Core 只保留通用 `platform_state` 动作种类。

## 4. 绑定术语

### 4.1 显式启动

当前用户消息包含 `$loop-engine`，且没有要求继续一个已唯一绑定的任务。只有这种情况
可以进入新任务 Intake 并创建 Pending Draft。

### 4.2 Pending Draft 绑定

Pending Draft 必须由当前 Codex 对话中最近一次显式启动创建，且当前对话只能有一个
候选 Draft。Adapter 依赖当前会话可见的交互链路，不得通过文件系统扫描寻找候选项。
该绑定只覆盖 Run 创建前的澄清和合同批准。

### 4.3 Goal/Run 持久绑定

Run 创建后，唯一可信的跨 turn 绑定同时需要：

1. `get_goal` 返回当前活动 Goal；
2. Goal objective 严格匹配规范标记、绝对 `run_dir` 和 `loop_id`；
3. Run 的追加式账本包含该 Goal 创建成功的 intent/result；
4. Goal、路径、Run 身份与真实状态相互一致。

只满足其中一部分不构成绑定。

## 5. 准入矩阵

| 当前消息 | 唯一绑定 | 当前任务状态 | Adapter 行为 |
|---|---|---|---|
| 含 `$loop-engine` | 无 | 无 | 开始一个新任务并进入 Intake |
| 含 `$loop-engine` | Pending Draft 或 Goal/Run | 可继续 | 明确继续已绑定任务，不重复创建任务 |
| 无触发词 | 当前对话唯一 Pending Draft | Run 创建前 | 只处理该 Draft 的澄清、完整摘要批准、拒绝或取消 |
| 无触发词 | 唯一且经账本验证的 Goal/Run | 非终态且未取消 | 只继续该 Run 的最小合法动作或处理用户反馈 |
| 无触发词 | 无、多个、陈旧或不一致 | 任意 | 不 Intake、不采用、不审批、不修改；要求显式 `$loop-engine` |
| 无触发词 | 唯一绑定 | `DONE`、`BLOCKED`、`BUDGET_EXHAUSTED` 或用户已取消 | 不继续原任务；新工作必须显式 `$loop-engine` 启动 |

显式触发始终可用于消除歧义，但不因此绕过当前合同或 Gate。隐式准入失败时，Adapter
不得把用户消息静默解释为新任务，也不得仅凭主题相似度采用旧 Run。

## 6. Run 创建前的自然语言批准

Pending Draft 阶段允许自然语言回复，但审批必须同时满足：

1. 当前对话只有一个匹配 Draft；
2. Adapter 已展示该 Draft 最新版本的完整 Ready-to-execute 摘要；
3. 当前单条回复对整份最新摘要表达无歧义批准；
4. 回复没有附加会改变范围、权限、风险、预算或实现决策的新条件。

“确认”“同意”“继续”“按此执行”等可以表达批准，但它们只是语义示例，不是新的固定
口令。`$loop-engine confirm` 不再是必需格式。问题、局部选择、条件性答复、对旧版本的
引用、无关消息和多条零散回答都不能被拼接成合同批准；Adapter 应继续澄清且不记录
approval。合同修订批准遵循相同规则。

用户在 Pending Draft 阶段自然语言取消时，Adapter 关闭当前对话中的 Draft 绑定；后续
普通消息不得重新采用它。新任务必须重新显式启动。

## 7. 默认 Goal 创建与账本绑定

每个新批准的 Codex Loop 任务都默认建立 Goal 绑定，不再要求单独 opt-in。该任务自己的
Loop Contract 必须在批准前精确披露：

```text
codex-goal:create:<resolved-absolute-run-directory>
codex-goal:complete:<resolved-absolute-run-directory>
```

两项都使用 `platform_state` ActionKind。创建顺序固定为：

1. 从已批准 Draft 创建 Run，并记录绑定当前合同版本、SHA-256 与全部风险 ID 的
   `contract_approval`；
2. 调用 `get_goal`；若存在无关活动 Goal，硬暂停且不替换、不接管；
3. 对精确的 Goal create 目标执行 `gate check`；
4. 记录包含 objective SHA-256 的创建 intent；
5. 调用 `create_goal`；只有用户明确给出 Token 数值时才传 `token_budget`；
6. 观察真实 Goal 后记录 result，形成 Goal/Run 持久绑定。

规范 objective 为：

```text
$loop-engine goal-bridge/v1
loop_id: <loop-id>
run_dir: <resolved-absolute-run-directory>
```

合同版本不写入 objective。合同修订继续使用同一个 Run；每次续跑都从账本读取当前合同
版本和批准状态。只有工具真实返回 Goal 标识时才记录它，Adapter 不推测宿主 Goal ID。

如果 Goal 工具不可用、存在无关 Goal 或创建结果无法核实，Run 硬暂停且不能获得隐式
续跑资格。用户仍可用显式 `$loop-engine` 进入保守的手动续跑；Adapter 不把缺失的 Goal
替换成“最新 Run”猜测。

## 8. 跨 turn 续跑算法

每个隐式 continuation 都必须从真实状态重新验证，不依赖模型记忆：

1. 调用 `get_goal` 并严格解析规范 objective；
2. 解析并边界检查绝对 `run_dir`，核对 `loop_id`；
3. 从 `run events` 验证 Goal 创建成功绑定，或对账中断的创建 intent；
4. 从 `run status` 读取状态、合同授权、批准和未决 intents；
5. 先核对所有未决外部副作用，禁止盲目重试；
6. 检查 Loop 工程预算；
7. 将当前自然语言输入只应用于这个 Run，并为下一最小动作执行正常 Gate/Maker Loop。

中断发生在 Goal 创建 intent 与 result 之间时，恢复流程先用 `get_goal` 对比 objective。
完全匹配才补记成功 result；不匹配或无法证明时暂停，不能再次创建 Goal。

Goal 自动 continuation 本身不能构成用户批准。只有来自用户、满足第 6 节完整性规则的
自然语言回复才能记录 approval。

## 9. 暂停、取消与终态

| Loop/Adapter 状态 | 隐式续跑行为 | Goal 行为 |
|---|---|---|
| 可执行非终态 | 继续 Maker Loop | 保持活动 |
| 等待用户澄清或批准 | 停止自动动作；接受已绑定任务的自然语言回复 | 保持活动 |
| 普通 `PAUSED` | 仅在回复明确处理暂停原因时恢复 | 保持活动 |
| 用户取消 | 以稳定的 `user_cancelled:` 原因进入/保持 `PAUSED`，关闭隐式绑定 | 不伪造完成或 blocked |
| `BLOCKED` / `BUDGET_EXHAUSTED` | 原 Run 不可隐式继续；需要显式启动符合 Core 规则的后续任务 | 保持未完成 |
| `DONE` | 不再执行原 Run | 完成精确 Gate 后标记 Goal complete |

用户取消是 Adapter 的持久关闭边界，不新增 Core `CANCELLED` 状态，也不滥用 `BLOCKED`
或 `DONE`。取消后的普通消息不能恢复原 Run；后续工作需要新的显式 `$loop-engine`。

`run complete` 必须先权威成功。随后 Adapter 对精确 Goal complete 目标执行 Gate，记录
intent，调用 `update_goal complete` 并记录真实 result。更新失败不改变 Loop 的 `DONE`，
只能报告为 Adapter 清理失败。

## 10. 双预算边界

- Goal Token 预算是宿主续跑的外层上限。
- Loop `max_iterations`、`max_minutes` 和 `max_checker_revisions` 是工程执行上限。
- 两者不换算、不自动扩展，也不互相授予权限。
- Goal 预算先耗尽时，Loop 账本保持可恢复；Loop 预算先耗尽时，不把 Goal 标为完成。

## 11. Gate 与安全语义

`platform_state` 是通用 ActionKind，不包含 Codex 专有字段。它属于必须精确披露的外部
平台状态修改：

- 精确目标和当前合同授权匹配时才允许；
- Autonomous 0.2.0 缺少目标时要求 `contract_revision`；
- 当前合同批准缺失或过期时要求 `contract_approval`；
- Collaborative 沿用现有危险操作门语义；
- 永久禁止项和其他 ActionKind 的判定顺序不变。

Goal objective 只是定位信息，不是权限令牌。任何 objective、路径、合同授权、账本绑定
或真实状态不一致都必须停止。Adapter 不扫描最新 Run、不按时间排序、不从多个候选中
猜测，也不让自然语言批准扩张合同。

## 12. 生命周期元数据

`adapters/codex/agents/openai.yaml` 必须设置：

```yaml
policy:
  allow_implicit_invocation: true
```

生命周期管理器把该精确值作为托管 Skill 标记的一部分：缺失、为 `false` 或结构异常都
应拒绝安装/卸载校验。这样“宿主可隐式选择”和“Adapter 仅接受唯一绑定任务”组成一个
不可拆分的安全边界。

## 13. 测试策略

仓库测试不创建真实 Codex Goal，而是验证可执行的 Adapter 合同和通用 Gate：

1. Adapter 静态合同测试锁定“仅新任务显式启动”、Pending Draft/Goal 双绑定、自然语言
   批准规则、取消边界与终态行为；
2. 静态测试证明不再要求固定 `$loop-engine confirm`，且隐式准入失败不能 Intake、采用
   或修改任何 Run；
3. 生命周期测试要求 `allow_implicit_invocation: true`，并拒绝缺失、`false` 或异常值；
4. Policy 测试继续证明 `platform_state` 精确授权可通过，缺失、变更和过期授权会暂停；
5. 全量测试、Ruff、`git diff --check` 和文档 EOF 检查作为最终质量门。

真实宿主调度验证只能在用户更新托管 Skill 并启动新 Codex 会话后进行，不能由仓库
单元测试伪造。

## 14. 最小实施顺序

1. 先修改 Adapter 与生命周期测试并确认新断言 RED；
2. 将宿主元数据和管理器标记切换为隐式可选；
3. 重写 Codex Skill 的启动、绑定、自然语言批准、默认 Goal、取消和终态规则；
4. 统一 ADR、Context、README 与接入指南；
5. 执行定向、全量、Ruff、diff 与 EOF 验证；
6. 由独立 Checker 复核合同、实际 diff 与原始证据。

## 15. 验收不变量

1. 没有显式 `$loop-engine` 就不能开始或采用新任务。
2. 隐式 turn 只能命中当前对话唯一 Pending Draft，或唯一 Goal/账本绑定的活动 Run。
3. 自然语言批准只绑定最新完整合同摘要，不能由片段、问题或旧回复拼接产生。
4. Goal 不能绕过合同批准、Gate、预算、证据、Checker 或 `DONE`。
5. 取消和任一终态都会关闭原任务的隐式续跑；新工作必须显式启动。
6. Core 不包含 Codex 专有模型、对话身份或调度流程。
