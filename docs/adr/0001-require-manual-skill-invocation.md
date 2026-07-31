---
status: accepted
---

# Require manual `$loop-engine` invocation

The Codex Adapter is activated only when the current user message explicitly invokes
`$loop-engine`. This replaces automatic task-based selection and the former
`$loop-engineering` trigger because execution governance should be an intentional user
choice, while the shorter name keeps repeated use practical.

Codex Skill selection is turn-scoped. Every later user message that should continue the
Skill must invoke `$loop-engine` again; the adapter does not claim persistent activation
that the host does not provide.

## Consequences

- `agents/openai.yaml` sets `policy.allow_implicit_invocation: false`, the Codex host policy
  that enforces the manual-only boundary.
- Every user turn that should run the Skill requires explicit invocation.
- No compatibility alias is retained for `$loop-engineering`.
- A hidden non-trigger marker lets the previous lifecycle manager revalidate the first
  update that changes the Skill name; it does not register the former invocation name.
- The product name, `loop-engineering` CLI, Core protocol, and control-mode rules do not change.

## Reference

- [OpenAI: Build skills](https://learn.chatgpt.com/docs/build-skills#optional-metadata)
