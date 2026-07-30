# Loop Engineering Core Protocol 0.1.0

## Normative terms

MUST, MUST NOT, SHOULD and MAY are requirement levels. A conforming adapter MUST
enforce every MUST/MUST NOT rule and MUST reject incompatible protocol versions.

## Admission

- Read-only questions MAY use investigate-verify-report without a run.
- Every state-changing task MUST create a Loop Contract.
- Mode MUST be collaborative or autonomous, MUST NOT be inherited, and defaults to collaborative.
- Autonomous execution MUST NOT start before explicit contract approval.

## Contract

The contract MUST identify objective, repositories, allowed paths, scope,
acceptance criteria, evidence commands, risk, permissions, Git policy, budgets,
human gates, assumptions and stop conditions. Objective, scope, acceptance,
dangerous permissions, repository targets, Git targets or budget expansion MUST
create a new contract version and pause execution.

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
- Collaborative runs and all high-risk runs MUST receive final human acceptance.

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

## Safety

- The adapter MUST resolve and boundary-check every path.
- Secrets, tokens, sensitive responses and full model reasoning MUST NOT be persisted.
- Unmatched intent events MUST be reconciled against real external state before retry.
- Force-push, history rewriting, reset --hard, automatic merge and automatic deployment are forbidden.
- Production and sensitive-data operations always require a fresh human gate.
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
