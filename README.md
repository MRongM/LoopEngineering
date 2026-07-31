# Loop Engineering

Loop Engineering 0.2.0 provides evidence-gated, recoverable execution loops for
coding agents. The Core is tool-independent; Codex and Claude Code adapters provide
host-specific discovery, approval, execution, and lifecycle guidance.

## Use it now

Without installing code, reference the approved design in your task and require an
approved Loop Contract before any mutation:

- [Design specification](docs/superpowers/specs/2026-07-30-loop-engineering-protocol-design.md)
- [Cross-project adoption guide](docs/adoption.md)

## Install in Codex

The managed flow requires Python 3.12+, Git and `uv`. It clones the complete
repository to the canonical Skill directory. It installs the CLI through the
checked-in lifecycle manager and never overwrites an existing destination.

### Unix one-line install

Run from any directory:

```bash
codex_home="${CODEX_HOME:-$HOME/.codex}"; skill_dir="$codex_home/skills/loop-engineering"; mkdir -p "$codex_home/skills" && git clone --depth 1 --branch master "https://github.com/MRongM/LoopEngineering.git" "$skill_dir" && python3 "$skill_dir/adapters/codex/scripts/manage.py" install --codex-home "$codex_home" && loop-engineering --version
```

### Windows PowerShell install

```powershell
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
$skillDir = Join-Path $codexHome "skills/loop-engineering"
$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path (Join-Path $codexHome "skills") | Out-Null
git clone --depth 1 --branch master "https://github.com/MRongM/LoopEngineering.git" "$skillDir"
if ($LASTEXITCODE -ne 0) { throw "Loop Engineering install failed" }
py -3.12 "$skillDir/adapters/codex/scripts/manage.py" install --codex-home "$codexHome"
if ($LASTEXITCODE -ne 0) { throw "Loop Engineering install failed" }
loop-engineering --version
if ($LASTEXITCODE -ne 0) { throw "Loop Engineering install failed" }
```

After the command reports the version, start a new Codex session and invoke
`$loop-engine`. The Skill is manual-only and is never selected from task semantics alone.
Include `$loop-engine` again in every later user message that should continue the Skill.

## Update the Skill from a shell

Run this manually in a terminal; it is not a Codex chat command. Update is
fast-forward-only. The manager requires the exact clean managed
checkout on `master`, verifies the official repository URL, runs
`git pull --ff-only origin master`, revalidates the updated Skill checkout, and then runs
`uv tool install --reinstall` from that checkout. It refuses local changes, extra branches,
stashes, unpreserved commits, detached HEAD, alternate origins, and non-fast-forward history.

If CLI reinstall fails after Git succeeds, the updated Skill checkout is retained. Resolve the
reported `uv` problem and rerun the same command; the manager never deletes or rewinds it.

### Unix one-line update

```bash
codex_home="${CODEX_HOME:-$HOME/.codex}"; skill_dir="$codex_home/skills/loop-engineering"; python3 "$skill_dir/adapters/codex/scripts/manage.py" update --codex-home "$codex_home" && loop-engineering --version
```

### Windows PowerShell update

```powershell
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
$skillDir = Join-Path $codexHome "skills/loop-engineering"
py -3.12 "$skillDir/adapters/codex/scripts/manage.py" update --codex-home "$codexHome"
if ($LASTEXITCODE -ne 0) { throw "Loop Engineering update failed" }
loop-engineering --version
if ($LASTEXITCODE -ne 0) { throw "Loop Engineering update failed" }
```

Start a new Codex session after the command reports the updated version.

## Uninstall from Codex

First change to a directory outside the Skill checkout. The manager requires explicit
`--yes`, refuses dirty or symlinked checkouts (including linked parent directories) and
local-only Git state, validates repository markers, and keeps the Skill directory when an
unexpected CLI uninstall error occurs. It accepts an already absent CLI so a partial
installation can still be cleaned up safely.

### Unix one-line uninstall

```bash
codex_home="${CODEX_HOME:-$HOME/.codex}"; skill_dir="$codex_home/skills/loop-engineering"; python3 "$skill_dir/adapters/codex/scripts/manage.py" uninstall --codex-home "$codex_home" --yes
```

### Windows PowerShell uninstall

```powershell
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
$skillDir = Join-Path $codexHome "skills/loop-engineering"
py -3.12 "$skillDir/adapters/codex/scripts/manage.py" uninstall --codex-home "$codexHome" --yes
```

Start a new Codex session after removal. Do not substitute a manual recursive delete;
if the manager refuses the checkout, inspect and preserve the reported local state.

## Install in Claude Code

The Claude Code adapter uses the native Plugin/Marketplace lifecycle. It requires
Claude Code with plugin support, Python 3.12+, Git and `uv`. Installation is a
user-operated bootstrap action: the Adapter never runs these commands on the user's behalf.

Install the Core CLI, register this repository as a marketplace, and install the plugin:

```bash
uv tool install "git+https://github.com/MRongM/LoopEngineering.git@master"
claude plugin marketplace add MRongM/LoopEngineering
claude plugin install loop-engineering@loop-engineering --scope user
loop-engineering --version
```

Start a new Claude Code session, or run `/reload-plugins`, then invoke the manual-only
Skill with `/loop-engineering:loop-engine`. Every later message that should continue
the workflow must invoke the Skill again. Some Claude Code versions also expose the
unqualified `/loop-engine` alias; the namespaced command is the stable documented entry.

Update the marketplace, plugin and CLI explicitly:

```bash
claude plugin marketplace update loop-engineering
claude plugin update loop-engineering@loop-engineering --scope user
uv tool install --reinstall "git+https://github.com/MRongM/LoopEngineering.git@master"
loop-engineering --version
```

Uninstall the plugin and CLI explicitly:

```bash
claude plugin uninstall loop-engineering@loop-engineering --scope user
uv tool uninstall loop-engineering
```

Plugin installation packages the complete repository so the Skill reads the authoritative
root `PROTOCOL.md`; only `adapters/claude/` is exposed as a Skill component. Use
`claude plugin validate .` in a checkout to validate its native manifests without installing.

## Safety boundary

The release has no scheduler, daemon, automatic merge, automatic deployment,
force-push or history rewrite. Autonomous production or sensitive-data access is
allowed only when the exact high risk is disclosed in a `0.2.0` contract and bound
to its single approval; there is no implicit production authority. Runtime state
under `.loop-runs/` is local and ignored by default.

## Development

```bash
uv sync --dev
uv run pytest -q
uv run ruff check "src" "tests" "adapters/codex/scripts"
claude plugin validate .
uv build
```

## Support status

| Capability | Status |
|---|---|
| Python 3.12 on macOS | Verified by the local release suite |
| Claude Code 2.1.176 plugin validation | Verified by the local adapter suite |
| Python 3.13–3.14 | Declared compatible; CI is required before claiming verified execution |
| Linux Core CLI | Designed and documented; Linux CI is required before claiming verified execution |
| Windows Core path/subprocess APIs | Designed and documented; Windows CI is required before claiming verified execution |
| Git worktree/commit/push | Verified against a local bare remote |
| GitHub PR creation | Requires an authenticated `gh` CLI |
| Scheduler or daemon | Not included |
| Automatic merge/deployment | Forbidden |
| Autonomous production/sensitive operation | Exact disclosed risk + bound approval required |
