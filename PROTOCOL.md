# Loop Engineering Core Protocol 0.3.0

## Normative terms

MUST, MUST NOT, SHOULD and MAY are requirement levels. A conforming adapter MUST
enforce every MUST/MUST NOT rule and MUST reject incompatible protocol versions.

## Admission

- Read-only questions MAY use investigate-verify-report without a run.
- Every state-changing task MUST create a Loop Contract.
- Mode MUST be autonomous and MUST NOT be inherited. A 0.3.0 contract that omits
  mode defaults to autonomous. A 0.1.0/0.2.0 contract MUST explicitly declare
  autonomous; collaborative and ambiguous legacy contracts MUST be rejected.
- Autonomous execution MUST NOT start before explicit contract approval.
- Autonomous 0.2.0/0.3.0 contract approval MUST include acceptance of every
  disclosed risk.
- Every Autonomous 0.2.0/0.3.0 action MUST be checked against the matching bound
  approval.

## Contract

The contract MUST identify objective, repositories, allowed paths, scope,
acceptance criteria, evidence commands, risk, permissions, Git policy, budgets,
human gates, assumptions and stop conditions. Objective, scope, acceptance,
dangerous permissions, repository targets, Git targets or budget expansion MUST
create a new contract version and pause execution.

Every 0.2.0/0.3.0 authorized operation MUST have a unique risk ID, exact kind and
target, risk level, impact, worst case, recovery and evidence. Production and
sensitive-data operations MUST be high risk and MUST have their corresponding
category permission. High-risk Autonomous contracts MUST contain at least one
high-risk disclosure. Every planned dangerous, production, sensitive-data and Git
mutation MUST be disclosed before approval; ordinary scoped actions remain bounded
by repositories and paths.

Rule priority is: platform safety and the latest explicit user instruction; the
approved Loop Contract; applicable `AGENTS.md`; repository architecture/testing
rules; then Core defaults. A new higher-priority instruction that conflicts with
the contract MUST pause execution and revise the contract before mutation.

## Loop

The legal lifecycle is intake -> discovering -> contract_drafting ->
awaiting_approval -> designing/planning -> executing -> verifying -> checking ->
deciding. Deciding MAY return to planning/executing or enter paused, done,
blocked or budget_exhausted. Done, blocked and budget_exhausted are immutable;
continuation creates a child run.

Each execution iteration MUST select one unmet criterion, record an intent,
perform the smallest scoped action, observe real feedback, record the result,
capture evidence, invoke Checker when required, and decide the next state.

## Evidence and verification

- Every acceptance criterion MUST have fresh evidence for the current fingerprint.
- Bug fixes SHOULD preserve before-fail and after-pass evidence.
- Validation MUST use argv execution with shell disabled.
- Tests MUST NOT be removed, weakened, skipped or hidden to claim success.
- Medium/high risk MUST receive independent Checker ACCEPT.
- Autonomous 0.2.0/0.3.0 MUST NOT add final human acceptance solely because risk
  is high; an explicitly declared final gate still applies.
- Legacy 0.1.0 high-risk Autonomous runs MUST retain their final human gate.

## Failure, recovery and budgets

- The same failed strategy MAY be retried at most once.
- Two consecutive iterations without new evidence or material progress MUST return
  to diagnosis before another state-changing attempt.
- Interrupted intents MUST be reconciled against worktrees, refs, remotes and
  external state before retrying.
- Iteration, time and Checker-revision limits are contract data and MUST be enforced.
- A contract contradiction pauses; missing external authority/state blocks; only a
  reached contract or global limit becomes budget_exhausted.

## Persistence

Each run MUST persist its approved contract, atomic state snapshot, append-only
JSONL events, evidence files and final report under `.loop-runs/<loop_id>/`.
Events MUST include monotonic intent/result pairs, transitions, approvals, Checker
verdicts and external side-effect identifiers. Runtime data MUST be ignored by Git
by default and MUST NOT contain secrets or full model reasoning.

An approved 0.2.0/0.3.0 `contract_approval` or `contract_revision` event MUST bind
the current `protocol_version`, `contract_version`, canonical `contract_sha256` and
complete `accepted_risk_ids`. A stale, incomplete or mismatched binding grants no
authority.

## Safety

- The adapter MUST resolve and boundary-check every path.
- Secrets, tokens, sensitive responses and full model reasoning MUST NOT be persisted.
- Unmatched intent events MUST be reconciled against real external state before retry.
- Force-push, history rewriting, reset --hard, automatic merge and automatic deployment are forbidden.
- Production and sensitive-data operations in Autonomous 0.2.0/0.3.0 MAY proceed
  without another human gate only when their exact risk is present in the current
  contract, the category permission is true, and the run ledger contains the matching
  bound approval. Legacy 0.1.0 runs require a fresh human gate.
- A new operation, target, permission or risk in Autonomous 0.2.0/0.3.0 MUST pause
  for one complete `contract_revision`; it MUST NOT be approved as an isolated
  danger prompt.
- Database changes require a forward plan, compatibility analysis and recovery strategy.
- Unresolved variables, broad globs and workspace-root destructive targets are forbidden.
- User changes of unknown origin MUST NOT be overwritten, reverted or deleted.
- Every approval, rejection and permission change MUST be appended to the run ledger.

## Git and cross-repository delivery

Git automation MUST re-check the exact repository, worktree, base branch, target
branch, remote and allowed paths immediately before mutation. It MUST stage only
explicit approved paths and MUST preserve unrelated dirty user work. Multi-repository
runs MUST follow the acyclic contract dependency order, use one branch and PR per
repository, and disclose prerequisite PRs. DONE means ready for human merge, never
merged or deployed.

## Engineering quality

- Read existing code, tests and local instructions before writing.
- Apply KISS and YAGNI; implement only the smallest accepted behavior.
- Apply DRY only to material repetition in scope; do not speculate with abstractions.
- Preserve SOLID responsibility, dependency and interface boundaries.
- Do not perform unrelated refactors, bulk formatting or dependency upgrades.
- Match the repository's comment language and explain reasons or constraints.
- A new dependency requires necessity, alternatives and authorization evidence.

## Termination

DONE means all criteria have fresh evidence, required Checker/human gates passed,
the diff remains in scope, and approved Git/PR delivery completed. BLOCKED is only
for missing authority, input or external state. BUDGET_EXHAUSTED is only for a
contract or global limit. Difficulty alone is not a terminal reason.

## Compatibility

Core 0.3.0 MAY load 0.1.0/0.2.0 contracts only when they explicitly declare
autonomous, and MUST preserve their original version-specific gate semantics. New
templates and adapters MUST create 0.3.0 contracts. An active legacy run MUST NOT be
silently upgraded; migration requires a new 0.3.0 contract version and explicit
approval of its complete risk disclosure. Protocol downgrades MUST be rejected.
