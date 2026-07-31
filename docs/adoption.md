# 在其他项目中使用 Loop Engineering

## 立即可用：人工引用规范

1. 在任务中提供规范地址：
   `https://github.com/MRongM/LoopEngineering/blob/master/docs/superpowers/specs/2026-07-30-loop-engineering-protocol-design.md`。
2. 明确控制模式：`collaborative` 或 `autonomous`。
3. 提供目标仓库、目标、验收标准和期望的 Git 权限。
4. 要求 Agent 先只读调查并起草 Loop Contract。
5. 审阅目标、范围、证据命令、预算、危险权限和 Git 目标。
6. 明确批准后再允许 Agent 修改代码。
7. 最终只接受包含测试证据、Checker 结论和 Git/PR 状态的报告。

Codex 与 Claude Code Adapter 未显式指定模式时默认 `autonomous`；用户显式指定
`collaborative` 或 `autonomous` 时始终以用户选择为准。Core 对缺少 `mode` 的合同仍默认 `collaborative`。
因此，该兼容路径不会被 Adapter 的缺省行为静默升级。

可直接使用以下任务模板：

```text
请读取 Loop Engineering 规范：
https://github.com/MRongM/LoopEngineering/blob/master/docs/superpowers/specs/2026-07-30-loop-engineering-protocol-design.md

控制模式：autonomous
目标仓库：/work/acme-orders
目标：实现一个明确、可验证的目标
验收标准：
- 可重复验证的行为一
- 可重复验证的行为二
Git 权限：允许创建隔离分支、原子提交、推送和 PR；禁止自动合并与部署

先只读调查并起草 Loop Contract，等待我明确批准后再执行。
```

## 托管安装与卸载：CLI + Codex Skill

### 0. 检查前置条件

- Python 3.12–3.14。
- `uv` 与 Git 可用。
- 只有创建 GitHub PR 时才需要已认证的 `gh` CLI。
- 托管安装固定使用 `<CODEX_HOME>/skills/loop-engineering`；未设置
  `CODEX_HOME` 时默认使用 `~/.codex`。
- 目标项目示例路径为 `/work/acme-orders`，请替换为自己的绝对路径。

生命周期管理器同时管理完整 Skill 检出和 CLI。它不覆盖已有目录、不使用
符号链接，也不会在卸载失败时继续删除 Skill。

### 1. Unix 托管安装

```bash
codex_home="${CODEX_HOME:-$HOME/.codex}"
skill_dir="$codex_home/skills/loop-engineering"
mkdir -p "$codex_home/skills" && \
git clone --depth 1 --branch master "https://github.com/MRongM/LoopEngineering.git" "$skill_dir" && \
python3 "$skill_dir/adapters/codex/scripts/manage.py" install --codex-home "$codex_home" && \
loop-engineering --version
```

预期输出：`0.2.0`。创建新的 Codex 会话以重新发现 Skill。

卸载前先切换到 Skill 目录之外。`--yes` 只确认删除经过校验的精确托管目录；
如果仓库存在修改、未跟踪或忽略文件，管理器会拒绝删除：

```bash
codex_home="${CODEX_HOME:-$HOME/.codex}"
skill_dir="$codex_home/skills/loop-engineering"
python3 "$skill_dir/adapters/codex/scripts/manage.py" uninstall --codex-home "$codex_home" --yes
```

CLI 已不存在时，管理器仍可清理完整且干净的 Skill 检出；其他 `uv` 错误会保留
Skill 目录以便排查。卸载后创建新的 Codex 会话。

### 2. Windows PowerShell 托管安装与卸载

安装：

```powershell
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
$skillDir = Join-Path $codexHome "skills/loop-engineering"
$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path (Join-Path $codexHome "skills") | Out-Null
git clone --depth 1 --branch master "https://github.com/MRongM/LoopEngineering.git" "$skillDir"
if ($LASTEXITCODE -ne 0) { throw "Loop Engineering install failed" }
py -3.12 "$skillDir/adapters/codex/scripts/manage.py" install --codex-home "$codexHome"
if ($LASTEXITCODE -ne 0) { throw "Loop Engineering install failed" }
loop-engineering --version
if ($LASTEXITCODE -ne 0) { throw "Loop Engineering install failed" }
```

卸载前将 PowerShell 当前目录切换到 Skill 检出之外，然后执行：

```powershell
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
$skillDir = Join-Path $codexHome "skills/loop-engineering"
py -3.12 "$skillDir/adapters/codex/scripts/manage.py" uninstall --codex-home "$codexHome" --yes
```

不要用手工递归删除替代管理器。如果管理器拒绝执行，应先检查并保留它报告的本地状态。

### 3. 初始化目标项目

```bash
loop-engineering project init --root "/work/acme-orders" --update-gitignore
```

该命令只创建 `.loop-engineering/project.yaml`，并按显式参数把
`.loop-runs/` 加入 `.gitignore`；不会选择自动模式，也不会复制 Core。

### 4. 添加项目入口约束

在项目根 `AGENTS.md` 中加入：

```markdown
Never invoke Loop Engineering automatically.
Only a current-message $loop-engine invocation starts a new Loop task.
Every user message that should run or continue Loop Engineering must include $loop-engine.
In Claude Code, only a current-message /loop-engineering:loop-engine invocation starts or continues a Loop task.
Require an approved Loop Contract before mutation and evidence before DONE.
```

### 5. 发起任务

```text
$loop-engine
控制模式：autonomous
目标：修复订单重复提交问题
验收：先复现失败，再证明修复；相关回归测试通过
Git：允许创建分支、提交、推送和 PR
```

### 6. 批准并观察

适配器的所有预备阶段文件写入都必须在目标项目的 `.loop-runs/` 中完成：审批前
契约草稿位于 `.loop-runs/.drafts/<loop-id>/contract.yaml`，运行创建后的请求、上下文、
验证缓存和临时输出位于对应运行目录，其中路径型 CLI 输入统一放入 `inputs/`。由于
草稿位于嵌套目录，契约中的仓库路径必须填写解析后的绝对路径。不得在系统临时目录、
用户主目录或其他项目外位置创建适配器控制文件，也不得提交 `.loop-runs/` 内容。

Agent 必须先展示 Loop Contract；Autonomous 契约还必须用一个风险表披露精确操作、
影响、最坏结果和恢复方式。一次批准后，运行状态位于：
`/work/acme-orders/.loop-runs/loop-example-001/`。契约内已接受风险不再逐项确认；
新目标、权限或风险会生成完整契约修订。平台自身的强制审批仍可能暂停执行。
后续批准或反馈消息若要继续该 Skill，也必须再次显式写出 `$loop-engine`，例如
`$loop-engine 确认`。

### 7. 验收交付

检查 `final-report.md`、测试证据、Checker 结论、提交和 PR。合并与部署仍由人工执行。

## Claude Code 原生 Plugin/Marketplace

Claude Code Adapter 使用宿主原生插件生命周期，不复制 Codex 的托管检出管理器。
需要支持 Plugin 的 Claude Code、Python 3.12+、Git 和 `uv`。以下均为用户在 Shell
中执行的 bootstrap 操作，Adapter 不得代替用户运行。

### 1. 安装

先安装 Core CLI，再注册仓库 Marketplace 并在 user scope 安装插件：

```bash
uv tool install "git+https://github.com/MRongM/LoopEngineering.git@master"
claude plugin marketplace add MRongM/LoopEngineering
claude plugin install loop-engineering@loop-engineering --scope user
loop-engineering --version
```

插件源是完整仓库，因此已安装 Skill 可以读取根级唯一权威 `PROTOCOL.md`；插件清单
只暴露 `adapters/claude/`。安装完成后运行 `/reload-plugins` 或启动新会话。

规范手动入口是：

```text
/loop-engineering:loop-engine
目标：实现一个明确、可验证的目标
```

Skill 设置 `disable-model-invocation: true`，Claude 不得根据任务语义自动调用。每条启动、
继续、批准或反馈消息都必须再次显式调用，例如：

```text
/loop-engineering:loop-engine confirm
```

部分 Claude Code 版本还会提供 `/loop-engine` 非命名空间别名；跨版本文档和审批恢复统一
使用规范命名空间入口。

### 2. 更新

Marketplace、插件与 CLI 分别显式更新：

```bash
claude plugin marketplace update loop-engineering
claude plugin update loop-engineering@loop-engineering --scope user
uv tool install --reinstall "git+https://github.com/MRongM/LoopEngineering.git@master"
loop-engineering --version
```

更新后运行 `/reload-plugins` 或启动新会话。不得通过 Hook、后台任务或 Adapter 自动更新。

### 3. 卸载

```bash
claude plugin uninstall loop-engineering@loop-engineering --scope user
uv tool uninstall loop-engineering
```

如不再需要该 Marketplace，可由用户通过 Claude 原生命令单独移除；删除 Marketplace
可能同时影响其插件状态，执行前应先使用 `claude plugin marketplace list` 核对精确名称。

### 4. 本地开发验证

从仓库根运行：

```bash
claude plugin validate .
```

该命令只验证 Marketplace、Plugin 与 Skill 元数据。完整验收仍需定向测试、全量测试、
Ruff、范围检查、独立 Checker 和 Core Completion Evaluator。
