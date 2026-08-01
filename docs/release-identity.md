# Loop Engineering 0.1.0 首版身份与边界

本文只定义首个发布版本的名称和拒绝边界。协议语义以
[Core Protocol](../PROTOCOL.md) 和
[0.1 执行闭合设计](superpowers/specs/2026-08-01-loop-engineering-0.1-execution-closure-design.md)
为准。

## 名称边界

| 身份 | 名称 |
|------|------|
| 产品与仓库 | Loop Engineering |
| Python 分发包 | `loop-engineering` |
| Codex 托管 checkout 目录 | `loop-engine` |
| Codex Skill 触发词 | `$loop-engine` |
| 唯一 Shell CLI | `loop-engine` |
| 项目控制目录 | `.loop-engine/` |

Python 分发包名不等于可执行命令。生命周期管理器按分发包名安装和卸载，但只验证
`loop-engine` executable，并且只管理 `<CODEX_HOME>/skills/loop-engine`。

## 首版协议边界

Core 只接受 `protocol_version: 0.1.0`、`mode: autonomous`、闭合
`execution_plan`、隔离验证和唯一 `contract_approval`。任何其他协议版本、控制模式、
缺失闭合计划或缺失隔离策略都会在模型边界确定性拒绝。

这是第一个版本，不存在旧协议读取器、版本兼容矩阵、升级/降级逻辑或自动迁移。
项目初始化只创建 `.loop-engine/`；遇到其他 Loop-owned 顶层目录时失败关闭，并保留
原始数据等待用户自行处理。

## 仓库记录

经用户明确确认，预发布规划、设计和兼容性材料已经移除。`.planning/` 只保存当前
首版项目状态与执行闭合诊断证据；`docs/superpowers/` 只保存当前 `0.1` 执行闭合设计。
