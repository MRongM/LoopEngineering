# Intake and contract playbook

Read this playbook for every explicit new task, its uniquely bound Pending Draft, and any
complete contract revision. Intake is read-only except for the one adapter-owned draft.

## Pending Draft binding

Before a Run exists, natural-language continuation is allowed only when the current Codex
conversation contains exactly one Draft created by an earlier explicit `$loop-engine` start.
Use the visible conversation chain; do not discover Drafts from the filesystem. The binding
covers clarification, the latest complete-contract decision, rejection and cancellation.

Natural-language clarification, approval, revision, pause recovery, cancellation and feedback
are permitted only when they unambiguously address the same bound task. Questions, partial
decisions, conditional replies, stale references and unrelated messages are not approvals.
Do not combine separate partial replies into approval. Cancellation closes the conversation
binding; a later message cannot silently revive or adopt that Draft.

## Hard gate

Do not edit files, install dependencies, create Git refs, commit, push, open a PR,
or call an external write API until the Loop Contract has been shown to the user
and explicitly approved. The contract's exact preauthorization may cover later
Git actions. New targets or permissions require a revised approval.

The sole preapproval write is the adapter-owned contract draft at
`<project-root>/.loop-runs/.drafts/<loop-id>/contract.yaml` for schema validation.
Perform every adapter-owned preparatory write inside the target project.
Use resolved absolute paths for every `repositories[].path` because relative paths are
resolved from the nested contract location.
Never create adapter-owned control files outside the target project, including system
temporary directories and the user's home directory. After the run exists, place every
path-based CLI input, validation cache and temporary output under the run directory; use
`<run-dir>/inputs/` for request and context documents. Never stage or commit `.loop-runs/`
content.

## Read-only Intake

1. Classify the request as read-only or state-changing.
2. Set `protocol_version: 0.3.0` and `mode: autonomous` for every new task.
   Do not ask the user to choose a control mode. Reject incompatible mode input instead of
   converting, recovering or inheriting it from another task. Resolve admission
   without a separate mode prompt.
3. Inspect the repository, instructions, tests, recent commits and dirty state read-only.
4. Draft `contract.yaml` from the Core template with exact repositories, paths,
   acceptance criteria, argv validation, budget, permissions and Git targets. For
   nontrivial work, include the key design decisions and the minimal implementation plan.
   List every planned dangerous, production, sensitive-data and Git mutation in
   `authorized_operations` before asking for approval.
   Every `authorized_operations` entry needs `risk_id`, `kind`, `repository_id`,
   exact `target`, `risk_level`, `impact`, `worst_case`, `recovery` and `evidence`.
   Keep the unapproved draft at
   `.loop-runs/.drafts/<loop-id>/contract.yaml` relative to the project root. Populate
   every `repositories[].path` with its resolved absolute Git root.
5. Always use `contract_approval`; do not add `design_approval` or `plan_approval` by default.
   Do not add `final_acceptance` by default. Preserve an extra gate only when the current
   user instruction, project rules or an existing compatible legacy contract explicitly
   requires it. Risk level alone never creates another human gate.
6. Run `loop-engine contract validate "<contract-path>"`.

## Complete execution approval

Present one `Ready-to-execute Loop Contract` summary in this order: mode and objective;
in/out of scope; acceptance criteria and validation; key design and implementation plan;
risk, permissions, exact Git targets and budget; preauthorized actions, remaining pause
conditions and stop conditions.

In autonomous mode, label the risk section `Autonomous Risk Acceptance` and show one table
containing each `risk_id`, `kind`, exact target, `impact`, `worst_case`, `recovery` and
`evidence`. Ask for one pre-execution approval of that complete summary.

Accept one unambiguous natural-language approval of the latest complete summary.
Do not require a fixed confirmation subcommand or trigger prefix.
Questions, partial decisions, conditional replies, stale references and unrelated messages are not approvals.
Before Run creation, require the unique current-conversation Pending Draft binding; after
Goal creation, require the verified Goal/Run binding. Never combine separate replies.

## Run creation

After approval, run
`loop-engine run create "<contract-path>" --project "<project-root>"`,
retain the created `intake` snapshot, record the discovering/drafting/awaiting
transitions and `contract_approval` with `loop-engine run approval`. Core binds
that event to the current contract version, SHA-256 and accepted risk IDs. Then
advance through designing or planning toward execution without another approval
unless an explicit extra gate applies.

The default design and plan stages continue without another approval. Do not add routine
stage confirmation after the one pre-execution approval.

## Contract revision and Autonomous execution

The Adapter has no alternate control-mode path. The one pre-execution approval accepts
the complete contract and every precisely disclosed risk. Continue through designing,
planning and ordinary implementation—including exact `production_access` and
`sensitive_data` entries—until DONE, BLOCKED, BUDGET_EXHAUSTED, contract revision,
user cancellation, or a platform or external-service hard gate. Risk level alone never
creates another human gate or final acceptance.

- A material target, scope, evidence, dangerous permission or budget change pauses the
  run, increments `contract_version`, re-enters contract_drafting/awaiting_approval,
  and invokes `loop-engine run revise` only after explicit approval.
- Record the combined execution authorization as `contract_approval`. Record
  `design_approval` or `plan_approval` separately only when an applicable rule or the
  approved contract explicitly requires that gate. Record final acceptance separately;
  a rejection never permits a forward transition.

## Approval quick reference

| Situation | Adapter action |
|---|---|
| New task | Set Autonomous Protocol 0.3 in the complete contract |
| Initial state-changing task | Request one approval of the ready-to-execute summary |
| Default design and plan stages | Continue without another approval |
| Explicit `design_approval` or `plan_approval` | Pause at the declared extra gate |
| Autonomous exact disclosed risk | Continue from the bound contract approval |
| Autonomous new scope, permission or risk | Request one revised complete-summary approval |
| Compatible legacy 0.1 dangerous action | Run the exact `dangerous_action` gate |

## Common approval mistakes

- Every new task is Autonomous Protocol 0.3; a standalone mode prompt adds no authorization.
- Put design and plan decisions in the ready-to-execute summary; default follow-up approval
  prompts fragment one decision into several.
- Treat scope questions as information gathering and the complete-summary response as
  authorization; never infer approval from partial answers.
- In Autonomous `0.2.0/0.3.0`, treat an emergent danger as contract scope change and bundle it
  into one revision approval; a standalone danger prompt would recreate the duplicate gate.
- Do not treat a contract file by itself as proof of risk acceptance. Use the run-backed
  gate check so the current hash and accepted risk IDs are verified.
- A platform or external-service hard gate is outside Loop authorization and may still
  require user action; never claim the adapter can bypass it.
