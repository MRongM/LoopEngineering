# Loop Engineering Codex Skill 更新命令设计

- 状态：用户已批准
- 日期：2026-07-31
- 执行模式：`autonomous`，主代理 inline 执行
- 基线：Loop Engineering Core Protocol 0.1.0 与现有 Codex 生命周期管理器

## 1. 背景

当前托管生命周期只提供 `install` 和 `uninstall`。安装会将完整仓库克隆到
`<CODEX_HOME>/skills/loop-engineering`，再从该检出安装 CLI；缺少更新入口时，
用户无法用同一组路径、来源和本地状态校验安全地同步 Skill 与 CLI。

## 2. 目标

新增用户主动调用的 `manage.py update` 子命令。它只接受现有精确托管检出，
只从官方 `origin/master` 执行快进更新，并从更新后的本地检出重新安装 CLI。
更新过程必须使用 argv 子进程和 `shell=False`，任何不安全或不一致状态均失败关闭。

## 3. 非目标

- 不更新其他 Codex Skills，也不增加定时、后台或自动更新。
- 不增加版本选择、降级、回滚、删除后重装或远程脚本执行。
- 不改变 Core CLI、协议、Schema、依赖或项目初始化。
- 不在开发验证中对真实安装目录执行更新或发起网络请求。
- 不创建分支、提交、推送、PR、合并、部署、强推或历史改写。

## 4. 命令接口

Unix：

```bash
codex_home="${CODEX_HOME:-$HOME/.codex}"
skill_dir="$codex_home/skills/loop-engineering"
python3 "$skill_dir/adapters/codex/scripts/manage.py" update --codex-home "$codex_home" && \
loop-engineering --version
```

Windows PowerShell：

```powershell
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
$skillDir = Join-Path $codexHome "skills/loop-engineering"
py -3.12 "$skillDir/adapters/codex/scripts/manage.py" update --codex-home "$codexHome"
if ($LASTEXITCODE -ne 0) { throw "Loop Engineering update failed" }
loop-engineering --version
if ($LASTEXITCODE -ne 0) { throw "Loop Engineering update failed" }
```

调用 `update` 本身就是对已公开 Git 拉取与 CLI 重装动作的明确授权，因此不增加
`--yes`。该命令不删除文件；卸载仍单独要求 `--yes`。

## 5. 组件边界

`adapters/codex/scripts/manage.py` 继续独占 Codex 生命周期行为。现有
`_validate_checkout` 负责路径、链接和仓库标记；现有 `_ensure_clean` 负责工作树、
本地引用和未保存提交。新增更新来源校验与编排函数，不向 Core 引入 Codex 或 GitHub
知识，也不增加依赖。

生命周期安装逻辑复用一个带 `reinstall` 参数的内部函数：普通 `install` 保持原有
argv，`update` 使用 `uv tool install --reinstall <repository>`。`uv tool upgrade`
不适用，因为它不能同步承载 Skill 文件的 Git 检出。

## 6. 更新流程

1. 解析并边界检查 `CODEX_HOME`。
2. 调用 `_validate_checkout`，要求仓库位于精确托管路径、不是链接且标记有效。
3. 调用 `_ensure_clean`，拒绝修改、未跟踪或忽略文件、额外本地分支、stash 和未被
   任一远端保存的提交。
4. 要求当前符号分支精确为 `master`；detached HEAD 和其他分支失败。
5. 要求 `origin` 只有一个 URL，且精确为
   `https://github.com/MRongM/LoopEngineering.git`。
6. 使用精确 argv 执行：

   ```text
   git -C <repository> pull --ff-only origin master
   ```

7. Git 成功后再次执行检出标记、清洁状态、分支和远端校验，防止更新结果或本地 Hook
   使托管状态偏离约束。
8. 使用精确 argv 执行：

   ```text
   uv tool install --reinstall <repository>
   ```

9. 输出成功信息。即使 Git 已是最新版本，也执行重装，以修复 CLI 缺失或与 Skill
   检出不同步的状态。

所有子进程继续统一经 `_run` 使用 `capture_output=True`、`check=False`、
`shell=False` 和 `text=True`。

## 7. 失败与恢复

- 更新前校验失败：不执行 Git 拉取或 uv。
- `git pull --ff-only` 失败：不执行 uv，不采用 merge、rebase、reset 或强制参数。
- Git 成功后的复验失败：不执行 uv，保留实际检出供人工检查。
- uv 失败：保留已更新检出和当前 CLI，明确报告“Git 更新已保留，可修复后重试”。
- 不自动回退分支，因为回退会引入历史改写或覆盖新检出内容的风险。
- 再次运行是统一恢复路径：快进步骤可为空操作，CLI 重装重新尝试。

## 8. 测试策略

先修改 `tests/test_codex_installer.py` 并观察 RED，再修改生产代码：

1. 帮助文本必须公开 `{install,update,uninstall}`。
2. 成功路径锁定清洁检查、分支/远端校验、快进拉取、更新后复验和 uv 重装的精确
   argv，并断言所有子进程使用 `shell=False`。
3. 脏检出、错误分支、detached HEAD、非官方或多个 origin URL 在 pull 前失败。
4. Git 非快进/网络错误不得调用 uv。
5. pull 后标记失效不得调用 uv。
6. uv 失败返回错误并保留 Skill 检出。

随后更新 `tests/test_adapter_contract.py`，锁定 README、采用指南和 Skill 中的 Unix、
PowerShell 命令与安全说明。最后运行定向测试、完整测试、Ruff 和 `git diff --check`。
测试只使用临时目录和桩化子进程，不访问真实网络或真实 Codex 安装。

## 9. 验收标准

1. `manage.py --help` 显示 `update`。
2. 只有精确、干净、官方来源、`master` 分支的托管检出可进入更新。
3. 更新只允许 fast-forward，并从更新后检出强制重装 CLI。
4. 所有失败路径保留 Skill 目录，不删除、不回退、不继续执行不安全后续步骤。
5. Unix 与 Windows 文档命令一致，明确更新后新建 Codex 会话。
6. 定向测试、完整测试、Ruff 与 diff 静态检查均通过。

## 10. 工程原则

- KISS/YAGNI：只增加一个显式子命令和所需校验，不设计通用 Skill 更新框架。
- DRY：复用检出、清洁检查、子进程和安装逻辑。
- SOLID：Codex 生命周期仍留在 Adapter，Core 保持工具无关；来源校验与更新编排各自
  保持单一职责。
