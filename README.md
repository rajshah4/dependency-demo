# Multi-Repo Dependency Propagation Agent

This repository implements an **OpenHands Cloud V1 conversation orchestrator** for propagating a dependency update from one upstream repository to its **direct dependents only**.

Instead of editing repositories locally, the orchestrator starts one **OpenHands V1 app conversation** per downstream repository. Each conversation receives a self-contained prompt that tells OpenHands to:

- update the dependency reference
- make only the smallest compatibility fixes required
- run validation commands
- create a branch
- open a pull request

## Problem this solves

A shared library changes upstream and multiple downstream services consume it. You want one focused pull request per direct dependent repository, with clear traceability back to the upstream change.

This project handles the orchestration layer. The actual repo work happens inside OpenHands Cloud conversations.

## Core design

The workflow is intentionally built around **OpenHands Cloud V1 conversations**:

- `POST /api/v1/app-conversations` starts a conversation for a target repo
- `GET /api/v1/app-conversations/start-tasks?ids=...` resolves async startup
- `GET /api/v1/app-conversations?ids=...` refreshes later status
- one target repository maps to one OpenHands conversation
- one OpenHands conversation is expected to produce one downstream PR

This keeps the system aligned with your requirement that the solution should use **OpenHands Cloud** and **V1 conversations** as the execution model.

## What this project does

Given:

- `source_repo`
- `dependency_graph`
- `target_repos`
- upstream change details
- per-repo hints
- per-repo validation commands

…the orchestrator will:

1. identify the direct dependents
2. validate that `target_repos` are actually direct dependents
3. render a self-contained prompt for each target repo
4. start one V1 app conversation per repo using `selected_repository`
5. poll the start-task until the conversation is ready
6. write a report containing conversation IDs, URLs, status, and prompts
7. optionally refresh those statuses later from the saved report

The actual code changes, validation, branch creation, and PR creation happen **inside OpenHands**.

## What this project does not do

- It does **not** recursively traverse transitive dependents.
- It does **not** edit downstream repositories locally.
- It does **not** create PRs itself with git commands.
- It does **not** infer the dependency graph for you.

## Repository layout

- `dep_propagator/client.py` — minimal OpenHands Cloud V1 API client
- `dep_propagator/config.py` — config loading and workflow dataclasses
- `dep_propagator/prompts.py` — prompt template for downstream repo conversations
- `dep_propagator/workflow.py` — orchestration logic and CLI entrypoints
- `examples/sample-config.json` — sample configuration
- `.agents/skills/dependency-propagation-analysis/SKILL.md` — reusable OpenHands skill for dependency-impact analysis and minimal downstream planning
- `examples/demo-template-config.json` — reusable demo config template
- `examples/rajshah4-public-demo-config.json` — validated public demo config for the live public repo set
- `docs/demo-runbook.md` — reproducible demo setup and execution guide
- `docs/demo-repo-blueprints.md` — exact downstream and upstream repo contents for the demo
- `docs/demo-bootstrap-commands.md` — copy-paste setup commands for the demo repos
- `docs/demo-script.md` — concise operator script for rehearsal and presentation
- `docs/cloud-demo-prompts.md` — copy/paste OpenHands Cloud prompts for analysis, dry-run, live-run, and troubleshooting
- `docs/demo-operator-log.md` — rehearsal and live-run handoff log
- `docs/public-demo-results.md` — actual public repo, conversation, and PR results from a successful live run
- `tests/test_workflow.py` — unit tests
- `AGENTS.md` — repository memory for future sessions

## Requirements

- Python 3.11+
- `OPENHANDS_CLOUD_API_KEY` or `OPENHANDS_API_KEY`
- target repositories available in OpenHands Cloud
- OpenHands Cloud repository access sufficient for branch creation and PR creation

For local CLI usage, the client now checks exported environment variables first and then falls back to a local `.env` file in the current working directory or one of its parents.

## Reproducible demo kit

If you want another operator to reproduce the demo, use these files:

- `docs/demo-runbook.md` — full setup and execution guide
- `docs/demo-repo-blueprints.md` — exact repo contents to create for the demo
- `docs/demo-bootstrap-commands.md` — copy-paste setup commands for the demo repos
- `docs/demo-script.md` — operator script for rehearsal and presentation
- `docs/cloud-demo-prompts.md` — exact Cloud UI prompts to paste on demo day
- `docs/demo-operator-log.md` — running handoff log for rehearsals and live demos
- `docs/public-demo-results.md` — successful public run with real conversation and PR URLs
- `examples/demo-template-config.json` — placeholder config for your real demo repos
- `examples/rajshah4-public-demo-config.json` — validated config for the public `rajshah4/*` demo repos

The recommended approach is to fork or copy small public starter repos into a GitHub org that OpenHands Cloud can access, then wire them into a simple dependency graph for the demo.

For repeatable Cloud UI usage, the repository now also includes a reusable skill at `.agents/skills/dependency-propagation-analysis/`. That skill captures the dependency-analysis workflow so the operator only has to provide the upstream change and the relevant repo set.

You can also generate a complete local demo bundle with:

```bash
python -m dep_propagator demo-bootstrap --owner yourorg --output demo-bundle
python -m dep_propagator demo-verify demo-bundle
```

## Quick start

### 1. Prepare your config

Start from the sample file:

```bash
cp examples/sample-config.json my-config.json
```

Update:

- upstream repository name
- dependency name
- dependency graph
- direct target repos
- upstream change summary and version
- per-repo repository slugs and validation commands

### 2. Run a dry-run first

The sample config already uses `dry_run: true`.

```bash
python -m dep_propagator start my-config.json --report conversation-report.json
```

In dry-run mode the orchestrator will:

- resolve direct dependents
- render prompts
- generate a report
- skip real OpenHands API calls

This is the safest way to validate configuration before launching live conversations.

### 3. Launch real OpenHands conversations

Provide credentials either by exporting:

```bash
export OPENHANDS_CLOUD_API_KEY="..."
```

or by placing the same variable in a local `.env` file at the repo root.

Then set `dry_run` to `false` in your config and run:

```bash
python -m dep_propagator start my-config.json --report conversation-report.json
```

### 4. Refresh conversation status later

```bash
python -m dep_propagator status conversation-report.json
```

## CLI reference

### Start conversations

```bash
python -m dep_propagator start <config> --report <output-file>
```

Behavior:

- loads config
- resolves direct dependents
- starts one OpenHands V1 conversation per repo
- writes a JSON report

### Refresh statuses

```bash
python -m dep_propagator status <report-file>
```

Behavior:

- reads an existing report
- fetches updated conversation state for any run that has an `app_conversation_id`
- rewrites the same report with refreshed execution and sandbox status

### Generate a local demo bundle

```bash
python -m dep_propagator demo-bootstrap --owner <github-owner> --output <bundle-dir>
```

Behavior:

- creates four local demo repositories under `<bundle-dir>/repos`
- writes `<bundle-dir>/demo-config.json`
- defaults that config to `dry_run=true`

### Verify a local demo bundle

```bash
python -m dep_propagator demo-verify <bundle-dir>
```

Behavior:

- runs local Node-based checks for each generated repo
- confirms direct-dependent resolution
- runs a dry-run workflow check using the generated config

## Configuration reference

See `examples/sample-config.json` for a full example.

### Top-level fields

| Field | Required | Description |
|---|---|---|
| `source_repo` | yes | Upstream repository identifier used in the dependency graph |
| `dependency_name` | yes | Dependency identifier the downstream repos reference |
| `dependency_graph` | yes | Mapping of repo → list of dependencies |
| `target_repos` | no | Explicit subset of direct dependents to process |
| `upstream_change` | yes | Summary, old/new version, usage notes |
| `repositories` | yes | Per-repository execution metadata |
| `base_url` | no | OpenHands Cloud base URL, default `https://app.all-hands.dev` |
| `title_template` | no | Conversation title template |
| `branch_template` | no | Suggested branch name template included in prompts |
| `pr_title_template` | no | PR title template included in prompts |
| `dry_run` | no | If true, render prompts and reports without calling OpenHands |
| `start_timeout_s` | no | Max wait time for async conversation startup |

### `upstream_change`

| Field | Required | Description |
|---|---|---|
| `summary` | yes | Human-readable upstream change summary |
| `old_version` | no | Prior version, if relevant |
| `new_version` | yes | New version to propagate |
| `usage_notes` | no | Extra migration notes passed into each repo prompt |

### Per-repository fields

| Field | Required | Description |
|---|---|---|
| `selected_repository` | yes | Repository slug passed to `selected_repository` in V1 |
| `selected_branch` | no | Base branch for the conversation, default `main` |
| `working_directory` | no | Reserved for future prompt enrichment |
| `dependency_hints` | no | Likely files or locations containing dependency references |
| `update_instructions` | no | Repo-specific migration instructions |
| `validation_commands` | no | Commands OpenHands should run inside the repo |
| `extra_context` | no | Any extra repo-specific information |
| `pr_base_branch` | no | Branch the PR should target; defaults to `selected_branch` |

## Prompt behavior

For each downstream repository, the orchestrator generates a self-contained prompt that tells OpenHands to:

1. inspect the selected repository
2. create the suggested branch
3. update the dependency reference
4. make only minimal compatibility fixes
5. run validation commands
6. commit relevant files only
7. open a PR targeting the configured base branch
8. include a clear PR description
9. return branch name, PR URL, changed files, validation summary, and blockers

Because each prompt is self-contained, every conversation can run independently with a fresh context window.

## Report format

The generated report includes, per repo:

- `repo_name`
- `selected_repository`
- `selected_branch`
- `branch_name`
- `title`
- `prompt`
- `start_task_id`
- `app_conversation_id`
- `conversation_url`
- `start_status`
- `execution_status`
- `sandbox_status`
- `status`
- `message`

Example dry-run report shape:

```json
[
  {
    "repo_name": "acme/service-a",
    "status": "dry_run",
    "app_conversation_id": null,
    "conversation_url": null
  }
]
```

## Verification performed

I verified the implementation locally in two ways.

### 1. Unit tests

Ran:

```bash
python3 -m unittest discover -s tests -t .
```

Verified:

- direct dependent resolution
- prompt rendering
- async start-task normalization
- dry-run startup without requiring an API key
- status refresh with a mocked conversation client
- dry-run status refresh without requiring an API key
- `.env`-based API key loading for CLI runs

### 2. End-to-end dry-run CLI check

Ran:

```bash
python3 -m dep_propagator start examples/sample-config.json --report /tmp/dep-propagator-report.json
python3 -m dep_propagator status /tmp/dep-propagator-report.json
```

Verified:

- CLI start command executes successfully in `dry_run`
- report file is created
- both target repos are included
- generated prompts are present
- status refresh works on a dry-run report without needing cloud credentials

### 3. Local demo bundle generation and verification

Ran:

```bash
python3 -m dep_propagator demo-bootstrap --owner demo-org --output /tmp/dep-demo-bundle.XXXXXX
python3 -m dep_propagator demo-verify /tmp/dep-demo-bundle.XXXXXX
```

Verified:

- the CLI can generate a full four-repo demo bundle
- the generated config resolves only the direct dependents
- local Node-based checks pass for all generated repos
- the generated config passes a dry-run workflow check

### 4. Public live run against real GitHub repos

Ran against the public repositories under `rajshah4`:

```bash
python3 -m dep_propagator start /tmp/rajshah4-demo-bundle/demo-config-live.json --report /tmp/rajshah4-demo-bundle/conversation-report-live.json
python3 -m dep_propagator status /tmp/rajshah4-demo-bundle/conversation-report-live.json
```

Verified:

- OpenHands Cloud started one conversation per direct dependent repo
- both conversations reached `execution_status=finished`
- one PR was created for `rajshah4/demo-service-a`
- one PR was created for `rajshah4/demo-service-b`
- no PR was created for `rajshah4/demo-service-c`
- each PR contained only the dependency update plus the required `LegacyClient -> ApiClient` compatibility fix

See `docs/public-demo-results.md` for the actual repo URLs, conversation URLs, and PR URLs.

### What is still environment-dependent

Live execution still depends on:

- a valid OpenHands Cloud API key
- repositories that are accessible in OpenHands Cloud
- permissions to create branches and pull requests in those repositories

This repository now includes a fully verified public example, but new repo sets still require the same environment prerequisites.

## Live execution notes

When `dry_run` is set to `false`:

- the orchestrator will call the OpenHands V1 API
- `POST /api/v1/app-conversations` may return either an `app_conversation_id` immediately or an async start-task
- the orchestrator will poll the start-task until it reaches a terminal startup state
- the resulting `app_conversation_id` is stored in the report
- the conversation URL is saved as `{base_url}/conversations/{app_conversation_id}`

## Common failure cases

### Missing API key

If `dry_run` is `false` and no key is set, startup will fail with:

- `Missing API key. Set one of: OPENHANDS_CLOUD_API_KEY, OPENHANDS_API_KEY`

### Invalid target repos

If `target_repos` contains a repo that is not a direct dependent of `source_repo`, the workflow will fail fast.

### Missing per-repo config

If a repo appears in the direct dependent set but is missing from `repositories`, that repo will be marked failed in the report.

### OpenHands repo access problems

Live runs may fail if the selected repository is not available or OpenHands lacks permission to work with it.

## Limitations

- direct dependents only
- one conversation per target repo
- no transitive propagation
- no built-in event scraping for extracting final PR URLs from conversation logs
- no batching or concurrency limit management yet
- no automatic retry policy yet

## Future improvements

Good next steps would be:

- extracting final PR URLs automatically from conversation events
- adding bounded concurrency for large target lists
- adding retry logic for transient OpenHands API failures
- adding optional event summaries per conversation
- adding an OpenHands automation wrapper for scheduled runs

## Summary

This repository now provides an OpenHands-native orchestration layer for dependency propagation:

- **OpenHands Cloud** execution model
- **V1 app conversations** as the unit of work
- **one conversation per direct dependent repo**
- **one focused downstream PR per repo**
- **clear JSON reporting for traceability**

If you want to run this live next, the main remaining step is to switch `dry_run` to `false`, provide a real config, and supply an OpenHands Cloud API key.
