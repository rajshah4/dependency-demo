# Demo Operator Log

Use this file to keep a running history of demo rehearsals and production demo runs.

## 2026-04-21 — Initial setup and verification

### What was completed

- Implemented an OpenHands Cloud V1 conversation orchestrator.
- Added local unit tests for dependency resolution, prompt rendering, dry-run behavior, and status refresh.
- Verified dry-run CLI flow works end-to-end.
- Added automatic `.env` loading for CLI usage when environment variables are not already exported.

### Verification results

- Unit tests passed locally.
- Dry-run start and status commands worked.
- OpenHands Cloud API authentication succeeded with a valid key.
- A generated local demo bundle passed `demo-bootstrap` and `demo-verify` successfully.
- The local demo bundle includes four repos plus a generated `demo-config.json`.

### Live-run result

- Initial live conversation startup against placeholder sample repos reached the OpenHands API successfully.
- That earlier attempt failed with:
  - `Git provider authentication issue when getting remote URL`
- A later live run against real public repos under `rajshah4` succeeded.
- OpenHands started one conversation for each direct dependent repo and both conversations finished.
- Pull requests were created successfully for:
  - `https://github.com/rajshah4/demo-service-a/pull/1`
  - `https://github.com/rajshah4/demo-service-b/pull/1`
- No pull request was created for the control repo `rajshah4/demo-service-c`.

### Interpretation

- API authentication is working.
- Real public repos accessible to OpenHands resolved the earlier git-provider blocker.
- The direct-dependent-only behavior is now verified end-to-end against public GitHub repos.

### Action for next operator

- Reuse the validated public config in `examples/rajshah4-public-demo-config.json` for rehearsal.
- If you need a fresh live rerun, close or clean up the existing demo PR branches first, or create a fresh repo set.
- Record new conversation URLs and PR URLs after each rehearsal.

---

## Rehearsal template

### Date

- YYYY-MM-DD

### Operator

- name

### Config used

- path:
- dry_run:

### Dry-run result

- success/failure:
- notes:

### Live-run result

- success/failure:
- conversation URLs:
- PR URLs:

### Problems encountered

- item 1
- item 2

### Follow-up actions

- item 1
- item 2
