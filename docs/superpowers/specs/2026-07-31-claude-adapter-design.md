# Loop Engineering Claude Code Adapter 设计

- 状态：用户已通过 Loop Contract 批准
- 日期：2026-07-31
- 协议基线：Loop Engineering Core Protocol 0.2.0
- 适用范围：Claude Code Adapter、原生插件分发与采用文档

## 1. 目标

在不修改 Core 行为的前提下，为 Claude Code 提供与现有 Codex Adapter 等价的
证据门控执行闭环。宿主无关的合同、Gate、Maker、Checker、证据和完成语义继续由
Core 定义；Claude Code 专有的发现、触发和生命周期行为只存在于 Adapter 与插件元数据中。

## 2. 关键决策

### 2.1 原生分发

采用 Claude Code 原生 Plugin/Marketplace：

- 仓库根 `.claude-plugin/plugin.json` 声明插件，并只暴露
  `./adapters/claude/` 中的 Skill。
- `.claude-plugin/marketplace.json` 将完整仓库作为插件源。
- 完整仓库打包使 Skill 可读取唯一权威根级 `PROTOCOL.md`，不在 Adapter 内复制协议。
- 不新增自定义生命周期管理器。插件安装、更新和卸载由 Claude Code 原生命令负责；
  Core CLI 由 `uv tool` 独立管理。

该结构遵循 Claude Code 官方的
[Plugin](https://code.claude.com/docs/en/plugins) 与
[Marketplace](https://code.claude.com/docs/en/plugin-marketplaces) 约定。

### 2.2 手动激活

Skill frontmatter 设置 `disable-model-invocation: true`，禁止 Claude 根据任务语义自动
选择该 Skill。规范调用名是 `/loop-engineering:loop-engine`；宿主提供的非命名空间
别名只能作为兼容入口，不作为文档主入口。

每个启动或继续 Loop Engineering 的用户消息都必须再次显式调用 Skill。该约束与
Claude Code 会在会话中保留已加载 Skill 内容的行为并存：内容持久化不是后续执行授权。

### 2.3 Core 与 Adapter 边界

Core 保持工具无关。Claude Adapter 只负责：

1. 解析当前消息的显式控制模式，省略时选择 `autonomous`。
2. 收集 Claude Code 可见的 `CLAUDE.md`、`.claude/rules/`、`AGENTS.md` 与项目配置。
3. 起草、展示并记录一次完整合同批准。
4. 在每个状态变化前调用 Core Gate、Intent、Result 和 Evidence 接口。
5. 中高风险时创建全新的独立 Checker 上下文。
6. 使用 Core 的严格完成评估进入 DONE。

不得把 Claude 工具名、Slash Command、插件缓存路径或生命周期命令加入
`src/loop_engineering/`。

## 3. 生命周期

生命周期属于用户执行的 bootstrap，不属于 Maker loop。安装由三个显式步骤组成：

1. 用 `uv tool` 安装 Core CLI。
2. 添加仓库 Marketplace。
3. 在 user scope 安装插件。

更新分别刷新 Marketplace、插件和 CLI；卸载分别移除插件和 CLI。Adapter 只能说明
命令，不能代用户执行。插件变更后使用 `/reload-plugins` 或启动新会话。

不使用远程脚本管道、自动安装 Hook、递归删除、覆盖式复制或宿主配置隐式修改。

## 4. 工作流语义

Claude Skill 复制的是行为契约而非宿主实现细节：

- 状态修改前仍需一次完整 Loop Contract 批准。
- 新目标、路径、危险权限、Git 目标或预算需要完整合同修订。
- Autonomous `0.2.0` 的精确风险接受绑定合同版本、哈希与风险 ID。
- 所有动作依次执行 Budget、Gate、Intent、真实操作、Result 和 Evidence。
- Medium/High 必须获得独立 Checker `ACCEPT`。
- DONE 必须由 Scope、Status、Events 和 Completion Evaluator 的当前证据导出。
- 强推、历史改写、`reset --hard`、自动合并和自动部署永久禁止。

## 5. 测试策略

采用测试先行：先增加失败测试并确认失败来自 Claude Adapter 文件缺失，再逐步实现。

自动化覆盖：

1. Marketplace 与 Plugin JSON 的发现路径和最小组件集。
2. Skill frontmatter 的手动调用边界和 Core 兼容声明。
3. 合同、Gate、Maker、Checker、完成与永久禁止策略标记。
4. README、采用指南与 Skill 中生命周期命令的一致性。
5. Claude 原生 `plugin validate`、定向测试、完整测试、Ruff 与 `git diff --check`。

不通过真实插件安装、用户主目录写入或网络发布来制造测试通过。

## 6. 验收标准

1. Claude Code 能从原生插件清单发现 `adapters/claude/SKILL.md`。
2. Skill 不能被模型自动调用，只能由当前用户消息显式启动。
3. Skill 从完整插件根读取 Core 0.2.0 协议，不维护协议副本。
4. 生命周期命令可复制执行，但 Adapter 自身绝不执行安装、更新或卸载。
5. Core、Schema、CLI、模板与 Codex Adapter 行为保持不变。
6. 所有定向、原生插件、回归、静态与范围验证通过。
