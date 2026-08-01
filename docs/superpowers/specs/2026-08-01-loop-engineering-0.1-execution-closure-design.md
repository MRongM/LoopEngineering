# Loop Engineering 0.1 执行闭合设计

## 定位

`0.1.0` 是 Loop Engineering 的首个版本。它从一开始只提供一套执行语义，不包含
历史协议解析、版本兼容分支或自动迁移。

核心不变量是“执行闭合合同”：合同批准前，设计决定、计划动作、验证方式、预算和
风险授权必须形成可执行闭包。批准后，Agent 在该闭包内持续工作，只有真正的合同变化、
外部强制门禁、无法调和的 intent、用户取消或权威终态才中断。

## 合同闭合

- `execution_plan.design_decisions` 至少包含一个非空决定。
- `execution_plan.actions` 至少包含一个严格 `ActionRequest`，动作身份不得重复。
- Core 使用与运行时相同的 GatePolicy 预检每个计划动作；任何 `PAUSE` 或 `DENY`
  都使合同校验失败。
- 允许路径只是边界，不会隐式授权未计划动作。
- 每个验证命令必须声明 `workspace_policy: isolated`。
- 一次完整验证的 timeout 总和不得超过合同活跃时间预算。
- 危险动作仍需精确 `authorized_operations`、完整风险披露和绑定批准；永久禁止项
  始终返回 `DENY`。

合同内唯一人类门禁是 `contract_approval`。设计、计划、危险动作和完成标准在完整
摘要中一次形成。批准绑定协议版本、合同版本、规范化 SHA-256 和完整风险 ID 集合。
新增目标、范围、动作、权限、预算或风险时，只创建一个完整合同修订。

## 单一项目控制根

```text
.loop-engine/
├── .gitignore
├── project.yaml
├── drafts/
├── runs/
└── cache/
```

内部 `.gitignore` 默认忽略全部内容，只允许自身和 `project.yaml` 被跟踪。草稿、Run、
隔离验证快照与缓存都留在该目录。Core 不修改项目根 `.gitignore`，也不会自动移动或
删除冲突目录。控制根及其受管子路径不得是 symlink 或 junction。

## 隔离验证

验证从源仓库的 tracked 与 non-ignored untracked 文件构造快照，放在
`.loop-engine/cache/runs/<loop-id>/validation/`，并初始化为一次性 Git 仓库。验证 argv
以 `shell=False` 在快照运行；通用临时目录和 XDG 缓存也指向同一控制根。

验证前后都计算源仓库指纹。快照内产生的编译产物、日志与缓存不会污染源仓库；验证
期间源仓库发生并发变化时证据失败。timeout 使用退出码 124，进程启动失败使用 127，
快照准备失败使用 126；三者都写入脱敏证据并关闭对应 intent。指向仓库外部的 symlink
不会复制到快照，避免验证借链接写出隔离边界。

## Gate 与恢复闭合

Run 只能从 `.loop-engine/runs/<loop-id>/` 打开；任何其他路径确定性拒绝。进入设计、
计划、执行、验证、检查或决策状态时都重新校验当前合同绑定，不能借 `PAUSED` 绕过
批准。存在未决 intent 时不能创建下一 intent，必须先依据真实状态调和。

Agent Shell 的 Git worktree、commit、push 与 PR 命令自行执行 Gate 校验，要求 Run
处于 `executing`，并自动写入 intent/result。`git_worktree` 使用
`<branch>@<absolute-worktree-path>` 作为精确目标；失败结果也会关闭 intent。

## 不间断执行

进入 `AWAITING_APPROVAL` 或 `PAUSED` 时暂停活跃时间计数，离开时累计暂停时长。
用户等待不消耗执行预算。批准后不再安排常规设计、计划、危险动作或最终验收确认；
非阻塞问题累计到最终报告。失败测试、Checker `REVISE` 和可用的新信息都留在诊断循环
中处理，不构成人工中断理由。
