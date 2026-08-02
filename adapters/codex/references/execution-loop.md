# Execution loop playbook

Read this playbook after the current bound contract approval when designing, planning,
executing, verifying, checking, deciding, revising or completing a Run.

## Autonomous decision loop

After the current bound contract approval, advance through
`designing -> planning -> executing -> verifying -> checking -> deciding` without a
routine confirmation between stages. Each iteration selects one unmet acceptance criterion,
chooses the next smallest action inside the approved scope, observes real feedback, records
fresh evidence, applies the required Checker verdict and then makes exactly one state decision.
The action must also be contained by `execution_plan`; allowed paths alone do not expand it.

| Observed facts | Required decision |
|---|---|
| Fresh evidence and material progress | Continue to the next smallest action or the next unmet criterion. |
| A test or command failure with new information | Return to diagnosis, form a new causal hypothesis and revise the plan before another mutation. |
| Two consecutive iterations without new evidence or material progress | Return to diagnosis; do not continue the same implementation strategy. |
| Checker `REVISE` | Return to planning or executing, apply the findings and consume one Checker revision. |
| Checker `BLOCK` | Stop mutations; enter BLOCKED only for missing external authority or state, otherwise return to diagnosis with the exact finding. |
| Checker `ACCEPT` plus every current DONE fact | Build the strict CompletionContext and run authoritative completion evaluation. |
| The authoritative budget check reports exhaustion | Transition to BUDGET_EXHAUSTED without expanding the approved budget. |

The same failed strategy may be attempted at most once. Difficulty is never evidence of
BLOCKED or DONE, and natural-language confidence never substitutes for command results.

## Maker action protocol

For each unmet acceptance criterion:

1. Run `loop-engine budget check "<run-dir>"`. An exhausted result transitions
   to BUDGET_EXHAUSTED. A diagnosis-required result returns to planning and requires
   a new causal hypothesis before another action. Otherwise choose one smallest
   verifiable increment.
2. Serialize the exact ActionRequest under `<run-dir>/inputs/` and run
   `loop-engine gate check "<run-dir>" "<request-json>"`.
   Handle the returned decision exactly:
   - `allow`: continue without another human confirmation.
   - `pause` with `required_gate=contract_revision`: add the new exact target,
     permission and full risk disclosure to the next contract version, then request
     one revised complete-summary approval.
   - `pause` with `required_gate=contract_approval`: the current bound approval is
     missing or stale; return to the complete contract approval instead of showing an
     isolated risk prompt.
   - `deny`: record the rejection and never execute the operation.
3. Immediately before every approved external state change, run
   `loop-engine run intent "<run-dir>" "<request-json>" --actor maker
   --summary "<planned-mutation>"`. Core rechecks current approval, state, budget and Gate in
   this operation and persists the exact checked `ActionRequest`; the earlier Gate check is only
   a preview and cannot authorize a different request.
4. Make the change without touching unrelated user work.
5. Run `loop-engine run result` immediately after observing real state,
   marking whether new evidence/progress occurred and whether the strategy was reused.
   Generic `loop-engine run result` cannot report Git or validator evidence. Use it only to
   close the matching ordinary action intent. Git intent/results come only from the
   `loop-engine git` subcommands, and validator intent/results come only from
   `loop-engine evidence run`; these dedicated paths bind their observed results to the
   checked request. Completion derives delivery and evidence only from those authoritative
   current-contract result events, never from generic JSON or prose.
6. Run `loop-engine evidence run "<run-dir>" "<VAL-ID>"`.
   Core executes validation in a disposable Git snapshot under
   `.loop-engine/cache/`, closes timeout/start failures as failed results and rejects any
   concurrent mutation of the source repository.
7. Do not repeat the same failed strategy more than once.
8. For multiple repositories, follow the contract's acyclic `depends_on` order,
   create one branch/PR per repository, and list prerequisite PRs in each dependent PR.

## Engineering and persistence

- Apply KISS and YAGNI to the accepted behavior; use DRY and SOLID only where the
  current scope contains material repetition or a clear responsibility boundary.
- Preserve unrelated user changes and follow the target repository's existing style.
- Treat `events.jsonl` as append-only. Never rewrite approvals, intents, results,
  evidence references or Checker findings to make a run appear successful.
- Persist only redacted operational evidence; never persist secrets or model reasoning.

## Checker protocol

- Low risk: Maker self-checks against the contract and raw evidence.
- Medium/high risk: dispatch a fresh independent Checker context.
- Checker reads the contract, actual diff and raw evidence, then returns only
  `ACCEPT`, `REVISE` or `BLOCK` with findings and evidence.
- Use the actual identifier returned by the host dispatch. Never invent or reuse a Checker ID.
- Record the verdict and findings with `loop-engine run checker "<run-dir>"
  --checker-id "<host-checker-id>" --verdict "<accept|revise|block>"
  --findings-json "<json-array>"`.
- Core derives and records `contract_sha256`, `source_fingerprints`, `evidence_digests` and
  `reviewed_through_sequence`; the Maker cannot supply those facts. Any later intent or result
  invalidates the attestation. A changed contract, source fingerprint or evidence digest also
  requires a new independent review.
- The host-provided ID is an Adapter trust assertion rather than cryptographic identity proof.
  If dispatch identity cannot be established from real host state, treat the independent Checker
  as unavailable.
- Checker never edits production code. `REVISE` returns to Maker and consumes a revision.
- If an independent Checker is unavailable, medium/high work cannot become DONE.

## Hard pause and stop boundaries

Pause automatic execution only when one of these facts is true:

- A complete contract revision is required for changed objective, scope, acceptance,
  repository/Git target, dangerous permission, budget or newly discovered risk.
- The current bound approval is missing, stale or mismatched against the current protocol,
  contract version, canonical hash or complete risk IDs.
- The Goal/Run binding is missing, ambiguous, stale or unrelated.
- A pending intent cannot be reconciled against real local, Git, native Goal or external state.
- A platform or external authentication hard gate requires human-only action.
- The necessary authority or input is unavailable and cannot be derived inside the contract.
- A required independent Checker is unavailable for medium/high-risk work.
- The user cancels or explicitly pauses the bound task.
- An authoritative budget or terminal state is reached.

Risk level alone is not a pause boundary. Ordinary authorized work, test failures with usable
feedback and Checker revisions are handled inside the loop without asking the user.
Permanent-deny operations remain denied and must never be converted into confirmation or
contract-revision prompts.

## Completion

Do not claim DONE from prose. Build the strict CompletionContext at
`<run-dir>/inputs/completion-context.json` and run
`loop-engine completion evaluate "<contract-path>" "<context-json>"`.
Populate it only from the current code fingerprint, fresh validator evidence, the current scope result,
required Checker `ACCEPT`, current contract authorization and no unresolved intent.
Never use prose, stale evidence or Maker confidence as completion evidence.
Only a zero exit code permits calling `loop-engine run complete "<run-dir>"
--actor maker --reason "all DONE requirements passed"`. That authoritative command
re-derives evidence records and hashes, current fingerprints, scope, Git delivery,
approvals, pending intents and Checker status before transitioning. Verify every
acceptance criterion has fresh evidence and approved Git/PR delivery completed. Use the
`loop-engine git` subcommands only after a matching gate decision and emit the
final report from `templates/final-report.md`.

Set `scope_valid` in CompletionContext only from
`loop-engine scope check "<contract-path>"`; do not infer it from Maker prose.
Derive `checker_verdict`, `gates_clear` and
`contract_current` from `loop-engine run status "<run-dir>"`: unresolved
intent IDs, a paused state, or a required contract gate without an approval event make
`gates_clear=false`, contract versions must match, and a Checker verdict counts only when
`checker_current=true`.
Populate evidence only from validator result events returned by
`loop-engine run events "<run-dir>"`.

The permanent deny list is force-push, history rewriting, reset --hard, automatic merge and automatic deployment.
不得自动合并或部署。不得强推、改写历史、执行 `git reset --hard`、泄露秘密，
或通过删除/弱化测试制造成功。
