# Phase 3 Pattern Map

## Target-to-Analog Mapping

| Target | Role | Closest existing analog | Pattern to preserve |
|--------|------|-------------------------|---------------------|
| `adapters/codex/SKILL.md` admission and continuation sections | Adapter instruction contract | Existing `Task-scoped continuation`, `Pending Draft binding`, `Resume a Goal/Run binding` | Use ordered, fail-closed steps; distinguish durable pointer from authorization; reconcile intent/result before retry. |
| `adapters/codex/SKILL.md` execution loop | Evidence-gated state machine | `PROTOCOL.md` Loop, Evidence, Failure and Termination sections | Select one unmet criterion, perform one bounded action, capture real evidence, use Checker verdict, then decide. |
| `tests/test_adapter_contract.py` | Executable specification for Skill prose | Existing `required`/`obsolete` tuple assertions | Pair positive required clauses with negative forbidden legacy clauses; assert exact command names and gate semantics. |

## Data Flow

`explicit $loop-engine start → Pending Draft → complete 0.3 Autonomous contract approval → Run + Goal binding → resume revalidation → budget/gate/intent/action/result/evidence/checker/decision → authoritative DONE → Goal completion`

## Constraints

- Keep Core tool-independent; all Goal behavior remains in `adapters/codex/`.
- Keep lifecycle instructions and managed checkout safety intact.
- Do not move release-wide README/adoption cleanup into this phase.
- Tests must fail on the old Skill before production prose is rewritten.
