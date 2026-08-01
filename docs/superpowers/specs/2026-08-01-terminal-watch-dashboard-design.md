# Loop Engineering 项目级终端 Watch 仪表盘设计

- 状态：已批准（用户授权剩余设计与 inline 实施自主推进）
- 日期：2026-08-01
- 适用范围：Shell/TUI 只读可视化、CLI 接口、项目内 Run 发现
- 协议版本：0.3.0

## 1. 目标

新增面向人的项目级终端仪表盘，让用户无需提供单个 Run 目录即可观察当前项目中
所有进行中或暂停的 Loop Run，并可显式查看终态历史。仪表盘只读取 Core 已持久化的
合同、状态、账本和证据，不执行验证、不改变 Run，也不成为任务采用、恢复或授权入口。

## 2. 命令接口

```bash
# 实时显示当前项目所有非终态 Run
loop-engine watch

# 实时显示非终态 Run，并包含全部终态历史
loop-engine watch --all
```

- 命令不接受 `run-dir`，也不提供 `loop-engine run watch` 别名。
- 从当前工作目录向上查找最近的 `.loop-engineering/project.yaml`，其所在目录为项目根。
- 找不到项目配置时返回 CLI 错误，不扫描用户主目录或其他项目。
- 默认排除 `DONE`、`BLOCKED` 和 `BUDGET_EXHAUSTED`；`--all` 包含这些终态。
- `.loop-runs/.drafts/`、隐藏目录、符号链接和 junction 不作为 Run 打开。
- 发现仅用于只读显示，不得据此采用 Run、恢复 Goal、推导批准或选择“最新 Run”。

## 3. 终端行为

- TTY 中每秒重新读取项目 Run，并使用 ANSI 原地刷新。
- 非 TTY、管道和重定向只输出一帧无 ANSI 文本后退出。
- `Ctrl-C` 恢复光标和终端样式后以成功状态退出，不改变任何 Run。
- 若启动时没有活动 Run，输出空状态和 `--all` 提示后退出。
- Watch 期间最后一个活动 Run 进入终态时，最后一帧保留本次观察过的 Run 终态，然后自动退出。
- `--all` 在有活动 Run 时持续刷新；所有活动 Run 结束后输出最后一帧并退出。启动时全是终态则输出一帧后退出。
- 宽终端显示分组卡片、预算条和活动时间线；窄终端自动退化为紧凑表格。
- TTY 且未设置 `NO_COLOR`、`TERM` 不是 `dumb` 时启用颜色；否则输出纯文本。
- 输出编码无法表示 Unicode 图形时使用 ASCII 状态符号和进度条。

## 4. 展示数据

每个 Run 显示：

- `loop_id`、状态、更新时间、合同版本、协议版本和当前授权是否匹配；
- 当前合同的验收条件数，以及已记录的通过、失败、运行中和缺失证据；
- 已用/最大迭代、分钟、Checker 修订和无进展循环；
- 未决 intent 数、当前动作、暂停原因和最新 Checker verdict；
- 最近事件摘要。

仪表盘使用“Recorded evidence/已记录证据”措辞。它不重新计算代码指纹、范围或 Git
交付，不把已记录 evidence 等同于权威 `DONE`。最终完成仍只能由
`loop-engine run complete` 重新派生并转换。

## 5. 架构

新增 `src/loop_engineering/watch.py`，包含三个内部职责，但只暴露一个 CLI 用例：

1. 项目发现与 Run 枚举：限制在最近项目根的配置 run root 直接子目录。
2. 严格只读快照：用严格 Pydantic 模型把合同、状态、当前版本事件聚合为展示数据。
3. 自适应渲染与 Watch：根据 TTY、宽度、颜色和编码生成文本并控制刷新生命周期。

`src/loop_engineering/cli.py` 只增加顶层 `watch` 参数解析和对该用例的调用。Core 的合同
模型、状态机、GatePolicy、RunStore 写接口、Schema 和协议行为不修改，也不新增第三方依赖。

## 6. 排序和异常处理

- 非终态 Run 排在终态之前；组内按 `updated_at` 降序，再按 `loop_id` 稳定排序。
- `.loop-runs` 不存在时按“没有活动 Run”处理。
- 某个 Run 在枚举和读取之间消失时，本轮忽略并在下一轮重试。
- 半写 JSONL、旧 collaborative Run、合同/状态不一致或其他无法打开的目录形成脱敏警告行，
  不阻断其他有效 Run 的展示。
- 不显示异常的原始 payload、秘密或完整路径内容；错误边界继续复用现有 CLI 脱敏策略。
- 刷新循环通过 `try/finally` 恢复光标、颜色和终端状态。

## 7. 测试策略

严格采用 RED→GREEN：

1. CLI 测试先固定顶层 `watch`、无 `run-dir` 和 `--all` 参数。
2. 单元测试固定嵌套目录项目发现、隐藏/链接过滤、活动/全部过滤和稳定排序。
3. 单元测试固定当前合同 evidence 聚合、预算、intent、Checker 和警告行。
4. 渲染测试固定宽/窄布局、无 ANSI 非 TTY、`NO_COLOR` 和 ASCII 回退。
5. Watch 测试固定空项目退出、终态最后一帧、非 TTY 单帧及 `Ctrl-C` 安全退出。
6. 更新 README 和接入文档，再运行针对性测试、全量 pytest、Ruff、构建及 `git diff --check`。

## 8. 非目标

- 不实现 curses/Textual 全屏应用、键盘导航、分页或鼠标交互。
- 不新增 Rich/Textual 等运行时依赖。
- 不显示或采用 `.drafts`。
- 不跨项目、主目录或全局 Codex Goal 搜索 Run。
- 不通过仪表盘暂停、恢复、批准、修订或完成 Run。
- 不改变协议、合同 Schema、Gate、预算或完成语义。
