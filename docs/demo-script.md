# Demo Script

Use this as a short operator script during rehearsal or a live presentation.

For copy/paste Cloud UI prompts, pair this script with `docs/cloud-demo-prompts.md`.

## Goal statement

"We updated a shared library upstream, and this tool fans that change out to direct dependents only. It uses one OpenHands Cloud V1 conversation per dependent repo, and each conversation is expected to produce one focused downstream pull request."

## Prerequisites before you start presenting

- final config file prepared
- OpenHands Cloud repo access verified
- API key available through environment or `.env`
- one successful rehearsal already completed
- conversation report path known
- PR URLs bookmarked if you plan to show final diffs

## Demo flow

### Step 1: Show the upstream change

Say:

"The upstream package changed from 1.0.0 to 1.1.0 and renamed `LegacyClient` to `ApiClient`."

Show:

- upstream repo name
- version bump
- renamed symbol

### Step 2: Show the dependency graph

Say:

"These are the repositories in scope. Only direct dependents should be updated."

Show:

- `demo-service-a -> demo-shared-lib`
- `demo-service-b -> demo-shared-lib`
- `demo-service-c -> unrelated`

Call out clearly:

- A and B should be targeted
- C should be ignored

### Step 3: Show the config

Say:

"The orchestrator is driven by an explicit config. We are not inferring the graph at runtime."

Show:

- `source_repo`
- `dependency_graph`
- `target_repos`
- `upstream_change`
- per-repo validation commands

### Step 4: Run dry-run first

Command:

```bash
python -m dep_propagator start demo-config.json --report conversation-report.json
```

If your config is still dry-run, say:

"This renders the repo-specific prompts and validates targeting without mutating anything."

Highlight in the output/report:

- only A and B are included
- one prompt per repo
- no conversation IDs in dry-run mode

### Step 5: Run live mode

Command:

```bash
python -m dep_propagator start demo-config.json --report conversation-report.json
```

Say:

"Now we are creating one OpenHands V1 conversation per direct dependent repository."

Highlight in the output/report:

- each target repo has its own result row
- each successful run gets its own `app_conversation_id`
- each successful run gets its own conversation URL

### Step 6: Refresh status

Command:

```bash
python -m dep_propagator status conversation-report.json
```

Say:

"The report gives us a simple way to track each downstream propagation attempt over time."

### Step 7: Open the conversations or PRs

Say:

"Each conversation runs independently with repo-specific instructions and should create one focused PR."

Show:

- conversation URL for service A
- conversation URL for service B
- PR URL for service A
- PR URL for service B

### Step 8: Show the PR diffs

For each PR, point out:

- dependency version updated
- import renamed from `LegacyClient` to `ApiClient`
- tests run
- no unrelated files changed

## What to emphasize verbally

- direct dependents only
- one conversation per repo
- one PR per repo
- explicit traceability through the report file
- minimal code changes only

## If something fails live

Use this language:

"The orchestration logic is still visible here: targeting, prompt generation, and per-repo execution tracking are working. The remaining issue is repository access or environment configuration, not the dependency analysis model itself."

Then fall back to:

- dry-run output
- rehearsal report
- screenshots of successful PRs from a prior run

## Suggested close

"The important pattern is not just the version bump. It is the controlled propagation workflow: explicit graph input, isolated repo execution, minimal downstream change sets, and traceable outputs for every dependent repository."
