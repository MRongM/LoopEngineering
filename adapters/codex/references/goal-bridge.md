# Codex Goal bridge playbook

Read this playbook after a contract is approved and a Run exists, and at the start of every
later host continuation. The Goal is only a durable pointer; the Loop ledger remains
authoritative for identity, approval, scope, budgets, evidence and completion.

## Create and bind the default Goal

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
2. Advance the approved Run through its required design/planning transitions into `executing`.
   Serialize the exact `platform_state` `ActionRequest` under `<run-dir>/inputs/` and run its
   `gate check` for Goal creation.
3. Record the checked request immediately before the host call with
   `loop-engine run intent "<run-dir>" "<request-json>" --actor maker
   --summary "create bound Codex Goal"`. Supplemental payload may contain the loop ID,
   absolute run directory and canonical objective SHA-256, but cannot replace the request.
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

## Yield, cancel and finish

- For `AWAITING_APPROVAL` or an ordinary `PAUSED`, stop automatic actions and accept an
  unambiguous natural-language reply for the verified binding.
- For user cancellation, close a Pending Draft binding or transition a mutable Run to
  `PAUSED` with a stable `user_cancelled:` reason. A cancelled task cannot resume implicitly;
  preserve its ledger and require explicit `$loop-engine` for new work.
- For `BLOCKED` or `BUDGET_EXHAUSTED`, leave the Goal unfinished and report the exact stop
  reason. These immutable Runs cannot continue implicitly or have either budget expanded.
- Only after authoritative Loop `DONE` may the Adapter serialize and gate the exact
  Goal-completion `platform_state` request, record it through the same request-bound intent
  command, call `update_goal` with `complete`, and record the observed generic platform result.
- Do not call `update_goal` with `blocked`; Codex blocking has separate host rules and is not
  a safe mapping from a Loop status.

## Independent budgets

Codex Goal token usage is an outer host limit. Loop iterations, elapsed minutes and Checker
revisions remain independent inner limits. Neither budget changes or authorizes the other.
