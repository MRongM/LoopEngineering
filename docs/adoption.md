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

## 实现完成后：CLI + Codex Skill

### 0. 检查前置条件

- Python 3.12–3.14。
- `uv` 与 Git 可用。
- 只有创建 GitHub PR 时才需要已认证的 `gh` CLI。
- 本地已检出 LoopEngineering；以下 Unix 示例路径为 `/opt/LoopEngineering`，
  目标项目示例路径为 `/work/acme-orders`，请替换为自己的绝对路径。

### 1. 安装 CLI

开发检出：

```bash
uv tool install --editable "/opt/LoopEngineering"
```

发布 `v0.1.0` 标签后：

```bash
uv tool install "git+https://github.com/MRongM/LoopEngineering.git@v0.1.0"
```

验证：

```bash
loop-engineering --version
```

预期输出：`0.1.0`。

### 2. 安装 Codex Skill

将仓库内 `adapters/codex` 链接到 Codex Skills 目录。目标路径必须由用户明确指定：

```bash
mkdir -p "/Users/alice/.codex/skills"
ln -s "/opt/LoopEngineering/adapters/codex" "/Users/alice/.codex/skills/loop-engineering"
```

如果目标已存在，先检查其来源，不要覆盖。创建新 Codex 会话以重新发现 Skill。

Windows PowerShell：

```powershell
New-Item -ItemType Directory -Force -Path "C:/Users/Alice/.codex/skills"
New-Item -ItemType SymbolicLink -Path "C:/Users/Alice/.codex/skills/loop-engineering" -Target "C:/Tools/LoopEngineering/adapters/codex"
```

### 3. 初始化目标项目

```bash
loop-engineering project init --root "/work/acme-orders" --update-gitignore
```

该命令只创建 `.loop-engineering/project.yaml`，并按显式参数把
`.loop-runs/` 加入 `.gitignore`；不会选择自动模式，也不会复制 Core。

### 4. 添加项目入口约束

在项目根 `AGENTS.md` 中加入：

```markdown
For every state-changing engineering task, invoke $loop-engineering.
Require an approved Loop Contract before mutation and evidence before DONE.
```

### 5. 发起任务

```text
$loop-engineering
控制模式：autonomous
目标：修复订单重复提交问题
验收：先复现失败，再证明修复；相关回归测试通过
Git：允许创建分支、提交、推送和 PR
```

### 6. 批准并观察

Agent 必须先展示 Loop Contract。批准后，运行状态位于：
`/work/acme-orders/.loop-runs/loop-example-001/`。自动模式只在终态或安全门禁暂停。

### 7. 验收交付

检查 `final-report.md`、测试证据、Checker 结论、提交和 PR。合并与部署仍由人工执行。
