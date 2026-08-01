# Requirements: Loop Engineering 0.1.0

**Defined:** 2026-08-01
**Core Value:** Agent 只能在明确批准且可验证的范围内自主执行，并且只有真实证据满足
合同后才能完成。

## First-release requirements

### Contract and authorization

- [x] **CORE-01**: Core、Python 包、Schema、模板和 Adapter 只接受或生成 `0.1.0`。
- [x] **CORE-02**: `autonomous` 是唯一控制模式。
- [x] **CORE-03**: 合同必须包含设计决定与完整最小动作计划，并在准入时通过真实 Gate
  预检。
- [x] **CORE-04**: 一次完整合同批准绑定协议、合同版本、规范化 SHA-256 和全部风险 ID。
- [x] **CORE-05**: 新目标、动作、权限、风险、预算或交付边界必须形成完整合同修订。

### Runtime closure

- [x] **RUN-01**: 目标项目只创建 `.loop-engine/` 一个 Loop-owned 顶层目录。
- [x] **RUN-02**: Run、草稿、证据和缓存全部位于 `.loop-engine/`，控制路径不得通过
  symlink 或 junction 逃逸。
- [x] **RUN-03**: 每次外部状态变更都有匹配的 intent/result；未决 intent 调和前禁止
  下一动作。
- [x] **RUN-04**: 等待批准和暂停不消耗活跃时间预算。
- [x] **RUN-05**: 批准后在合同闭包内持续执行，只在合同修订、外部硬门、无法调和的
  intent、取消或权威终态暂停。

### Evidence and safety

- [x] **EVID-01**: 验证只在 `.loop-engine/cache/` 的一次性 Git 快照中运行。
- [x] **EVID-02**: timeout、启动失败、快照失败和源工作区变化都产生关闭的失败证据。
- [x] **SAFE-01**: 仓库及 worktree 使用解析后的绝对路径；动作同时匹配计划、范围、
  权限和精确风险授权。
- [x] **SAFE-02**: 强推、历史改写、reset-hard、自动合并和部署永久禁止。
- [x] **SAFE-03**: 所有子进程使用 argv、`shell=False` 和明确 timeout。

### Product surfaces

- [x] **NAME-01**: Python 分发包保持 `loop-engineering`。
- [x] **NAME-02**: Codex 托管安装目录、Skill 名和唯一 Agent Shell CLI 均为
  `loop-engine`。
- [x] **DOC-01**: README、接入指南、协议、发布身份和 Adapter 对首版语义一致。
- [x] **TEST-01**: 全量测试、Ruff、Schema 重建、构建和差异完整性检查全部通过。

## Out of scope

- 协议版本分支、旧合同读取、升级、降级或自动迁移。
- scheduler、daemon、自动合并、自动部署、强推或历史改写。
- 隐式生产环境或敏感数据权限。
- 将 Codex 专有状态引入 Core。

## Traceability

| Requirement group | Delivery | Status |
|---|---|---|
| CORE | Contract models, GatePolicy, ledger | Complete |
| RUN | Project layout, state machine, Adapter | Complete |
| EVID / SAFE | ValidationRunner, Git Shell, strict paths | Complete |
| NAME / DOC | Lifecycle manager and release documents | Complete |
| TEST | Regression, static, schema and package evidence | Complete |

---
*Last updated: 2026-08-01 after first-release convergence*
