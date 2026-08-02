---
gsd_state_version: 1.0
milestone: v0.1.0
milestone_name: first-public-release
status: completed
last_updated: "2026-08-01T15:38:06Z"
last_activity: 2026-08-01 -- Resolved runtime Gate and Checker attestation hardening
progress:
  total_phases: 1
  completed_phases: 1
  total_plans: 1
  completed_plans: 1
  percent: 100
---

# Project State

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-08-01)

**Core value:** Agent 只能在明确批准且可验证的范围内自主执行，并且只有真实证据满足
合同后才能完成。

**Current focus:** 保持首版 `0.1.0` 的运行时执行闭合与证据新鲜度。

## Current Position

Workflow: inline `gsd-debug`
Status: resolved runtime Gate and Checker attestation hardening
Artifact: `.planning/debug/runtime-gate-checker-binding.md`

Progress: `[██████████] 100%`

## Current Decisions

- Protocol `0.1.0` 是首个公开版本；Core 不提供旧版本读取、转换或迁移。
- 唯一控制模式是 `autonomous`；一次完整批准绑定设计、计划、权限与风险。
- 目标项目只使用 `.loop-engine/` 一个 Loop-owned 顶层目录。
- Codex 托管安装目录、Skill 名和 Shell CLI 使用 `loop-engine`；Python 分发包保持
  `loop-engineering`。
- 批准后在合同闭包内持续执行，只有硬边界可以暂停。
- Action intent 入口在同一操作中绑定精确 request，并重验当前批准、状态、预算和 Gate；Git 与验证
  权威结果只能由专用执行路径产生。
- 中高风险完成只消费绑定当前合同哈希、源码指纹、证据摘要和账本序列的 Checker
  attestation；独立身份仍由宿主 Adapter 根据真实调度断言。
- Core 是协作式强制协议而非对抗式宿主沙箱；合规 Adapter 必须路由全部外部变更。
- 经用户明确确认，预发布 Roadmap、Phase、设计与兼容性记录已移除。

## Verification

- Full pytest: `264 passed`
- Ruff: all checks passed
- Adapter contract: `19 passed`; entrypoint remains within its `2113`-word budget
- Schema: all three files regenerated to a temporary directory and matched byte-for-byte
- Package: sdist and wheel built as `0.1.0` in an isolated temporary directory
- Agent Shell: wheel exposes only `loop-engine`
- Diff integrity and active-surface residue checks: passed

## Blockers

None.

## Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260801-my8 | Backport Codex Skill progressive disclosure while preserving Protocol 0.1.0 | 2026-08-01 | uncommitted | [260801-my8-backport-codex-skill-progressive-disclos](./quick/260801-my8-backport-codex-skill-progressive-disclos/) |

## Constraints Preserved

- 未创建分支，未提交或推送 Git。
- 未自动迁移、移动或删除用户运行时数据。
- 未放宽 Gate、Schema 或测试。
- 未新增依赖、调度器、daemon、自动合并、部署或对抗式宿主沙箱。

## Session Continuity

Last session: 2026-08-01T15:38:06Z
Stopped at: resolved runtime Gate and Checker attestation hardening
Resume file: `.planning/debug/runtime-gate-checker-binding.md`
