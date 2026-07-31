# LoopEngineering repository instructions

- Read `PROTOCOL.md` and the approved design before changing behavior.
- Use Python 3.12+, strict Pydantic models, argv subprocesses and `shell=False`.
- Add a failing test before production code and preserve fresh command evidence.
- Never weaken gates, tests or schemas to obtain a passing result.
- Never add automatic merge, deployment, force-push, history rewrite or production access.
- Do not commit runtime data, secrets, tokens or complete model reasoning.
- Keep Core tool-independent; Codex-specific behavior belongs in `adapters/codex/`.

<!-- GSD:project-start source:PROJECT.md -->
## Current Project

Loop Engineering is an evidence-gated, recoverable execution protocol and toolset for coding agents.

The active milestone advances Core Protocol to 0.3.0, removes `collaborative`, keeps only `autonomous`, and makes `loop-engine` the sole Agent Shell CLI. Product, repository, Python distribution package `loop-engineering`, and `$loop-engine` Skill trigger names remain unchanged.

**Core value:** An Agent operates autonomously only inside an explicitly approved, verifiable contract and reaches `DONE` only when fresh evidence satisfies that contract.

Read `.planning/PROJECT.md` for the complete active scope, constraints, and superseding decisions.
<!-- GSD:project-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before changing repository files, enter through the appropriate GSD workflow so planning state and execution evidence remain synchronized:

- `$gsd-quick` for small fixes, documentation updates, and ad hoc tasks.
- `$gsd-debug` for investigations and bug fixes.
- `$gsd-execute-phase` for planned phase work.

Do not edit outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->
