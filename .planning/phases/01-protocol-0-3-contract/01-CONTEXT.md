# Phase 1: Protocol 0.3 Contract - Context

**Gathered:** 2026-07-31
**Status:** Ready for planning
**Mode:** Auto-generated (pure infrastructure phase)

<domain>
## Phase Boundary

建立取代旧局部设计的 Core Protocol 0.3.0 合同语义：新合同只允许 Autonomous，旧 0.1.0/0.2.0 仅在明确为 Autonomous 时可读取，所有 collaborative 合同与 Run 均被确定性拒绝，同时保留批准绑定、风险、Checker、证据、预算和永久禁止项。

</domain>

<decisions>
## Implementation Decisions

### the agent's Discretion
- 旧 0.1.0/0.2.0 合同若省略 `mode` 必须拒绝，因为其历史缺省语义是 collaborative；只有 0.3.0 可以省略并解析为 Autonomous，避免静默权限升级。
- 使用现有严格 Pydantic 模型和版本分支扩展 0.3.0，不引入平行合同模型或迁移层。
- 0.3.0 沿用 0.2.0 的完整风险披露、合同哈希与风险 ID 绑定语义；0.1.0 Autonomous 继续保留旧高风险最终验收规则。
- 新建 0.3.0 设计文档取代冲突决策，保留历史设计文件作为决策记录，不改写其原始内容。

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/loop_engineering/models/contract.py` 集中定义严格合同、控制模式、版本和风险校验。
- `src/loop_engineering/contract.py` 已提供确定性 JSON Schema 导出。
- `src/loop_engineering/ledger.py` 已实现合同批准指纹与风险 ID 的账本绑定。
- `tests/factories.py`、`tests/test_contract.py`、`tests/test_ledger.py` 和 `tests/test_policy.py` 提供现有 0.1/0.2 兼容及安全门禁测试模式。

### Established Patterns
- 所有模型继承 `StrictModel` 并拒绝额外字段。
- 协议差异在合同版本上显式分支，不从项目或对话隐式继承模式。
- Schema 由 Pydantic 模型生成并以排序 JSON 确定性落盘。
- 风险授权通过 `contract_version`、规范化 SHA-256 与完整 `accepted_risk_ids` 绑定。

### Integration Points
- `templates/contract.yaml`、`templates/project.yaml` 与 `schemas/loop-contract.schema.json` 必须随模型同步。
- `RunStore.open` 通过 `LoopContract.model_validate` 成为拒绝旧 collaborative Run 的统一入口。
- `GatePolicy`、`RunStore.current_contract_authorization` 和 `DoneEvaluator` 共同保持 0.2/0.3 Autonomous 与 0.1 legacy 门禁语义。

</code_context>

<specifics>
## Specific Ideas

不增加 collaborative 迁移、恢复或兼容别名；不削弱任何安全 Gate；所有生产代码变更严格执行测试先行。

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

