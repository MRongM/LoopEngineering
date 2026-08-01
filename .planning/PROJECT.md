# Loop Engineering

## What This Is

Loop Engineering 是面向编码 Agent 的证据门控、可恢复执行协议与工具集。它使用严格
合同、追加式账本、风险门禁、新鲜验证证据和独立 Checker，约束 Agent 在明确范围内
持续执行，并以可审计事实而不是自然语言声明判定完成。

当前工作把执行闭合语义定义为首个公开版本 `0.1.0`。项目不承诺或实现任何更早协议
版本的读取、升级、降级或迁移。

## Core Value

Agent 只能在明确批准且可验证的范围内自主执行，并且只有真实证据满足合同后才能完成。

## Active Requirements

- Core、Schema、模板、CLI、Adapter 与发布文档只接受/生成 Protocol `0.1.0`。
- 唯一控制模式是 `autonomous`；每个新任务形成一个执行闭合合同。
- 完整合同摘要只取得一次 `contract_approval`，绑定合同哈希与完整风险 ID。
- 批准后在合同边界内不中断执行；只有合同修订、外部强制门、未决 intent、取消或权威
  终态可以暂停。
- 所有验证在 `.loop-engine/cache/` 的一次性 Git 快照中运行，源工作区污染使证据失败。
- 项目只使用 `.loop-engine/` 一个 Loop-owned 顶层目录；只有 `project.yaml` 和内部
  `.gitignore` 可跟踪。
- 安装目录、Codex Skill 触发词与 Shell CLI 均使用 `loop-engine`；Python 分发包保持
  `loop-engineering`。
- 活跃时间预算排除等待批准与暂停时长；启动失败和 timeout 必须关闭对应 intent。

## Out of Scope

- 任何协议版本兼容层或自动迁移。
- scheduler、daemon、自动合并、自动部署、强推、历史改写或生产环境隐式权限。
- 把 Codex 专有模型引入 Core。
- 提交运行时数据、秘密、Token 或完整模型推理。

## Constraints

- Python 3.12+、strict Pydantic models、argv subprocesses 与 `shell=False`。
- 生产代码前先保留失败测试证据；不得弱化测试、Gate 或 Schema。
- 每个外部状态变更都必须先记录 intent，再记录真实 result。
- Core 保持工具无关；Codex 行为位于 `adapters/codex/`。
- 不得自动移动或删除冲突的项目控制数据。

## Current Decision

执行闭合合同是首版的根不变量：设计决定、最小动作计划、验证、预算、权限与风险必须在
批准前形成可执行闭包。经用户明确确认，预发布规划、设计和兼容性记录已经移除；当前
仓库只保留首版 `0.1.0` 的产品定义与验证事实。

---
*Last updated: 2026-08-01 during execution-convergence debug workflow*
