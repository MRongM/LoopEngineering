---
quick_id: 260801-kqj
status: complete
subsystem: codex-adapter-skill
tags: [codex, skill, progressive-disclosure, protocol, tdd]
provides:
  - A 736-word always-visible Codex safety kernel and stage router
  - Four directly routed Intake, Goal, execution, and lifecycle playbooks
  - Adapter contract coverage for inline invariants, composed semantics, route resolution, and prompt budget
key-files:
  created:
    - adapters/codex/references/intake-contract.md
    - adapters/codex/references/goal-bridge.md
    - adapters/codex/references/execution-loop.md
    - adapters/codex/references/lifecycle.md
    - docs/superpowers/specs/2026-08-01-codex-skill-progressive-disclosure-design.md
    - docs/superpowers/plans/2026-08-01-codex-skill-progressive-disclosure.md
  modified:
    - adapters/codex/SKILL.md
    - tests/test_adapter_contract.py
key-decisions:
  - "Keep admission, authorization, fail-closed routing, and permanent denies always visible."
  - "Resolve references/*.md from the directory containing SKILL.md, never from the target project."
  - "Keep Core unchanged until project-preflight or resume-snapshot demand has real usage evidence."
duration: 52min
completed: 2026-08-01
---

# Quick Task 260801-kqj：Codex Skill 渐进披露重构总结

Codex `$loop-engine` 入口已从 3251 词收敛到 736 词，常驻上下文减少 77.36%；完整
Protocol 0.3.0 语义由始终可见的安全内核和四份按阶段读取的 playbook 共同承载。

## 完成内容

- 将 `SKILL.md` 收敛为显式触发、任务绑定、合同硬门、阶段路由和永久禁止项。
- 新建 Intake/contract、Goal bridge、execution loop、lifecycle 四个单一职责 playbook。
- 路由使用相对 `SKILL.md` 所在目录的 `references/*.md`，并在缺失、不可读、歧义或
  版本不兼容时 fail closed。
- 测试分别约束入口安全内核、直接路由、Skill 相对路径解析、组合语料完整语义和
  2113 词上限；既有 required/obsolete 断言没有删除或放宽。
- 记录了全仓审计、三方案比较和分阶段路线；本轮选择“安全内核 + 渐进披露”，Core/CLI
  自动化保留为有真实使用证据后的后续工作。

## TDD 与验证证据

- 初始 RED `E-e22c7b00410246bd8ebc2fbfb501e22b`：3 failed、21 passed，精确暴露
  3233 词超限、入口安全措辞缺失和四份引用尚不存在。
- Checker 修订 RED `E-990acd74d0084de99c811f351e5f1ec0`：1 failed、23 passed，精确暴露
  仓库根路由不能按 Skill 目录解析的问题。
- 聚焦 GREEN `E-5c7480dec8ce40ca930877a6895a22e3`：24 passed。
- 全量 GREEN `E-2468a33a17824fc0aed065c945fd9541`：250 passed。
- 静态检查 `E-156bb895a8684cdbbb9eccd0bfec15ac`：Ruff 全部通过。
- 差异检查 `E-71d5611c664448c7bc14211b37e44fb6`：退出码 0、无输出。
- 上述四个通过记录共享指纹
  `8d65d5437cdb099c70e375b86bc18cf5e89cf01866eb4151418b13a06ac1a93e`；scope 为
  `valid: true`，无越界路径。
- 独立 Checker 先因真实路由缺陷给出 `REVISE`，修复后给出 `ACCEPT` 且无剩余发现。

本摘要和 `.planning/STATE.md` 本身属于获批的最终跟踪变更，因此写入后会产生新指纹。
Loop 会在该最终指纹上重新执行 `VAL-1` 至 `VAL-4` 和独立 Checker；为避免递归改写本摘要，
终态证据 ID 与权威 DONE 结果只以 append-only Run 账本为准。

## 文件边界

- `adapters/codex/SKILL.md`：始终加载的安全内核与直接路由器。
- `adapters/codex/references/*.md`：四个按职责拆分的阶段 playbook。
- `tests/test_adapter_contract.py`：入口、路由、组合语义和词数预算契约。
- `docs/superpowers/specs/2026-08-01-codex-skill-progressive-disclosure-design.md`：审计、
  方案权衡与分阶段设计。
- `docs/superpowers/plans/2026-08-01-codex-skill-progressive-disclosure.md`：测试先行实施计划。
- `.planning/quick/260801-kqj-refactor-codex-loop-engine-skill-into-pr/`：GSD inline 追踪。

未修改 Core、CLI、Schema、模板、README、adoption 或 ADR；未新增依赖，也未安装或覆盖
用户目录中的 managed Skill。

## 偏差与恢复

- 首次测试补丁早于 intent。发现后已用 Gate/intent 精确回退到 HEAD，再按合法顺序重做；
  append-only 账本未被重写。
- 本地 `.venv/bin/pytest` 的 shebang 残留指向相邻 checkout。权威验证改用 Run-local cache、
  `UV_ISOLATED=1`、`UV_OFFLINE=1` 和 `UV_LOCKED=1`，避免继续使用漂移环境。
- 一次隔离环境诊断意外报告工具下载；它没有改变依赖声明或 tracked 文件，偏差已追加记录，
  此后所有 uv 验证均强制离线与锁定。
- 早期账本曾记录 707 词，随后实测更正为 720；加入 Checker 要求的路径基准说明后，最终
  实测为 736 词，仍比基线减少 77.36%。
- Checker 发现仓库根路由在真实 Skill 解析规则下会重复路径；新增失败测试后改为
  `references/*.md`，并同步设计和实施计划。

## Git 与后续工作

没有创建分支、worktree、commit、push、PR、merge 或部署。当前交付保持 `uncommitted`，
符合用户选择的 inline 执行与 Contract v1 Git policy。

后续候选保持独立范围：项目配置 preflight、只读 resume snapshot、真实 Codex Goal 宿主场景
测试。只有出现可归因的运行证据后才应扩展 Core。

## 用户操作

本轮只优化仓库源文件。若要让已安装的 managed Skill 使用该版本，需要在未来由用户按
lifecycle playbook 执行安装或更新；该操作不在本合同范围内，本轮未代为执行。

---
*Quick task: 260801-kqj-refactor-codex-loop-engine-skill-into-pr*
*Completed: 2026-08-01*
