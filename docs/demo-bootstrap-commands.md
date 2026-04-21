# Demo Bootstrap Commands

This document gives one operator a copy-paste-friendly way to create the demo repositories.

Fastest option:

```bash
python -m dep_propagator demo-bootstrap --owner yourorg --output demo-bundle
python -m dep_propagator demo-verify demo-bundle
```

Use the manual commands below if you want to create the repos directly in GitHub with `gh`.

These commands are examples. Adjust org name, package scope, and branch names as needed.

## Assumptions

- GitHub CLI (`gh`) is installed and authenticated
- npm is installed
- OpenHands Cloud will be granted access to the resulting repos
- default branch name is `main`

Set your org or username once:

```bash
export DEMO_OWNER="yourorg"
export DEMO_SCOPE="@yourorg"
```

## 1. Create the repositories

```bash
gh repo create "$DEMO_OWNER/demo-shared-lib" --public --clone --description "Demo shared library for OpenHands dependency propagation"
gh repo create "$DEMO_OWNER/demo-service-a" --public --clone --description "Demo downstream service A for OpenHands dependency propagation"
gh repo create "$DEMO_OWNER/demo-service-b" --public --clone --description "Demo downstream service B for OpenHands dependency propagation"
gh repo create "$DEMO_OWNER/demo-service-c" --public --clone --description "Demo unrelated service C for OpenHands dependency propagation"
```

## 2. Initialize `demo-shared-lib` at version 1.0.0

```bash
cd "demo-shared-lib"
cat > package.json <<'EOF'
{
  "name": "@yourorg/demo-shared-lib",
  "version": "1.0.0",
  "main": "src/index.ts",
  "types": "src/index.ts",
  "scripts": {
    "test": "node -e \"console.log('shared-lib ok')\""
  }
}
EOF
mkdir -p src
cat > src/index.ts <<'EOF'
export class LegacyClient {
  getMessage(): string {
    return 'hello from shared lib';
  }
}
EOF
cat > README.md <<'EOF'
# demo-shared-lib

Shared library used for the dependency propagation demo.
EOF
git add .
git commit -m "chore: initialize shared lib v1.0.0"
git push -u origin main
cd ..
```

After creating the repo, replace `@yourorg/demo-shared-lib` with your real scope if needed.

## 3. Apply the upstream change to `demo-shared-lib`

```bash
cd "demo-shared-lib"
cat > package.json <<'EOF'
{
  "name": "@yourorg/demo-shared-lib",
  "version": "1.1.0",
  "main": "src/index.ts",
  "types": "src/index.ts",
  "scripts": {
    "test": "node -e \"console.log('shared-lib ok')\""
  }
}
EOF
cat > src/index.ts <<'EOF'
export class ApiClient {
  getMessage(): string {
    return 'hello from shared lib';
  }
}
EOF
git add .
git commit -m "feat: rename LegacyClient to ApiClient in 1.1.0"
git push
cd ..
```

## 4. Initialize `demo-service-a`

```bash
cd "demo-service-a"
cat > package.json <<'EOF'
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
EOF
mkdir -p src
cat > src/client.ts <<'EOF'
import { LegacyClient } from '@yourorg/demo-shared-lib';

export function fetchMessage(): string {
  return new LegacyClient().getMessage();
}
EOF
cat > test.js <<'EOF'
const fs = require('fs');
const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
const source = fs.readFileSync('src/client.ts', 'utf8');
const version = pkg.dependencies['@yourorg/demo-shared-lib'];
const expected = version === '1.1.0' ? 'ApiClient' : 'LegacyClient';

if (!source.includes(expected)) {
  throw new Error(`Expected ${expected} usage for dependency version ${version}`);
}

console.log('demo-service-a test passed');
EOF
cat > README.md <<'EOF'
# demo-service-a

Direct dependent of demo-shared-lib for the propagation demo.
EOF
git add .
git commit -m "chore: initialize service a"
git push -u origin main
cd ..
```

## 5. Initialize `demo-service-b`

```bash
cd "demo-service-b"
cat > package.json <<'EOF'
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
EOF
mkdir -p src
cat > src/service.ts <<'EOF'
import { LegacyClient } from '@yourorg/demo-shared-lib';

export function buildGreeting(): string {
  const client = new LegacyClient();
  return `service-b: ${client.getMessage()}`;
}
EOF
cat > test.js <<'EOF'
const fs = require('fs');
const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
const source = fs.readFileSync('src/service.ts', 'utf8');
const version = pkg.dependencies['@yourorg/demo-shared-lib'];
const expected = version === '1.1.0' ? 'ApiClient' : 'LegacyClient';

if (!source.includes(expected)) {
  throw new Error(`Expected ${expected} usage for dependency version ${version}`);
}

console.log('demo-service-b test passed');
EOF
cat > README.md <<'EOF'
# demo-service-b

Second direct dependent of demo-shared-lib for the propagation demo.
EOF
git add .
git commit -m "chore: initialize service b"
git push -u origin main
cd ..
```

## 6. Initialize `demo-service-c`

```bash
cd "demo-service-c"
cat > package.json <<'EOF'
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
EOF
mkdir -p src
cat > src/index.ts <<'EOF'
export function status(): string {
  return 'service-c is unrelated';
}
EOF
cat > test.js <<'EOF'
console.log('demo-service-c test passed');
EOF
cat > README.md <<'EOF'
# demo-service-c

Unrelated service used to prove direct-dependent filtering.
EOF
git add .
git commit -m "chore: initialize service c"
git push -u origin main
cd ..
```

## 7. Grant OpenHands access

In OpenHands Cloud:

1. open Settings
2. open Integrations
3. confirm GitHub access includes all four demo repos
4. verify each repo appears in the Cloud UI repo picker

Docs:

- https://docs.openhands.dev/openhands/usage/cloud/github-installation
- https://docs.openhands.dev/openhands/usage/cloud/cloud-ui

## 8. Prepare the orchestrator config

Copy the template:

```bash
cp examples/demo-template-config.json demo-config.json
```

Update:

- `yourorg` placeholders
- package scope
- `dry_run` value

## 9. Rehearse the flow

Run dry-run first:

```bash
python -m dep_propagator start demo-config.json --report conversation-report.json
python -m dep_propagator status conversation-report.json
```

Then run live mode after setting `dry_run` to `false`.

## 10. Record results

After a rehearsal or live run, update:

- `docs/demo-operator-log.md`

Capture:

- config used
- conversation URLs
- PR URLs
- blockers
