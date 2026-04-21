# Analysis Patterns

Use this reference for practical repo inspection and minimal-diff decisions.

## Direct dependency evidence

Treat these as strong evidence that a repo is a direct dependent:

- upstream package listed in a manifest dependency section
- upstream repo referenced directly in a lockfile or package source declaration
- build files importing or resolving the upstream package directly

Treat these as weaker signals that need confirmation:

- source code imports without a matching manifest entry
- comments or docs mentioning the upstream library
- transitive dependency references only in generated lock output

## Ecosystem inspection hints

### Node.js / TypeScript

Check in roughly this order:

1. `package.json`
2. `package-lock.json`
3. `pnpm-lock.yaml`
4. `yarn.lock`
5. source imports under `src/`, `lib/`, or `test/`

Common compatibility-fix patterns:

- renamed import symbols
- renamed named exports
- updated package entrypoint path
- tiny call-site updates after method signature changes

### Python

Check in roughly this order:

1. `pyproject.toml`
2. `requirements.txt`
3. `poetry.lock`
4. imports under application modules and tests

Common compatibility-fix patterns:

- renamed imports
- moved modules
- changed keyword arguments
- lightly changed return types requiring small assertions or call-site updates

### .NET

Check in roughly this order:

1. `Directory.Packages.props`
2. `.csproj`
3. `packages.lock.json`
4. `using` statements and call sites in source files

Common compatibility-fix patterns:

- renamed types
- namespace changes
- package version centralization updates

### Java / JVM

Check in roughly this order:

1. `pom.xml`
2. `build.gradle`
3. `gradle.lockfile`
4. import sites and constructor or method usages

Common compatibility-fix patterns:

- artifact version updates
- renamed classes
- package path changes
- minimal invocation updates

## Minimal-diff heuristics

Prefer these edits:

- update the version in the main manifest first
- update the lockfile only if it is present and relevant
- update only the call sites that are broken by the upstream change
- preserve formatting unless the edited lines require otherwise

Avoid these edits unless required by validation:

- large refactors
- renaming unrelated symbols for consistency
- moving files
- lint-only churn across untouched files
- dependency upgrades unrelated to the upstream change

## Repo classification rubric

### `update-version`

Choose this when:

- the dependency reference clearly needs a version bump
- no direct code usage appears affected
- validation is expected to pass without source changes

### `update-version-and-code`

Choose this when:

- the dependency reference needs a version bump
- there is direct evidence of a renamed symbol, moved import, or small API change
- the compatibility fix is narrow and obvious

### `blocked`

Choose this when:

- the dependency reference is unclear
- the graph says direct dependent but the repo contents do not support that claim
- the downstream fix appears larger than the allowed minimal scope
- validation failure suggests a broad migration rather than a small propagation fix

## Handoff pattern for orchestrated execution

When handing analysis to an orchestrator or downstream conversation, keep the repo-specific handoff concise:

- why repo is in scope
- exact files likely to change
- exact compatibility fix expected
- validation command
- branch and PR naming guidance if already defined

## Demo-friendly output guidance

For demos, make sure the explanation clearly shows:

- why each targeted repo is a direct dependent
- why the control repo is excluded
- why the final diff is minimal
- which exact validation command passed
