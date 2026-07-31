# Loop Engineering 0.3 Autonomous-only 设计

- 状态：已批准（用户授权自主决策）
- 日期：2026-07-31
- 适用范围：Core Protocol、合同模型、模板、Schema 与兼容读取
- 协议版本：0.3.0

## 1. 目标

Loop Engineering 0.3 移除 `collaborative` 控制模式。Core、Adapter 和 Skill 只运行
`autonomous`：一次完整 Loop Contract 获批后，在合同边界、风险授权、预算和平台硬门
内持续设计、计划、执行、验证、检查与决策。

本设计取代既有设计中关于 Core 或 Codex Adapter 保留 `collaborative`、默认
`collaborative` 或允许用户选择 `collaborative` 的局部决策。历史文档保留作为审计记录。

## 2. 合同语义

- 新合同使用 `protocol_version: 0.3.0`。
- 0.3.0 省略 `mode` 时解析为 `autonomous`；模板仍显式写出该值。
- 任何受支持协议版本显式提供 `mode: collaborative` 都必须确定性拒绝。
- 0.1.0/0.2.0 合同只有显式提供 `mode: autonomous` 才可兼容读取。
- 旧合同省略 `mode` 必须拒绝，因为其历史默认值为 `collaborative`；不得把省略字段
  静默解释为更高权限的 Autonomous。
- 不提供 collaborative 合同或 Run 的迁移、恢复、兼容开关或别名。

## 3. 授权与安全

0.3.0 沿用 0.2.0 的完整风险披露和绑定批准语义。合同批准必须绑定当前
`protocol_version`、`contract_version`、规范化合同 SHA-256 和完整风险 ID 集合；绑定
过期、缺失或不匹配时没有执行权限。

0.1.0 显式 Autonomous 合同保留原始规则，包括高风险最终验收门。0.2.0 与 0.3.0
显式 Autonomous 合同使用同一风险授权规则。Checker、证据新鲜度、预算、范围边界、
中断意图对账以及永久禁止的强推、历史改写、自动合并和自动部署均不变。

## 4. Schema 与项目配置

Pydantic 模型是合同 Schema 的唯一事实来源。生成的 JSON Schema 必须表达：

- 协议默认值为 `0.3.0`，并接受 0.1.0、0.2.0、0.3.0；
- `mode` 只有 `autonomous`，默认值也是 `autonomous`；
- 对 0.1.0/0.2.0 使用条件约束要求 `mode` 字段显式存在。

新项目的协议约束为 `>=0.3,<0.4`。现有 `>=0.2,<0.3` 项目配置仍可读取，以便显式
Autonomous 的 0.2 运行完成兼容检查；初始化不会把旧配置自动改写。

## 5. 生命周期与兼容边界

0.3 新建运行只允许 Autonomous。打开历史 Run 时必须重新验证其合同；任何
collaborative 或省略模式的旧 Run 都拒绝，不创建隐式子 Run，也不改写账本。
从 0.1/0.2 升级到 0.3 必须创建新合同版本并重新取得完整绑定批准。协议降级始终拒绝。

CLI 可执行入口统一为 `loop-engine`，Python 分发包、产品名、仓库名和 `$loop-engine`
Skill 触发词保持不变；该入口变更由后续生命周期阶段实现。

## 6. 验证策略

先用失败测试固定 0.3 默认值、所有版本的 collaborative 拒绝、旧版本省略模式拒绝、
显式旧 Autonomous 兼容、项目约束和 Schema 条件，再实现最小模型变更。随后验证
风险绑定、策略门、历史 Run、模板、生成 Schema、完整测试和静态检查，且不通过删除、
跳过或放宽安全断言获得通过。
