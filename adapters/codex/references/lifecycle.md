# Adapter lifecycle playbook

Read this playbook only for installation, update, status, uninstall or target-project
initialization. These are user-operated bootstrap actions, not Maker-loop actions.

## Adapter lifecycle

Installation and removal are user-operated bootstrap actions, not Maker-loop
actions. Explain the exact command, but never run it on the user's behalf. The
managed checkout is exactly `<CODEX_HOME>/skills/loop-engine`; resolve
`CODEX_HOME` explicitly, defaulting to `~/.codex` only when it is unset.

Unix install reference:

```bash
codex_home="${CODEX_HOME:-$HOME/.codex}"
skill_dir="$codex_home/skills/loop-engine"
mkdir -p "$codex_home/skills" && \
git clone --depth 1 --branch master "https://github.com/MRongM/LoopEngineering.git" "$skill_dir" && \
python3 "$skill_dir/adapters/codex/scripts/manage.py" install --codex-home "$codex_home" && \
loop-engine --version
```

PowerShell install reference:

```powershell
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
$skillDir = Join-Path $codexHome "skills/loop-engine"
$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path (Join-Path $codexHome "skills") | Out-Null
git clone --depth 1 --branch master "https://github.com/MRongM/LoopEngineering.git" "$skillDir"
if ($LASTEXITCODE -ne 0) { throw "Loop Engineering install failed" }
py -3.12 "$skillDir/adapters/codex/scripts/manage.py" install --codex-home "$codexHome"
if ($LASTEXITCODE -ne 0) { throw "Loop Engineering install failed" }
loop-engine --version
if ($LASTEXITCODE -ne 0) { throw "Loop Engineering install failed" }
```

For uninstall, first move outside the checkout. Use the same resolved home and run
`python3 "<skill-dir>/adapters/codex/scripts/manage.py" uninstall --codex-home "<resolved-home>" --yes`
on Unix or replace `python3` with `py -3.12` in PowerShell.

- The manager rejects wrong paths, linked directories, invalid markers, dirty or
  untracked files, local branches, stashes, unpreserved commits, execution from
  inside the checkout, missing prerequisites and unexpected `uv` failures. An
  already absent CLI is a valid partial-uninstall state.
- Never replace the manager with raw `rm`, an overwrite, a force flag, a symlink,
  or a remote script pipe. Start a new Codex session after either lifecycle action.

Use the copy-paste Unix and Windows commands in the repository `README.md` and
`docs/adoption.md`; run `manage.py --help` for the local command reference.

## Target-project initialization

Project initialization is also user-operated. Explain, but do not run, the exact command:

```bash
loop-engine project init --root "<resolved-project-root>"
```

It may create only the canonical `.loop-engine/` control root described by Core Protocol
0.1.0. If `.loop-engine/project.yaml` already exists, inspect it instead of overwriting it.
Initialization must fail closed on a conflicting Loop-owned top-level directory and must
never move or delete user data.
