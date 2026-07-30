---
name: loop-engineering
description: Use for every state-changing engineering task when the user wants a collaborative or autonomous evidence-gated coding loop.
---

# Loop Engineering for Codex

Compatible Core: >=0.1,<0.2

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
2. For state-changing work, ask for `collaborative` or `autonomous` unless supplied.
3. Default to `collaborative`; never reuse the previous task's mode.
4. Inspect the repository, instructions, tests, recent commits and dirty state read-only.
5. Draft `contract.yaml` from the Core template with exact repositories, paths,
   acceptance criteria, argv validation, budget, permissions and Git targets. Keep
   the unapproved draft in an ephemeral temporary directory, not the target project.
6. Run `loop-engineering contract validate "<contract-path>"`.
7. Present a compact Loop Contract summary and wait for approval.
8. After approval, run
   `loop-engineering run create "<contract-path>" --project "<project-root>"`,
   retain the created `intake` snapshot, record the discovering/drafting/awaiting
   transitions and the approval event with `loop-engineering run approval`, then
   transition into designing or planning.

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

- `collaborative`: pause at contract, nontrivial design, plan, new dangerous action
  and final acceptance.
- `autonomous`: continue inside the approved contract until DONE, BLOCKED,
  BUDGET_EXHAUSTED or a hard human gate.
- The user may downgrade to collaborative at any time. Upgrading requires explicit approval.
- A material target, scope, evidence, dangerous permission or budget change pauses the
  run, increments `contract_version`, re-enters contract_drafting/awaiting_approval,
  and invokes `loop-engineering run revise` only after explicit approval.
- Record every collaborative design, plan and final decision with
  `loop-engineering run approval "<run-dir>" --actor user --gate "<gate>"
  --decision approve --summary "explicit user approval"`; use `--decision reject`
  for rejection, which never permits forward transition.

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
