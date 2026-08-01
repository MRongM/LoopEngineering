# Loop Engineering Core Protocol 0.1.0

## Purpose

Loop Engineering is an evidence-gated, recoverable execution protocol for coding agents.
An Agent may operate autonomously only inside one explicitly approved, verifiable contract
and may reach `DONE` only when fresh evidence satisfies that contract.

Protocol `0.1.0` is the first release. Core accepts exactly this protocol version; it has no
older-version parser, compatibility branch, downgrade path or automatic migration.

## Core invariants

- The only control mode is `autonomous`.
- A state-changing task MUST begin with a complete, execution-closed Loop Contract.
- The user MUST approve that complete contract once before execution.
- Approval MUST bind the protocol version, contract version, canonical contract SHA-256 and
  the complete set of accepted risk IDs.
- Every runtime action MUST match both the approved execution plan and the contract policy.
- A new action, target, permission, risk, budget or delivery target MUST produce
  `contract_revision`; it MUST NOT create an isolated confirmation prompt.
- Force-push, history rewrite, reset-hard behavior, automatic merge and deployment are
  permanently denied.
- Every external state change MUST have a persisted intent before execution and a matching
  observed result afterward.
- Evidence MUST be fresh, command-backed, bound to the current contract and source
  fingerprint, and collected with argv subprocesses using `shell=False`.
- The Agent MUST NOT claim `DONE` from prose, confidence or stale output.

## Project control root

Each target project has exactly one Loop-owned top-level directory:

```text
.loop-engine/
├── .gitignore
├── project.yaml
├── drafts/
├── runs/
└── cache/
```

Only `.loop-engine/project.yaml` and `.loop-engine/.gitignore` are trackable. Drafts, run
ledgers, evidence and cache data are local runtime state. Core MUST ignore `.loop-engine/`
when calculating source fingerprints and scope. Project initialization MUST fail closed when
another Loop-owned top-level directory conflicts; it MUST NOT move or delete data.
Control directories and files MUST NOT be symlinks or junctions.

## Loop Contract

A contract MUST include:

- loop identity and monotonically increasing `contract_version`;
- `protocol_version: 0.1.0` and `mode: autonomous`;
- objective, repositories, exact allowed paths, scope and exclusions;
- acceptance criteria and their required validation evidence;
- isolated validation commands, argv, working directory and timeout;
- permissions, overall risk level and complete authorized-operation disclosures;
- an execution plan containing key `design_decisions` and exact `actions`;
- exact Git delivery policy;
- iteration, active-time and Checker-revision budgets;
- exactly one human gate, `contract_approval`;
- assumptions and all terminal stop conditions.

Unknown fields MUST be rejected. References, repository dependencies and Git targets MUST
be internally consistent. Paths and refs MUST be resolved and non-option-like. Inline secret
arguments MUST be rejected.

Every authorized operation MUST disclose a unique `risk_id`, exact kind, repository, target,
risk level, impact, worst case, recovery and evidence. Production and sensitive-data actions
MUST be high risk. Permissions MUST explicitly enable every disclosed privileged category.

## Execution closure

Before admission, Core MUST evaluate each `execution_plan.actions` entry against a synthetic
authorization for the complete contract. Every entry MUST return `allow`. A plan that would
pause or deny after approval is not execution-closed and MUST be rejected.

Runtime allowed paths are boundaries, not implied authorization. Every actual action MUST be
represented by the approved plan. A material design or plan change is one complete contract
revision followed by a new bound approval.

## Approval and authorization

The adapter presents one `Ready-to-execute Loop Contract` summary containing the design,
minimal action plan, validation, risks, permissions, Git targets, budget and stop conditions.
One unambiguous approval records `contract_approval` with:

- `protocol_version`;
- `contract_version`;
- `contract_sha256`;
- sorted `accepted_risk_ids`.

Any contract mutation invalidates the binding. A replacement contract MUST keep the loop ID,
increment `contract_version` by exactly one, return to `AWAITING_APPROVAL`, and record one
fresh `contract_revision` approval. After valid approval, ordinary planned work continues
without routine human confirmations. Non-blocking questions are accumulated for the final
report.

## State machine and budgets

The ordinary lifecycle is:

```text
intake -> discovering -> contract_drafting -> awaiting_approval
       -> designing -> planning -> executing -> verifying
       -> checking -> deciding
```

Terminal states are `done`, `blocked` and `budget_exhausted`; `paused` is recoverable.
Illegal transitions MUST be rejected. Leaving `awaiting_approval` requires a current bound
authorization.

The elapsed-time budget counts active execution time only. Time spent awaiting approval or
paused MUST NOT consume it. The sum of one pass through all validation timeouts MUST fit
inside the active-time budget. Iterations, Checker revisions and same-strategy retry limits
are independently enforced.

## Intent/result ledger

`events.jsonl` is append-only and monotonically sequenced. An Agent records an `intent`
immediately before an external mutation and a matching `result` immediately after observing
real state. A crash between them leaves a pending intent that MUST be reconciled before any
retry. Secrets and complete model reasoning MUST NOT be persisted.

Contract replacement invalidates evidence from prior contract versions. Cleanup or a source
revision invalidates fingerprints. Ledger corruption and partial tails MUST fail closed.

## Validation evidence

Every validation command MUST use `workspace_policy: isolated`. Core copies the current Git
tracked and non-ignored working snapshot into a disposable repository under
`.loop-engine/cache/`, then runs the exact argv with `shell=False` and a bounded timeout.
Generic temporary and cache environment variables MUST also point inside `.loop-engine/cache/`.

The source repository fingerprint is captured before and after validation. A validator start
failure, timeout, non-zero exit, source mutation or unavailable workspace state MUST create a
closed failed result, never an unmatched intent. Evidence records include timestamps, exit
status, redacted stdout/stderr hashes, source fingerprint and workspace-integrity facts.

## Gate policy

Gate evaluation order is:

1. permanently forbidden actions return `deny`;
2. missing or stale contract binding returns `contract_approval`;
3. an action outside the execution plan returns `contract_revision`;
4. scope, permission, Git-target and exact-risk checks run;
5. a fully matching action returns `allow`.

Production, sensitive-data, database, dependency, network, platform-state and Git mutations
may run only when the exact planned request and any required risk disclosure match the
current bound contract. A direct contract file is never proof of approval; authorization is
derived from the run ledger.

The Agent Shell Git commands MUST enforce the bound Gate decision themselves, require the
`executing` state, and automatically record a matching intent/result pair. A failed Git
operation MUST close its intent with an observed failed result.

## DONE predicate

`DONE` requires all of the following current facts:

- every acceptance criterion has passing evidence from its required command;
- evidence contract version, repository, criterion and fingerprint match;
- medium/high risk has Checker `ACCEPT`;
- required Git delivery has observed successful results;
- actual diff is inside approved scope;
- no pending intent or unresolved gate remains;
- current contract authorization is valid.

The authoritative completion command MUST reconstruct these facts from persisted evidence,
Git state and the append-only ledger before transitioning to `DONE`.
