# Loop Engineering

Loop Engineering 0.1.0 provides evidence-gated, recoverable execution loops for
coding agents. The Core is tool-independent; the first adapter targets Codex.

## Use it now

Without installing code, reference the approved design in your task and require an
approved Loop Contract before any mutation:

- [Design specification](docs/superpowers/specs/2026-07-30-loop-engineering-protocol-design.md)
- [Cross-project adoption guide](docs/adoption.md)

## Install in Codex

### One-line install

This command downloads the complete repository directly into the Codex Skills
directory and installs the CLI. Codex discovers `adapters/codex/SKILL.md` recursively,
so do not create a symlink or copy another `SKILL.md` to the repository root. The
clone safely stops if the destination already exists.

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills" && git clone --depth 1 --branch master "https://github.com/MRongM/LoopEngineering.git" "${CODEX_HOME:-$HOME/.codex}/skills/loop-engineering" && uv tool install "${CODEX_HOME:-$HOME/.codex}/skills/loop-engineering"
```

Start a new Codex turn, invoke `$loop-engineering`, and choose `collaborative` or
`autonomous` for that task.

### One-line uninstall

This command first verifies the exact cloned Skill marker, then uninstalls the CLI
and removes only that repository directory. Inspect the resolved path before running
the command if `CODEX_HOME` is customized.

```bash
skill_dir="${CODEX_HOME:-$HOME/.codex}/skills/loop-engineering"; test -f "$skill_dir/adapters/codex/SKILL.md" && uv tool uninstall "loop-engineering" && command rm -r -- "$skill_dir"
```

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
