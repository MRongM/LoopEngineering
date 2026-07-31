# Autonomous 单次风险接受设计

- 状态：用户已批准
- 日期：2026-07-31
- 目标版本：Loop Engineering Core Protocol 0.2.0
- 适用范围：Core、Codex Adapter、新建 `0.2.0` 契约

## 1. 问题

`0.1.0` 在 Autonomous 中仍会为生产访问、敏感数据、未单独批准的危险操作和
高风险最终验收暂停。用户虽然已经批准完整 Loop Contract，运行期仍会重复请求
语义相同的风险确认。审批事件也只记录门名和布尔值，无法证明用户接受的是哪一版
契约及哪些风险。

## 2. 决策

Autonomous `0.2.0` 使用一次性风险接受：执行前的完整契约摘要同时承担范围授权和
风险接受。批准后，契约内精确列明的高风险、生产和敏感数据操作不再触发人工门，
并持续运行到终态、契约变更或平台硬性门。

这不是全局的 `accept_all_high_risk` 开关。授权严格绑定当前契约版本、规范化摘要和
风险项 ID；任何新目标、新权限或新风险都必须形成新契约版本，再进行一次完整确认。

## 3. 保留的边界

- 强推、历史改写、`reset --hard`、自动合并和自动部署永久拒绝。
- Medium/High 继续要求独立 Checker `ACCEPT`；Checker 不属于人工确认。
- Collaborative 保留运行期危险操作门和最终人工验收。
- 用户或项目显式声明的额外人工门继续生效。
- 平台沙箱、操作系统权限和外部服务自身的强制审批不能由 Loop 绕过。
- 未列明或不能解析到精确目标的操作不能获得一次性授权。
- 数据库操作仍必须提供前向方案、兼容性分析和恢复方案。

## 4. 协议版本与兼容性

此变更改变安全门语义，因此协议升级为 `0.2.0`。Core 同时读取 `0.1.0` 和
`0.2.0` 契约：

- 新模板、项目配置和 Codex Adapter 生成 `0.2.0` 契约。
- `0.1.0` 契约保持原行为：生产/敏感操作始终暂停，高风险 Autonomous 仍要求最终验收。
- 运行中的 `0.1.0` 契约不得静默升级；升级必须创建显式的 `0.2.0` 契约版本并重新批准。
- `0.2.0` Codex Adapter 只声明兼容 `>=0.2,<0.3`，避免用新交互驱动旧 Core。

## 5. 风险授权数据

### 5.1 精确操作

`AuthorizedOperation` 在 `0.2.0` 中必须包含：

| 字段 | 含义 |
|---|---|
| `risk_id` | 契约内唯一的 `RISK-*` 标识 |
| `kind` | 与 `ActionKind` 对应的操作类型 |
| `repository_id` | 可选的精确仓库 ID |
| `target` | 精确目标，不接受宽泛 glob 或未解析变量 |
| `risk_level` | `low`、`medium` 或 `high` |
| `impact` | 预期状态变化 |
| `worst_case` | 可向用户说明的最坏结果 |
| `recovery` | 回滚、前向修复或补救方式 |
| `evidence` | 为什么执行该操作 |

`0.1.0` 继续接受原来的 `kind/repository_id/target` 结构。`0.2.0` 的生产访问和
敏感数据操作必须标为 `high`，并同时启用对应权限。风险 ID 必须唯一，契约总体
风险不得低于任一操作风险。高风险 Autonomous 至少包含一条高风险披露；所有计划内
危险、生产、敏感数据和 Git 写操作必须在首次确认前列入风险表。

### 5.2 审批绑定

批准 `contract_approval` 或 `contract_revision` 时，账本自动记录：

```json
{
  "gate": "contract_approval",
  "approved": true,
  "protocol_version": "0.2.0",
  "contract_version": 1,
  "contract_sha256": "<canonical-contract-sha256>",
  "accepted_risk_ids": ["RISK-1"]
}
```

摘要使用契约模型的 JSON 表示、稳定键排序和固定分隔符计算。Gate 只信任当前运行
账本中与当前版本、摘要和风险 ID 同时匹配的批准，不能只信任任意磁盘上的契约文件。

## 6. Gate 判定

按以下顺序判定：

1. 永久禁止操作直接 `DENY`。
2. 对 Autonomous `0.2.0`，任何操作都必须先证明当前运行存在匹配的契约批准。
3. 校验文件边界、Git 精确目标和类别权限。
4. 对 Autonomous `0.2.0`：
   - 普通操作必须位于批准的仓库路径内；危险操作必须精确匹配已接受风险项才 `ALLOW`；
   - 生产和敏感数据也遵循同一规则，不再创建 `dangerous_action` 门；
   - 操作未列明、目标不匹配或新增权限时 `PAUSE`，要求 `contract_revision`；
   - 契约精确但批准缺失或过期时 `PAUSE`，要求 `contract_approval`。
5. Collaborative 和 `0.1.0` 继续使用原有危险操作人工门。

`GateDecision` 明确返回 `required_gate`。CLI 只有在
`required_gate=dangerous_action` 时生成逐操作确认文本；`contract_approval` 和
`contract_revision` 由 Adapter 汇总成完整契约确认，避免重复风险弹窗。

## 7. CLI 与运行流程

`gate check` 的第一个参数接受运行目录或旧式契约文件：

- 运行目录：读取持久化契约和当前版本账本授权，是 `0.2.0` 的标准调用方式。
- 契约文件：保留 `0.1.0` 兼容；对需要一次性授权的 `0.2.0` 操作无法证明批准，返回暂停。

Codex Adapter 在执行前展示一个风险表，至少包含风险 ID、操作、精确目标、影响、
最坏结果和恢复方式。用户一次确认后创建运行并记录绑定审批。执行期间：

- `allow`：记录 intent，执行并记录 result。
- `contract_revision`：把新增风险写入完整新契约，只请求一次修订确认。
- `dangerous_action`：只用于 Collaborative 或 `0.1.0` 兼容流程。
- `deny`：停止该操作，不请求能够覆盖永久禁止项的批准。

## 8. 完成语义

- Autonomous `0.2.0` 不因风险等级自动添加 `final_acceptance`。
- Collaborative `0.2.0` 仍必须包含 `final_acceptance`。
- 显式写入 Autonomous 契约的 `final_acceptance` 仍会生效。
- `0.1.0` 高风险 Autonomous 保持强制最终验收。
- 所有版本的 Medium/High 都必须获得独立 Checker `ACCEPT`。

## 9. 错误处理

- `0.2.0` 风险字段缺失、风险 ID 重复或生产/敏感风险不是 `high`：契约校验失败。
- 契约内容或版本变化导致摘要不匹配：旧批准失效。
- 批准事件缺少绑定字段：不能授权任何 `0.2.0` Autonomous 操作。
- 高风险 Autonomous 风险表为空或总体风险低报：契约校验失败。
- 新操作没有精确目标：不得写入授权列表，保持暂停。
- 不可恢复操作必须如实说明恢复限制；不能用空泛的恢复文本绕过校验。

## 10. 验收标准

1. 一个 Autonomous `0.2.0` 契约可在一次批准中接受多个已披露风险。
2. 所有 Autonomous 操作都必须证明当前契约已经绑定批准。
3. 精确批准的生产和敏感数据操作通过 Gate 时不再请求人工确认。
4. 精确批准的高风险 Autonomous 可在 Checker 接受后无最终人工门进入 `DONE`。
5. 新目标、权限、风险或过期批准只能通过新契约版本恢复执行。
6. Collaborative 与 `0.1.0` 的现有门禁行为保持兼容。
7. 永久禁止操作在所有模式和版本中继续 `DENY`。
8. Schema、模板、协议、Skill、CLI 和测试对 `0.2.0` 语义一致。
