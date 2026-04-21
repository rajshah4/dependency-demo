# Cloud Demo Prompts

Use this document as the copy/paste prompt pack for running the dependency propagation demo from the OpenHands Cloud UI.

## When to use this file

Use these prompts when:

- the Cloud UI conversation is opened on `rajshah4/dependency-demo` or an equivalent controller repo
- the conversation has GitHub access to the demo repos
- the environment includes `OPENHANDS_CLOUD_API_KEY` or `OPENHANDS_API_KEY`

For the validated public demo set, use:

- config: `examples/rajshah4-public-demo-config.json`
- public results reference: `docs/public-demo-results.md`

## Operator prerequisites

Before pasting any prompt, confirm:

1. the conversation is opened on the controller repo
2. the repo can read `examples/rajshah4-public-demo-config.json`
3. the Cloud environment can access:
   - `rajshah4/demo-shared-lib`
   - `rajshah4/demo-service-a`
   - `rajshah4/demo-service-b`
   - `rajshah4/demo-service-c`
4. an OpenHands Cloud API key is available in the environment

## Prompt 1: Skill-based analysis only

Use this when showing the reusable analysis layer before any live execution.

```text
Use the dependency propagation analysis skill from `.agents/skills/dependency-propagation-analysis/`.

Upstream package: @rajshah4/demo-shared-lib
Source repo: rajshah4/demo-shared-lib
Change: 1.0.0 -> 1.1.0
Compatibility note: LegacyClient -> ApiClient
Candidate repos:
- rajshah4/demo-service-a
- rajshah4/demo-service-b
- rajshah4/demo-service-c

First identify only the direct dependents.
Then produce a minimal downstream execution plan for each in-scope repo.
Explicitly explain why `rajshah4/demo-service-c` is out of scope.
Do not create PRs yet.
```

Expected outcome:

- A and B identified as direct dependents
- C excluded
- a minimal plan per target repo

## Prompt 2: Dry-run orchestrator prompt

Use this to demonstrate the real controller flow without mutating anything.

```text
You are in the `dependency-demo` repository.

Use `examples/rajshah4-public-demo-config.json` as the starting point.

Before starting:
1. Confirm that the config file exists.
2. Confirm that an OpenHands Cloud API key is available from the environment.
3. If either prerequisite is missing, stop and tell me exactly what is missing.

Then do this:
1. Run a dry-run using:
   `python -m dep_propagator start examples/rajshah4-public-demo-config.json --report /tmp/rajshah4-ui-dry-run-report.json`
2. Summarize:
   - which repos are targeted
   - why only the direct dependents are targeted
   - why `rajshah4/demo-service-c` is excluded
3. Do not create any PRs or modify the checked-in config.
4. Only write temporary files under `/tmp`.
```

Expected outcome:

- prompts rendered for service A and service B
- no conversation IDs yet because dry-run remains local to the controller flow
- clear explanation of why service C is untouched

## Prompt 3: Live run with unique branch and PR suffixes

Use this for the real fan-out demo. It avoids collisions with older rehearsals.

```text
You are in the `dependency-demo` repository.

I want you to use this repo’s orchestrator to propagate the validated public demo dependency update using OpenHands Cloud V1 conversations as the execution primitive.

Important constraints:
- Use `examples/rajshah4-public-demo-config.json` as the starting point.
- Do not make permanent changes to this repository.
- Only write temporary files under `/tmp`.
- Keep the run focused on the validated public demo repos under `rajshah4`.
- Do not modify unrelated files.

Before starting:
1. Confirm that `examples/rajshah4-public-demo-config.json` exists.
2. Confirm that an OpenHands Cloud API key is available from the environment.
3. If either prerequisite is missing, stop and tell me exactly what is missing.

Then do this:
1. Run a dry-run first using:
   `python -m dep_propagator start examples/rajshah4-public-demo-config.json --report /tmp/rajshah4-ui-dry-run-report.json`
2. Summarize the dry-run result.
3. Create a temporary live config copy at:
   `/tmp/rajshah4-public-demo-config-live.json`
4. In that temporary config:
   - set `dry_run` to `false`
   - update `branch_template` to include a unique UTC timestamp suffix so the run does not collide with prior demo branches
   - update `pr_title_template` to include the same timestamp suffix so the rerun is easy to identify
5. Run the live propagation using that temporary config and write the report to:
   `/tmp/rajshah4-ui-live-report.json`
6. Poll status until all started conversations reach a terminal state, or until 15 minutes have passed:
   `python -m dep_propagator status /tmp/rajshah4-ui-live-report.json`
7. Give me a final summary with:
   - targeted repos
   - conversation URLs
   - final status per repo
   - PR URLs if you can determine them
   - whether exactly one PR was created per direct dependent repo
   - whether `rajshah4/demo-service-c` remained untouched
   - any blockers or failures
8. If a rerun is blocked by an existing branch or PR collision, stop and explain the exact collision instead of making risky changes.
9. Do not commit or push changes to this `dependency-demo` repo itself.
```

Expected outcome:

- one downstream conversation for service A
- one downstream conversation for service B
- one PR per direct dependent repo
- no PR for service C

## Prompt 4: Rerun-safe troubleshooting prompt

Use this when there are collisions or access issues and the operator wants a controlled diagnosis.

```text
You are in the `dependency-demo` repository.

Diagnose why the validated public dependency propagation demo cannot run cleanly right now.

Use `examples/rajshah4-public-demo-config.json` as the reference config, but do not modify it.
Only write temporary files under `/tmp`.

Please check, in order:
1. whether the config file exists
2. whether an OpenHands Cloud API key is available
3. whether the target repos are still accessible in OpenHands Cloud
4. whether existing PRs or branch names are likely to collide with a new live run

Then summarize:
- what is healthy
- what is blocked
- the safest next step

If a live run would be risky, do not start it.
```

## Prompt 5: Short demo-day prompt

Use this when time is short and the operator wants a compact version.

```text
Use `examples/rajshah4-public-demo-config.json` as the starting point.
First run a dry-run and confirm only the direct dependents are targeted.
Then create a temporary live config under `/tmp` with `dry_run=false` and unique timestamp-based branch and PR title suffixes.
Run the propagation, poll status to completion, and summarize the conversation URLs, PR URLs, and whether `rajshah4/demo-service-c` remained untouched.
Do not modify the checked-in config or commit anything in this repo.
```

## Suggested spoken framing during the demo

Use language like:

- "The Cloud UI conversation is acting as the controller."
- "It reads a provided dependency graph instead of inferring one at runtime."
- "It fans the work out into one downstream conversation per direct dependent repo."
- "Each downstream conversation should produce one focused PR."

## Important caution for the validated public demo

The public `rajshah4/*` repos already have successful demo PRs recorded in `docs/public-demo-results.md`.

For a fresh live rerun, either:

- use unique branch and PR title suffixes, or
- create a fresh set of demo repos, or
- clean up old demo branches and PRs first
