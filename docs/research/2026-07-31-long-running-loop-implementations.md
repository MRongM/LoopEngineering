# Ralph、Codex Goal 与 Loop Engineering 长任务机制调研

日期：2026-07-31

## 结论

`cobusgreyling/loop-engineering` 不是 Ralph 式常驻执行器，也不是 Codex Goal 的替代运行时。它主要是长任务的**设计层与控制面工具箱**：定义 scheduling、skill、durable state、worktree、Maker/Checker、budget、gate、run log 等组合方式；真正负责持续唤醒和执行的 heartbeat 来自产品内 Automation、cron/GitHub Actions，或 companion runtime `harness-foundry`。

三种实现的核心差异是“谁负责启动下一轮”：

| 方案 | 下一轮由谁启动 | 跨轮状态 | 终止方式 |
|---|---|---|---|
| Ralph（`snarktank/ralph`） | Bash `for` 循环重新启动一个全新 agent 进程 | `prd.json`、`progress.txt`、Git 历史 | 输出 `<promise>COMPLETE</promise>` 或达到最大轮数 |
| Codex Goal | thread idle 生命周期钩子读取持久化 goal，注入 continuation，再启动新 turn | SQLite 中的 thread goal、同一 thread、当前 worktree | complete/blocked、pause/clear、token/usage/error 限制 |
| `cobusgreyling/loop-engineering` | 外部 scheduler、CI、产品 Automation 或 companion runtime | `STATE.md`、run log、ledger、Git/worktree | gate、breaker、budget、人工升级；具体 runtime 由宿主负责 |
| 当前 Python LoopEngineering | 当前用户/agent 逐条调用 CLI；没有内置 scheduler/daemon | 严格 contract、原子 state、append-only events、evidence | 状态机、预算、Checker 和证据门禁 |

共同的本质不是让一个模型调用永不结束，而是把长任务拆成**多个有界 turn/attempt**，并把目标、进度、证据和停止条件放到模型上下文之外。

## 1. Ralph：最小可用的外层进程循环

参考实现 `snarktank/ralph` 的机制非常直接：

1. `ralph.sh` 设置 `MAX_ITERATIONS`，进入固定次数的 `for` 循环。
2. 每轮通过 CLI 启动一个新的 Amp 或 Claude Code 实例，因此获得干净上下文。
3. 新实例读取同一个 `prd.json` 和 append-only `progress.txt`，选择优先级最高且 `passes: false` 的一条 story。
4. agent 修改代码、运行检查、提交、更新 story 状态并追加经验。
5. shell 从标准输出识别 `<promise>COMPLETE</promise>`；未完成则继续，达到轮数上限则退出失败。

一手实现：[`ralph.sh`](https://github.com/snarktank/ralph/blob/main/ralph.sh)、[`prompt.md`](https://github.com/snarktank/ralph/blob/main/prompt.md)、[README](https://github.com/snarktank/ralph#ralph)。

值得借鉴的是：

- 每轮只处理一个可验证增量，限制 blast radius。
- 每轮使用新模型上下文，避免历史对话持续膨胀和错误假设固化。
- 将任务列表、完成位和经验外置，进程崩溃后仍可恢复。
- 外层控制器设置硬轮数上限；模型不能自行取消该上限。

不应直接照搬的是：

- 完成仅靠模型输出的文本标记，容易误报；应由证据和状态机重新推导。
- 示例以 `--dangerously-allow-all` / `--dangerously-skip-permissions` 运行，并忽略 agent 进程错误，不符合本项目安全约束。
- 每轮自动 commit、分支切换，不保留精确 intent/result 和作用域审批。
- `progress.txt` 是自由文本，适合简单原型，不适合并发、审计或精确恢复。

## 2. Codex Goal：事件驱动的 turn chaining

官方文档把 `/goal` 定义为“跨 turns 持续工作，直到可验证停止条件成立”，并支持 pause、resume、edit、clear。它不是一个 shell busy loop，而是 thread 生命周期上的 continuation 机制。[Follow a goal](https://learn.chatgpt.com/use-cases/follow-goals)；[Long-running work](https://learn.chatgpt.com/docs/long-running-work)。

OpenAI Codex 源码中的关键路径为：

1. `create_goal` 把 objective、status、token budget 等写入持久化 `thread_goals`；同一 thread 有未完成 goal 时拒绝创建新 goal。
2. goal extension 在 thread start/resume 时注册或恢复 per-thread runtime。
3. 每次 thread 进入 idle，`on_thread_idle` 调用 `continue_if_idle()`。
4. runtime 确认 feature、持久化状态、live thread、deferral 和 goal status 均允许继续。
5. runtime 生成 continuation steering item，并调用 `try_start_turn_if_idle(...)` 开始下一 turn。
6. turn start/stop、token usage 和 tool finish 钩子累计时间与 tokens；达到预算或发生不可恢复错误时停止自动续跑。
7. 模型侧 `update_goal` 只能将 goal 标为 complete 或 blocked；pause/resume、budget/usage limited 由用户或系统控制。

一手源码：[`runtime.rs`](https://github.com/openai/codex/blob/main/codex-rs/ext/goal/src/runtime.rs)、[`extension.rs`](https://github.com/openai/codex/blob/main/codex-rs/ext/goal/src/extension.rs)、[`tool.rs`](https://github.com/openai/codex/blob/main/codex-rs/ext/goal/src/tool.rs)、[`goals.rs`](https://github.com/openai/codex/blob/main/codex-rs/state/src/runtime/goals.rs)、[continuation prompt](https://github.com/openai/codex/blob/main/codex-rs/ext/goal/templates/goals/continuation.md)。

最值得借鉴的是：

- **事件驱动续跑**：以 `idle -> enqueue continuation -> new turn` 代替进程内无限循环，天然允许用户插入消息、暂停和恢复。
- **控制权分离**：模型只能声明完成/阻塞，用户或系统拥有暂停、恢复和预算限制的最终控制权。
- **持久化 goal 是小而严格的控制记录**：objective、status、budget、usage，而不是保存完整思维过程。
- **并发与竞态保护**：在读取 goal 和启动 continuation 的窗口持有 permit，并使用 `try_start_turn_if_idle` 避免重复 turn。
- **失败即断路**：不可恢复 turn error 会阻塞 goal，避免 compaction 等基础设施错误触发耗费 token 的自动重试。
- **续跑 prompt 重新锚定原始目标**：强调 worktree/外部状态为权威、不得把目标缩小成容易完成的子集、完成前必须重新验证。

## 3. `cobusgreyling/loop-engineering` 实际实现了什么

本次检查的本地快照为 commit `0507826981e9b982caafc17323b2d94485215961`。

### 3.1 定位：Design/Control Plane，而非完整 Runtime

仓库 README 明确将生态拆为 Memory、Design、Runtime、Govern、Fleet，并把“this repo”标为 Design，把 `harness-foundry` 标为 Runtime。统一 `loop` CLI 主要执行 init、doctor、status、audit、cost 等脚手架和诊断操作，并不在后台持续调用 agent。

来源：[README 的工具与生态分层](https://github.com/cobusgreyling/loop-engineering/blob/0507826981e9b982caafc17323b2d94485215961/README.md#L100-L135)。

### 3.2 它定义的标准运行链路

仓库给出的单轮链路是：

```text
Scheduler
  -> Skill / Pattern
  -> 读取 STATE、预算与上轮结果
  -> 创建隔离 worktree
  -> Maker 实现
  -> 独立 Checker 验证
  -> policy/budget gate
  -> PR/报告或人工升级
  -> 写入 durable state/run log
  -> 等待下一 heartbeat
```

来源：[architecture diagrams](https://github.com/cobusgreyling/loop-engineering/blob/0507826981e9b982caafc17323b2d94485215961/docs/architecture-diagrams.md#L7-L74)、[primitives](https://github.com/cobusgreyling/loop-engineering/blob/0507826981e9b982caafc17323b2d94485215961/docs/primitives.md)。

### 3.3 真正有执行语义的组件

- `loop-context`：确定性地读取 attempts ledger，检测同错误重复、相似动作重复、连续失败、token 上限和 iteration 上限；同时裁剪长堆栈、只保留最近窗口并折叠重复失败。它只返回 continue/escalate，不启动下一轮 agent。
- `loop-gate`：只判断“准备执行什么”，例如 path denylist、文件数和 auto-merge allowlist；有意不读取运行历史，历史熔断由 `loop-context` 负责。
- `loop-worktree` / `loop-sandbox`：为一次 attempt 创建隔离工作树、捕获 patch、清理隔离环境。
- `loop-action`：在 GitHub Actions 中组合 audit、breaker、sandbox 和用户配置的 agent command；它是执行包装器，不是自主规划器。
- `goal-audit` / `goal-init`：检查和生成 GOAL、skill、verifier、budget、CI、run-log 等准备材料；它们不执行 goal。
- GitHub workflows：提供仓库自身的定时 heartbeat 示例，其中 deterministic daily triage 会更新状态、运行验证并开 PR。

核心熔断源码：[context-manager.ts](https://github.com/cobusgreyling/loop-engineering/blob/0507826981e9b982caafc17323b2d94485215961/tools/loop-context/src/context-manager.ts)。

### 3.4 与 Ralph 的关系

仓库 `resources/sources.md` 列出的直接来源主要是 Cobus Greyling、Addy Osmani、Anthropic/Claude Code 等，并未把 Ralph 列为直接实现来源。因此更准确的表述是：两者共享外层循环、外置状态、完成检查和 attempt cap 等架构思想；不能据此称该仓库是 Ralph fork 或 Ralph 的直接改写。

## 4. 对当前 Python LoopEngineering 最值得借鉴的部分

当前项目已经有比 Ralph 和参考仓库更严格的基础：批准后的 typed contract、合法状态转换、原子 state、append-only intent/result、evidence freshness、Checker、预算和禁止自动 merge/force-push。当前缺口是 README 已明确的：**没有 scheduler/daemon**；Codex adapter 中的 Maker loop 是由模型逐条调用 CLI 的操作协议，不是持续运行的 driver。

### P0：增加“单步 driver”，不要先造常驻 daemon

建议新增一个薄的、可恢复的 `tick(run_id)` 边界：

```text
load + reconcile
  -> claim lease
  -> evaluate budget/gate
  -> perform at most one bounded transition/attempt
  -> persist result/evidence
  -> return CONTINUE | WAIT | COMPLETE | ESCALATE
```

外部 Codex Goal、Automation、cron 或 CI 只负责再次调用 `tick`。Core 保持 tool-independent；Codex 的 continuation/steering 属于 `adapters/codex/`。这样同时获得 Ralph 的简单性和 Codex Goal 的事件驱动可控性。

### P0：为 continuation 增加 lease 和幂等键

只判断 status=active 不足以防止两个 heartbeat 同时执行。建议持久化：

- `lease_owner`、`lease_expires_at`
- `continuation_id` 或 `tick_id`
- CAS 所需的 `state_version`
- 与 intent 绑定的幂等键

启动下一轮前以原子 compare-and-set claim；恢复时先对 unmatched intent 做现状核对。Codex 的 permit + `try_start_turn_if_idle` 是这里最直接的参考。

### P0：保持“证据推导完成”，不要采用完成口令

Ralph 的 `<promise>COMPLETE</promise>` 适合演示，但生产协议必须继续由 contract acceptance criteria、fresh evidence、scope、Checker verdict 和交付结果共同推导 DONE。模型的“我完成了”只能是候选事件，不能是事实来源。

### P1：分离完整账本与 prompt projection

借鉴 `loop-context`：

- 完整 events/evidence 永不裁剪，作为审计事实。
- 给下一 turn 注入的 context 是确定性 projection：原始 objective、当前 criterion、最近 N 次 attempt、去重后的错误签名、已尝试策略、剩余预算、下一合法动作。
- 裁剪只影响 prompt，不修改事实账本。

这能减少 context rot，同时符合当前项目“不保存完整 model reasoning”的要求。

### P1：让熔断信号由观测自动生成

当前协议已有 `same_strategy_retries` 和 `no_progress_cycles`，但输入较依赖调用者诚实标记。可以增加确定性辅助信号：

- 规范化错误签名及连续重复次数。
- action fingerprint / target fingerprint。
- evidence fingerprint 是否变化。
- 相同 validation command 的结果是否变化。
- 单位新证据的 token/time 成本。

这些信号用于建议 diagnosis/escalation，最终状态仍由严格状态机写入，避免模糊相似度直接授权变更。

### P1：正式化 fresh Checker 上下文

Maker 只提交 patch、变更声明和证据索引；Checker 从 contract 和真实 worktree 重新推导验收项，不接收 Maker 的完整推理。Checker verdict 应携带 contract hash、worktree HEAD/diff hash、validation evidence IDs，防止验证陈旧对象。

### P1：支持 cheap no-op heartbeat

定时 loop 的多数 tick 可能没有任务。先用确定性/便宜逻辑 discovery，只有确认存在可执行增量后才启动昂贵 agent；无任务时记录 `noop` 并立即退出。这是降低长期运行成本最有效的措施之一。

### P2：渐进式自治，而非一次开放全部权限

采用参考仓库的 L1/L2/L3 思路，但由本项目 contract 强制执行：

- L1：只读、报告。
- L2：准备 patch/PR，人工批准关键外部副作用。
- L3：只在明确 allowlist、预算、Checker、kill switch 和稳定历史均成立时做预授权动作。
- 事故、成本异常或 verifier 漂移自动降级。

## 5. 不应从参考仓库照搬的实现

- 某些 runner 支持 shell 字符串或 `shell: true`；本项目应继续只接受 argv 且 `shell=False`。
- 仓库自身 workflow 含 `git push --force-with-lease` 和自动 merge；本项目协议已明确禁止，两者不能作为实现模板。
- path gate 只有被每个副作用入口强制调用才是安全边界；“存在一个 gate CLI”或 readiness score 不是安全证明。
- Markdown `STATE.md` 适合人读，不应替代严格 Pydantic schema、原子 state 和 append-only event log。
- 基于相似度的“重复动作”检测可作为熔断提示，不能作为批准高风险操作或判定 DONE 的依据。

## 6. 推荐落地顺序

1. 定义 `LoopDriver.tick()` 输入、返回决策和 crash-recovery 语义；每次最多一个 bounded unit。
2. 增加 lease/CAS/idempotency，完成并发与重启安全。
3. 增加 deterministic context projection 和自动熔断 fingerprints。
4. 先实现 Codex Goal adapter：Goal 负责续 turn，Core driver 负责事实、权限和停止判断。
5. 再实现通用 scheduler adapter（cron/CI/queue），不把 scheduler 逻辑放进 Core。
6. 最后按 L1 -> L2 -> L3 逐级开放；保持自动 merge、deployment、force-push 永久禁止。

## 7. 最小架构建议

```text
                 ┌──────────────────────────┐
heartbeat ──────>│ adapter: Codex/cron/CI   │
                 └────────────┬─────────────┘
                              │ tick(run_id, continuation_id)
                 ┌────────────▼─────────────┐
                 │ Core LoopDriver          │
                 │ lease + state machine    │
                 │ budget + policy + done   │
                 └──────┬───────────┬───────┘
                        │           │
              ┌─────────▼───┐   ┌──▼────────────┐
              │ executor     │   │ durable store │
              │ argv only    │   │ state/events  │
              └──────────────┘   │ evidence      │
                                 └───────────────┘
```

这条路线遵循 KISS：Core 只决定“现在能否安全推进一个单位，以及之后是什么状态”，宿主只决定“何时再唤醒”；两边都不需要维护一个脆弱的无限循环。

