import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import IO

from pydantic import ValidationError

from loop_engineering import __version__
from loop_engineering.contract import export_schemas, load_contract
from loop_engineering.evidence import DoneEvaluator, ValidationRunner, evaluate_scope
from loop_engineering.git_automation import GitAutomation
from loop_engineering.ledger import RunStore
from loop_engineering.models.evidence import CompletionContext
from loop_engineering.models.run import CheckerVerdict, LoopStatus
from loop_engineering.policy import (
    ActionRequest,
    GateOutcome,
    GatePolicy,
    GateRequirement,
    render_confirmation,
)
from loop_engineering.project import initialize_project
from loop_engineering.redaction import redact
from loop_engineering.state_machine import BudgetCondition, budget_status


def _json(value: object, *, stream: IO[str] | None = None) -> None:
    print(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False),
        file=stream or sys.stdout,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="loop-engine")
    parser.add_argument("--version", action="version", version=__version__)
    groups = parser.add_subparsers(dest="group", required=True)

    project = groups.add_parser("project")
    project_commands = project.add_subparsers(dest="command", required=True)
    project_init = project_commands.add_parser("init")
    project_init.add_argument("--root", type=Path, default=Path.cwd())
    project_init.add_argument("--update-gitignore", action="store_true")

    contract = groups.add_parser("contract")
    contract_commands = contract.add_subparsers(dest="command", required=True)
    contract_validate = contract_commands.add_parser("validate")
    contract_validate.add_argument("path", type=Path)

    schema = groups.add_parser("schema")
    schema_commands = schema.add_subparsers(dest="command", required=True)
    schema_export = schema_commands.add_parser("export")
    schema_export.add_argument("output", type=Path)

    run = groups.add_parser("run")
    run_commands = run.add_subparsers(dest="command", required=True)
    run_create = run_commands.add_parser("create")
    run_create.add_argument("contract", type=Path)
    run_create.add_argument("--project", type=Path, required=True)
    run_status = run_commands.add_parser("status")
    run_status.add_argument("run_dir", type=Path)
    run_events = run_commands.add_parser("events")
    run_events.add_argument("run_dir", type=Path)
    run_transition = run_commands.add_parser("transition")
    run_transition.add_argument("run_dir", type=Path)
    run_transition.add_argument(
        "target",
        choices=[status.value for status in LoopStatus],
    )
    run_transition.add_argument("--actor", required=True)
    run_transition.add_argument("--reason", required=True)
    run_complete = run_commands.add_parser("complete")
    run_complete.add_argument("run_dir", type=Path)
    run_complete.add_argument("--actor", required=True)
    run_complete.add_argument("--reason", required=True)
    run_intent = run_commands.add_parser("intent")
    run_intent.add_argument("run_dir", type=Path)
    run_intent.add_argument("--actor", required=True)
    run_intent.add_argument("--summary", required=True)
    run_intent.add_argument("--payload-json", default="{}")
    run_result = run_commands.add_parser("result")
    run_result.add_argument("run_dir", type=Path)
    run_result.add_argument("action_id")
    run_result.add_argument("--actor", required=True)
    run_result.add_argument("--summary", required=True)
    run_result.add_argument("--payload-json", default="{}")
    run_result.add_argument(
        "--progress",
        choices=["yes", "no", "unknown"],
        default="unknown",
    )
    run_result.add_argument(
        "--same-strategy",
        choices=["yes", "no", "unknown"],
        default="unknown",
    )
    run_approval = run_commands.add_parser("approval")
    run_approval.add_argument("run_dir", type=Path)
    run_approval.add_argument("--actor", required=True)
    run_approval.add_argument("--gate", required=True)
    run_approval.add_argument(
        "--decision",
        choices=["approve", "reject"],
        required=True,
    )
    run_approval.add_argument("--summary", required=True)
    run_checker = run_commands.add_parser("checker")
    run_checker.add_argument("run_dir", type=Path)
    run_checker.add_argument("--actor", required=True)
    run_checker.add_argument(
        "--verdict",
        choices=[verdict.value for verdict in CheckerVerdict],
        required=True,
    )
    run_checker.add_argument("--findings-json", default="[]")
    run_revise = run_commands.add_parser("revise")
    run_revise.add_argument("run_dir", type=Path)
    run_revise.add_argument("contract", type=Path)
    run_revise.add_argument("--actor", required=True)
    run_revise.add_argument("--summary", required=True)

    evidence = groups.add_parser("evidence")
    evidence_commands = evidence.add_subparsers(dest="command", required=True)
    evidence_run = evidence_commands.add_parser("run")
    evidence_run.add_argument("run_dir", type=Path)
    evidence_run.add_argument("command_id")

    budget = groups.add_parser("budget")
    budget_commands = budget.add_subparsers(dest="command", required=True)
    budget_check = budget_commands.add_parser("check")
    budget_check.add_argument("run_dir", type=Path)

    completion = groups.add_parser("completion")
    completion_commands = completion.add_subparsers(dest="command", required=True)
    completion_evaluate = completion_commands.add_parser("evaluate")
    completion_evaluate.add_argument("contract", type=Path)
    completion_evaluate.add_argument("context", type=Path)

    gate = groups.add_parser("gate")
    gate_commands = gate.add_subparsers(dest="command", required=True)
    gate_check = gate_commands.add_parser("check")
    gate_check.add_argument("source", type=Path)
    gate_check.add_argument("request", type=Path)

    scope = groups.add_parser("scope")
    scope_commands = scope.add_subparsers(dest="command", required=True)
    scope_check = scope_commands.add_parser("check")
    scope_check.add_argument("contract", type=Path)

    git = groups.add_parser("git")
    git_commands = git.add_subparsers(dest="command", required=True)
    for command in ("prepare", "push"):
        child = git_commands.add_parser(command)
        child.add_argument("run_dir", type=Path)
        child.add_argument("repository_id")
    git_commit = git_commands.add_parser("commit")
    git_commit.add_argument("run_dir", type=Path)
    git_commit.add_argument("repository_id")
    git_commit.add_argument("--message", required=True)
    git_commit.add_argument("--path", action="append", required=True)
    git_pr = git_commands.add_parser("pr")
    git_pr.add_argument("run_dir", type=Path)
    git_pr.add_argument("repository_id")
    git_pr.add_argument("--title", required=True)
    git_pr.add_argument("--body-file", type=Path, required=True)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if (args.group, args.command) == ("project", "init"):
            config = initialize_project(
                args.root,
                update_gitignore=args.update_gitignore,
            )
            _json(config.model_dump(mode="json"))
        elif (args.group, args.command) == ("contract", "validate"):
            contract = load_contract(args.path)
            _json({"valid": True, "loop_id": contract.loop_id})
        elif (args.group, args.command) == ("schema", "export"):
            _json({"schemas": [str(path) for path in export_schemas(args.output)]})
        elif (args.group, args.command) == ("run", "create"):
            store = RunStore.create(args.project, load_contract(args.contract))
            _json({"run_dir": str(store.run_dir)})
        elif (args.group, args.command) == ("run", "status"):
            _json(RunStore.open(args.run_dir).summary())
        elif (args.group, args.command) == ("run", "events"):
            _json(
                [
                    event.model_dump(mode="json")
                    for event in RunStore.open(args.run_dir).events()
                ]
            )
        elif (args.group, args.command) == ("run", "transition"):
            state = RunStore.open(args.run_dir).record_transition(
                actor=args.actor,
                target=LoopStatus(args.target),
                reason=args.reason,
            )
            _json(state.model_dump(mode="json"))
        elif (args.group, args.command) == ("run", "complete"):
            state = RunStore.open(args.run_dir).complete(
                actor=args.actor,
                reason=args.reason,
            )
            _json(state.model_dump(mode="json"))
        elif (args.group, args.command) == ("run", "intent"):
            action_id = RunStore.open(args.run_dir).record_intent(
                actor=args.actor,
                summary=args.summary,
                payload=json.loads(args.payload_json),
            )
            _json({"action_id": action_id})
        elif (args.group, args.command) == ("run", "result"):
            event = RunStore.open(args.run_dir).record_result(
                action_id=args.action_id,
                actor=args.actor,
                summary=args.summary,
                payload=json.loads(args.payload_json),
                made_progress=(
                    None if args.progress == "unknown" else args.progress == "yes"
                ),
                same_strategy=(
                    None
                    if args.same_strategy == "unknown"
                    else args.same_strategy == "yes"
                ),
            )
            _json(event.model_dump(mode="json"))
        elif (args.group, args.command) == ("run", "approval"):
            event = RunStore.open(args.run_dir).record_approval(
                actor=args.actor,
                gate=args.gate,
                approved=args.decision == "approve",
                summary=args.summary,
            )
            _json(event.model_dump(mode="json"))
        elif (args.group, args.command) == ("run", "checker"):
            event = RunStore.open(args.run_dir).record_checker(
                actor=args.actor,
                verdict=CheckerVerdict(args.verdict),
                findings=json.loads(args.findings_json),
            )
            _json(event.model_dump(mode="json"))
        elif (args.group, args.command) == ("run", "revise"):
            state = RunStore.open(args.run_dir).replace_contract(
                load_contract(args.contract),
                actor=args.actor,
                summary=args.summary,
            )
            _json(state.model_dump(mode="json"))
        elif (args.group, args.command) == ("evidence", "run"):
            store = RunStore.open(args.run_dir)
            record = ValidationRunner(load_contract(store.contract_path), store).run(
                args.command_id
            )
            _json(record.model_dump(mode="json"))
        elif (args.group, args.command) == ("budget", "check"):
            store = RunStore.open(args.run_dir)
            result = budget_status(
                load_contract(store.contract_path),
                store.load_state(),
            )
            _json(result.model_dump(mode="json"))
            if result.condition is BudgetCondition.EXHAUSTED:
                return 4
            if result.condition is BudgetCondition.DIAGNOSIS_REQUIRED:
                return 5
            return 0
        elif (args.group, args.command) == ("completion", "evaluate"):
            context = CompletionContext.model_validate_json(
                args.context.read_text(encoding="utf-8")
            )
            result = DoneEvaluator(load_contract(args.contract)).evaluate(context)
            _json(result.model_dump(mode="json"))
            return 0 if result.done else 3
        elif (args.group, args.command) == ("gate", "check"):
            request = ActionRequest.model_validate_json(
                args.request.read_text(encoding="utf-8")
            )
            if args.source.is_dir():
                store = RunStore.open(args.source)
                policy = GatePolicy(
                    load_contract(store.contract_path),
                    authorization=store.current_contract_authorization(),
                )
            else:
                policy = GatePolicy(load_contract(args.source))
            decision = policy.evaluate(request)
            output = decision.model_dump(mode="json")
            if (
                decision.outcome is GateOutcome.PAUSE
                and decision.required_gate is GateRequirement.DANGEROUS_ACTION
            ):
                output["confirmation"] = render_confirmation(request, decision)
            _json(output)
        elif (args.group, args.command) == ("scope", "check"):
            result = evaluate_scope(load_contract(args.contract))
            _json(result.model_dump(mode="json"))
            return 0 if result.valid else 6
        elif args.group == "git":
            store = RunStore.open(args.run_dir)
            automation = GitAutomation(
                load_contract(store.contract_path),
                args.repository_id,
            )
            if args.command == "prepare":
                _json({"worktree": str(automation.prepare_worktree())})
            elif args.command == "commit":
                _json({"commit": automation.commit(args.path, args.message)})
            elif args.command == "push":
                automation.push()
                _json({"pushed": True})
            elif args.command == "pr":
                _json(
                    {
                        "url": automation.create_pr(
                            args.title,
                            args.body_file.read_text(encoding="utf-8"),
                        )
                    }
                )
            else:
                raise AssertionError("unreachable Git command")
        else:
            raise AssertionError("unreachable command")
    # The CLI boundary converts all failures into sanitized, machine-readable output.
    except Exception as error:  # noqa: BLE001
        if isinstance(error, ValidationError):
            message = "; ".join(
                f"{'.'.join(str(part) for part in item['loc'])}: {item['msg']}"
                for item in error.errors(include_url=False, include_input=False)
            )
        else:
            message = str(redact(str(error)))
        _json(
            {"error": type(error).__name__, "message": message},
            stream=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
