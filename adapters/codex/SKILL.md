---
name: loop-engine
description: Use when a coding task must run autonomously inside an approved, evidence-gated Loop Contract.
---

# Loop Engineering for Codex

Core Protocol: 0.1.0

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
rank candidates by time, or adopt a
task because its topic resembles the current message.

### Pending Draft binding

Before a Run exists, natural-language continuation is allowed only when the current Codex
conversation contains exactly one Draft created by an earlier explicit `$loop-engine` start.
Use the visible conversation chain; do not discover Drafts from the filesystem. The binding
covers clarification, the latest complete-contract decision, rejection and cancellation.

Questions, partial decisions, conditional replies, stale references and unrelated messages
are not approvals. Do not combine separate partial replies into approval. Cancellation closes
the conversation binding; a later message cannot silently revive or adopt that Draft.

### Create and bind the default Goal

Every newly approved Codex Loop task uses Goal binding by default. Before approval, include
exact `platform_state` operations for both `codex-goal:create:<resolved-run-dir>` and
`codex-goal:complete:<resolved-run-dir>` in both the complete Loop Contract risk disclosure
and `execution_plan.actions`.
Do not create the Goal before the Run exists and current contract approval is recorded.

The canonical Goal marker is `$loop-engine goal-bridge/v1`; its objective must begin with:

```text
$loop-engine goal-bridge/v1
loop_id: <loop-id>
run_dir: <resolved-absolute-run-directory>
```

The objective is only a durable pointer. It grants no approval, permission, risk acceptance,
budget expansion or completion authority. Do not include the contract version because a
contract revision stays in the same Run; re-read current authorization from the ledger.

After Run creation and approval:

1. Call `get_goal`. If an unrelated active Goal exists, treat it as a platform hard gate;
   never replace or adopt it. Reconcile an already matching Goal instead of creating another.
2. Serialize and run the exact `platform_state` `gate check` for Goal creation.
3. Record a Loop intent containing the loop ID, absolute run directory and canonical
   objective SHA-256.
4. Call `create_goal`. Do not set `token_budget` unless the user explicitly supplies it;
   never infer a token amount from Loop budgets.
5. Observe the real Goal state and record the result. Persist a Goal identifier only when
   the tool actually returns one; never invent it.

If the native Goal tools are unavailable, a Goal is unrelated, or creation cannot be proven,
hard-pause Goal binding. Explicit `$loop-engine` may conservatively continue the identified
Run, but implicit selection may not substitute a newest-Run guess.

If execution stops between the create intent and result, call `get_goal` and compare the
canonical objective before doing anything else. A match reconciles the existing intent; a
mismatch or ambiguous response pauses. Never create a second Goal as a blind retry.

### Resume a Goal/Run binding

At the start of every host continuation:

1. Use `get_goal` to verify the canonical objective, loop ID and absolute run directory.
2. Run `loop-engine run events` and require a matching successful Goal binding, or
   reconcile the one pending Goal-create intent against real host state.
3. Run `loop-engine run status` and revalidate the current contract authorization binding:
   current `protocol_version`, `contract_version`, `contract_sha256` and complete
   `accepted_risk_ids` must match the append-only approval event.
4. Reconcile every pending intent against real Git, filesystem, native Goal or external
   service state before any new action; never retry an unmatched intent blindly.
5. Run `loop-engine budget check`, followed by the ordinary per-action Gate and Maker loop.
   Never rely on model memory as the source of truth.
6. Apply a user message only when it unambiguously addresses this task or its current prompt;
   otherwise return without mutation.

Any mismatch, unrelated active Goal, missing Goal tool, stale contract approval or pending
intent pauses the bridge. Never infer approval or task identity from Goal continuation alone.

### Yield, cancel and finish

- For `AWAITING_APPROVAL` or an ordinary `PAUSED`, stop automatic actions and accept an
  unambiguous natural-language reply for the verified binding.
- For user cancellation, close a Pending Draft binding or transition a mutable Run to
  `PAUSED` with a stable `user_cancelled:` reason. A cancelled task cannot resume implicitly;
  preserve its ledger and require explicit `$loop-engine` for new work.
- For `BLOCKED` or `BUDGET_EXHAUSTED`, leave the Goal unfinished and report the exact stop
  reason. These immutable Runs cannot continue implicitly or have either budget expanded.
- Only after authoritative Loop `DONE` may the Adapter gate the exact Goal-completion
  `platform_state`, record its intent, call `update_goal` with `complete`, and record the
  observed result.
- Do not call `update_goal` with `blocked`; Codex blocking has separate host rules and is not
  a safe mapping from a Loop status.

Codex Goal token usage is an outer host limit. Loop iterations, elapsed minutes and Checker
revisions remain independent inner limits. Neither budget changes or authorizes the other.

## Adapter lifecycle

Installation and removal are user-operated bootstrap actions, not Maker-loop
actions. Explain the exact command, but never run it on the user's behalf. The
managed checkout is exactly `<CODEX_HOME>/skills/loop-engine`; resolve
`CODEX_HOME` explicitly, defaulting to `~/.codex` only when it is unset.

Unix install reference:

```bash
codex_home="${CODEX_HOME:-$HOME/.codex}"
skill_dir="$codex_home/skills/loop-engine"
mkdir -p "$codex_home/skills" && \
git clone --depth 1 --branch master "https://github.com/MRongM/LoopEngineering.git" "$skill_dir" && \
python3 "$skill_dir/adapters/codex/scripts/manage.py" install --codex-home "$codex_home" && \
loop-engine --version
```

PowerShell install reference:

```powershell
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
$skillDir = Join-Path $codexHome "skills/loop-engine"
$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path (Join-Path $codexHome "skills") | Out-Null
git clone --depth 1 --branch master "https://github.com/MRongM/LoopEngineering.git" "$skillDir"
if ($LASTEXITCODE -ne 0) { throw "Loop Engineering install failed" }
py -3.12 "$skillDir/adapters/codex/scripts/manage.py" install --codex-home "$codexHome"
if ($LASTEXITCODE -ne 0) { throw "Loop Engineering install failed" }
loop-engine --version
if ($LASTEXITCODE -ne 0) { throw "Loop Engineering install failed" }
```

For uninstall, first move outside the checkout. Use the same resolved home and run
`python3 "<skill-dir>/adapters/codex/scripts/manage.py" uninstall --codex-home "<resolved-home>" --yes`
on Unix or replace `python3` with `py -3.12` in PowerShell.

- The manager rejects wrong paths, linked directories, invalid markers, dirty or
  untracked files, local branches, stashes, unpreserved commits, execution from
  inside the checkout, missing prerequisites and unexpected `uv` failures. An
  already absent CLI is a valid partial-uninstall state.
- Never replace the manager with raw `rm`, an overwrite, a force flag, a symlink,
  or a remote script pipe. Start a new Codex session after either lifecycle action.

Use the copy-paste Unix and Windows commands in the repository `README.md` and
`docs/adoption.md`; run `manage.py --help` for the local command reference.

Read `PROTOCOL.md`, the target project's `.loop-engine/project.yaml`,
every existing configured instruction file, all applicable `AGENTS.md`, and the
approved Loop Contract before modifying state.

Resolve `PROTOCOL.md` from the LoopEngineering repository containing this Skill.
If it is absent or its version is not exactly `0.1.0`, stop instead of
silently falling back.

## Hard gate

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

## Intake

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
   boundaries below may interrupt.

## Autonomous decision loop

After the current bound contract approval, advance through
`designing -> planning -> executing -> verifying -> checking -> deciding` without a
routine confirmation between stages. Each iteration selects one unmet acceptance criterion,
chooses the next smallest action inside the approved scope, observes real feedback, records
fresh evidence, applies the required Checker verdict and then makes exactly one state decision.
The action must also be contained by `execution_plan`; allowed paths alone do not expand it.

| Observed facts | Required decision |
|---|---|
| Fresh evidence and material progress | Continue to the next smallest action or the next unmet criterion. |
| A test or command failure with new information | Return to diagnosis, form a new causal hypothesis and revise the plan before another mutation. |
| Two consecutive iterations without new evidence or material progress | Return to diagnosis; do not continue the same implementation strategy. |
| Checker `REVISE` | Return to planning or executing, apply the findings and consume one Checker revision. |
| Checker `BLOCK` | Stop mutations; enter BLOCKED only for missing external authority or state, otherwise return to diagnosis with the exact finding. |
| Checker `ACCEPT` plus every current DONE fact | Build the strict CompletionContext and run authoritative completion evaluation. |
| The authoritative budget check reports exhaustion | Transition to BUDGET_EXHAUSTED without expanding the approved budget. |

The same failed strategy may be attempted at most once. Difficulty is never evidence of
BLOCKED or DONE, and natural-language confidence never substitutes for command results.

### Maker action protocol

For each unmet acceptance criterion:

1. Run `loop-engine budget check "<run-dir>"`. An exhausted result transitions
   to BUDGET_EXHAUSTED. A diagnosis-required result returns to planning and requires
   a new causal hypothesis before another action. Otherwise choose one smallest
   verifiable increment.
2. Serialize the exact ActionRequest under `<run-dir>/inputs/` and run
   `loop-engine gate check "<run-dir>" "<request-json>"`.
   Handle the returned decision exactly:
   - `allow`: continue without another human confirmation.
   - `pause` with `required_gate=contract_revision`: add the new exact target,
     permission and full risk disclosure to the next contract version, then request
     one revised complete-summary approval.
   - `pause` with `required_gate=contract_approval`: the current bound approval is
     missing or stale; return to the complete contract approval instead of showing an
     isolated risk prompt.
   - `deny`: record the rejection and never execute the operation.
3. Immediately before every approved external state change, run
   `loop-engine run intent` with the exact action and target.
4. Make the change without touching unrelated user work.
5. Run `loop-engine run result` immediately after observing real state,
   marking whether new evidence/progress occurred and whether the strategy was reused.
   Git results use payload shape
   `{"git":{"repository_id":"target","operation":"push","success":true,
   "commit_sha":"<sha>","pr_url":"<url-or-empty>"}}`; record `create_pr` as a
   separate successful operation. Completion derives per-repository delivery only
   from these current-contract result events, never from prose.
6. Run `loop-engine evidence run "<run-dir>" "<VAL-ID>"`.
   Core executes validation in a disposable Git snapshot under
   `.loop-engine/cache/`, closes timeout/start failures as failed results and rejects any
   concurrent mutation of the source repository.
7. Do not repeat the same failed strategy more than once.
8. For multiple repositories, follow the contract's acyclic `depends_on` order,
   create one branch/PR per repository, and list prerequisite PRs in each dependent PR.

## Engineering and persistence

- Apply KISS and YAGNI to the accepted behavior; use DRY and SOLID only where the
  current scope contains material repetition or a clear responsibility boundary.
- Preserve unrelated user changes and follow the target repository's existing style.
- Treat `events.jsonl` as append-only. Never rewrite approvals, intents, results,
  evidence references or Checker findings to make a run appear successful.
- Persist only redacted operational evidence; never persist secrets or model reasoning.

### Checker protocol

- Low risk: Maker self-checks against the contract and raw evidence.
- Medium/high risk: dispatch a fresh independent Checker context.
- Checker reads the contract, actual diff and raw evidence, then returns only
  `ACCEPT`, `REVISE` or `BLOCK` with findings and evidence.
- Record the verdict and findings with `loop-engine run checker`.
- Checker never edits production code. `REVISE` returns to Maker and consumes a revision.
- If an independent Checker is unavailable, medium/high work cannot become DONE.

## Autonomous execution

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

## Hard pause and stop boundaries

Pause automatic execution only when one of these facts is true:

- A complete contract revision is required for changed objective, scope, acceptance,
  repository/Git target, dangerous permission, budget or newly discovered risk.
- The current bound approval is missing, stale or mismatched against the current protocol,
  contract version, canonical hash or complete risk IDs.
- The Goal/Run binding is missing, ambiguous, stale or unrelated.
- A pending intent cannot be reconciled against real local, Git, native Goal or external state.
- A platform or external authentication hard gate requires human-only action.
- The necessary authority or input is unavailable and cannot be derived inside the contract.
- A required independent Checker is unavailable for medium/high-risk work.
- The user cancels or explicitly pauses the bound task.
- An authoritative budget or terminal state is reached.

Risk level alone is not a pause boundary. Ordinary authorized work, test failures with usable
feedback and Checker revisions are handled inside the loop without asking the user.
Permanent-deny operations remain denied and must never be converted into confirmation or
contract-revision prompts.

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

## Completion

Do not claim DONE from prose. Build the strict CompletionContext at
`<run-dir>/inputs/completion-context.json` and run
`loop-engine completion evaluate "<contract-path>" "<context-json>"`.
Populate it only from the current code fingerprint, fresh validator evidence, the current scope result,
required Checker `ACCEPT`, current contract authorization and no unresolved intent.
Never use prose, stale evidence or Maker confidence as completion evidence.
Only a zero exit code permits calling `loop-engine run complete "<run-dir>"
--actor maker --reason "all DONE requirements passed"`. That authoritative command
re-derives evidence records and hashes, current fingerprints, scope, Git delivery,
approvals, pending intents and Checker status before transitioning. Verify every
acceptance criterion has fresh evidence and approved Git/PR delivery completed. Use the
`loop-engine git` subcommands only after a matching gate decision and emit the
final report from `templates/final-report.md`.

Set `scope_valid` in CompletionContext only from
`loop-engine scope check "<contract-path>"`; do not infer it from Maker prose.
Derive `checker_verdict`, `gates_clear` and
`contract_current` from `loop-engine run status "<run-dir>"`: unresolved
intent IDs, a paused state, or a required contract gate without an approval event make
`gates_clear=false`, and contract versions must match.
Populate evidence only from validator result events returned by
`loop-engine run events "<run-dir>"`.

The permanent deny list is force-push, history rewriting, reset --hard, automatic merge and automatic deployment.
不得自动合并或部署。不得强推、改写历史、执行 `git reset --hard`、泄露秘密，
或通过删除/弱化测试制造成功。
