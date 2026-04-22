# Multi-Repo Dependency Propagation Agent

This repository demonstrates an OpenHands Cloud workflow for propagating a dependency change from one shared library repo to its direct dependants only.

## What the demo does

Given:
- an upstream library change
- a provided dependency graph
- a set of downstream repositories

The workflow:
1. identifies the direct dependants
2. starts one OpenHands Cloud V1 conversation per dependant repo
3. updates the dependency reference in each repo
4. makes the smallest compatibility fix needed
5. runs validation if available
6. creates one focused PR per repo

This is intentionally single-level only. It does not recursively traverse the whole graph.

## Why this demo is useful

It shows a practical way to handle multi-repo dependency changes without putting all repos into one giant agent run.

The model is:
- 1 controller step to read the graph and select targets
- 1 conversation per direct dependant repo to make the downstream change
- 1 PR per repo for traceability and isolation

## Validated public demo

This repo includes a validated public example using:
- `rajshah4/demo-shared-lib`
- `rajshah4/demo-service-a`
- `rajshah4/demo-service-b`
- `rajshah4/demo-service-c`

Verified live outcome:
- PR created for `demo-service-a`
- PR created for `demo-service-b`
- no PR for `demo-service-c`

See:
- `docs/public-demo-results.md`

## Fastest way to understand or reproduce it

### If you just want the story
Start here:
- `docs/demo-script.md` - short talk track for the demo
- `docs/public-demo-results.md` - validated live results with conversation and PR URLs

### If you want to run it from OpenHands Cloud UI
Use:
- `docs/cloud-demo-prompts.md` - copy/paste prompts for analysis, dry-run, live-run, and troubleshooting

### If you want to reproduce the demo end-to-end
Use:
- `docs/demo-runbook.md` - setup and execution guide
- `examples/rajshah4-public-demo-config.json` - validated public demo config

## Quick reproduction path

### 1. Prerequisites
You need:
- Python 3.11+
- `OPENHANDS_CLOUD_API_KEY` or `OPENHANDS_API_KEY`
- target repos accessible in OpenHands Cloud
- repo permissions sufficient for branch and PR creation

### 2. Rehearse safely with dry-run
```bash
python -m dep_propagator start examples/rajshah4-public-demo-config.json --report conversation-report.json
python -m dep_propagator status conversation-report.json
```

### 3. Run live
For demo-day Cloud UI operation, use the prompts in:
- `docs/cloud-demo-prompts.md`

For the validated public example, remember that prior demo PRs already exist. Use the rerun-safe prompt that adds unique branch and PR title suffixes.

## Key docs
- `docs/demo-runbook.md` - full reproduction guide
- `docs/cloud-demo-prompts.md` - exact Cloud UI prompts
- `docs/demo-script.md` - concise operator script
- `docs/public-demo-results.md` - live public demo evidence
- `docs/technical-reference.md` - deeper CLI, config, and implementation reference

## Scope and limits
- direct dependants only
- one conversation per target repo
- one PR per target repo
- dependency graph is provided, not inferred
- minimal downstream changes only

## Technical note
The orchestrator itself does not edit downstream repos locally. It creates repo-scoped OpenHands Cloud conversations, and those conversations perform the actual repo updates and PR creation.
