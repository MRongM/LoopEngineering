# Codex Goal bridge playbook

Read this playbook after a contract is approved and a Run exists, and at the start of every
later host continuation. The Goal is only a durable pointer; the Loop ledger remains
authoritative for identity, approval, scope, budgets, evidence and completion.

## Create and bind the default Goal

Every newly approved Codex Loop task uses Goal binding by default. Before approval, include
exact `platform_state` operations for both `codex-goal:create:<resolved-run-dir>` and
`codex-goal:complete:<resolved-run-dir>` in the complete Loop Contract risk disclosure.
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

## Resume a Goal/Run binding

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

## Yield and cancellation

- For `AWAITING_APPROVAL` or an ordinary `PAUSED`, stop automatic actions and accept an
  unambiguous natural-language reply for the verified binding.
- For user cancellation, close a Pending Draft binding or transition a mutable Run to
  `PAUSED` with a stable `user_cancelled:` reason. A cancelled task cannot resume implicitly;
  preserve its ledger and require explicit `$loop-engine` for new work.
- For `BLOCKED` or `BUDGET_EXHAUSTED`, leave the Goal unfinished and report the exact stop
  reason. These immutable Runs cannot continue implicitly or have either budget expanded.

## Complete the Goal

- Only after authoritative Loop `DONE` may the Adapter gate the exact Goal-completion
  `platform_state`, record its intent, call `update_goal` with `complete`, and record the
  observed result.
- Do not call `update_goal` with `blocked`; Codex blocking has separate host rules and is not
  a safe mapping from a Loop status.

## Independent budgets

Codex Goal token usage is an outer host limit. Loop iterations, elapsed minutes and Checker
revisions remain independent inner limits. Neither budget changes or authorizes the other.
