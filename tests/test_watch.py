from datetime import UTC, datetime, timedelta
from io import StringIO
from pathlib import Path

from loop_engineering import watch
from loop_engineering.ledger import RunStore
from loop_engineering.models.contract import LoopContract
from loop_engineering.models.evidence import EvidenceRecord
from loop_engineering.models.run import CheckerVerdict, EventKind, LoopStatus
from loop_engineering.project import initialize_project
from loop_engineering.watch import discover_project
from tests.factories import valid_contract_data


class FakeStream(StringIO):
    def __init__(self, *, tty: bool, encoding: str = "utf-8") -> None:
        super().__init__()
        self._tty = tty
        self._encoding = encoding

    def isatty(self) -> bool:
        return self._tty

    @property
    def encoding(self) -> str:
        return self._encoding


def create_run(project: Path, loop_id: str) -> RunStore:
    contract_data = valid_contract_data()
    contract_data["loop_id"] = loop_id
    contract_data["repositories"][0]["path"] = str(project)
    return RunStore.create(project, LoopContract.model_validate(contract_data))


def test_discover_project_from_nested_directory(tmp_path: Path) -> None:
    project = tmp_path / "project"
    nested = project / "src" / "feature"
    nested.mkdir(parents=True)
    initialize_project(project)

    root, config = discover_project(nested)

    assert root == project.resolve()
    assert config.protocol_version == "0.1.0"


def test_load_dashboard_reads_only_direct_valid_run_directories(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    initialize_project(project)
    store = create_run(project, "loop-active")
    run_root = project / ".loop-engine" / "runs"
    (run_root / ".draft").mkdir()
    (run_root / "broken").mkdir()
    (run_root / "linked").symlink_to(
        store.run_dir,
        target_is_directory=True,
    )

    dashboard = watch.load_dashboard(project)

    assert [run.loop_id for run in dashboard.runs] == ["loop-active"]
    assert dashboard.warnings == ["broken: FileNotFoundError"]


def test_load_dashboard_isolates_malformed_run_payloads(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    initialize_project(project)
    create_run(project, "loop-valid")
    malformed = create_run(project, "loop-malformed")
    malformed.append_event(
        actor="checker",
        kind=EventKind.CHECKER,
        summary="invalid checker payload",
        payload={"verdict": "unexpected"},
    )

    dashboard = watch.load_dashboard(project)

    assert [run.loop_id for run in dashboard.runs] == ["loop-valid"]
    assert dashboard.warnings == ["loop-malformed: ValueError"]


def test_load_dashboard_aggregates_current_run_facts(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    initialize_project(project)
    store = create_run(project, "loop-current")
    fixed_now = datetime(2026, 8, 1, 8, 0, tzinfo=UTC)
    evidence = EvidenceRecord(
        evidence_id="E-watch",
        contract_version=1,
        command_id="VAL-1",
        repository_id="target",
        criterion_ids=["AC-1"],
        started_at=fixed_now,
        ended_at=fixed_now,
        exit_code=0,
        passed=True,
        code_fingerprint="current",
        stdout_file="E-watch.stdout.txt",
        stderr_file="E-watch.stderr.txt",
        stdout_sha256="0" * 64,
        stderr_sha256="0" * 64,
    )
    validation_id = store.record_intent(
        actor="validator",
        summary="run VAL-1",
        payload={},
    )
    store.record_result(
        action_id=validation_id,
        actor="validator",
        summary="VAL-1 passed",
        payload={"evidence": evidence.model_dump(mode="json")},
    )
    for target in (
        LoopStatus.DISCOVERING,
        LoopStatus.CONTRACT_DRAFTING,
        LoopStatus.AWAITING_APPROVAL,
    ):
        store.record_transition(actor="maker", target=target, reason=target.value)
    store.record_approval(
        actor="user",
        gate="contract_approval",
        approved=True,
        summary="approved",
    )
    pending_id = store.record_intent(
        actor="maker",
        summary="update documentation",
        payload={},
    )
    store.record_checker(
        actor="checker",
        verdict=CheckerVerdict.REVISE,
        findings=["Clarify the command example"],
    )
    state = store.load_state().model_copy(
        update={
            "status": LoopStatus.EXECUTING,
            "iterations_used": 2,
            "no_progress_cycles": 1,
            "started_at": fixed_now - timedelta(minutes=12),
            "updated_at": fixed_now - timedelta(seconds=5),
            "paused_at": None,
            "paused_seconds": 0,
        }
    )
    store.save_state(state)

    run = watch.load_dashboard(project, now=fixed_now).runs[0]

    assert run.contract_version == 1
    assert run.protocol_version == "0.1.0"
    assert run.authorized is True
    assert [(item.criterion_id, item.state) for item in run.criteria] == [
        ("AC-1", "passed")
    ]
    assert run.iterations_used == 2
    assert run.max_iterations == 3
    assert run.elapsed_minutes == 12
    assert run.max_minutes == 30
    assert run.checker_revisions_used == 1
    assert run.max_checker_revisions == 0
    assert run.no_progress_cycles == 1
    assert run.pending_intent_ids == [pending_id]
    assert run.current_action == "update documentation"
    assert run.checker_verdict is CheckerVerdict.REVISE
    assert run.recent_events[-1].summary == "checker verdict: revise"


def test_load_dashboard_does_not_treat_old_contract_intent_as_running(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    initialize_project(project)
    store = create_run(project, "loop-revised")
    old_intent_id = store.record_intent(
        actor="validator",
        summary="run VAL-1",
        payload={},
    )
    for target in (
        LoopStatus.DISCOVERING,
        LoopStatus.CONTRACT_DRAFTING,
        LoopStatus.AWAITING_APPROVAL,
    ):
        store.record_transition(actor="maker", target=target, reason=target.value)
    revised_data = valid_contract_data()
    revised_data["loop_id"] = "loop-revised"
    revised_data["contract_version"] = 2
    revised_data["repositories"][0]["path"] = str(project)
    store.replace_contract(
        LoopContract.model_validate(revised_data),
        actor="user",
        summary="approved revision",
    )

    run = watch.load_dashboard(project).runs[0]

    assert run.criteria[0].state is watch.CriterionState.MISSING
    assert run.pending_intent_ids == [old_intent_id]
    assert [event.summary for event in run.recent_events] == ["approved revision"]


def test_load_dashboard_sorts_active_before_terminal_then_by_update_time(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    initialize_project(project)
    now = datetime(2026, 8, 1, 8, 0, tzinfo=UTC)
    older = create_run(project, "loop-older")
    newer = create_run(project, "loop-newer")
    terminal = create_run(project, "loop-terminal")
    older.save_state(
        older.load_state().model_copy(update={"updated_at": now - timedelta(minutes=2)})
    )
    newer.save_state(
        newer.load_state().model_copy(update={"updated_at": now - timedelta(minutes=1)})
    )
    terminal.save_state(
        terminal.load_state().model_copy(
            update={"status": LoopStatus.DONE, "updated_at": now}
        )
    )

    dashboard = watch.load_dashboard(project, now=now)

    assert [run.loop_id for run in dashboard.runs] == [
        "loop-newer",
        "loop-older",
        "loop-terminal",
    ]


def test_render_dashboard_adapts_wide_and_compact_output(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    initialize_project(project)
    active = create_run(project, "loop-active")
    terminal = create_run(project, "loop-terminal")
    active.save_state(
        active.load_state().model_copy(
            update={
                "status": LoopStatus.EXECUTING,
                "iterations_used": 2,
                "no_progress_cycles": 1,
            }
        )
    )
    active.record_intent(
        actor="maker",
        summary="implement watch dashboard",
        payload={},
    )
    terminal.save_state(
        terminal.load_state().model_copy(update={"status": LoopStatus.DONE})
    )
    dashboard = watch.load_dashboard(project)

    wide = watch.render_dashboard(
        dashboard,
        include_terminal=False,
        width=120,
        color=False,
        unicode=True,
    )
    compact = watch.render_dashboard(
        dashboard,
        include_terminal=True,
        width=72,
        color=False,
        unicode=False,
    )

    assert "LOOP ENGINEERING" in wide
    assert "Active 1" in wide
    assert "Terminal 1 hidden" in wide
    assert "loop-active" in wide
    assert "loop-terminal" not in wide
    assert "Recorded evidence 0 / 1" in wide
    assert "Iterations" in wide
    assert "Checker revisions 0/0" in wide
    assert "No-progress cycles 1" in wide
    assert "Pending intents 1" in wide
    assert "Current implement watch dashboard" in wide
    assert "RECENT ACTIVITY" in wide
    assert "\x1b[" not in wide
    assert "RUN" in compact
    assert "loop-active" in compact
    assert "loop-terminal" in compact
    assert "#" in compact
    assert "●" not in compact
    assert "━" not in compact


def test_render_dashboard_distinguishes_terminal_outcomes(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    initialize_project(project)
    done = create_run(project, "loop-done")
    blocked = create_run(project, "loop-blocked")
    exhausted = create_run(project, "loop-exhausted")
    done.save_state(done.load_state().model_copy(update={"status": LoopStatus.DONE}))
    blocked.save_state(
        blocked.load_state().model_copy(update={"status": LoopStatus.BLOCKED})
    )
    exhausted.save_state(
        exhausted.load_state().model_copy(
            update={"status": LoopStatus.BUDGET_EXHAUSTED}
        )
    )
    dashboard = watch.load_dashboard(project)

    unicode_output = watch.render_dashboard(
        dashboard,
        include_terminal=True,
        width=120,
        color=False,
        unicode=True,
    )
    ascii_output = watch.render_dashboard(
        dashboard,
        include_terminal=True,
        width=120,
        color=False,
        unicode=False,
    )
    color_output = watch.render_dashboard(
        dashboard,
        include_terminal=True,
        width=120,
        color=True,
        unicode=True,
    )

    assert "✓ loop-done" in unicode_output
    assert "✗ loop-blocked" in unicode_output
    assert "! loop-exhausted" in unicode_output
    assert "OK loop-done" in ascii_output
    assert "X loop-blocked" in ascii_output
    assert "! loop-exhausted" in ascii_output
    assert "\x1b[32mDONE" in color_output
    assert "\x1b[31mBLOCKED" in color_output
    assert "\x1b[33mBUDGET_EXHAUSTED" in color_output


def test_render_dashboard_strips_untrusted_terminal_control_sequences(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    initialize_project(project)
    contract_data = valid_contract_data()
    contract_data["loop_id"] = "loop-untrusted-text"
    contract_data["repositories"][0]["path"] = str(project)
    contract_data["acceptance_criteria"][0]["description"] = (
        "safe\x1b[2J\nnext\x00item"
    )
    RunStore.create(project, LoopContract.model_validate(contract_data))
    (project / ".loop-engine" / "runs" / "broken\x1b[31m").mkdir()

    output = watch.render_dashboard(
        watch.load_dashboard(project),
        include_terminal=False,
        width=120,
        color=False,
        unicode=True,
    )

    assert "\x1b" not in output
    assert "\x00" not in output
    assert "safe next item" in output
    assert "broken: FileNotFoundError" in output


def test_watch_project_writes_one_plain_frame_for_non_tty(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    initialize_project(project)
    create_run(project, "loop-active")
    stream = FakeStream(tty=False)

    watch.watch_project(
        project,
        include_terminal=False,
        stream=stream,
        sleeper=lambda _: (_ for _ in ()).throw(AssertionError("must not sleep")),
    )

    assert "loop-active" in stream.getvalue()
    assert "\x1b[" not in stream.getvalue()


def test_watch_project_keeps_final_terminal_frame_then_exits(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    initialize_project(project)
    store = create_run(project, "loop-active")
    store.save_state(
        store.load_state().model_copy(update={"status": LoopStatus.EXECUTING})
    )
    stream = FakeStream(tty=True)
    sleep_calls: list[float] = []

    def finish_run(interval: float) -> None:
        sleep_calls.append(interval)
        store.save_state(
            store.load_state().model_copy(update={"status": LoopStatus.DONE})
        )

    watch.watch_project(
        project,
        include_terminal=False,
        stream=stream,
        interval_seconds=0.25,
        sleeper=finish_run,
    )

    output = stream.getvalue()
    assert sleep_calls == [0.25]
    assert "loop-active" in output
    assert "DONE" in output
    assert output.startswith("\x1b[?25l")
    assert output.endswith("\x1b[0m\x1b[?25h")


def test_watch_project_restores_terminal_after_keyboard_interrupt(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    initialize_project(project)
    create_run(project, "loop-active")
    stream = FakeStream(tty=True)

    def interrupt(_: float) -> None:
        raise KeyboardInterrupt

    watch.watch_project(
        project,
        include_terminal=False,
        stream=stream,
        sleeper=interrupt,
    )

    assert stream.getvalue().endswith("\x1b[0m\x1b[?25h")
