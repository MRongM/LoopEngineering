# Loop Engineering

Loop Engineering 0.1.0 provides evidence-gated, recoverable execution loops for
coding agents. The Core is tool-independent; the first adapter targets Codex.

## Use it now

Without installing code, reference the approved design in your task and require an
approved Loop Contract before any mutation:

- [Design specification](docs/superpowers/specs/2026-07-30-loop-engineering-protocol-design.md)
- [Cross-project adoption guide](docs/adoption.md)

## Install the implementation

```bash
uv tool install --editable "/opt/LoopEngineering"
loop-engineering --version
```

Link `adapters/codex` into an explicitly chosen Codex Skills directory, initialize
the target project, then invoke `$loop-engineering`. Full commands for Unix and
Windows are in `docs/adoption.md`.

## Safety boundary

The first release has no scheduler, daemon, automatic merge, automatic deployment,
force-push, history rewrite or implicit production access. Runtime state under
`.loop-runs/` is local and ignored by default.

## Development

```bash
uv sync --dev
uv run pytest -q
uv run ruff check "src" "tests"
uv build
```

## Support status

| Capability | Status |
|---|---|
| Python 3.12 on macOS | Verified by the local release suite |
| Python 3.13–3.14 | Declared compatible; CI is required before claiming verified execution |
| Linux Core CLI | Designed and documented; Linux CI is required before claiming verified execution |
| Windows Core path/subprocess APIs | Designed and documented; Windows CI is required before claiming verified execution |
| Git worktree/commit/push | Verified against a local bare remote |
| GitHub PR creation | Requires an authenticated `gh` CLI |
| Scheduler or daemon | Not included |
| Automatic merge/deployment/production access | Forbidden |
