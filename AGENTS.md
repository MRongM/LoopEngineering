# LoopEngineering repository instructions

- Read `PROTOCOL.md` and the approved design before changing behavior.
- Use Python 3.12+, strict Pydantic models, argv subprocesses and `shell=False`.
- Add a failing test before production code and preserve fresh command evidence.
- Never weaken gates, tests or schemas to obtain a passing result.
- Never add automatic merge, deployment, force-push, history rewrite or production access.
- Do not commit runtime data, secrets, tokens or complete model reasoning.
- Keep Core tool-independent; Codex-specific behavior belongs in `adapters/codex/`.
