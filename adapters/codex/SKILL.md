---
name: loop-engine
description: Use when a coding task must run autonomously inside an approved, evidence-gated Loop Contract.
---

# Loop Engineering for Codex

Core Protocol: 0.1.0

## Always-on safety kernel

Loop Engineering permits autonomous work only inside the latest explicitly approved,
verifiable contract. The append-only Loop ledger, not conversation memory or a Goal pointer,
is authoritative for task identity, approval, scope, permissions, budgets, evidence, Checker
findings and completion.

Do not mutate before the complete Loop Contract is explicitly approved. The only preapproval
writes are canonical project initialization under `.loop-engine/` and the adapter-owned Draft
at `<project-root>/.loop-engine/drafts/<loop-id>/contract.yaml`; never write preparatory state
outside the target project or stage runtime content.

Never use prose as evidence of `DONE`. Every external mutation still requires current contract
authorization, an ordinary budget and Gate check, a preceding append-only intent, an observed
result and fresh validator evidence. Medium/high-risk work still requires an independent Checker.

## Task-scoped continuation

Only explicit `$loop-engine` may start a new Loop task.
`allow_implicit_invocation: true` is eligibility, not authorization.
After a task is uniquely bound, later user messages may continue it in natural language.
Never use implicit selection to start or adopt a task.
The trigger name does not rename Loop Engineering, the `loop-engineering` Python
distribution, or repository.

Natural-language clarification, approval, revision, pause recovery, cancellation and feedback
are permitted only when they unambiguously address the same bound task. An unrelated message
does not become Loop input merely because a task is active.

Resolve admission before Intake, approval, Run adoption or any other mutation:

1. An explicit `$loop-engine` message with no bound task may start a new Intake.
2. An explicit message that addresses one uniquely bound task continues that task and does
   not create another one.
3. Without the trigger, continue only one Pending Draft bound to the current conversation or
   one active Goal/Run binding verified from native Goal state and the append-only ledger.
4. If the binding is missing, ambiguous, stale, unrelated, cancelled or terminal, make no
   Loop mutation. Require explicit `$loop-engine` for a new task or conservative recovery.

Do not scan `.loop-engine/drafts/` or `.loop-engine/runs/` for the newest Draft or Run,
rank candidates by time, or adopt a task because its topic resembles the current message.

## Required project reads

Read `PROTOCOL.md`, the target project's `.loop-engine/project.yaml`, every existing configured
instruction file, all applicable `AGENTS.md`, the latest approved Loop Contract and each routed
playbook required for the current stage before modifying state.

Resolve `PROTOCOL.md` from the LoopEngineering repository containing this Skill. If it is
absent or its version is not exactly `0.1.0`, stop instead of silently falling back.

For every new task set `protocol_version: 0.1.0` and `mode: autonomous`. Do not ask the user
to choose a control mode. Reject incompatible mode input instead of converting, recovering or
inheriting it from another task.

## Stage routing

Read each required reference directly from this routing table before acting. Multiple rows
may apply to one turn. Resolve each route from the directory containing this `SKILL.md`, not
from the target project's working directory. Do not follow a second layer of playbook references.

| Current operation or stage | Required reference |
|---|---|
| Explicit new task, Pending Draft, complete approval or contract revision | `references/intake-contract.md` |
| Goal creation, reconciliation, continuation, cancellation or Goal completion | `references/goal-bridge.md` |
| Designing, planning, executing, verifying, checking, deciding or Loop completion | `references/execution-loop.md` |
| Installation, update, status, uninstall or project initialization | `references/lifecycle.md` |

If a required reference is missing, unreadable, ambiguous or incompatible with Core Protocol
`0.1.0`, stop. A route grants no Intake, approval, permission, budget expansion or completion
authority.

## Contract and mutation hard gate

Before approval, only read state and perform the two explicitly allowed preapproval writes
described by the safety kernel and Intake playbook. The latest complete
`Ready-to-execute Loop Contract` must disclose objective, scope, acceptance, isolated
validation, design decisions, exact action plan, permissions, risks, Git targets and budgets.
One unambiguous approval must bind the protocol version, contract version, canonical SHA-256
and every accepted risk ID through the run ledger.

After approval, apply the routed execution playbook to every action. A new objective, action,
target, scope, acceptance criterion, validation command, permission, risk, Git target or budget
requires one complete contract revision. Missing or stale authorization, an unreconciled intent,
an unrelated Goal, a platform hard gate, unavailable authority, an unavailable independent
Checker, cancellation or an authoritative budget/terminal state requires the exact pause or stop
defined by the routed playbook.

## Autonomous execution

The Adapter has no alternate control-mode path. The one complete approval authorizes continuous
design, planning, ordinary implementation, verification and correction only inside the
execution-closed contract. Risk level alone never adds a routine human gate. Difficulty, a usable
test failure or a remediable Checker finding is not `BLOCKED` or `DONE`.

## Permanent denies

The permanent deny list is force-push, history rewriting, `git reset --hard`, automatic merge and automatic deployment.
Never expose secrets, persist complete model reasoning, overwrite unrelated user changes, or
delete, weaken, skip or hide tests, Gates or schemas to manufacture success.

不得自动合并或部署。不得强推、改写历史、执行 `git reset --hard`、泄露秘密，
或通过删除、弱化、跳过或隐藏测试制造成功。
