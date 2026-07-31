---
name: loop-engineering
description: Use when a state-changing engineering task needs a collaborative or autonomous evidence-gated coding loop, or when the user asks how to install or uninstall the Loop Engineering Codex adapter.
---

# Loop Engineering for Codex

Compatible Core: >=0.1,<0.2

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
If it is absent or its version does not satisfy `>=0.1,<0.2`, stop instead of
silently falling back.

## Hard gate

Do not edit files, install dependencies, create Git refs, commit, push, open a PR,
or call an external write API until the Loop Contract has been shown to the user
and explicitly approved. The contract's exact preauthorization may cover later
Git actions. New targets or permissions require a revised approval.

The sole preapproval write is an adapter-owned contract draft in a newly created
temporary directory for schema validation. It must not touch the target project and
is removed after the approved contract is persisted.

## Intake

1. Classify the request as read-only or state-changing.
2. Resolve the mode from the current request. Use an explicit `collaborative` or
   `autonomous` choice when supplied; otherwise set `collaborative` without a separate mode prompt.
   Never reuse the previous task's mode.
3. Inspect the repository, instructions, tests, recent commits and dirty state read-only.
4. Draft `contract.yaml` from the Core template with exact repositories, paths,
   acceptance criteria, argv validation, budget, permissions and Git targets. For
   nontrivial work, include the key design decisions and the minimal implementation plan.
   Keep the unapproved draft in an ephemeral temporary directory, not the target project.
5. Use `contract_approval` and any required `final_acceptance`; do not add `design_approval` or `plan_approval` by default. Preserve either extra gate when
   the current user instruction, project rules or an existing contract explicitly requires it.
6. Run `loop-engineering contract validate "<contract-path>"`.
7. Present one `Ready-to-execute Loop Contract` summary in this order: mode and
   objective; in/out of scope; acceptance criteria and validation; key design and
   implementation plan; risk, permissions, exact Git targets and budget; preauthorized
   actions, remaining pause conditions and stop conditions.
8. Ask for one pre-execution approval of that complete summary. Clarifying missing
   information is not approval, and separate partial answers must not be combined into it.
9. After approval, run
   `loop-engineering run create "<contract-path>" --project "<project-root>"`,
   retain the created `intake` snapshot, record the discovering/drafting/awaiting
   transitions and `contract_approval` with `loop-engineering run approval`, then
   advance through designing or planning toward execution without another approval
   unless an explicit extra gate applies.

## Maker loop

For each unmet acceptance criterion:

1. Run `loop-engineering budget check "<run-dir>"`. An exhausted result transitions
   to BUDGET_EXHAUSTED. A diagnosis-required result returns to planning and requires
   a new causal hypothesis before another action. Otherwise choose one smallest
   verifiable increment.
2. Serialize the exact ActionRequest and run
   `loop-engineering gate check "<contract-path>" "<request-json>"`.
   A `pause` decision returns the complete professional confirmation text; show
   it verbatim and wait for an explicit “是”“确认” or “继续”. Record the human
   approval with `loop-engineering run approval "<run-dir>" --actor user --gate
   dangerous_action --decision approve --summary "approved exact action"`; only an
   approval continues. Use `--decision reject` for rejection. Record a policy `deny`
   as rejected and never execute it.
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
- `autonomous`: after the same contract approval, continue inside the approved contract
  until DONE, BLOCKED, BUDGET_EXHAUSTED or a hard human gate. Low/medium-risk autonomous work may reach DONE without final acceptance; high-risk work still requires it.
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
| Mode omitted | Select `collaborative` and disclose it in the complete summary |
| Initial state-changing task | Request one approval of the ready-to-execute summary |
| Default design and plan stages | Continue without another approval |
| Explicit `design_approval` or `plan_approval` | Pause at the declared extra gate |
| New scope, permission or dangerous action | Revise the contract or run the exact safety gate |
| Collaborative or high-risk completion | Require final acceptance |

## Common approval mistakes

- Resolve an omitted mode to `collaborative` and disclose it in the summary; a standalone
  mode prompt adds no authorization.
- Put design and plan decisions in the ready-to-execute summary; default follow-up approval
  prompts fragment one decision into several.
- Treat scope questions as information gathering and the complete-summary response as
  authorization; never infer approval from partial answers.
- Keep emergent-danger and final-acceptance gates distinct from the single pre-execution
  approval; reducing prompt count does not broaden permission.

## Completion

Do not claim DONE from prose. Build the strict CompletionContext and run
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

不得自动合并或部署。不得强推、改写历史、执行 `git reset --hard`、泄露秘密，
或通过删除/弱化测试制造成功。
