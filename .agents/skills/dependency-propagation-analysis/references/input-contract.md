# Input Contract

Use this reference when collecting inputs for a dependency propagation analysis run.

## Minimum required inputs

Provide at least these fields:

- `source_repo` or `dependency_name`
- `upstream_change.summary`
- `candidate_repos` or `target_repos` or `dependency_graph`

Strongly prefer also providing:

- `upstream_change.old_version`
- `upstream_change.new_version`
- `upstream_change.usage_notes`
- `validation_commands` per repo

## Recommended normalized payload

```json
{
  "source_repo": "org/shared-lib",
  "dependency_name": "@org/shared-lib",
  "candidate_repos": [
    "org/service-a",
    "org/service-b",
    "org/service-c"
  ],
  "dependency_graph": {
    "org/service-a": ["org/shared-lib"],
    "org/service-b": ["org/shared-lib"],
    "org/service-c": ["org/other-lib"]
  },
  "upstream_change": {
    "summary": "Version 1.1.0 renames LegacyClient to ApiClient.",
    "old_version": "1.0.0",
    "new_version": "1.1.0",
    "usage_notes": [
      "Rename LegacyClient imports to ApiClient if they exist."
    ]
  },
  "repositories": {
    "org/service-a": {
      "validation_commands": ["npm test"]
    },
    "org/service-b": {
      "validation_commands": ["npm test"]
    }
  }
}
```

## Input handling rules

### When both `candidate_repos` and `dependency_graph` are available

Use the graph as the source of truth for direct-dependency determination. Use the candidate list to constrain which repos should be considered.

### When only `candidate_repos` are available

Inspect each candidate repo for direct evidence that it depends on the upstream package or repo.

### When only `target_repos` are available

Treat them as candidate repos, not guaranteed positives, unless the user explicitly states they are already confirmed direct dependents.

### When validation commands are missing

Try to discover obvious build or test commands from repository files. If none are obvious, mark validation as unknown.

## Minimal analysis output shape

```json
[
  {
    "repo": "org/service-a",
    "in_scope": true,
    "reason": "package.json directly references @org/shared-lib",
    "dependency_files": ["package.json", "package-lock.json"],
    "usage_files": ["src/client.ts"],
    "validation": ["npm test"],
    "next_action": "update-version-and-code"
  },
  {
    "repo": "org/service-c",
    "in_scope": false,
    "reason": "no direct reference to @org/shared-lib",
    "dependency_files": [],
    "usage_files": [],
    "validation": [],
    "next_action": "skip"
  }
]
```

## Failure-handling expectations

If any of these are true, stop and ask for clarification:

- the upstream dependency identifier is ambiguous
- the repo list is missing and graph inference is out of scope
- the graph conflicts with direct file evidence in a way that affects targeting
- the user’s scope is unclear about direct versus recursive propagation
