---
name: loop-engine
description: Run evidence-gated Loop Engineering workflows and manage the Codex adapter lifecycle.
---

# Loop Engineering for Codex

Compatible Core: >=0.3,<0.4
<!-- Legacy lifecycle updater compatibility: name: loop-engineering -->

## Always-on safety kernel

Loop Engineering permits autonomous work only inside the latest explicitly approved,
verifiable contract. The Loop ledger, not conversation memory, is authoritative for task
identity, approval, scope, permissions, budgets, evidence, Checker findings and completion.

Do not mutate before the complete Loop Contract is explicitly approved. The sole
preapproval write is the adapter-owned Draft at
`<project-root>/.loop-runs/.drafts/<loop-id>/contract.yaml`; keep every adapter-owned
preparatory file inside the target project. After Run creation, keep path-based inputs,
validation caches and temporary outputs under `<run-dir>/inputs/`.

Never use prose as evidence of `DONE`. Every mutation still requires the current contract
authorization, an ordinary budget and Gate check, a preceding append-only intent, an observed
result and fresh validator evidence. Medium/high-risk work requires an independent Checker.

## Task-scoped continuation

Only explicit `$loop-engine` may start a new Loop task.
`allow_implicit_invocation: true` is eligibility, not authorization.
After a task is uniquely bound, later user messages may continue it in natural language.
Never use implicit selection to start or adopt a task.

Natural-language clarification, approval, revision, pause recovery, cancellation and feedback
are permitted only when they unambiguously address the same bound task. Without the trigger,
continue only one Pending Draft bound to the visible current conversation or one active
Goal/Run binding verified from native Goal state and the append-only ledger.

If the binding is missing, ambiguous, stale, unrelated, cancelled or terminal, make no Loop
mutation. Require explicit `$loop-engine` for a new task or conservative recovery.
Never scan `.loop-runs/` for a newest Draft or Run.
Do not scan `.loop-runs/` for the newest Draft or Run, rank candidates by time, or adopt a
task because its topic resembles the current message.

## Required project reads

Read `PROTOCOL.md`, the target project's `.loop-engineering/project.yaml`, every existing
configured instruction file, all applicable `AGENTS.md`, and the approved Loop Contract before
modifying state. Resolve `PROTOCOL.md` from the LoopEngineering repository containing this
Skill. If it is absent or its version does not satisfy `>=0.3,<0.4`, stop instead of silently
falling back.

For each new task set `protocol_version: 0.3.0` and `mode: autonomous`. Do not ask the user to
choose a control mode. Reject incompatible mode input; never convert or inherit it.

## Stage routing

Read each required reference directly from this routing table before acting. Multiple rows
may apply to one turn. Resolve each route from the directory containing this `SKILL.md`,
not from the target project's working directory. Do not follow a second layer of playbook references.

| Current operation or stage | Required reference |
|---|---|
| Explicit new task, Pending Draft, complete approval or contract revision | `references/intake-contract.md` |
| Goal creation, reconciliation, continuation, cancellation or Goal completion | `references/goal-bridge.md` |
| Designing, planning, executing, verifying, checking, deciding or Loop completion | `references/execution-loop.md` |
| Installation, update, status, uninstall or project initialization | `references/lifecycle.md` |

If a required reference is missing, unreadable, ambiguous or incompatible with the current
Core version, stop. A route grants no Intake, approval, permission, budget expansion or
completion authority.

## Contract and mutation hard gate

Before approval, only read state and write the one Draft for schema validation. The latest
complete `Ready-to-execute Loop Contract` must disclose objective, scope, acceptance,
validation, design, implementation plan, permissions, exact risks, Git targets and budgets.
One unambiguous approval must bind the current protocol version, contract version, canonical
SHA-256 and every accepted risk ID.

After approval, apply the detailed execution playbook to every action. A new objective,
target, scope, acceptance criterion, evidence contract, dangerous permission, risk, Git target
or budget requires one complete contract revision. Missing or stale authorization, an
unreconciled intent, unrelated Goal, platform hard gate, unavailable authority, unavailable
independent Checker, cancellation or authoritative budget/terminal state requires a pause or
stop exactly as the routed playbook specifies.

## Autonomous execution

The Adapter has no alternate control-mode path. Approval authorizes continuous design,
planning, ordinary implementation, verification and correction only inside the contract.
Risk level alone never adds a routine human gate. Difficulty, a usable test failure or a
remediable Checker finding is not `BLOCKED` or `DONE`.

## Permanent denies

The permanent deny list is force-push, history rewriting, `git reset --hard`, automatic merge and automatic deployment.
Never expose secrets, persist complete model reasoning, overwrite unrelated user changes, or
delete, weaken, skip or hide tests, Gates or schemas to manufacture success.

不得自动合并或部署。不得强推、改写历史、执行 `git reset --hard`、泄露秘密，
或通过删除、弱化、跳过或隐藏测试制造成功。
