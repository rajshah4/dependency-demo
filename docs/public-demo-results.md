# Validated Public Demo Results

This document records a successful end-to-end live run against public GitHub repositories under `rajshah4`.

## Public repositories

- Shared library: https://github.com/rajshah4/demo-shared-lib
- Direct dependent A: https://github.com/rajshah4/demo-service-a
- Direct dependent B: https://github.com/rajshah4/demo-service-b
- Unrelated control repo: https://github.com/rajshah4/demo-service-c

## Upstream history

The shared library repository was seeded with two commits and two tags:

- `v1.0.0` — exports `LegacyClient`
- `v1.1.0` — exports `ApiClient`

## Validated config

Use:

- `examples/rajshah4-public-demo-config.json`

This checked-in config defaults to `dry_run: true` for safety. Flip it to `false` when you want to reproduce the live run.

## OpenHands Cloud conversations

- Service A conversation: https://app.all-hands.dev/conversations/61452765296d4812b9c633c0fb5a3d39
- Service B conversation: https://app.all-hands.dev/conversations/f93836345b4b48a880fc7dfc78a4c9ec

Observed final status from the orchestrator report:

- `rajshah4/demo-service-a` — `execution_status=finished`
- `rajshah4/demo-service-b` — `execution_status=finished`

## Pull requests created

- Service A PR: https://github.com/rajshah4/demo-service-a/pull/1
- Service B PR: https://github.com/rajshah4/demo-service-b/pull/1

Confirmed:

- one PR per direct dependent repo
- no PR for `rajshah4/demo-service-c`

## PR diff summary

### `rajshah4/demo-service-a`

Changed files:

- `package.json`
- `package-lock.json`
- `src/client.ts`

Change summary:

- dependency updated from `1.0.0` to `1.1.0`
- `LegacyClient` renamed to `ApiClient`
- validation command recorded as `npm test`

### `rajshah4/demo-service-b`

Changed files:

- `package.json`
- `package-lock.json`
- `src/service.ts`

Change summary:

- dependency updated from `1.0.0` to `1.1.0`
- `LegacyClient` renamed to `ApiClient`
- validation command recorded as `npm test`

## Control repo result

`rajshah4/demo-service-c` received no pull request, confirming that the workflow targeted only direct dependents.

## Reproduction notes

1. Start with `examples/rajshah4-public-demo-config.json`.
2. Keep `dry_run: true` for a safe rehearsal.
3. When ready, set `dry_run: false` and run:

```bash
python -m dep_propagator start examples/rajshah4-public-demo-config.json --report conversation-report.json
python -m dep_propagator status conversation-report.json
```

## Important caution

Because the PRs above already exist, rerunning the live flow unchanged may create branch or PR collisions. For a fresh live rerun, either:

- close and clean up the existing demo PR branches, or
- copy the public repos to a fresh set of repo names and regenerate the config
