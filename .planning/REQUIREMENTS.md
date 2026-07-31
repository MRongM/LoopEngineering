# Requirements: Loop Engineering

**Defined:** 2026-07-31
**Core Value:** Agent 只能在明确批准且可验证的范围内自主执行，并且只有真实证据满足合同后才能完成。

## v1 Requirements

### Core Protocol

- [ ] **CORE-01**: Core Protocol 与 Python 包版本均为 `0.3.0`
- [ ] **CORE-02**: `autonomous` 是唯一控制模式，合同省略 `mode` 时自动使用该模式
- [ ] **CORE-03**: 任何协议版本的合同显式填写 `collaborative` 都会校验失败
- [ ] **CORE-04**: Adapter 不再提供模式选择、降级或 collaborative 专属流程
- [ ] **CORE-05**: 0.3.0 明确拒绝旧 collaborative 合同与 Run，不执行静默转换或恢复
- [ ] **CORE-06**: 旧 0.1.0/0.2.0 autonomous 合同仍可读取，并保留其原有风险与最终门禁语义

### Autonomous Skill

- [ ] **AUTO-01**: `$loop-engine` 启动的所有新任务均为 Autonomous，不询问或展示模式选择
- [ ] **AUTO-02**: 一次完整合同批准后，Skill 自主完成设计、计划、执行、验证、Checker、修正和决策循环
- [ ] **AUTO-03**: Skill 根据测试、命令反馈和 Checker 结论自主选择下一最小动作
- [ ] **AUTO-04**: Skill 仅在合同扩展、批准失效、平台或外部硬门、预算终止、缺少必要权限或输入以及用户取消时暂停
- [ ] **AUTO-05**: 跨 turn 续跑重新验证 Goal、Run、账本、授权、预算和未决 intent，不依赖对话记忆或猜测最新 Run

### CLI and Lifecycle

- [ ] **CLI-01**: Agent Shell CLI 的唯一入口是 `loop-engine`，并完整提供现有命令组
- [ ] **CLI-02**: 包不注册 `loop-engineering` 或 `loop-agent` CLI 别名
- [ ] **CLI-03**: Adapter、README、接入指南、示例和测试中的执行命令全部使用 `loop-engine`
- [ ] **LIFE-01**: 生命周期管理器继续管理 Python 包 `loop-engineering`，并正确安装、验证和移除 `loop-engine` 可执行入口
- [ ] **NAME-01**: 产品名、Python 包名和仓库名保持 Loop Engineering / `loop-engineering`，Codex Skill 触发词保持 `$loop-engine`

### Safety and Verification

- [ ] **SAFE-01**: 一次批准继续绑定合同版本、规范化 SHA-256 和完整风险 ID
- [ ] **SAFE-02**: 精确风险授权、Checker、证据新鲜度、范围检查和预算在 Autonomous-only 模式下继续生效
- [ ] **SAFE-03**: 强推、历史改写、`reset --hard`、自动合并和自动部署继续永久禁止
- [ ] **TEST-01**: 模型、通用模板和生成 JSON Schema 一致且可以确定性重建
- [ ] **TEST-02**: 协议、CLI、生命周期、Adapter 合同、全量测试、Ruff、构建和 `git diff --check` 全部通过

## v2 Requirements

None. 当前里程碑只交付上述 Autonomous-only 0.3.0 能力。

## Out of Scope

| Feature | Reason |
|---------|--------|
| collaborative 控制模式 | 用户明确要求从新版 Core 与 Adapter 中彻底移除 |
| collaborative 合同或 Run 自动迁移 | 静默转换会伪造授权语义；0.3.0 明确拒绝读取 |
| `loop-engineering` 或 `loop-agent` CLI 别名 | `loop-engine` 是唯一执行入口 |
| 产品、Python 包或仓库重命名 | 变更仅针对执行入口与控制模式 |
| scheduler、daemon、自动合并或自动部署 | 超出当前目标，并与现有安全边界冲突 |
| 绕过合同、平台权限或永久禁止项 | Autonomous 只在批准范围内自主，不是无限权限 |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| CORE-01 | TBD | Pending |
| CORE-02 | TBD | Pending |
| CORE-03 | TBD | Pending |
| CORE-04 | TBD | Pending |
| CORE-05 | TBD | Pending |
| CORE-06 | TBD | Pending |
| AUTO-01 | TBD | Pending |
| AUTO-02 | TBD | Pending |
| AUTO-03 | TBD | Pending |
| AUTO-04 | TBD | Pending |
| AUTO-05 | TBD | Pending |
| CLI-01 | TBD | Pending |
| CLI-02 | TBD | Pending |
| CLI-03 | TBD | Pending |
| LIFE-01 | TBD | Pending |
| NAME-01 | TBD | Pending |
| SAFE-01 | TBD | Pending |
| SAFE-02 | TBD | Pending |
| SAFE-03 | TBD | Pending |
| TEST-01 | TBD | Pending |
| TEST-02 | TBD | Pending |

**Coverage:**
- v1 requirements: 21 total
- Mapped to phases: 0
- Unmapped: 21 ⚠️

---
*Requirements defined: 2026-07-31*
*Last updated: 2026-07-31 after initial definition*
