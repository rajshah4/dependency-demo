from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .config import WorkflowConfig, load_config


@dataclass(slots=True, frozen=True)
class DemoBootstrapResult:
    bundle_dir: Path
    config_path: Path
    repo_paths: dict[str, Path]


@dataclass(slots=True, frozen=True)
class DemoVerificationResult:
    bundle_dir: Path
    config_path: Path
    direct_dependents: list[str]
    repo_test_outputs: dict[str, str]
    run_statuses: dict[str, str]


def _normalize_owner(owner: str) -> str:
    value = owner.strip().strip("/")
    if not value:
        raise ValueError("owner must not be empty")
    return value


def _normalize_scope(owner: str, scope: str | None) -> str:
    if scope is None or not scope.strip():
        return f"@{owner}"
    value = scope.strip()
    return value if value.startswith("@") else f"@{value}"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _json(payload: object) -> str:
    return json.dumps(payload, indent=2) + "\n"


def _package_lock(package_name: str, version: str, dependencies: dict[str, str]) -> str:
    payload = {
        "name": package_name,
        "version": version,
        "lockfileVersion": 3,
        "requires": True,
        "packages": {
            "": {
                "name": package_name,
                "version": version,
                "dependencies": dependencies,
            }
        },
    }
    return _json(payload)


def _shared_lib_files(scope: str) -> dict[str, str]:
    package_name = f"{scope}/demo-shared-lib"
    return {
        "README.md": "# demo-shared-lib\n\nShared library used for the dependency propagation demo.\n",
        "UPSTREAM_CHANGE.md": (
            "# Upstream change\n\n"
            "Previous version: `1.0.0` exported `LegacyClient`.\n\n"
            "Current version: `1.1.0` exports `ApiClient`.\n"
        ),
        "package.json": _json(
            {
                "name": package_name,
                "version": "1.1.0",
                "main": "src/index.ts",
                "types": "src/index.ts",
                "scripts": {"test": "node -e \"console.log('shared-lib ok')\""},
            }
        ),
        "src/index.ts": (
            "export class ApiClient {\n"
            "  getMessage(): string {\n"
            "    return 'hello from shared lib';\n"
            "  }\n"
            "}\n"
        ),
    }


def _service_files(*, service_name: str, source_path: str, scope: str) -> dict[str, str]:
    dependency_name = f"{scope}/demo-shared-lib"
    package_json = {
        "name": service_name,
        "version": "1.0.0",
        "private": True,
        "scripts": {"test": "node test.js"},
        "dependencies": {dependency_name: "1.0.0"},
    }
    source_code = {
        "demo-service-a": (
            "import { LegacyClient } from '@SCOPE/demo-shared-lib';\n\n"
            "export function fetchMessage(): string {\n"
            "  return new LegacyClient().getMessage();\n"
            "}\n"
        ),
        "demo-service-b": (
            "import { LegacyClient } from '@SCOPE/demo-shared-lib';\n\n"
            "export function buildGreeting(): string {\n"
            "  const client = new LegacyClient();\n"
            "  return `service-b: ${client.getMessage()}`;\n"
            "}\n"
        ),
    }[service_name].replace("@SCOPE", scope)
    test_script = (
        "const fs = require('fs');\n"
        "const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));\n"
        f"const source = fs.readFileSync('{source_path}', 'utf8');\n"
        f"const version = pkg.dependencies['{dependency_name}'];\n"
        "const expected = version === '1.1.0' ? 'ApiClient' : 'LegacyClient';\n"
        "if (!source.includes(expected)) {\n"
        "  throw new Error(`Expected ${expected} usage for dependency version ${version}`);\n"
        "}\n"
        f"console.log('{service_name} test passed');\n"
    )
    readme = f"# {service_name}\n\nDirect dependent of demo-shared-lib for the propagation demo.\n"
    return {
        "README.md": readme,
        "package.json": _json(package_json),
        "package-lock.json": _package_lock(service_name, "1.0.0", {dependency_name: "1.0.0"}),
        source_path: source_code,
        "test.js": test_script,
    }


def _service_c_files() -> dict[str, str]:
    package_json = {
        "name": "demo-service-c",
        "version": "1.0.0",
        "private": True,
        "scripts": {"test": "node test.js"},
        "dependencies": {"left-pad": "1.3.0"},
    }
    return {
        "README.md": "# demo-service-c\n\nUnrelated service used to prove direct-dependent filtering.\n",
        "package.json": _json(package_json),
        "package-lock.json": _package_lock("demo-service-c", "1.0.0", {"left-pad": "1.3.0"}),
        "src/index.ts": (
            "export function status(): string {\n"
            "  return 'service-c is unrelated';\n"
            "}\n"
        ),
        "test.js": "console.log('demo-service-c test passed');\n",
    }


def _bundle_readme(owner: str, scope: str) -> str:
    return (
        "# Generated demo bundle\n\n"
        f"Owner: `{owner}`\n\n"
        f"Package scope: `{scope}`\n\n"
        "This bundle contains four local repositories under `repos/` and a ready-to-edit `demo-config.json`.\n"
        "Use the repos as the source of truth when creating or syncing real GitHub demo repositories.\n"
    )


def _build_config(owner: str, scope: str, *, dry_run: bool) -> dict[str, object]:
    dependency_repo = f"{owner}/demo-shared-lib"
    dependency_name = f"{scope}/demo-shared-lib"
    service_a = f"{owner}/demo-service-a"
    service_b = f"{owner}/demo-service-b"
    service_c = f"{owner}/demo-service-c"
    return {
        "source_repo": dependency_repo,
        "dependency_name": dependency_name,
        "dependency_graph": {
            service_a: [dependency_repo],
            service_b: [dependency_repo],
            service_c: [f"{owner}/demo-other-lib"],
        },
        "target_repos": [service_a, service_b],
        "upstream_change": {
            "summary": "Version 1.1.0 renames LegacyClient to ApiClient and includes a small bugfix release.",
            "old_version": "1.0.0",
            "new_version": "1.1.0",
            "usage_notes": [
                "Rename LegacyClient imports to ApiClient if they exist.",
                "Keep the final PR focused to the dependency update plus minimal compatibility fixes.",
            ],
        },
        "base_url": "https://app.all-hands.dev",
        "branch_template": "deps/propagate/{dependency_slug}-{version_slug}",
        "pr_title_template": "chore: update {dependency_name} to {new_version}",
        "dry_run": dry_run,
        "repositories": {
            service_a: {
                "selected_repository": service_a,
                "selected_branch": "main",
                "dependency_hints": ["package.json", "package-lock.json", "src/client.ts"],
                "update_instructions": [
                    "Update the npm dependency version first, then regenerate the lockfile if needed.",
                    "If LegacyClient imports exist, rename them to ApiClient.",
                ],
                "validation_commands": ["npm test"],
                "extra_context": [
                    "This service contains one obvious LegacyClient usage for the demo.",
                ],
                "pr_base_branch": "main",
            },
            service_b: {
                "selected_repository": service_b,
                "selected_branch": "main",
                "dependency_hints": ["package.json", "package-lock.json", "src/service.ts"],
                "update_instructions": [
                    "Keep the downstream diff small enough to explain in one slide.",
                    "If LegacyClient imports exist, rename them to ApiClient.",
                ],
                "validation_commands": ["npm test"],
                "extra_context": [
                    "This service also uses the renamed client so the PR needs a tiny code fix.",
                ],
                "pr_base_branch": "main",
            },
        },
    }


def bootstrap_demo_bundle(
    output_dir: str | Path,
    *,
    owner: str,
    scope: str | None = None,
    dry_run: bool = True,
) -> DemoBootstrapResult:
    normalized_owner = _normalize_owner(owner)
    normalized_scope = _normalize_scope(normalized_owner, scope)
    bundle_dir = Path(output_dir)
    if bundle_dir.exists() and any(bundle_dir.iterdir()):
        raise FileExistsError(f"Output directory is not empty: {bundle_dir}")
    bundle_dir.mkdir(parents=True, exist_ok=True)

    repos_dir = bundle_dir / "repos"
    repos_dir.mkdir(parents=True, exist_ok=True)

    repo_contents = {
        "demo-shared-lib": _shared_lib_files(normalized_scope),
        "demo-service-a": _service_files(
            service_name="demo-service-a",
            source_path="src/client.ts",
            scope=normalized_scope,
        ),
        "demo-service-b": _service_files(
            service_name="demo-service-b",
            source_path="src/service.ts",
            scope=normalized_scope,
        ),
        "demo-service-c": _service_c_files(),
    }

    repo_paths: dict[str, Path] = {}
    for repo_name, files in repo_contents.items():
        repo_path = repos_dir / repo_name
        repo_paths[repo_name] = repo_path
        for relative_path, content in files.items():
            _write(repo_path / relative_path, content)

    config_path = bundle_dir / "demo-config.json"
    _write(config_path, _json(_build_config(normalized_owner, normalized_scope, dry_run=dry_run)))
    _write(bundle_dir / "README.md", _bundle_readme(normalized_owner, normalized_scope))

    return DemoBootstrapResult(bundle_dir=bundle_dir, config_path=config_path, repo_paths=repo_paths)


def verify_demo_bundle(bundle_dir: str | Path) -> DemoVerificationResult:
    from .workflow import resolve_direct_dependents, start_workflow

    root = Path(bundle_dir)
    config_path = root / "demo-config.json"
    config = load_config(config_path)
    direct_dependents = resolve_direct_dependents(config)

    repo_test_outputs: dict[str, str] = {}
    for repo_name in ("demo-shared-lib", "demo-service-a", "demo-service-b", "demo-service-c"):
        repo_path = root / "repos" / repo_name
        completed = subprocess.run(
            ["node", "test.js"] if repo_name != "demo-shared-lib" else ["node", "-e", "console.log('shared-lib ok')"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        output = completed.stdout.strip() or completed.stderr.strip() or "ok"
        repo_test_outputs[repo_name] = output

    dry_run_config = WorkflowConfig(
        source_repo=config.source_repo,
        dependency_name=config.dependency_name,
        dependency_graph=config.dependency_graph,
        upstream_change=config.upstream_change,
        repositories=config.repositories,
        target_repos=config.target_repos,
        base_url=config.base_url,
        title_template=config.title_template,
        branch_template=config.branch_template,
        pr_title_template=config.pr_title_template,
        dry_run=True,
        start_timeout_s=config.start_timeout_s,
    )
    runs = start_workflow(dry_run_config)
    run_statuses = {run.repo_name: run.status for run in runs}

    return DemoVerificationResult(
        bundle_dir=root,
        config_path=config_path,
        direct_dependents=direct_dependents,
        repo_test_outputs=repo_test_outputs,
        run_statuses=run_statuses,
    )


def remove_demo_bundle(bundle_dir: str | Path) -> None:
    shutil.rmtree(Path(bundle_dir))
