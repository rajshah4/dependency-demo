# Reproducible Demo Runbook

This runbook explains how to reproduce the dependency propagation demo with a clean, controlled setup that another operator can run without prior context.

## Demo goal

Show that a single upstream dependency change can be propagated to its **direct dependents only** using:

- OpenHands Cloud
- V1 app conversations
- one conversation per downstream repository
- one pull request per downstream repository

## Recommended demo topology

Use four repositories in a GitHub org or account that OpenHands Cloud can access:

- `yourorg/demo-shared-lib`
- `yourorg/demo-service-a`
- `yourorg/demo-service-b`
- `yourorg/demo-service-c`

Expected dependency graph:

- `demo-service-a` depends on `demo-shared-lib`
- `demo-service-b` depends on `demo-shared-lib`
- `demo-service-c` does **not** depend on `demo-shared-lib`

This gives a clean demo story:

- A and B should receive PRs
- C should be ignored

## Recommended seed repositories

Do **not** run the demo against random production repos.

Instead, fork or copy small public starters into your own org and simplify them:

- https://github.com/nodejsapps/TypeScript-Node-Starter
- https://github.com/xddq/nodejs-typescript-modern-starter
- https://github.com/timelessco/node-ts-library-template

Forking into your own org is preferred because OpenHands needs reliable repository access for branching and PR creation.

## Suggested demo scenario

### Upstream library change

In `demo-shared-lib`:

- version bump: `1.0.0 -> 1.1.0`
- rename exported symbol: `LegacyClient -> ApiClient`

### Downstream repos

In `demo-service-a` and `demo-service-b`:

- depend on `@yourorg/demo-shared-lib`
- import `LegacyClient`
- have one small test command such as `npm test`

The expected downstream PR should contain:

- dependency version update
- minimal import/code fix
- passing validation command
- focused PR description

## OpenHands prerequisites

Before running the live demo, verify all of the following:

1. OpenHands Cloud GitHub integration is installed for the target org or repos.
2. OpenHands can access all demo repos from the Cloud UI.
3. OpenHands can open a normal manual conversation on `demo-service-a`.
4. The current environment has a valid API key available as:
   - `OPENHANDS_CLOUD_API_KEY`, or
   - `OPENHANDS_API_KEY`
5. The target repos allow branch creation and PR creation.

Relevant docs:

- Cloud UI: https://docs.openhands.dev/openhands/usage/cloud/cloud-ui
- GitHub integration: https://docs.openhands.dev/openhands/usage/cloud/github-installation
- Secrets management: https://docs.openhands.dev/openhands/usage/settings/secrets-settings

## Repo preparation checklist

For each repo:

### `demo-shared-lib`

- create package and publish/install strategy suitable for the demo
- tag or document old version `1.0.0`
- prepare upstream change `1.1.0`
- confirm changelog/message describing `LegacyClient -> ApiClient`

### `demo-service-a`

- add dependency on `@yourorg/demo-shared-lib`
- add one `LegacyClient` usage in a small source file
- add fast validation command

### `demo-service-b`

- same shape as service A, but not identical code

### `demo-service-c`

- confirm it does not depend on the shared lib
- keep it in the config graph so the filtering behavior is visible

## Config preparation

Fastest path:

```bash
python -m dep_propagator demo-bootstrap --owner yourorg --output demo-bundle
python -m dep_propagator demo-verify demo-bundle
```

This generates:

- `demo-bundle/repos/` — four local demo repositories
- `demo-bundle/demo-config.json` — ready-to-edit workflow config

You can then sync those local repos into GitHub or use them as the source of truth while creating the remote demo repos.

Start from:

- `examples/demo-template-config.json`

Use these companion docs while preparing the demo:

- `docs/demo-repo-blueprints.md` — exact repository contents to create
- `docs/demo-bootstrap-commands.md` — copy-paste commands for repo creation
- `docs/demo-script.md` — operator script for rehearsal and presentation
- `docs/cloud-demo-prompts.md` — exact Cloud UI prompts for analysis, dry-run, live-run, and rerun troubleshooting

Replace placeholder values with your real repo slugs and package name.

Validated public example:

- config: `examples/rajshah4-public-demo-config.json`
- results: `docs/public-demo-results.md`

## Dry-run procedure

Use dry-run first to validate the story before live execution.

```bash
python -m dep_propagator start examples/demo-template-config.json --report conversation-report.json
python -m dep_propagator status conversation-report.json
```

Expected dry-run outcome:

- direct dependents are resolved correctly
- prompts are generated for service A and service B
- no conversation is started
- `demo-service-c` is not processed if it is not listed as a target or inferred as a direct dependent

## Live-run procedure

1. Ensure the config has `dry_run: false`.
2. Ensure the API key is available in the environment or `.env`.
3. Run:

```bash
python -m dep_propagator start demo-config.json --report conversation-report.json
```

4. Refresh status later:

```bash
python -m dep_propagator status conversation-report.json
```

Expected live outcome:

- one V1 conversation per downstream repo
- one conversation URL per repo in the report
- each conversation opens one PR

## Verification checklist

### Before demo day

- [ ] unit tests pass
- [ ] dry-run works with final config
- [ ] OpenHands manual conversation works on `demo-service-a`
- [ ] OpenHands manual conversation works on `demo-service-b`
- [ ] both repos can create branches and PRs
- [ ] one rehearsal live run succeeds end-to-end

### During the demo

- [ ] show upstream change
- [ ] show dependency graph
- [ ] show only direct dependents are targeted
- [ ] show one conversation per repo
- [ ] show one PR per repo
- [ ] show unrelated repo is ignored

## Artifacts to capture

Save these after a successful rehearsal:

- the exact config used
- `conversation-report.json`
- conversation URLs
- PR URLs
- screenshots of each PR diff
- validation output summary

Store them in a shared handoff location so another operator can rehearse quickly.

## Known blocker discovered during testing

A live test against the placeholder sample config authenticated successfully but failed startup with:

- `Git provider authentication issue when getting remote URL`

That error occurred because the sample repo slugs were not real repos accessible to OpenHands. To avoid this, always verify repo access from the Cloud UI before running the orchestrator.

## Fallback plan

If live repo access is broken on demo day:

1. run the dry-run flow
2. show generated prompts and report output
3. show a previously recorded successful report / PR screenshots from rehearsal

## Operator handoff notes

Each time someone rehearses or runs the demo, they should add a dated note to:

- `docs/demo-operator-log.md`

Include:

- config used
- dry-run result
- live-run result
- conversation URLs
- PR URLs
- blockers encountered
