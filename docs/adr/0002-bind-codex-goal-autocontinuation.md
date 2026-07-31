---
status: accepted
---

# Bind Codex tasks for Goal-backed continuation

Only a new Loop task requires explicit invocation with `$loop-engine`. Before Run creation,
one Draft created by that start may remain uniquely bound to the current conversation, so
clarification and approval of the latest complete summary can use natural language.

After contract approval, every new Codex Loop task uses a canonical Goal by default. The
Goal objective begins with `$loop-engine goal-bridge/v1`, names the absolute Run directory
and Loop ID, and is bound by a successful intent/result in the append-only Run ledger.
Every continuation revalidates `get_goal`, the objective, ledger, current authorization,
pending intents, budgets and Gate decision.

`agents/openai.yaml` enables implicit Skill selection only so the Adapter can inspect that
binding. Selection grants no Intake, approval, permission, budget or completion authority.
Without exactly one current-conversation Pending Draft or one verified Goal/Run binding,
the Adapter performs no Loop mutation and requires explicit `$loop-engine` for new work.
It never scans for the newest Run or adopts an unrelated Goal.

Natural-language approval must unambiguously accept the latest complete summary in one
reply. Questions, partial or conditional decisions, stale references and unrelated messages
are not approval. No fixed `confirm` subcommand or trigger prefix is required after binding.

## Goal lifecycle

- Goal create and complete are exact `platform_state` operations disclosed by the current
  contract and protected by the bound approval plus intent/result ledger.
- Missing Goal tools, an unrelated Goal or an unverifiable binding hard-pauses implicit
  continuation. Explicit invocation remains the conservative recovery path.
- User cancellation closes the binding with a `user_cancelled:` pause reason rather than
  inventing a Core cancellation state or misusing `BLOCKED`/`DONE`.
- `DONE`, `BLOCKED`, `BUDGET_EXHAUSTED` and cancelled tasks do not continue implicitly;
  follow-up work starts as a new explicitly invoked task.
- Only authoritative Loop `DONE` permits `update_goal complete`. The Adapter never calls
  `update_goal blocked` as a mapping from Loop state.

Codex Goal Token budgets remain independent from Loop iterations, elapsed minutes and
Checker revisions. Goal is a scheduler and durable pointer; Loop remains authoritative for
scope, permissions, evidence, budgets, Checker findings and completion.

## Consequences

- ADR 0001 continues to protect the new-task boundary while no longer requiring a trigger
  on every later turn of the same verified task.
- Core gains only the generic `platform_state` action kind; all Goal and conversation
  behavior remains in the Codex Adapter.
- Repository tests validate the Adapter contract and lifecycle marker, not real host
  scheduling. Real use requires a user-operated managed Skill update and new Codex session.
