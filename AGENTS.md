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

The active milestone defines the first public Core Protocol as 0.1.0. It is execution-closed, keeps only `autonomous`, uses `loop-engine` as the sole Agent Shell CLI and Codex Skill trigger, installs the managed Skill checkout at `skills/loop-engine`, and keeps the Python distribution package `loop-engineering`.

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
