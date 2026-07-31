---
name: loop-engine
description: Run evidence-gated Loop Engineering workflows in Claude Code.
disable-model-invocation: true
---

# Loop Engineering for Claude Code

Compatible Core: >=0.2,<0.3

## Manual invocation

Start this Skill only when the current user message explicitly invokes `/loop-engineering:loop-engine`.
Do not infer activation from task semantics, a plain-language mention, or a previous task.
Claude Code versions that expose an unqualified plugin alias may also accept `/loop-engine`,
but the namespaced command is canonical. Every later user message that should continue this Skill must invoke it again.
Whenever this Skill pauses, require the user's next message to
start with the canonical command. The command does not rename Loop Engineering, the
`loop-engineering` CLI, or Core.

`disable-model-invocation: true` is a host-enforced boundary. Do not remove it or replace
manual invocation with model-selected activation, a hook, or task-semantic inference.

## Adapter lifecycle

Installation, update, and removal are user-operated bootstrap actions, not Maker-loop
actions. Explain the exact commands, but never run lifecycle commands on the user's behalf.
Use Claude Code's native marketplace and plugin lifecycle; do not maintain a second adapter
installer.

Install the Core CLI and plugin from a user shell:

```bash
uv tool install "git+https://github.com/MRongM/LoopEngineering.git@master"
claude plugin marketplace add MRongM/LoopEngineering
claude plugin install loop-engineering@loop-engineering --scope user
loop-engineering --version
```

Update both components explicitly:

```bash
claude plugin marketplace update loop-engineering
claude plugin update loop-engineering@loop-engineering --scope user
uv tool install --reinstall "git+https://github.com/MRongM/LoopEngineering.git@master"
loop-engineering --version
```

Uninstall both components explicitly:

```bash
claude plugin uninstall loop-engineering@loop-engineering --scope user
uv tool uninstall loop-engineering
```

Use `/reload-plugins` after plugin lifecycle changes, or start a new Claude Code session.
Never substitute a recursive delete, an overwrite, a force option, a symlink, or a remote
script pipe. Use the repository `README.md` and `docs/adoption.md` as the copy-paste command
reference. `claude plugin validate .` validates a local checkout without installing it.

## Required context

Before modifying state, read:

1. `${CLAUDE_PLUGIN_ROOT}/PROTOCOL.md` from the complete installed plugin source.
2. The target project's `.loop-engineering/project.yaml`, when present.
3. Every configured instruction file, including applicable `CLAUDE.md`, `.claude/rules/`,
   and `AGENTS.md` files.
4. The approved Loop Contract and any applicable approved design.

Stop if the authoritative protocol is absent or does not satisfy `>=0.2,<0.3`. Do not use a
copied protocol, silently fall back to remembered rules, or place host-specific behavior in
Core.

## Hard gate

Do not edit project files, install dependencies, create Git refs, commit, push, open a PR,
or call an external write API until the complete Loop Contract has been shown to the user
and explicitly approved. New targets or permissions require a revised approval.

The sole preapproval write is the adapter-owned draft at
`.loop-runs/.drafts/<loop-id>/contract.yaml` under the target project. Use resolved absolute
paths for every `repositories[].path`. Never create adapter control files in a system
temporary directory, the user's home directory, or another project. After creating a run,
put every path-based CLI input under `<run-dir>/inputs/`. Never stage or commit `.loop-runs/`.

## Intake

1. Classify the request as read-only or state-changing.
2. Use an explicit `collaborative` or `autonomous` choice when supplied; otherwise select
   `autonomous`. Never inherit a previous task's mode.
3. Inspect the repository, instructions, approved design, tests, recent commits, and dirty
   state read-only.
4. Draft the strict Core `0.2.0` contract with exact repositories, absolute paths, scope,
   acceptance criteria, argv validation, budget, permissions, Git targets, key design
   decisions, and the minimal implementation plan.
5. Disclose every planned dangerous, production, sensitive-data, and Git mutation in
   `authorized_operations`. Each entry requires `risk_id`, `kind`, `repository_id`, exact
   `target`, `risk_level`, `impact`, `worst_case`, `recovery`, and `evidence`.
6. Use `contract_approval`. Do not add `design_approval` or `plan_approval` unless a current
   instruction or existing contract explicitly requires it. Add `final_acceptance` only for
   collaborative mode or another explicit rule.
7. Run `loop-engineering contract validate "<contract-path>"`.
8. Present one `Ready-to-execute Loop Contract` summary in this order: mode and objective;
   in/out of scope; acceptance and validation; design and plan; risk, permissions, Git
   targets, and budget; preauthorized operations, remaining pauses, and stop conditions.
9. In autonomous mode, label the risk section `Autonomous Risk Acceptance` and show one
   table containing every risk ID, operation, exact target, impact, worst case, recovery,
   and evidence.
10. Ask for one approval of the complete summary. Require the user to reply with `/loop-engineering:loop-engine confirm`;
    partial answers are not authorization.

After approval, run:

```text
loop-engineering run create "<contract-path>" --project "<project-root>"
```

Retain the created intake snapshot. Record the discovering, contract_drafting, and
awaiting_approval transitions, followed by the user's `contract_approval`. Core binds the
approval to the current contract version, SHA-256, and complete accepted risk ID set. Then
advance through designing or planning without another default approval.

## Maker loop

For each unmet acceptance criterion:

1. Run `loop-engineering budget check "<run-dir>"`. An exhausted result becomes
   `BUDGET_EXHAUSTED`; a diagnosis-required result returns to planning with a new causal
   hypothesis.
2. Serialize the exact `ActionRequest` under `<run-dir>/inputs/`, then run
   `loop-engineering gate check "<run-dir>" "<request-json>"`.
3. Handle the decision exactly:
   - `allow`: continue.
   - `pause` with `required_gate=contract_revision`: add the new exact target, permission,
     and full disclosure to a new contract version, then request one revised complete-summary
     approval. Do not record `dangerous_action`.
   - `pause` with `required_gate=contract_approval`: restore the complete contract approval;
     do not ask for an isolated operation confirmation.
   - `pause` with `required_gate=dangerous_action`: show and record the returned professional
     confirmation. This route applies only to collaborative or legacy contracts.
   - `deny`: record the rejection and never execute the operation.
4. Immediately before each allowed state change, run `loop-engineering run intent` with the
   exact action and target.
5. Make the smallest scoped change without touching unrelated user work.
6. Immediately after observing real state, run `loop-engineering run result`, recording
   progress, strategy reuse, and any external identifiers. Record Git push and PR creation
   as separate operations with their real commit SHA and URL.
7. Run `loop-engineering evidence run "<run-dir>" "<VAL-ID>"`.
8. Do not repeat the same failed strategy more than once. After two no-progress cycles,
   return to diagnosis.

For multiple repositories, follow the contract's acyclic `depends_on` order. Use one branch
and PR per repository and list prerequisite PRs in every dependent PR.

## Engineering and persistence

- Apply KISS and YAGNI. Use DRY and SOLID only for material repetition or a clear
  responsibility boundary in the accepted scope.
- Preserve unrelated user changes and the repository's existing comment language and style.
- Use Python 3.12+, strict models, argv subprocesses, and `shell=False` where applicable.
- Add a failing test before production code and retain fresh command evidence.
- Treat `events.jsonl` as append-only. Never rewrite approvals, intents, results, evidence,
  or Checker findings to manufacture success.
- Persist only redacted operational evidence; never persist secrets or complete reasoning.

## Checker

- Low risk: Maker self-checks the contract, diff, and raw evidence.
- Medium/high risk: dispatch a fresh independent Checker context.
- Checker reads the current contract, actual diff, and raw evidence, then returns only
  `ACCEPT`, `REVISE`, or `BLOCK` with findings and evidence.
- Record the verdict with `loop-engineering run checker`. Checker never edits production
  code. `REVISE` returns to Maker and consumes one revision.
- If an independent Checker is unavailable, medium/high work cannot become DONE.

## Control modes

- `collaborative`: the complete pre-execution approval covers design, plan, and ordinary
  implementation. Pause only for a material contract change, a returned dangerous-action
  gate, an explicit extra gate, or final acceptance.
- `autonomous`: the complete approval accepts every precisely disclosed risk. Continue
  through approved low, medium, and high-risk work until DONE, BLOCKED, BUDGET_EXHAUSTED,
  contract revision, or a platform/external-service hard gate. Risk level alone adds no
  further human gate.
- A material target, scope, evidence, dangerous permission, Git target, or budget change
  increments `contract_version`, pauses the run, and requires one complete revision approval.
- Users may downgrade to collaborative at any time. Upgrading requires explicit approval.

## Completion

Do not claim DONE from prose. Build `<run-dir>/inputs/completion-context.json` and run:

```text
loop-engineering completion evaluate "<contract-path>" "<context-json>"
```

Set `scope_valid` only from `loop-engineering scope check "<contract-path>"`. Derive
`checker_verdict`, `human_accepted`, `gates_clear`, and `contract_current` from
`loop-engineering run status "<run-dir>"`. Populate evidence only from validator result
events returned by `loop-engineering run events "<run-dir>"`.

Only a zero completion-evaluation exit code permits:

```text
loop-engineering run complete "<run-dir>" --actor maker --reason "all DONE requirements passed"
```

Verify fresh evidence for every criterion, current fingerprints, scope, approvals, resolved
intents, required Checker status, and any approved Git/PR delivery. Emit the final report from
`templates/final-report.md`.

The permanent deny list is force-push, history rewriting, reset --hard, automatic merge and automatic deployment.
Never disclose secrets, weaken tests or schemas, or delete evidence to manufacture success.
