---
name: dependency-propagation-analysis
description: This skill should be used when the user asks to "analyze dependency impact", "propagate a dependency update", "find direct dependents", "prepare downstream dependency updates", "update downstream repos after an upstream change", or wants to pass a source repo/package and a relevant repo list so OpenHands can determine which repos need downstream changes.
triggers:
- dependency propagation
- dependency analysis
- direct dependents
- propagate dependency update
- downstream repos
---

# Dependency Propagation Analysis

Use this skill to analyze an upstream dependency change and turn a set of relevant repositories into a minimal downstream execution plan.

The purpose of this skill is to make dependency propagation repeatable. Keep the reasoning pattern stable even when repo names, package managers, or API changes differ between runs.

## When to use this skill

Use this skill when all of the following are true:

1. An upstream library, package, or shared repo changed.
2. A list of candidate repositories or a dependency graph is already available.
3. The task is to identify only the repositories that need direct downstream updates.
4. The expected result is a focused change set per target repo, often ending in one PR per repo.

Do not use this skill to infer a large organization-wide graph from scratch unless the user explicitly asks for that broader discovery work. Prefer a provided graph or candidate repo list.

## Required inputs

Collect or confirm these inputs before proceeding:

- source repository slug or package name
- upstream change summary
- old version and new version, if versioned
- candidate repositories or target repositories
- dependency graph, if available
- optional validation command per repo
- optional branch and PR naming rules

If key inputs are missing, stop early and ask for them instead of guessing.

For a fuller input contract and example payload, read:

- `references/input-contract.md`

## Core workflow

Follow this workflow in order.

### 1. Normalize the upstream change

Restate the change in a form that can be applied consistently downstream:

- package or repo being updated
- old version
- new version
- any API compatibility note
- the smallest acceptable downstream outcome

Example normalization:

- dependency: `@org/shared-lib`
- version change: `1.0.0 -> 1.1.0`
- compatibility change: `LegacyClient -> ApiClient`
- minimal downstream outcome: update dependency reference and rename imports only where needed

### 2. Restrict scope to direct dependents only

If a dependency graph is provided, use it directly.

If only a candidate repo list is provided, inspect each candidate for a direct reference to the upstream package or repo. Mark repos as one of:

- direct dependent
- not a direct dependent
- unclear / blocked

Never recurse into second-order dependents unless the user explicitly asks for recursive propagation.

### 3. Inspect each direct dependent repo

For each direct dependent repo, find:

- dependency declaration location
- lockfile or resolved version location
- obvious usage sites for renamed symbols or changed APIs
- validation command, if one exists

Use likely file locations first. Examples:

- Node: `package.json`, `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`
- Python: `pyproject.toml`, `requirements.txt`, `poetry.lock`
- .NET: `.csproj`, `Directory.Packages.props`, `packages.lock.json`
- Java: `pom.xml`, `build.gradle`, `gradle.lockfile`

For additional patterns, read:

- `references/analysis-patterns.md`

### 4. Classify required downstream work

Classify each direct dependent into one of these buckets:

1. version-only bump
2. version bump plus minimal compatibility fix
3. blocked because the dependency reference or compatibility impact is unclear

Prefer the smallest valid bucket. Avoid expanding the scope unless the repo truly requires it.

### 5. Build a per-repo execution plan

For each target repo, produce a compact plan containing:

- repo slug
- why it is in scope
- where the dependency is referenced
- which files likely need edits
- which validation command should run
- expected PR title / branch name if available

The plan should be concise enough to hand to another OpenHands conversation or to feed into an orchestrator.

### 6. Preserve minimal diffs

Keep downstream changes tightly scoped:

- update only the dependency reference and required compatibility fixes
- avoid opportunistic refactors
- avoid unrelated formatting churn
- avoid editing files with no relation to the dependency update
- do not broaden the fix if validation already passes with a smaller change set

### 7. Validate before declaring success

Prefer real repo validation commands when available. Examples:

- `npm test`
- `pytest -q`
- `mvn test`
- `dotnet test`

If validation infrastructure is missing, report that explicitly instead of implying correctness.

### 8. Produce traceable outputs

When execution is part of the task, ensure the final output contains:

- targeted repos
- ignored repos and why
- files changed per repo
- validation results per repo
- branch names
- PR URLs or blockers

## Decision rules

Apply these rules consistently:

- Prefer provided graph data over inference.
- Prefer direct evidence in files over assumptions.
- Prefer smaller diffs over generalized cleanup.
- Prefer explicit blockers over silent partial success.
- Prefer one PR per repo.
- Prefer stopping for clarification when the direct-dependent relationship is uncertain.

## Recommended output format

When performing only analysis, summarize per repo using this shape:

- `repo`: repository slug
- `in_scope`: yes/no
- `reason`: direct dependency evidence or exclusion reason
- `dependency_files`: likely files to edit
- `usage_files`: likely compatibility-fix files
- `validation`: command or `unknown`
- `next_action`: `skip`, `update-version`, `update-version-and-code`, or `blocked`

When performing execution, extend that output with:

- branch name
- PR title
- final status
- PR URL or blocker

## Cloud UI and orchestrator usage

This skill works well in two modes:

1. analysis-only mode inside a single Cloud UI conversation
2. orchestrated mode where one controller conversation fans out to one downstream conversation per target repo

For a Cloud UI usage pattern and prompt shape, read:

- `references/cloud-ui-usage.md`

## Additional resources

### Reference files

Consult these files as needed:

- `references/input-contract.md` — expected inputs, normalized payload shape, and examples
- `references/analysis-patterns.md` — ecosystem-specific inspection hints and minimal-diff heuristics
- `references/cloud-ui-usage.md` — Cloud UI operator flow and prompt structure

## Success criteria

Treat the analysis as good when all of the following are true:

- only direct dependents are targeted
- each in-scope repo has clear evidence for why it needs an update
- the planned edits are minimal and specific
- validation expectations are explicit
- the output is clear enough to hand off to another agent or an orchestrator without re-analysis
