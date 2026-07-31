# Codex Adapter 默认 Autonomous 设计

- 状态：用户已批准
- 日期：2026-07-31
- 适用范围：Codex Adapter 新任务的模式解析
- 协议基线：Loop Engineering Core Protocol 0.2.0

## 1. 背景与目标

当前 Codex Adapter 在用户未显式指定控制模式时选择 `collaborative`。本变更将
Adapter 的缺省选择改为 `autonomous`，使新发起的状态变更任务在一次完整 Loop
Contract 批准后持续执行到终态、契约修订或平台硬门。

该目标只改变 Codex Adapter 的任务准入行为，不改变 Core 对缺少 `mode` 字段的
合同解析语义。所有由 Adapter 起草的新合同仍必须显式写入解析后的模式。

## 2. 决策

模式解析顺序调整为：

1. 用户显式指定 `collaborative` 或 `autonomous` 时采用该值。
2. 用户未指定时，Codex Adapter 采用 `autonomous`。
3. Adapter 在完整执行合同摘要中披露解析结果，并在任何状态修改前获得一次明确批准。
4. 模式不从上一个任务继承。

Core 的 `LoopContract.mode`、通用合同模板和 JSON Schema 默认值继续保持
`collaborative`。因此，绕过 Adapter 创建且省略 `mode` 的合同、旧工具调用以及兼容
读取路径不会被静默升级为 Autonomous。

## 3. 方案边界

### 3.1 Codex Adapter

更新 `adapters/codex/SKILL.md` 的 Intake、审批快速参考和常见错误说明，使所有
面向 Codex 的缺省模式描述一致指向 `autonomous`。显式模式优先、一次完整合同批准、
精确风险绑定、范围修订和平台硬门保持不变。

### 3.2 Core 与协议

以下内容不变：

- `PROTOCOL.md` 对通用缺省合同的 `collaborative` 语义。
- `LoopContract` Pydantic 模型的默认值。
- `templates/contract.yaml` 和生成的 JSON Schema 默认值。
- `0.1.0` 兼容语义和现有运行合同。
- Checker、预算、最终状态和永久禁止操作。

### 3.3 文档决策优先级

本文取代以下旧设计中“Codex Adapter 在模式省略时选择 `collaborative`”的局部决策：

- `2026-07-30-loop-engineering-protocol-design.md` 的 Adapter 模式解析说明。
- `2026-07-31-single-execution-approval-design.md` 的默认模式说明与相关非目标。

旧文档保留历史背景，并增加指向本文的取代说明；其他已批准决策继续有效。

## 4. 执行数据流

```text
用户发起状态变更任务
  -> Codex Adapter 检查是否显式指定模式
      -> 已指定：使用显式值
      -> 未指定：使用 autonomous
  -> 起草包含显式 mode 的 Loop Contract
  -> 展示范围、验收、风险、权限、Git 目标和预算
  -> 用户批准当前版本、哈希和风险 ID
  -> 在批准范围内执行；新增目标、权限或风险时修订合同
```

Core 单独加载一个缺少 `mode` 的合同仍得到 `collaborative`，该路径不经过上述
Adapter 缺省解析。

## 5. 安全与错误处理

- Autonomous 仍然必须在执行前取得完整合同批准；默认值不等于免审批。
- 危险、生产、敏感数据和 Git 写操作仍需精确目标、完整风险披露及匹配权限。
- 新操作、目标、权限或风险进入 `contract_revision`，不能由默认模式隐式吸收。
- 强推、历史改写、`reset --hard`、自动合并和自动部署继续永久拒绝。
- 平台沙箱、操作系统权限和外部服务审批不受 Adapter 默认值影响。
- 用户随时可以显式选择或降级到 `collaborative`。

## 6. 兼容性

该变更不修改合同 Schema 或协议版本，因为每份新 Adapter 合同仍显式携带 `mode`，
Core 数据格式和解析结果没有变化。现有合同、运行账本和第三方 Adapter 不迁移。

托管安装目录不会由本仓库任务直接更新。用户发布或更新 Skill 后，需要启动新的
Codex 会话才能使用新的 Adapter 默认行为。

## 7. 测试策略

采用测试先行：

1. Adapter 契约测试先断言模式省略时必须选择 `autonomous`，并拒绝旧的
   `collaborative` 缺省措辞。
2. Adapter 测试确认显式两种模式仍然优先，并确认本文作为最新决策存在。
3. Core 合同测试继续断言缺少 `mode` 时解析为 `collaborative`。
4. 项目配置测试继续断言初始化配置不引入 `mode` 或 `default_mode`。
5. 运行定向测试、完整测试、Ruff 和 `git diff --check`。

## 8. 未采用方案

### 协议级全局默认 Autonomous

拒绝。它会让缺少 `mode` 的旧合同改变含义，属于安全相关的破坏性兼容变更，需要
新协议版本和迁移机制，超出当前需求。

### 项目级 `default_mode` 配置

暂不实现。它能提供更细粒度控制，但会增加配置模型、模板、迁移和优先级规则；当前
需求只要求 Codex Skill 采用一个明确默认值。

## 9. 验收标准

1. Codex Adapter 未收到显式模式时选择 `autonomous`。
2. 显式 `collaborative` 或 `autonomous` 始终覆盖缺省值。
3. Adapter 起草的合同继续显式包含解析后的模式。
4. Core、通用模板和 Schema 的缺省值继续是 `collaborative`。
5. 风险授权、Checker、平台门禁和永久拒绝规则没有被削弱。
6. 文档与自动化测试能够明确区分 Adapter 默认值和 Core 兼容默认值。
