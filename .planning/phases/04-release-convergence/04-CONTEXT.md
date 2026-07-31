# Phase 4: Release Convergence - Context

**Gathered:** 2026-07-31
**Status:** Ready for planning
**Mode:** Auto-generated from the approved 0.3 design and explicit autonomous inline authorization

<domain>
## Phase Boundary

统一当前面向用户和维护者的 0.3 发布表面：所有可执行示例使用唯一 Agent Shell
入口 `loop-engine`，同时清楚区分产品名、Python 分发包、托管 checkout、Codex Skill
触发词和 CLI。补充兼容性说明，并用跨协议、CLI、生命周期、Adapter、测试、静态
检查和构建证据证明 0.3.0 可一致发布。本阶段不改变 Core 或生命周期行为。

</domain>

<decisions>
## Implementation Decisions

### Current command surface

- **D-01:** README、adoption guide、当前术语说明和正向测试示例中的所有执行命令使用 `loop-engine`；`loop-engineering` 只作为 Python 分发包、checkout 或历史标识出现。
- **D-02:** 当前文档声明 0.3.0 是 Autonomous-only：不提供模式选择，不提供 `loop-engineering`/`loop-agent` CLI alias，也不迁移 collaborative 合同或 Run。

### Stable identities and history

- **D-03:** 产品和仓库继续叫 Loop Engineering，Python 分发包与托管 checkout 继续叫 `loop-engineering`，Codex Skill 触发词继续是 `$loop-engine`，唯一 Shell CLI 是 `loop-engine`。
- **D-04:** `docs/superpowers/` 下的旧设计和计划保留为审计记录；兼容性文档明确这些历史命令与模式描述不是当前执行指南，当前入口只链接 0.3 规范。

### Release evidence

- **D-05:** 发布验证必须使用新鲜的 focused/full tests、Ruff、schema drift、真实 CLI version/help、生命周期测试、临时目录构建、wheel 元数据和 `git diff --check` 证据。
- **D-06:** 不执行全局安装或卸载。生命周期行为由隔离测试验证；构建和 Schema 重建只写入 `/private/tmp`，不污染仓库。

### the agent's Discretion

- 在不扩大语义的前提下精简 README 和 adoption 中重复的模式说明。
- 选择结构化测试断言，区分合法身份文字、负向 alias 断言与真正的旧执行命令。

</decisions>

<canonical_refs>
## Canonical References

- `PROTOCOL.md` — 当前 0.3.0 协议与兼容、安全边界。
- `docs/superpowers/specs/2026-07-31-loop-engineering-0.3-autonomous-only-design.md` — 已批准的 Autonomous-only 与命名决策。
- `pyproject.toml` — 分发包版本和唯一 console script 的事实来源。
- `adapters/codex/scripts/manage.py` — 分发包、checkout、Skill 和 executable 身份分离。
- `.planning/REQUIREMENTS.md` — CLI-03、NAME-01、TEST-02。

</canonical_refs>

<active_surfaces>
## Active Release Surfaces

- `README.md`
- `docs/adoption.md`
- `docs/compatibility.md`
- `CONTEXT.md`
- `docs/adr/0001-require-manual-skill-invocation.md`
- `adapters/codex/SKILL.md`
- `tests/test_adapter_contract.py`

</active_surfaces>

<deferred>
## Deferred Ideas

- 不重写历史设计/计划正文；它们是审计材料，不是 0.3 快速开始文档。
- 不新增 CLI shim、迁移器、scheduler、daemon、自动 merge/deploy 或发布自动化服务。

</deferred>

---
*Phase: 04-release-convergence*
*Context gathered: 2026-07-31 via approved autonomous decisions*
