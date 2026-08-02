# Loop Engineering 托管更新脚本设计

## 目标

在仓库根目录提供可直接运行的 `update.sh`，让已安装到
`<CODEX_HOME>/skills/loop-engine` 的托管 checkout 能从 Shell 发起自我更新。
脚本不支持更新任意开发仓库，也不引入新的更新策略。

## 方案选择

采用薄 POSIX Shell 包装器，委托现有
`adapters/codex/scripts/manage.py update` 生命周期入口。

不在 Shell 中重复 `git pull`、来源校验或 `uv tool install`，避免两套安全逻辑发生偏移；
也不向工具无关的 `loop-engine` Core CLI 添加 Codex 专有更新命令。

## 行为

1. 使用 `#!/bin/sh` 与 `set -eu`，遇到未定义变量或失败命令立即退出。
2. 从脚本自身位置定位同一 checkout 内的生命周期管理器，因此调用者可位于任意工作目录。
3. 使用 `CODEX_HOME`；未设置时采用 `$HOME/.codex`，与 README 和管理器现有契约一致。
4. 以带引号的独立参数调用 `python3 <manager> update --codex-home <path>`。
5. 通过 `exec` 直接传播管理器的标准输出、标准错误与退出状态。

管理器继续独占以下职责：校验规范安装路径、链接边界、干净 Git 状态、唯一 `master`
分支、官方 origin 与仅快进历史；更新后重新校验 checkout，重装 CLI 并验证版本。

## 错误处理与安全边界

- 路径允许包含空格，所有参数必须完整引用。
- 缺少 `HOME`/`python3`、管理器不存在或管理器拒绝更新时，脚本返回非零状态。
- 脚本不删除、重置、强推、迁移或自动修复 checkout。
- 更新后的 Skill 仍需按现有文档要求在新的 Codex 会话中生效。

## 测试与文档

- 先新增失败测试，证明根脚本尚不存在。
- 在含空格的临时托管路径中真实执行脚本，验证从任意工作目录定位管理器，并验证
  `CODEX_HOME` 显式值与默认值均生成精确 argv。
- 验证管理器的非零退出状态原样传播，并运行 `sh -n update.sh`。
- 运行新增测试、完整 pytest 与 Ruff；README 在现有 Unix 更新章节补充 `update.sh` 用法。
