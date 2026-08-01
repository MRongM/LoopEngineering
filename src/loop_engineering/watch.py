import os
import re
import shutil
import time
from collections.abc import Callable
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import TextIO

import yaml

from loop_engineering.contract import load_contract
from loop_engineering.ledger import RunStore
from loop_engineering.models.contract import StrictModel
from loop_engineering.models.evidence import EvidenceRecord
from loop_engineering.models.run import CheckerVerdict, EventKind, LoopStatus
from loop_engineering.project import ProjectConfig
from loop_engineering.redaction import redact
from loop_engineering.state_machine import TERMINAL

_ANSI_ESCAPE = re.compile(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|[@-_])")


class CriterionState(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    RUNNING = "running"
    MISSING = "missing"


class CriterionProgress(StrictModel):
    criterion_id: str
    description: str
    state: CriterionState
    required_evidence: list[str]


class EventProgress(StrictModel):
    timestamp: datetime
    kind: EventKind
    actor: str
    summary: str


class RunProgress(StrictModel):
    loop_id: str
    objective: str
    contract_version: int
    protocol_version: str
    status: LoopStatus
    updated_at: datetime
    terminal: bool
    authorized: bool
    criteria: list[CriterionProgress]
    iterations_used: int
    max_iterations: int
    elapsed_minutes: int
    max_minutes: int
    checker_revisions_used: int
    max_checker_revisions: int
    no_progress_cycles: int
    pending_intent_ids: list[str]
    current_action: str | None
    pause_reason: str | None
    checker_verdict: CheckerVerdict | None
    recent_events: list[EventProgress]


class WatchDashboard(StrictModel):
    project_root: Path
    generated_at: datetime
    runs: list[RunProgress]
    warnings: list[str]


def discover_project(start: Path) -> tuple[Path, ProjectConfig]:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        config_path = candidate / ".loop-engineering" / "project.yaml"
        if config_path.is_file():
            raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
            return candidate, ProjectConfig.model_validate(raw)
    raise FileNotFoundError("no .loop-engineering/project.yaml found")


def _load_run_progress(run_dir: Path, *, now: datetime) -> RunProgress:
    store = RunStore.open(run_dir)
    state = store.load_state()
    contract = load_contract(store.contract_path)
    events = store.events()
    summary = store.summary()
    current_events = [
        event
        for event in events
        if event.contract_version == state.contract_version
    ]
    evidence_by_command: dict[str, EvidenceRecord] = {}
    for event in current_events:
        if event.kind is not EventKind.RESULT:
            continue
        raw_evidence = event.payload.get("evidence")
        if not isinstance(raw_evidence, dict):
            continue
        try:
            evidence = EvidenceRecord.model_validate(raw_evidence)
        except ValueError:
            continue
        if evidence.contract_version == state.contract_version:
            evidence_by_command[evidence.command_id] = evidence
    pending = store.pending_intents()
    current_pending = [
        event for event in pending if event.contract_version == state.contract_version
    ]
    validation_ids = {command.id for command in contract.validation_commands}
    running_commands = {
        event.summary.removeprefix("run ")
        for event in current_pending
        if event.actor == "validator"
        and event.summary.startswith("run ")
        and event.summary.removeprefix("run ") in validation_ids
    }
    criteria: list[CriterionProgress] = []
    for criterion in contract.acceptance_criteria:
        required = criterion.required_evidence
        if running_commands.intersection(required):
            criterion_state = CriterionState.RUNNING
        elif all(
            command_id in evidence_by_command
            and evidence_by_command[command_id].passed
            for command_id in required
        ):
            criterion_state = CriterionState.PASSED
        elif any(
            command_id in evidence_by_command
            and not evidence_by_command[command_id].passed
            for command_id in required
        ):
            criterion_state = CriterionState.FAILED
        else:
            criterion_state = CriterionState.MISSING
        criteria.append(
            CriterionProgress(
                criterion_id=criterion.id,
                description=criterion.description,
                state=criterion_state,
                required_evidence=required,
            )
        )
    checker_verdict = summary["checker_verdict"]
    return RunProgress(
        loop_id=state.loop_id,
        objective=contract.objective,
        contract_version=contract.contract_version,
        protocol_version=contract.protocol_version,
        status=state.status,
        updated_at=state.updated_at,
        terminal=state.status in TERMINAL,
        authorized=bool(summary["contract_authorized"]),
        criteria=criteria,
        iterations_used=state.iterations_used,
        max_iterations=contract.budget.max_iterations,
        elapsed_minutes=max(
            0,
            int((now - state.started_at).total_seconds() / 60),
        ),
        max_minutes=contract.budget.max_minutes,
        checker_revisions_used=state.checker_revisions_used,
        max_checker_revisions=contract.budget.max_checker_revisions,
        no_progress_cycles=state.no_progress_cycles,
        pending_intent_ids=[
            event.action_id for event in pending if event.action_id is not None
        ],
        current_action=pending[-1].summary if pending else None,
        pause_reason=state.pause_reason,
        checker_verdict=(
            CheckerVerdict(checker_verdict)
            if checker_verdict is not None
            else None
        ),
        recent_events=[
            EventProgress(
                timestamp=event.timestamp,
                kind=event.kind,
                actor=event.actor,
                summary=event.summary,
            )
            for event in current_events[-4:]
        ],
    )


def load_dashboard(
    start: Path,
    *,
    now: datetime | None = None,
) -> WatchDashboard:
    project_root, config = discover_project(start)
    run_root = project_root / config.run_root
    generated_at = now or datetime.now(UTC)
    runs: list[RunProgress] = []
    warnings: list[str] = []
    if run_root.is_dir():
        for child in run_root.iterdir():
            if (
                child.name.startswith(".")
                or child.is_symlink()
                or child.is_junction()
                or not child.is_dir()
            ):
                continue
            try:
                runs.append(_load_run_progress(child, now=generated_at))
            except FileNotFoundError:
                if child.exists():
                    warnings.append(f"{child.name}: FileNotFoundError")
            except Exception as error:  # noqa: BLE001
                warnings.append(f"{child.name}: {type(error).__name__}")
    runs.sort(
        key=lambda run: (
            run.terminal,
            -run.updated_at.timestamp(),
            run.loop_id,
        )
    )
    return WatchDashboard(
        project_root=project_root,
        generated_at=generated_at,
        runs=runs,
        warnings=sorted(warnings),
    )


def _safe_text(value: str) -> str:
    without_ansi = _ANSI_ESCAPE.sub("", str(redact(value)))
    printable = "".join(
        character if character.isprintable() else " " for character in without_ansi
    )
    return " ".join(printable.split())


def _bar(used: int, maximum: int, *, size: int, unicode: bool) -> str:
    filled = 0 if maximum <= 0 else min(size, max(0, round(size * used / maximum)))
    full, empty = ("█", "░") if unicode else ("#", "-")
    return full * filled + empty * (size - filled)


def _age(updated_at: datetime, generated_at: datetime) -> str:
    seconds = max(0, int((generated_at - updated_at).total_seconds()))
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h"
    return f"{hours // 24}d"


def _marker(run: RunProgress, *, unicode: bool) -> str:
    if run.status is LoopStatus.PAUSED:
        return "Ⅱ" if unicode else "||"
    if run.status is LoopStatus.DONE:
        return "✓" if unicode else "OK"
    if run.status is LoopStatus.BLOCKED:
        return "✗" if unicode else "X"
    if run.status is LoopStatus.BUDGET_EXHAUSTED:
        return "!"
    return "●" if unicode else "*"


def _criterion_marker(state: CriterionState, *, unicode: bool) -> str:
    if unicode:
        return {
            CriterionState.PASSED: "✓",
            CriterionState.FAILED: "✗",
            CriterionState.RUNNING: "◉",
            CriterionState.MISSING: "○",
        }[state]
    return {
        CriterionState.PASSED: "+",
        CriterionState.FAILED: "!",
        CriterionState.RUNNING: ">",
        CriterionState.MISSING: "-",
    }[state]


def _paint(value: str, code: str, *, color: bool) -> str:
    return f"\x1b[{code}m{value}\x1b[0m" if color else value


def _status_color(status: LoopStatus) -> str:
    if status is LoopStatus.DONE:
        return "32"
    if status is LoopStatus.BLOCKED:
        return "31"
    if status in {LoopStatus.PAUSED, LoopStatus.BUDGET_EXHAUSTED}:
        return "33"
    return "36"


def _visible_runs(
    dashboard: WatchDashboard,
    *,
    include_terminal: bool,
    retained_terminal_ids: frozenset[str],
) -> list[RunProgress]:
    if include_terminal:
        return dashboard.runs
    return [
        run
        for run in dashboard.runs
        if not run.terminal or run.loop_id in retained_terminal_ids
    ]


def render_dashboard(
    dashboard: WatchDashboard,
    *,
    include_terminal: bool,
    width: int,
    color: bool,
    unicode: bool,
    retained_terminal_ids: frozenset[str] = frozenset(),
) -> str:
    visible = _visible_runs(
        dashboard,
        include_terminal=include_terminal,
        retained_terminal_ids=retained_terminal_ids,
    )
    active_count = sum(
        not run.terminal and run.status is not LoopStatus.PAUSED
        for run in dashboard.runs
    )
    paused_count = sum(run.status is LoopStatus.PAUSED for run in dashboard.runs)
    terminal_count = sum(run.terminal for run in dashboard.runs)
    if width < 96:
        lines = [
            f"LOOP ENGINEERING · {_safe_text(str(dashboard.project_root))}",
            (
                f"Active {active_count}  Paused {paused_count}  "
                f"Terminal {terminal_count}"
            ),
            "",
            "RUN                         STATE            EVIDENCE  ITERATIONS  UPDATED",
        ]
        for run in visible:
            passed = sum(
                criterion.state is CriterionState.PASSED
                for criterion in run.criteria
            )
            lines.append(
                f"{_marker(run, unicode=unicode):<2} "
                f"{run.loop_id[:26]:<26} "
                f"{run.status.value.upper():<16} "
                f"{passed}/{len(run.criteria):<7} "
                f"{_bar(run.iterations_used, run.max_iterations, size=6, unicode=unicode)} "
                f"{_age(run.updated_at, dashboard.generated_at):>7}"
            )
        if not visible:
            lines.append("No active Loop runs. Use --all to include terminal history.")
        if dashboard.warnings:
            lines.extend(("", f"Warnings {len(dashboard.warnings)}"))
            lines.extend(f"! {_safe_text(warning)}" for warning in dashboard.warnings)
        return "\n".join(lines) + "\n"

    separator = ("━" if unicode else "-") * min(width, 110)
    terminal_label = (
        f"Terminal {terminal_count}"
        if include_terminal
        else f"Terminal {terminal_count} hidden"
    )
    lines = [
        f"LOOP ENGINEERING · {_safe_text(str(dashboard.project_root))}",
        separator,
        f"Active {active_count}     Paused {paused_count}     {terminal_label}",
    ]
    for run in visible:
        passed = sum(
            criterion.state is CriterionState.PASSED for criterion in run.criteria
        )
        status = _paint(
            run.status.value.upper(),
            _status_color(run.status),
            color=color,
        )
        authorization = "✓ authorized" if run.authorized else "! unauthorized"
        if not unicode:
            authorization = "authorized" if run.authorized else "unauthorized"
        lines.extend(
            (
                "",
                (
                    f"{_marker(run, unicode=unicode)} {run.loop_id}"
                    f"    {status}    updated {_age(run.updated_at, dashboard.generated_at)} ago"
                ),
                (
                    f"  Contract v{run.contract_version} · protocol {run.protocol_version} · "
                    f"{authorization}"
                ),
                f"  Recorded evidence {passed} / {len(run.criteria)}",
            )
        )
        for criterion in run.criteria:
            lines.append(
                f"    {_criterion_marker(criterion.state, unicode=unicode)} "
                f"{criterion.criterion_id}  {_safe_text(criterion.description)}"
            )
        lines.extend(
            (
                (
                    "  Iterations "
                    f"{_bar(run.iterations_used, run.max_iterations, size=10, unicode=unicode)} "
                    f"{run.iterations_used}/{run.max_iterations}    "
                    "Time "
                    f"{_bar(run.elapsed_minutes, run.max_minutes, size=10, unicode=unicode)} "
                    f"{run.elapsed_minutes}/{run.max_minutes}m"
                ),
                (
                    f"  Pending intents {len(run.pending_intent_ids)}    "
                    f"Checker {run.checker_verdict.value.upper() if run.checker_verdict else '—'}"
                ),
                (
                    f"  Checker revisions {run.checker_revisions_used}/"
                    f"{run.max_checker_revisions}    "
                    f"No-progress cycles {run.no_progress_cycles}"
                ),
            )
        )
        if run.current_action:
            lines.append(f"  Current {_safe_text(run.current_action)}")
        if run.pause_reason:
            lines.append(f"  Pause {_safe_text(run.pause_reason)}")
    if not visible:
        lines.extend(("", "No active Loop runs. Use --all to include terminal history."))
    recent = sorted(
        (
            (event.timestamp, run.loop_id, event)
            for run in visible
            for event in run.recent_events
        ),
        reverse=True,
        key=lambda item: (item[0], item[1]),
    )[:5]
    if recent:
        lines.extend(("", "RECENT ACTIVITY"))
        for timestamp, loop_id, event in recent:
            lines.append(
                f"  {timestamp:%H:%M:%S}  {loop_id:<26} "
                f"{event.kind.value:<10} {_safe_text(event.summary)}"
            )
    if dashboard.warnings:
        lines.extend(("", f"WARNINGS {len(dashboard.warnings)}"))
        lines.extend(f"  ! {_safe_text(warning)}" for warning in dashboard.warnings)
    lines.extend((separator, "Recorded evidence is informational; DONE remains authoritative."))
    return "\n".join(lines) + "\n"


def _supports_unicode(stream: TextIO) -> bool:
    encoding = stream.encoding or "utf-8"
    try:
        "●━█░✓✗◉○Ⅱ—".encode(encoding)
    except (LookupError, UnicodeEncodeError):
        return False
    return True


def watch_project(
    start: Path,
    *,
    include_terminal: bool,
    stream: TextIO,
    interval_seconds: float = 1.0,
    sleeper: Callable[[float], None] = time.sleep,
) -> None:
    if interval_seconds <= 0:
        raise ValueError("watch interval must be positive")
    is_tty = stream.isatty()
    unicode = _supports_unicode(stream)
    color = (
        is_tty
        and "NO_COLOR" not in os.environ
        and os.environ.get("TERM") != "dumb"
    )
    width = shutil.get_terminal_size(fallback=(120, 24)).columns if is_tty else 120
    if not is_tty:
        dashboard = load_dashboard(start)
        stream.write(
            render_dashboard(
                dashboard,
                include_terminal=include_terminal,
                width=width,
                color=False,
                unicode=unicode,
            )
        )
        stream.flush()
        return

    observed_active_ids: set[str] = set()
    last_frame: str | None = None
    stream.write("\x1b[?25l")
    stream.flush()
    try:
        while True:
            dashboard = load_dashboard(start)
            active_ids = {
                run.loop_id for run in dashboard.runs if not run.terminal
            }
            observed_active_ids.update(active_ids)
            retained = (
                frozenset(observed_active_ids)
                if observed_active_ids and not active_ids
                else frozenset()
            )
            frame = render_dashboard(
                dashboard,
                include_terminal=include_terminal,
                width=width,
                color=color,
                unicode=unicode,
                retained_terminal_ids=retained,
            )
            if frame != last_frame:
                stream.write("\x1b[2J\x1b[H")
                stream.write(frame)
                stream.flush()
                last_frame = frame
            if not active_ids:
                break
            sleeper(interval_seconds)
    except KeyboardInterrupt:
        pass
    finally:
        stream.write("\x1b[0m\x1b[?25h")
        stream.flush()
