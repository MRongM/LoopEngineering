# Loop Engineering

Loop Engineering 定义证据门控的软件工程执行闭环，以及用户、Adapter 与 Core 之间的授权边界。

## Language

**手动触发（Manual Invocation）**：
仅当用户在当前消息中显式写出 `$loop-engine` 时，才允许启动 Loop Engineering Skill。语义相似的任务、普通名称提及或历史消息中的调用都不构成触发。
_Avoid_：自动触发、推断触发、沿用触发

**Skill 激活（Skill Activation）**：
Codex 在当前用户消息对应的 turn 中装载 Loop Engineering Skill。每条需要运行或继续该 Skill 的用户消息都必须显式触发；宿主不提供跨 turn 的持久 Skill 激活。该限制不约束 CLI、Core、其他 Adapter 或已经取得合同授权的运行数据。
_Avoid_：CLI 启动、Core 启动、运行续执行

**Skill 触发词（Skill Trigger）**：
用户手动激活 Codex Adapter 时使用的唯一入口 `$loop-engine`；旧入口不保留兼容别名。它不改变产品名 `Loop Engineering`、CLI 命令 `loop-engineering` 或协议名称。
_Avoid_：`$loop-engineering`、`$loop`

**控制模式（Control Mode）**：
Skill 激活后的执行方式，取值为 `autonomous` 或 `collaborative`。未显式指定时采用 `autonomous`，用户的显式选择始终优先；控制模式不决定 Skill 是否激活。
_Avoid_：触发模式、激活模式

**Claude Code Skill 激活（Claude Code Skill Activation）**：
Claude Code 仅在当前用户消息显式调用 Loop Engineering Skill 时启动或继续流程。虽然已加载的 Skill 内容可能保留在会话上下文中，但该持久化不构成后续用户消息的执行授权。
_Avoid_：上下文仍存在、自动续用、模型推断续用

**Claude Code Skill 触发词（Claude Code Skill Trigger）**：
Claude Code Adapter 的规范入口为 `/loop-engineering:loop-engine`。宿主版本可能同时提供非命名空间别名 `/loop-engine`，但文档、审批恢复和跨版本交互统一使用规范入口。
_Avoid_：`$loop-engine`、语义触发、Hook 自动触发
