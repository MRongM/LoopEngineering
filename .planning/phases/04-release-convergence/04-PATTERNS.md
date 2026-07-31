# Phase 4 Pattern Map

## Target-to-Analog Mapping

| Target | Role | Closest existing analog | Pattern to preserve |
|--------|------|-------------------------|---------------------|
| `README.md` and `docs/adoption.md` | Current install/use guidance | Existing managed lifecycle sections | Keep cross-platform install/update/uninstall safety; change executable spelling and current protocol semantics only. |
| `docs/compatibility.md` | Canonical identity and migration boundary | Approved 0.3 design sections 2 and 5 | State exact supported legacy Autonomous cases and deterministic rejections; never imply silent migration. |
| `CONTEXT.md` and ADR 0001 | Current vocabulary/decision consequences | Existing trigger and continuation definitions | Separate product, distribution, checkout, Skill trigger and CLI identities explicitly. |
| `tests/test_adapter_contract.py` | Executable documentation contract | Existing required/obsolete tuple assertions | Assert positive current examples and negative legacy execution patterns without banning legitimate package/history references. |
| Release evidence | Cross-layer verification | Phase 1–3 verification reports | Use fresh command output, local runtime/build behavior and exact artifact metadata. |

## Identity Matrix

| Identity | 0.3 value |
|----------|-----------|
| Product/repository | Loop Engineering |
| Python distribution | `loop-engineering` |
| Managed checkout directory | `loop-engineering` |
| Codex Skill trigger | `$loop-engine` |
| Agent Shell executable | `loop-engine` |
| Legacy executable aliases | none |
| Core control mode | `autonomous` only |

## Constraints

- Historical `docs/superpowers/` artifacts remain audit records; current docs must label them non-normative rather than rewriting their history.
- Positive executable examples must use `loop-engine`; negative alias assertions may name legacy executables.
- No global lifecycle mutation is required for release proof.
- Documentation tests must fail before current release prose is changed.
