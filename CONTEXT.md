# Loop Engineering

Loop Engineering 定义证据门控的软件工程执行闭环，以及用户、Adapter 与 Core 之间的授权边界。

## Language

**手动触发（Manual Invocation）**：
仅当用户在当前消息中显式写出 `$loop-engine` 时，才允许开始新的 Loop 任务。已唯一绑定的同一任务可以在后续 turn 中用自然语言继续；语义相似或历史消息不能创建、采用或替换任务。
_Avoid_：隐式新建、推断采用、按主题恢复

**Skill 激活（Skill Activation）**：
Codex 宿主可以隐式选择 Loop Engineering Skill，但选择资格不构成 Intake、审批或修改授权。Adapter 只有在当前对话存在唯一 Pending Draft，或当前 Goal 与追加式账本共同绑定唯一活动 Run 时，才允许自然语言续跑。
_Avoid_：宿主选择等于授权、扫描最新 Run、多候选猜测

**Skill 触发词（Skill Trigger）**：
用户手动激活 Codex Adapter 时使用的唯一入口 `$loop-engine`；旧入口不保留兼容别名。它不改变产品名 `Loop Engineering`、CLI 命令 `loop-engineering` 或协议名称。
_Avoid_：`$loop-engineering`、`$loop`

**任务级续跑（Task-scoped Continuation）**：
从显式启动创建的唯一 Pending Draft，到合同批准后默认创建并与账本绑定的 Goal/Run，构成一个任务的连续身份。澄清、完整摘要批准、修订、继续、暂停恢复、取消和反馈可以自然语言表达；绑定缺失、歧义、取消或终态会关闭隐式续跑。
_Avoid_：逐 turn 口令、固定 confirm 子命令、终态复活

**Goal 绑定续跑（Goal-bound Continuation）**：
Codex 宿主根据以 `$loop-engine goal-bridge/v1` 开头的 Goal objective 继续一个已批准 Run；每次续跑都必须用 `get_goal` 和运行账本重新验证同一个绝对运行目录。Goal 只是调度指针，不授予权限、预算或完成结论。
_Avoid_：可选 Goal、接管无关 Goal、Goal 作为合同批准

**控制模式（Control Mode）**：
Skill 激活后的执行方式，取值为 `autonomous` 或 `collaborative`。未显式指定时采用 `autonomous`，用户的显式选择始终优先；控制模式不决定 Skill 是否激活。
_Avoid_：触发模式、激活模式
