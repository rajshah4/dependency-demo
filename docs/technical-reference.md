# Technical Reference

This document keeps the lower-level operator and implementation detail out of the main README.

## Core API model

The workflow uses OpenHands Cloud V1 conversations as the execution primitive:

- `POST /api/v1/app-conversations` starts a conversation for a target repo
- `GET /api/v1/app-conversations/start-tasks?ids=...` resolves async startup
- `GET /api/v1/app-conversations?ids=...` refreshes later status
- one target repository maps to one OpenHands conversation
- one OpenHands conversation is expected to produce one downstream PR

## Repository layout

- `dep_propagator/client.py` - minimal OpenHands Cloud V1 API client
- `dep_propagator/config.py` - config loading and workflow dataclasses
- `dep_propagator/prompts.py` - prompt template for downstream repo conversations
- `dep_propagator/workflow.py` - orchestration logic and CLI entrypoints
- `dep_propagator/demo.py` - local demo bundle generation and verification
- `examples/sample-config.json` - sample configuration
- `examples/demo-template-config.json` - reusable demo config template
- `examples/rajshah4-public-demo-config.json` - validated public demo config for the live public repo set
- `.agents/skills/dependency-propagation-analysis/SKILL.md` - reusable OpenHands skill for dependency-impact analysis
- `docs/demo-runbook.md` - reproducible demo setup and execution guide
- `docs/cloud-demo-prompts.md` - copy/paste OpenHands Cloud prompts for demo-day operation
- `docs/public-demo-results.md` - actual public repo, conversation, and PR results from a successful live run

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
| `dependency_graph` | yes | Mapping of repo to list of dependencies |
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

## Verification performed

Latest verified checks included:

- `python3 -m unittest discover -s tests -t .`
- `python3 -m dep_propagator start examples/sample-config.json --report /tmp/dep-propagator-report.json`
- `python3 -m dep_propagator status /tmp/dep-propagator-report.json`
- `python3 -m dep_propagator demo-bootstrap --owner demo-org --output /tmp/dep-demo-bundle.XXXXXX`
- `python3 -m dep_propagator demo-verify /tmp/dep-demo-bundle.XXXXXX`
- live public run against `rajshah4/demo-shared-lib`, `rajshah4/demo-service-a`, `rajshah4/demo-service-b`, and `rajshah4/demo-service-c`

See `docs/public-demo-results.md` for the actual conversation URLs and PR URLs from the successful public live run.

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
