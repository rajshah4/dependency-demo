# Cloud UI Usage

Use this reference when launching dependency propagation analysis from the OpenHands Cloud UI.

## Recommended operator flow

1. Open the controller repository conversation in OpenHands Cloud.
2. Confirm GitHub access is available for every candidate repo.
3. Confirm an OpenHands Cloud API key is available if the workflow will fan out using the V1 API.
4. Ask the conversation to use the dependency propagation analysis skill.
5. Start with dry-run analysis before live fan-out.

## Prompt shape

Use a short prompt that supplies only run-specific details.

```text
Use the dependency propagation analysis skill.

Upstream package: @org/shared-lib
Source repo: org/shared-lib
Change: 1.0.0 -> 1.1.0
Compatibility note: LegacyClient -> ApiClient
Candidate repos:
- org/service-a
- org/service-b
- org/service-c

First perform analysis and identify only the direct dependents.
Then prepare a minimal downstream execution plan per in-scope repo.
If requested, run the orchestrator in dry-run first and summarize the expected PRs.
```

## Expected operator-friendly summary

A good Cloud UI result should summarize:

- direct dependents selected
- control repos excluded
- evidence used for each inclusion or exclusion
- files expected to change in each target repo
- validation command per repo
- whether the workflow is ready for dry-run or live execution

## Live-run caution

If the run will create real PRs, prefer:

- a unique branch naming suffix
- a unique PR title suffix for repeated demos
- stopping on branch or PR collisions instead of force-updating existing demo branches
