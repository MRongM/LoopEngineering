# Loop Engineering 0.3.0 兼容性与命名

本文是当前发布的兼容性入口。规范语义以 [Core Protocol](../PROTOCOL.md) 和
[0.3 Autonomous-only 设计](superpowers/specs/2026-07-31-loop-engineering-0.3-autonomous-only-design.md)
为准。

## 名称边界

| 身份 | 当前名称 |
|------|----------|
| 产品与仓库 | Loop Engineering |
| Python 分发包 | `loop-engineering` |
| Codex 托管 checkout | `loop-engineering` |
| Codex Skill 触发词 | `$loop-engine` |
| 唯一 Shell CLI | `loop-engine` |

0.3.0 不提供 CLI alias：`loop-engineering` 和 `loop-agent` 都不是可执行入口。
生命周期管理器仍按 Python 分发包名安装或卸载，同时验证唯一的 `loop-engine`
executable。名称相似不表示它们可以互换。

## 合同与 Run 兼容矩阵

0.3.0 省略 `mode` 时解析为 `autonomous`；旧版本省略 `mode` 时拒绝读取，
因为不能把历史上低权限的缺省语义静默提升为 Autonomous。

| 输入 | 0.3 行为 |
|------|----------|
| 0.3.0 省略 `mode` | 解析为 `autonomous` |
| 0.3.0 显式 `mode: autonomous` | 接受 |
| 0.1.0/0.2.0 显式 `mode: autonomous` | 兼容读取，并保留对应历史风险与最终门禁规则 |
| 0.1.0/0.2.0 省略 `mode` | 拒绝；旧版本省略 `mode` 时拒绝读取 |
| 任意版本显式 `mode: collaborative` | 确定性拒绝 |
| collaborative 或省略模式的历史 Run | 拒绝恢复 |

升级旧 Autonomous 工作时，应创建新的 0.3 合同版本，并重新取得绑定当前版本、
规范化 SHA-256 和完整风险 ID 的批准。系统不提供自动迁移，不会把旧合同、旧 Run
或缺失字段静默转换成更高权限的 Autonomous。

## 历史材料

`docs/superpowers/` 中较早的设计和计划保留为历史审计记录，其中可能包含已经移除
的命令拼写或控制模式。这些文件不是当前执行指南，也不构成 CLI alias 或兼容承诺。
复制命令时只使用 README、本接入指南和当前 `$loop-engine` Skill 中的示例。
