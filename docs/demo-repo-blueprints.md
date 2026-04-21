# Demo Repository Blueprints

This document defines a minimal set of repositories for reproducing the dependency propagation demo.

The goal is not to build production services. The goal is to make the demo:

- easy to set up
- fast to validate
- easy to explain
- predictable for OpenHands

## Target repository set

Create these repositories in a GitHub org or account that OpenHands Cloud can access:

- `yourorg/demo-shared-lib`
- `yourorg/demo-service-a`
- `yourorg/demo-service-b`
- `yourorg/demo-service-c`

Recommended default branch for all repos:

- `main`

## Shared design choices

Use the same ecosystem everywhere:

- Node.js
- TypeScript
- npm

Keep every repo small:

- 1 to 3 source files
- 1 quick test command
- no Docker
- no monorepo setup
- no external services

## Expected demo flow

1. `demo-shared-lib` changes from `1.0.0` to `1.1.0`.
2. The library renames `LegacyClient` to `ApiClient`.
3. `demo-service-a` and `demo-service-b` still use `LegacyClient`.
4. The propagation workflow updates dependency references and fixes imports.
5. `demo-service-c` is ignored because it does not depend on the shared lib.

## Repository blueprint: `demo-shared-lib`

### Purpose

This is the upstream package.

### Minimal file tree

```text
package.json
src/index.ts
README.md
```

### Version 1.0.0 shape

#### `package.json`

```json
{
  "name": "@yourorg/demo-shared-lib",
  "version": "1.0.0",
  "main": "src/index.ts",
  "types": "src/index.ts",
  "scripts": {
    "test": "node -e \"console.log('shared-lib ok')\""
  }
}
```

#### `src/index.ts`

```ts
export class LegacyClient {
  getMessage(): string {
    return 'hello from shared lib';
  }
}
```

### Version 1.1.0 change

#### `package.json`

```json
{
  "name": "@yourorg/demo-shared-lib",
  "version": "1.1.0",
  "main": "src/index.ts",
  "types": "src/index.ts",
  "scripts": {
    "test": "node -e \"console.log('shared-lib ok')\""
  }
}
```

#### `src/index.ts`

```ts
export class ApiClient {
  getMessage(): string {
    return 'hello from shared lib';
  }
}
```

### Upstream commit message suggestion

```text
feat: rename LegacyClient to ApiClient in 1.1.0
```

## Repository blueprint: `demo-service-a`

### Purpose

First direct dependent of the shared library.

### Minimal file tree

```text
package.json
package-lock.json
src/client.ts
test.js
README.md
```

### `package.json`

Use the package name and version you actually publish or otherwise install for the demo.

```json
{
  "name": "demo-service-a",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "test": "node test.js"
  },
  "dependencies": {
    "@yourorg/demo-shared-lib": "1.0.0"
  }
}
```

### `src/client.ts`

```ts
import { LegacyClient } from '@yourorg/demo-shared-lib';

export function fetchMessage(): string {
  return new LegacyClient().getMessage();
}
```

### `test.js`

```js
const fs = require('fs');
const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
const source = fs.readFileSync('src/client.ts', 'utf8');
const version = pkg.dependencies['@yourorg/demo-shared-lib'];
const expected = version === '1.1.0' ? 'ApiClient' : 'LegacyClient';

if (!source.includes(expected)) {
  throw new Error(`Expected ${expected} usage for dependency version ${version}`);
}

console.log('demo-service-a test passed');
```

### Post-propagation expected state

#### `package.json`

```json
{
  "dependencies": {
    "@yourorg/demo-shared-lib": "1.1.0"
  }
}
```

#### `src/client.ts`

```ts
import { ApiClient } from '@yourorg/demo-shared-lib';

export function fetchMessage(): string {
  return new ApiClient().getMessage();
}
```

The same `test.js` continues to pass after propagation because it checks the expected client class based on the dependency version.

## Repository blueprint: `demo-service-b`

### Purpose

Second direct dependent of the shared library.

### Minimal file tree

```text
package.json
package-lock.json
src/service.ts
test.js
README.md
```

### `package.json`

```json
{
  "name": "demo-service-b",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "test": "node test.js"
  },
  "dependencies": {
    "@yourorg/demo-shared-lib": "1.0.0"
  }
}
```

### `src/service.ts`

```ts
import { LegacyClient } from '@yourorg/demo-shared-lib';

export function buildGreeting(): string {
  const client = new LegacyClient();
  return `service-b: ${client.getMessage()}`;
}
```

### `test.js`

```js
const fs = require('fs');
const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
const source = fs.readFileSync('src/service.ts', 'utf8');
const version = pkg.dependencies['@yourorg/demo-shared-lib'];
const expected = version === '1.1.0' ? 'ApiClient' : 'LegacyClient';

if (!source.includes(expected)) {
  throw new Error(`Expected ${expected} usage for dependency version ${version}`);
}

console.log('demo-service-b test passed');
```

### Post-propagation expected state

#### `package.json`

```json
{
  "dependencies": {
    "@yourorg/demo-shared-lib": "1.1.0"
  }
}
```

#### `src/service.ts`

```ts
import { ApiClient } from '@yourorg/demo-shared-lib';

export function buildGreeting(): string {
  const client = new ApiClient();
  return `service-b: ${client.getMessage()}`;
}
```

The same `test.js` continues to pass after propagation because it checks the expected client class based on the dependency version.

## Repository blueprint: `demo-service-c`

### Purpose

Control repo that should be ignored by the propagation workflow.

### Minimal file tree

```text
package.json
src/index.ts
test.js
README.md
```

### `package.json`

```json
{
  "name": "demo-service-c",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "test": "node test.js"
  },
  "dependencies": {
    "left-pad": "1.3.0"
  }
}
```

### `src/index.ts`

```ts
export function status(): string {
  return 'service-c is unrelated';
}
```

### `test.js`

```js
console.log('demo-service-c test passed');
```

## Practical package distribution choices

For the demo, use whichever package distribution strategy is easiest for your environment:

### Option A: publish a real package version

Best for the cleanest story if your org already publishes npm packages.

### Option B: use GitHub package references

Fine if your environment already supports GitHub Packages.

### Option C: skip actual installability and optimize for code diffs

For a pure PR demo, the most important outcomes are:

- dependency reference changed
- import name changed
- validation command passed

If real package publication adds too much ceremony, make the tests simple and source-based so the PR is still easy to verify on screen.

## Branching and PR expectations

For each downstream repo, the OpenHands prompt should result in:

- branch name like `deps/propagate/demo-shared-lib-1-1-0`
- one focused PR
- only dependency and compatibility changes

## Demo success criteria

The repo setup is good enough when all of these are true:

- OpenHands can manually open each target repo from Cloud UI
- `demo-service-a` and `demo-service-b` both contain `LegacyClient`
- both target repos reference version `1.0.0`
- `demo-service-c` does not reference the shared lib
- `npm test` is fast in both target repos

## Operator note

After creating the repos, record the exact repo URLs and any deviations from this blueprint in `docs/demo-operator-log.md`.
