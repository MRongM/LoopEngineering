---
status: resolved
trigger: "grill 诊断当前仓库的 Loop Engine：合同批准后执行经常中断，并要求目标项目只占用 .loop-engine 一个控制目录。"
created: 2026-08-01
updated: 2026-08-01
---

# Loop Execution Convergence

## Symptoms

- expected: 完整合同经用户一次批准后，Agent 在闭合边界内自主设计、计划、执行、验证
  和修正；常规失败与非阻塞问题留在循环内处理。
- actual: 验证会污染源工作区，等待时间消耗预算，验证启动失败留下悬空 intent；计划、
  风险和 Git 执行又没有形成同一个可执行授权闭包。
- reproduction: 让验证命令生成未跟踪文件，命令退出 0 后范围检查仍失败；清理触发新
  门禁，修订又使证据失效。
- user boundary: 当前执行闭合语义是首个公开版本 `0.1.0`，不保留协议版本兼容；目标
  项目只允许 `.loop-engine/` 一个 Loop-owned 顶层目录；安装目录为 `skills/loop-engine`。

## Root Cause

预发布实现分别表达了合同、风险、计划、验证和 Git 权限，但没有在批准前证明它们组成
同一个可执行闭包。运行时又把验证副作用、暂停时间、异常进程和未决 intent 留在闭包
之外，因此合法任务会不断制造新的合同外事实并被迫中断。

## Fix

- 将 Core、Schema、模板、Adapter、生命周期管理器和发布文档固定为首版 `0.1.0`；
  删除运行时版本分支、版本范围和迁移逻辑。
- 新增严格 `ExecutionPlan`/`ActionRequest`，合同创建时用真实 GatePolicy 预检每个计划
  动作；所有授权风险必须对应已计划的精确动作。
- 合并控制路径为 `.loop-engine/{project.yaml,drafts,runs,cache}`，内部 `.gitignore`
  只允许自身与项目配置被跟踪；拒绝冲突目录、非规范 Run 路径和链接型控制路径。
- 验证在 `.loop-engine/cache/` 的一次性 Git 快照中运行，隔离临时/缓存数据，拒绝逃逸
  symlink，并在快照创建前后比较源指纹。
- timeout、进程启动失败与快照准备失败都产生失败证据并关闭 intent；已有未决 intent
  未调和前禁止创建下一 intent。
- 活跃时间预算扣除 `AWAITING_APPROVAL` 与 `PAUSED`；持久化状态强制校验 pause clock。
- 所有执行流状态入口重新校验当前绑定批准，不能通过 `PAUSED` 绕过。
- Agent Shell Git 命令自行检查计划、风险、当前批准和 `executing` 状态，并自动记录
  intent/result；失败同样关闭 intent。
- Codex Adapter 在批准前批量收敛设计、计划与风险，批准后不再询问常规确认；非阻塞
  问题累计到最终报告，只在硬边界暂停。
- 仓库与 worktree 授权路径必须是解析后的绝对路径，防止工作目录或链接别名使已批准
  目标漂移。
- 生命周期管理器只识别当前 `loop-engine`，不保留旧 CLI 名称探测或清理分支。

## TDD Evidence

- 初始闭环用例：`13 failed, 4 passed`，命中执行计划、单目录、验证异常/污染和暂停预算。
- 隔离验证用例：新增源工作区污染与缓存路由后先得到 `2 failed`。
- 首版单版本模型：版本唯一、计划必填、隔离策略必填先得到 `3 failed`。
- Adapter 流程契约：旧范围、分散确认与旧安装路径先得到 `6 failed, 6 passed`。
- 内联安全复审：Run 路径、批准绕过、allowed-path 扩权、快照竞态与 symlink 逃逸先得到
  `7 failed`。
- Git Shell Gate：无批准直接创建 worktree 与缺少 `git_worktree` 动作类型先得到
  `2 failed`。
- 控制目录链接、状态 pause clock、未决 intent 串行化与授权/计划一致性均保留独立
  RED 证据后实现。
- 首版安装器残留定义先得到 `1 failed`；绝对/解析路径授权先后得到 `2 failed` 与
  `2 failed`，再收紧生产模型。
- 根 `.gitignore` 的旧运行目录规则先得到 `1 failed`，随后移除并保留负向回归断言。

## Verification

- focused tests: passing
- full pytest: `236 passed`
- Ruff: `All checks passed!`
- schema rebuild: regenerated from the final strict models
- CLI identity: `loop-engine --version` equivalent reports `0.1.0`
- active-surface residue scan: no old protocol version, compatibility field, old install
  directory, old runtime directory or legacy CLI symbol found
- package build: `loop_engineering-0.1.0.tar.gz` and
  `loop_engineering-0.1.0-py3-none-any.whl`; wheel registers only `loop-engine`
- diff integrity: `git diff --check` passed

## Constraints Preserved

- Core 保持工具无关；Codex 行为留在 `adapters/codex/`。
- 所有子进程使用 argv 与 `shell=False`。
- 永久禁止自动合并、部署、强推、历史改写与 reset-hard 行为。
- 未创建分支、未提交或推送 Git、未迁移或删除用户运行时目录。
- 经用户明确确认，预发布规划、设计与兼容性记录从当前仓库移除。
- `.superpowers/` 交互草稿与运行数据不在已确认删除目标内，未作修改。
