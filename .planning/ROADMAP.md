# Roadmap: Loop Engineering 0.1.0

## Overview

首个公开版本建立一套执行闭合语义：完整合同在一次批准前固定设计、动作、验证、预算、
权限和风险；批准后 Agent 在该闭包内自主执行、诊断、修正和验证，只有硬边界可以暂停。

## Phase 1: First-release execution closure

**Status:** Complete
**Goal:** 交付工具无关、证据门控、可恢复且默认不中断的 Autonomous Loop Engine。

### Delivered

1. Core、包、模板和 Schema 固定为 `0.1.0`，不包含协议版本分支或迁移路径。
2. 严格 ExecutionPlan 与运行时 Gate 使用同一动作、范围、权限和风险语义。
3. 目标项目控制状态统一进入 `.loop-engine/`。
4. 验证在隔离快照运行，所有异常路径都关闭 intent 并保留失败证据。
5. 活跃预算排除等待和暂停时间，所有执行状态入口重新验证当前批准。
6. Git Shell 在变更前执行 Gate 并自动记录 intent/result。
7. Codex Adapter 批量收敛批准前决策，批准后不询问常规确认。
8. 托管安装目录、Skill 名及唯一 CLI 统一为 `loop-engine`。

### Success criteria

- [x] 合同准入证明每个计划动作可以在批准后执行。
- [x] 只有 `.loop-engine/` 承载目标项目控制数据。
- [x] 验证不会用构建产物污染源工作区。
- [x] 非阻塞问题不会中断已批准循环。
- [x] 当前协议和发布表面只表达首版 `0.1.0`。
- [x] 全量回归、Ruff、Schema、构建和差异检查通过。

## Progress

| Phase | Plans complete | Status | Completed |
|---|---:|---|---|
| First-release execution closure | 1/1 | Complete | 2026-08-01 |
