---
name: loop-engine
description: Run evidence-gated Loop Engineering workflows and manage the Codex adapter lifecycle.
---

# Loop Engineering for Codex

Compatible Core: >=0.2,<0.3
<!-- Legacy lifecycle updater compatibility: name: loop-engineering -->

## Manual invocation

Start this Skill only when the current user message explicitly invokes `$loop-engine`.
Do not infer activation from the task type, a plain-language mention, or a previous task.
Every later user message that should continue this Skill must invoke `$loop-engine` again.
Whenever this Skill pauses, require the user's reply to begin with `$loop-engine`.
The trigger name does not rename Loop Engineering, the `loop-engineering` CLI, or Core.

## Adapter lifecycle

Installation and removal are user-operated bootstrap actions, not Maker-loop
actions. Explain the exact command, but never run it on the user's behalf. The
managed checkout is exactly `<CODEX_HOME>/skills/loop-engineering`; resolve
`CODEX_HOME` explicitly, defaulting to `~/.codex` only when it is unset.

Unix install reference:

```bash
codex_home="${CODEX_HOME:-$HOME/.codex}"
skill_dir="$codex_home/skills/loop-engineering"
mkdir -p "$codex_home/skills" && \
git clone --depth 1 --branch master "https://github.com/MRongM/LoopEngineering.git" "$skill_dir" && \
python3 "$skill_dir/adapters/codex/scripts/manage.py" install --codex-home "$codex_home" && \
loop-engineering --version
```

PowerShell install reference:

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

Read `PROTOCOL.md`, the target project's `.loop-engineering/project.yaml`,
every existing configured instruction file, all applicable `AGENTS.md`, and the
approved Loop Contract before modifying state.

Resolve `PROTOCOL.md` from the LoopEngineering repository containing this Skill.
If it is absent or its version does not satisfy `>=0.2,<0.3`, stop instead of
silently falling back.

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

## Intake

1. Classify the request as read-only or state-changing.
2. Resolve the mode from the current request. Use an explicit `collaborative` or
   `autonomous` choice when supplied; otherwise set `autonomous` without a separate mode prompt.
   Never reuse the previous task's mode.
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
   Add `final_acceptance` for collaborative mode. Autonomous `0.2.0` does not add `final_acceptance` based on risk level; preserve any extra gate explicitly required by
   the current user instruction, project rules or an existing contract.
6. Run `loop-engineering contract validate "<contract-path>"`.
7. Present one `Ready-to-execute Loop Contract` summary in this order: mode and
   objective; in/out of scope; acceptance criteria and validation; key design and
   implementation plan; risk, permissions, exact Git targets and budget; preauthorized
   actions, remaining pause conditions and stop conditions. In autonomous mode, label
   the risk section `Autonomous Risk Acceptance` and show one table containing each
   `risk_id`, `kind`, exact target, `impact`, `worst_case`, `recovery` and `evidence`.
8. Ask for one pre-execution approval of that complete summary. Clarifying missing
   information is not approval, and separate partial answers must not be combined into it.
   Ask the user to reply with `$loop-engine confirm` so the approval turn explicitly
   reactivates this Skill.
9. After approval, run
   `loop-engineering run create "<contract-path>" --project "<project-root>"`,
   retain the created `intake` snapshot, record the discovering/drafting/awaiting
   transitions and `contract_approval` with `loop-engineering run approval`. Core binds
   that event to the current contract version, SHA-256 and accepted risk IDs. Then
   advance through designing or planning toward execution without another approval
   unless an explicit extra gate applies.

## Maker loop

For each unmet acceptance criterion:

1. Run `loop-engineering budget check "<run-dir>"`. An exhausted result transitions
   to BUDGET_EXHAUSTED. A diagnosis-required result returns to planning and requires
   a new causal hypothesis before another action. Otherwise choose one smallest
   verifiable increment.
2. Serialize the exact ActionRequest under `<run-dir>/inputs/` and run
   `loop-engineering gate check "<run-dir>" "<request-json>"`.
   Handle the returned decision exactly:
   - `allow`: continue without another human confirmation.
   - `pause` with `required_gate=contract_revision`: add the new exact target,
     permission and full risk disclosure to the next contract version, then request
     one revised complete-summary approval; do not record `dangerous_action` for this route.
   - `pause` with `required_gate=contract_approval`: the current bound approval is
     missing or stale; return to the complete contract approval instead of showing an
     isolated risk prompt.
   - `pause` with `required_gate=dangerous_action`: this is a collaborative or legacy
     gate. Show the returned professional confirmation and record the explicit decision
     with `loop-engineering run approval`.
   - `deny`: record the rejection and never execute the operation.
3. Immediately before every approved external state change, run
   `loop-engineering run intent` with the exact action and target.
4. Make the change without touching unrelated user work.
5. Run `loop-engineering run result` immediately after observing real state,
   marking whether new evidence/progress occurred and whether the strategy was reused.
   Git results use payload shape
   `{"git":{"repository_id":"target","operation":"push","success":true,
   "commit_sha":"<sha>","pr_url":"<url-or-empty>"}}`; record `create_pr` as a
   separate successful operation. Completion derives per-repository delivery only
   from these current-contract result events, never from prose.
6. Run `loop-engineering evidence run "<run-dir>" "<VAL-ID>"`.
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

## Checker

- Low risk: Maker self-checks against the contract and raw evidence.
- Medium/high risk: dispatch a fresh independent Checker context.
- Checker reads the contract, actual diff and raw evidence, then returns only
  `ACCEPT`, `REVISE` or `BLOCK` with findings and evidence.
- Record the verdict and findings with `loop-engineering run checker`.
- Checker never edits production code. `REVISE` returns to Maker and consumes a revision.
- If an independent Checker is unavailable, medium/high work cannot become DONE.

## Control modes

- `collaborative`: one pre-execution approval covers the complete contract summary,
  including its key design and plan. Continue through designing, planning and ordinary
  implementation inside that contract; pause for a new dangerous action, a material
  contract change, an explicit extra gate, or final acceptance before DONE.
- `autonomous`: the one pre-execution approval accepts every precisely disclosed risk.
  Continue through low, medium and high-risk operations—including exact
  `production_access` and `sensitive_data` entries—until DONE, BLOCKED,
  BUDGET_EXHAUSTED, contract revision, or a platform or external-service hard gate.
  Risk level alone never creates another human gate or final acceptance.
- The user may downgrade to collaborative at any time. Upgrading requires explicit approval.
- A material target, scope, evidence, dangerous permission or budget change pauses the
  run, increments `contract_version`, re-enters contract_drafting/awaiting_approval,
  and invokes `loop-engineering run revise` only after explicit approval.
- Record the combined execution authorization as `contract_approval`. Record
  `design_approval` or `plan_approval` separately only when an applicable rule or the
  approved contract explicitly requires that gate. Record final acceptance separately;
  a rejection never permits a forward transition.

## Approval quick reference

| Situation | Adapter action |
|---|---|
| Mode omitted | Select `autonomous` and disclose it in the complete summary |
| Initial state-changing task | Request one approval of the ready-to-execute summary |
| Default design and plan stages | Continue without another approval |
| Explicit `design_approval` or `plan_approval` | Pause at the declared extra gate |
| Autonomous exact disclosed risk | Continue from the bound contract approval |
| Autonomous new scope, permission or risk | Request one revised complete-summary approval |
| Collaborative dangerous action | Run the exact `dangerous_action` gate |
| Collaborative completion | Require final acceptance |

## Common approval mistakes

- Resolve an omitted mode to `autonomous` and disclose it in the summary; a standalone
  mode prompt adds no authorization.
- Put design and plan decisions in the ready-to-execute summary; default follow-up approval
  prompts fragment one decision into several.
- Treat scope questions as information gathering and the complete-summary response as
  authorization; never infer approval from partial answers.
- In Autonomous `0.2.0`, treat an emergent danger as contract scope change and bundle it
  into one revision approval; a standalone danger prompt would recreate the duplicate gate.
- Do not treat a contract file by itself as proof of risk acceptance. Use the run-backed
  gate check so the current hash and accepted risk IDs are verified.
- A platform or external-service hard gate is outside Loop authorization and may still
  require user action; never claim the adapter can bypass it.

## Completion

Do not claim DONE from prose. Build the strict CompletionContext at
`<run-dir>/inputs/completion-context.json` and run
`loop-engineering completion evaluate "<contract-path>" "<context-json>"`.
Only a zero exit code permits calling `loop-engineering run complete "<run-dir>"
--actor maker --reason "all DONE requirements passed"`. That authoritative command
re-derives evidence records and hashes, current fingerprints, scope, Git delivery,
approvals, pending intents and Checker status before transitioning. Verify every
acceptance criterion has fresh evidence and approved Git/PR delivery completed. Use the
`loop-engineering git` subcommands only after a matching gate decision and emit the
final report from `templates/final-report.md`.

Set `scope_valid` in CompletionContext only from
`loop-engineering scope check "<contract-path>"`; do not infer it from Maker prose.
Derive `checker_verdict`, `human_accepted`, `gates_clear` and
`contract_current` from `loop-engineering run status "<run-dir>"`: unresolved
intent IDs, a paused state, or a required contract gate without an approval event make
`gates_clear=false`, and contract versions must match.
Populate evidence only from validator result events returned by
`loop-engineering run events "<run-dir>"`.

The permanent deny list is force-push, history rewriting, reset --hard, automatic merge and automatic deployment.
不得自动合并或部署。不得强推、改写历史、执行 `git reset --hard`、泄露秘密，
或通过删除/弱化测试制造成功。
