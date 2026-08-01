# Loop Engineering

Loop Engineering 0.3.0 provides evidence-gated, recoverable execution loops for
coding agents. The Core is tool-independent; the first adapter targets Codex.
Protocol 0.3 is Autonomous-only: every new task uses one approved contract and
continues inside its verified scope without a control-mode choice.

## Use it now

Without installing code, reference the approved design in your task and require an
approved Loop Contract before any mutation:

- [0.3 Autonomous-only design](docs/superpowers/specs/2026-07-31-loop-engineering-0.3-autonomous-only-design.md)
- [Cross-project adoption guide](docs/adoption.md)
- [Compatibility and naming](docs/compatibility.md)

## Install in Codex

The managed flow requires Python 3.12+, Git and `uv`. It clones the complete
repository to the canonical Skill directory. It installs the CLI through the
checked-in lifecycle manager and never overwrites an existing destination.

### Unix one-line install

Run from any directory:

```bash
codex_home="${CODEX_HOME:-$HOME/.codex}"; skill_dir="$codex_home/skills/loop-engineering"; mkdir -p "$codex_home/skills" && git clone --depth 1 --branch master "https://github.com/MRongM/LoopEngineering.git" "$skill_dir" && python3 "$skill_dir/adapters/codex/scripts/manage.py" install --codex-home "$codex_home" && loop-engine --version
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
loop-engine --version
if ($LASTEXITCODE -ne 0) { throw "Loop Engineering install failed" }
```

After the command reports the version, start a new Codex session. Only a new task starts with
`$loop-engine`; later turns for the uniquely bound task may use natural language. Host
selection alone cannot create or adopt a task, approve a contract, or modify a Run.

### Codex task-scoped continuation

An explicit start first binds one Pending Draft to the current conversation. Clarifications,
approval of its latest complete summary, revisions, pause recovery, cancellation and feedback
can then be expressed naturally without a fixed confirmation subcommand. Questions, partial
answers, stale references and unrelated messages grant no approval.

After contract approval, every new Codex Loop task uses a canonical Goal bound to the Run and
append-only ledger by default. The contract must disclose exact Goal create and complete
operations before approval. A missing Goal tool, unrelated active Goal, binding mismatch or
multiple candidate tasks causes a hard pause; the Adapter never scans for or adopts a latest
Run. Explicit `$loop-engine` remains available for conservative recovery.

The Goal is only a scheduler. Loop Engineering remains authoritative for scope, permissions,
evidence, engineering budgets, Checker findings and `DONE`; Goal token usage is not converted
into Loop iterations or time. Cancellation or a terminal Run closes implicit continuation,
and new work again requires `$loop-engine`. Only authoritative Loop `DONE` can complete the
Goal.

The managed checkout must contain this adapter version, and Codex must be restarted after a
user-operated update before task-scoped continuation is available.

## Watch project progress

From any directory inside an initialized target project, open the read-only terminal
dashboard with:

```bash
loop-engine watch
loop-engine watch --all
```

The first command shows active and paused Runs; `--all` also includes terminal history.
The command discovers the nearest `.loop-engineering/project.yaml` by walking upward and
does not accept a Run-directory argument. An interactive terminal refreshes in place until
no active Run remains or you press Ctrl-C; redirected output emits one plain snapshot.
Watching never adopts, resumes, approves or otherwise mutates a Run, and displayed evidence
does not replace authoritative completion evaluation.

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
codex_home="${CODEX_HOME:-$HOME/.codex}"; skill_dir="$codex_home/skills/loop-engineering"; python3 "$skill_dir/adapters/codex/scripts/manage.py" update --codex-home "$codex_home" && loop-engine --version
```

### Windows PowerShell update

```powershell
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
$skillDir = Join-Path $codexHome "skills/loop-engineering"
py -3.12 "$skillDir/adapters/codex/scripts/manage.py" update --codex-home "$codexHome"
if ($LASTEXITCODE -ne 0) { throw "Loop Engineering update failed" }
loop-engine --version
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

## Safety boundary

The release has no scheduler, daemon, automatic merge, automatic deployment,
force-push or history rewrite. Autonomous production or sensitive-data access is
allowed only when the exact high risk is disclosed in a `0.3.0` contract and bound
to its single approval; there is no implicit production authority. Runtime state
under `.loop-runs/` is local and ignored by default.

## Names and compatibility

The product and repository remain **Loop Engineering**. The Python distribution and
managed checkout remain `loop-engineering`; the Codex Skill trigger remains
`$loop-engine`; the only Agent Shell executable is `loop-engine`. The distribution
does not install legacy CLI aliases. See [compatibility and naming](docs/compatibility.md)
for supported legacy Autonomous contracts and deterministic rejection boundaries.

## Development

```bash
uv sync --dev
uv run pytest -q
uv run ruff check "src" "tests" "adapters/codex/scripts"
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
| Automatic merge/deployment | Forbidden |
| Autonomous production/sensitive operation | Exact disclosed risk + bound approval required |
