# Repository Memory

- Project purpose: orchestrate dependency propagation using OpenHands Cloud V1 app conversations.
- Entry points:
  - `python -m dep_propagator start <config> --report <file>`
  - `python -m dep_propagator status <report>`
  - `python -m dep_propagator demo-bootstrap --owner <owner> --output <bundle-dir>`
  - `python -m dep_propagator demo-verify <bundle-dir>`
- This repo does not update downstream repos locally; each downstream repo is handled by its own OpenHands conversation.
- Authentication uses `OPENHANDS_CLOUD_API_KEY` first, then `OPENHANDS_API_KEY`.
- For CLI runs, the client also auto-loads a local `.env` file from the current working directory or its parents before checking those env vars.
- JSON config works out of the box; YAML requires `PyYAML`.
- Tests: `python -m unittest discover -s tests -t .`.
- Demo handoff artifacts live in `docs/demo-runbook.md`, `docs/demo-repo-blueprints.md`, `docs/demo-bootstrap-commands.md`, `docs/demo-script.md`, `docs/demo-operator-log.md`, `docs/public-demo-results.md`, `examples/demo-template-config.json`, and `examples/rajshah4-public-demo-config.json`.
- Reusable repository skill lives at `.agents/skills/dependency-propagation-analysis/`; use it when the operator wants to pass an upstream change plus a relevant repo set and reuse the same dependency-analysis workflow in Cloud UI or orchestrated runs.
- `demo-bootstrap` generates a four-repo local bundle plus `demo-config.json`; `demo-verify` runs local Node checks and a dry-run workflow check against that bundle.
- A real live run succeeded against public repos `rajshah4/demo-shared-lib`, `rajshah4/demo-service-a`, `rajshah4/demo-service-b`, and `rajshah4/demo-service-c`.
- Successful live outputs: OpenHands conversations `61452765296d4812b9c633c0fb5a3d39` and `f93836345b4b48a880fc7dfc78a4c9ec`; PRs `demo-service-a#1` and `demo-service-b#1`; no PR for `demo-service-c`.
- Placeholder sample repo slugs can still fail with `Git provider authentication issue when getting remote URL`; use real repos already accessible in OpenHands Cloud.
