from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_BASE_URL = "https://app.all-hands.dev"


@dataclass(slots=True)
class UpstreamChange:
    summary: str
    old_version: str | None = None
    new_version: str = ""
    usage_notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RepoTarget:
    name: str
    selected_repository: str
    selected_branch: str = "main"
    working_directory: str | None = None
    dependency_hints: list[str] = field(default_factory=list)
    update_instructions: list[str] = field(default_factory=list)
    validation_commands: list[str] = field(default_factory=list)
    extra_context: list[str] = field(default_factory=list)
    pr_base_branch: str | None = None


@dataclass(slots=True)
class WorkflowConfig:
    source_repo: str
    dependency_name: str
    dependency_graph: dict[str, list[str]]
    upstream_change: UpstreamChange
    repositories: dict[str, RepoTarget]
    target_repos: list[str] = field(default_factory=list)
    base_url: str = DEFAULT_BASE_URL
    title_template: str = "Propagate {dependency_name} {new_version} to {repo_name}"
    branch_template: str = "deps/propagate/{dependency_slug}-{version_slug}"
    pr_title_template: str = "chore: update {dependency_name} to {new_version}"
    dry_run: bool = False
    start_timeout_s: int = 600


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("PyYAML is required to load YAML configs.") from exc

    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _parse_repo(name: str, payload: dict[str, Any]) -> RepoTarget:
    return RepoTarget(
        name=name,
        selected_repository=payload.get("selected_repository", name),
        selected_branch=payload.get("selected_branch", "main"),
        working_directory=payload.get("working_directory"),
        dependency_hints=list(payload.get("dependency_hints", [])),
        update_instructions=list(payload.get("update_instructions", [])),
        validation_commands=list(payload.get("validation_commands", [])),
        extra_context=list(payload.get("extra_context", [])),
        pr_base_branch=payload.get("pr_base_branch"),
    )


def load_config(path: str | Path) -> WorkflowConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(config_path)

    if config_path.suffix in {".yaml", ".yml"}:
        payload = _read_yaml(config_path)
    else:
        payload = _read_json(config_path)

    repositories = {
        name: _parse_repo(name, repo_payload)
        for name, repo_payload in payload.get("repositories", {}).items()
    }

    upstream_payload = payload["upstream_change"]
    upstream_change = UpstreamChange(
        summary=upstream_payload["summary"],
        old_version=upstream_payload.get("old_version"),
        new_version=upstream_payload["new_version"],
        usage_notes=list(upstream_payload.get("usage_notes", [])),
    )

    return WorkflowConfig(
        source_repo=payload["source_repo"],
        dependency_name=payload["dependency_name"],
        dependency_graph={name: list(deps) for name, deps in payload["dependency_graph"].items()},
        upstream_change=upstream_change,
        repositories=repositories,
        target_repos=list(payload.get("target_repos", [])),
        base_url=payload.get("base_url", DEFAULT_BASE_URL),
        title_template=payload.get(
            "title_template",
            "Propagate {dependency_name} {new_version} to {repo_name}",
        ),
        branch_template=payload.get(
            "branch_template",
            "deps/propagate/{dependency_slug}-{version_slug}",
        ),
        pr_title_template=payload.get(
            "pr_title_template",
            "chore: update {dependency_name} to {new_version}",
        ),
        dry_run=payload.get("dry_run", False),
        start_timeout_s=int(payload.get("start_timeout_s", 600)),
    )
