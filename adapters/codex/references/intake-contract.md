# Intake and contract playbook

Read this playbook for every explicit new task, its uniquely bound Pending Draft, complete
contract approval and contract revision. Intake is read-only except for the approved
project-control initialization and one adapter-owned Draft described below.

## Pending Draft binding

Before a Run exists, natural-language continuation is allowed only when the current Codex
conversation contains exactly one Draft created by an earlier explicit `$loop-engine` start.
Use the visible conversation chain; do not discover Drafts from the filesystem. The binding
covers clarification, the latest complete-contract decision, rejection and cancellation.

Questions, partial decisions, conditional replies, stale references and unrelated messages
are not approvals. Do not combine separate partial replies into approval. Cancellation closes
the conversation binding; a later message cannot silently revive or adopt that Draft.

## Contract and mutation hard gate

Do not edit files, install dependencies, create Git refs, commit, push, open a PR,
or call an external write API until the Loop Contract has been shown to the user
and explicitly approved. The contract's exact preauthorization may cover later
Git actions. New targets or permissions require a revised approval.

The only preapproval writes are the canonical project control root created by
`loop-engine project init --root "<project-root>"` and the adapter-owned contract draft at
`<project-root>/.loop-engine/drafts/<loop-id>/contract.yaml` for schema validation.
The control root contains only `.loop-engine/project.yaml`, its internal `.gitignore`,
`.loop-engine/drafts/`, `.loop-engine/runs/<loop-id>/` and `.loop-engine/cache/`;
never create another Loop-owned top-level path.
Use resolved absolute paths for every `repositories[].path` because relative paths are
resolved from the nested contract location.
Never create adapter-owned control files outside the target project, including system
temporary directories and the user's home directory. After the run exists, use
`<run-dir>/inputs/` for request and context documents and `.loop-engine/cache/` for isolated
validation snapshots. Never stage or commit runtime content; only
`.loop-engine/project.yaml` and `.loop-engine/.gitignore` may be committed.

## Intake and contract drafting

1. Classify the request as read-only or state-changing.
2. Set `protocol_version: 0.1.0` and `mode: autonomous` for every new task.
   Do not ask the user to choose a control mode. Reject incompatible mode input instead of
   converting, recovering or inheriting it from another task. Resolve admission
   without a separate mode prompt.
3. Inspect the repository, instructions, tests, recent commits and dirty state read-only.
4. Draft `contract.yaml` from the Core template with exact repositories, paths,
   acceptance criteria, argv validation, budget, permissions and Git targets. For
   every task, persist the key decisions in `execution_plan.design_decisions` and the
   complete minimal action boundary in `execution_plan.actions`; every planned runtime
   ActionRequest must evaluate to `allow` under the
   approved contract. Set every validation command to `workspace_policy: isolated`.
   List every planned dangerous, production, sensitive-data and Git mutation in
   `authorized_operations` before asking for approval.
   Every `authorized_operations` entry needs `risk_id`, `kind`, `repository_id`,
   exact `target`, `risk_level`, `impact`, `worst_case`, `recovery` and `evidence`.
   Represent worktree creation as `git_worktree` with exact target
   `<branch>@<resolved-absolute-worktree-path>` in both the risk grant and action plan.
   Keep the unapproved draft at
   `.loop-engine/drafts/<loop-id>/contract.yaml` relative to the project root. Populate
   every `repositories[].path` with its resolved absolute Git root.
5. Use exactly one human gate: `contract_approval`. Fold all required design, plan and
   risk decisions into the complete contract summary. If a higher-priority rule cannot be
   represented by that approval, do not claim the contract is execution-closed.
6. Run `loop-engine contract validate "<contract-path>"`.
7. Batch every unresolved pre-execution decision into the complete summary. Present one
   `Ready-to-execute Loop Contract` summary in this order: mode and
   objective; in/out of scope; acceptance criteria and validation; key design and
   implementation plan; risk, permissions, exact Git targets and budget; preauthorized
   actions, remaining pause conditions and stop conditions. In autonomous mode, label
   the risk section `Autonomous Risk Acceptance` and show one table containing each
   `risk_id`, `kind`, exact target, `impact`, `worst_case`, `recovery` and `evidence`.
8. Ask for one pre-execution approval of that complete summary.
   Accept one unambiguous natural-language approval of the latest complete summary.
   Do not require a fixed confirmation subcommand or trigger prefix.
   Questions, partial decisions, conditional replies, stale references and unrelated messages are not approvals.
   Before Run creation, require the unique current-conversation Pending Draft binding; after
   Goal creation, require the verified Goal/Run binding. Never combine separate replies.
9. After approval, run
   `loop-engine run create "<contract-path>" --project "<project-root>"`,
   retain the created `intake` snapshot, record the discovering/drafting/awaiting
   transitions and `contract_approval` with `loop-engine run approval`. Core binds
   that event to the current contract version, SHA-256 and accepted risk IDs. Then
   advance through designing or planning toward execution without another approval
   unless a genuine scope, permission or risk change requires a complete revision.
   After approval, do not ask for routine confirmations.
   Accumulate non-blocking questions and report them with the final result; only the hard
   boundaries in the execution playbook may interrupt.

## Contract revision and autonomous authorization

The Adapter has no alternate control-mode path. The one pre-execution approval accepts
the complete contract and every precisely disclosed risk. Continue through designing,
planning and ordinary implementation—including exact `production_access` and
`sensitive_data` entries—until DONE, BLOCKED, BUDGET_EXHAUSTED, contract revision,
user cancellation, or a platform or external-service hard gate. Risk level alone never
creates another human gate or final acceptance.

- A material target, scope, evidence, dangerous permission or budget change pauses the
  run, increments `contract_version`, re-enters contract_drafting/awaiting_approval,
  and invokes `loop-engine run revise` only after explicit approval.
- Record the combined execution authorization as `contract_approval`. The contract does
  not record separate design, plan, dangerous-action or final-acceptance gates; a rejection
  never permits a forward transition.

## Approval quick reference

| Situation | Adapter action |
|---|---|
| New task | Set execution-closed Autonomous Protocol 0.1 in the complete contract |
| Initial state-changing task | Request one approval of the ready-to-execute summary |
| Default design and plan stages | Continue without another approval |
| Design, plan and disclosed danger decisions | Include them in the one complete approval |
| Autonomous exact disclosed risk | Continue from the bound contract approval |
| Autonomous new scope, permission or risk | Request one revised complete-summary approval |

## Common approval mistakes

- Every new task is execution-closed Autonomous Protocol 0.1; a standalone mode prompt adds no authorization.
- Put design and plan decisions in the ready-to-execute summary; default follow-up approval
  prompts fragment one decision into several.
- Treat scope questions as information gathering and the complete-summary response as
  authorization; never infer approval from partial answers.
- Treat an emergent danger as a contract scope change and bundle it
  into one revision approval; a standalone danger prompt would recreate the duplicate gate.
- Do not treat a contract file by itself as proof of risk acceptance. Use the run-backed
  gate check so the current hash and accepted risk IDs are verified.
- A platform or external-service hard gate is outside Loop authorization and may still
  require user action; never claim the adapter can bypass it.
