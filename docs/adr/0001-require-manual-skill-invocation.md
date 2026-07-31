---
status: amended
---

# Require explicit `$loop-engine` task start

Only the current user message's explicit `$loop-engine` invocation may start a new Loop
task. Task semantics, an old trigger, a similar topic, or a previous Run never authorizes
Intake or adoption.

The original decision required the trigger on every user-authored turn. ADR 0002 amends
that part: after the current conversation uniquely binds a Pending Draft, or native Goal
state plus the append-only ledger uniquely bind an active Run, later messages may continue
the same task in natural language.

Host selection and Loop authorization remain separate. The host may select the Skill
implicitly so it can inspect a possible continuation, but a missing, ambiguous, stale,
unrelated, cancelled or terminal binding must return without Loop mutation.

## Consequences

- `agents/openai.yaml` sets `policy.allow_implicit_invocation: true` so the host can offer
  a bound continuation to the Adapter.
- The Adapter admission guard, rather than the host selection flag, enforces the new-task
  boundary.
- `$loop-engine` remains the only task-start trigger; no `$loop-engineering` compatibility
  alias is retained.
- Natural-language approval still requires one current complete contract summary and an
  unambiguous decision; it does not grant new scope or permissions.
- The product remains Loop Engineering and the Python distribution remains
  `loop-engineering`; Protocol 0.3 has one Autonomous control mode and `loop-engine` is
  the only Agent Shell executable.

## Follow-up decision

- [ADR 0002: Bind Codex tasks for Goal-backed continuation](0002-bind-codex-goal-autocontinuation.md)

## Reference

- [OpenAI: Build skills](https://learn.chatgpt.com/docs/build-skills#optional-metadata)
