from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .client import OpenHandsV1Client
from .config import RepoTarget, WorkflowConfig, load_config
from .demo import bootstrap_demo_bundle, verify_demo_bundle
from .prompts import render_prompt


@dataclass(slots=True)
class ConversationRun:
    repo_name: str
    selected_repository: str
    selected_branch: str
    branch_name: str
    title: str
    prompt: str
    start_task_id: str | None = None
    app_conversation_id: str | None = None
    conversation_url: str | None = None
    start_status: str | None = None
    execution_status: str | None = None
    sandbox_status: str | None = None
    status: str = "pending"
    message: str = ""


class WorkflowError(RuntimeError):
    pass


def _slug(value: str) -> str:
    return "-".join(part for part in "".join(ch if ch.isalnum() else "-" for ch in value).split("-") if part).lower()


def resolve_direct_dependents(config: WorkflowConfig) -> list[str]:
    inferred = sorted(
        repo_name
        for repo_name, dependencies in config.dependency_graph.items()
        if config.source_repo in dependencies
    )
    if not config.target_repos:
        return inferred

    invalid = sorted(set(config.target_repos) - set(inferred))
    if invalid:
        raise WorkflowError(
            f"Target repos are not direct dependents of {config.source_repo}: {', '.join(invalid)}"
        )
    return config.target_repos


def build_branch_name(config: WorkflowConfig) -> str:
    return config.branch_template.format(
        dependency_name=config.dependency_name,
        new_version=config.upstream_change.new_version,
        dependency_slug=_slug(config.dependency_name),
        version_slug=_slug(config.upstream_change.new_version),
    )


def build_title(config: WorkflowConfig, repo_name: str) -> str:
    return config.title_template.format(
        dependency_name=config.dependency_name,
        new_version=config.upstream_change.new_version,
        source_repo=config.source_repo,
        repo_name=repo_name,
    )


def build_pr_title(config: WorkflowConfig) -> str:
    return config.pr_title_template.format(
        dependency_name=config.dependency_name,
        new_version=config.upstream_change.new_version,
        source_repo=config.source_repo,
    )


def _conversation_url(base_url: str, conversation_id: str | None) -> str | None:
    if not conversation_id:
        return None
    return f"{base_url.rstrip('/')}/conversations/{conversation_id}"


def _normalize_start_response(
    *,
    response: dict[str, Any],
    client: OpenHandsV1Client,
    timeout_s: int,
) -> tuple[str | None, str | None, dict[str, Any] | None]:
    app_conversation_id = response.get("app_conversation_id")
    start_task_id = response.get("id")
    task_payload = None

    if app_conversation_id:
        return start_task_id, app_conversation_id, task_payload
    if not start_task_id:
        raise WorkflowError(f"Unexpected conversation start response: {response}")

    task_payload = client.poll_start_task_until_ready(start_task_id, timeout_s=timeout_s)
    return start_task_id, task_payload.get("app_conversation_id"), task_payload


def start_repo_conversation(
    client: OpenHandsV1Client | None,
    config: WorkflowConfig,
    repo: RepoTarget,
) -> ConversationRun:
    branch_name = build_branch_name(config)
    title = build_title(config, repo.name)
    pr_title = build_pr_title(config)
    prompt = render_prompt(config, repo, branch_name, pr_title)

    if config.dry_run:
        return ConversationRun(
            repo_name=repo.name,
            selected_repository=repo.selected_repository,
            selected_branch=repo.selected_branch,
            branch_name=branch_name,
            title=title,
            prompt=prompt,
            status="dry_run",
            message="Prompt rendered; no conversation started because dry_run=true.",
        )

    if client is None:
        raise WorkflowError("An OpenHands V1 client is required when dry_run is false.")

    start_response = client.app_conversation_start(
        initial_message=prompt,
        selected_repository=repo.selected_repository,
        selected_branch=repo.selected_branch,
        title=title,
        run=True,
    )
    start_task_id, app_conversation_id, task_payload = _normalize_start_response(
        response=start_response,
        client=client,
        timeout_s=config.start_timeout_s,
    )
    conversation = client.app_conversation_get(app_conversation_id) if app_conversation_id else None
    start_status = None if task_payload is None else str(task_payload.get("status") or "")
    failure_detail = None if task_payload is None else task_payload.get("detail")
    message = "Conversation started."
    if not app_conversation_id:
        if failure_detail:
            message = str(failure_detail)
        elif start_status:
            message = f"Conversation start finished with status {start_status} but no app_conversation_id was returned."
        else:
            message = "Conversation did not return an app_conversation_id."

    return ConversationRun(
        repo_name=repo.name,
        selected_repository=repo.selected_repository,
        selected_branch=repo.selected_branch,
        branch_name=branch_name,
        title=title,
        prompt=prompt,
        start_task_id=start_task_id,
        app_conversation_id=app_conversation_id,
        conversation_url=_conversation_url(config.base_url, app_conversation_id),
        start_status=start_status,
        execution_status=None if conversation is None else conversation.get("execution_status"),
        sandbox_status=None if conversation is None else conversation.get("sandbox_status"),
        status="started" if app_conversation_id else "failed",
        message=message,
    )


def start_workflow(config: WorkflowConfig, client: OpenHandsV1Client | None = None) -> list[ConversationRun]:
    api = client
    results: list[ConversationRun] = []
    for repo_name in resolve_direct_dependents(config):
        repo = config.repositories.get(repo_name)
        if repo is None:
            results.append(
                ConversationRun(
                    repo_name=repo_name,
                    selected_repository=repo_name,
                    selected_branch="main",
                    branch_name=build_branch_name(config),
                    title=build_title(config, repo_name),
                    prompt="",
                    status="failed",
                    message=f"Missing repository configuration for {repo_name}",
                )
            )
            continue
        try:
            if api is None and not config.dry_run:
                api = OpenHandsV1Client.from_env(base_url=config.base_url)
            results.append(start_repo_conversation(api, config, repo))
        except Exception as exc:  # noqa: BLE001
            results.append(
                ConversationRun(
                    repo_name=repo.name,
                    selected_repository=repo.selected_repository,
                    selected_branch=repo.selected_branch,
                    branch_name=build_branch_name(config),
                    title=build_title(config, repo.name),
                    prompt="",
                    status="failed",
                    message=str(exc),
                )
            )
    return results


def status_workflow(
    report_path: str | Path,
    client: OpenHandsV1Client | None = None,
    *,
    base_url: str | None = None,
) -> list[ConversationRun]:
    payload = json.loads(Path(report_path).read_text(encoding="utf-8"))
    if not payload:
        return []

    updated = [ConversationRun(**item) for item in payload]
    if not any(run.app_conversation_id for run in updated):
        return updated

    inferred_base_url = payload[0].get("conversation_url", "").split("/conversations/")[0] or None
    api = client or OpenHandsV1Client.from_env(base_url=base_url or inferred_base_url or "https://app.all-hands.dev")

    for run in updated:
        if run.app_conversation_id:
            conversation = api.app_conversation_get(run.app_conversation_id) or {}
            run.execution_status = conversation.get("execution_status")
            run.sandbox_status = conversation.get("sandbox_status")
            if run.execution_status == "running":
                run.status = "running"
            elif run.execution_status:
                run.status = str(run.execution_status)
    return updated


def write_report(path: str | Path, runs: list[ConversationRun]) -> None:
    Path(path).write_text(json.dumps([asdict(run) for run in runs], indent=2) + "\n", encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OpenHands Cloud V1 dependency propagation orchestrator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    start_parser = subparsers.add_parser("start", help="Start one OpenHands V1 conversation per direct dependent repo")
    start_parser.add_argument("config", help="Path to workflow config JSON or YAML")
    start_parser.add_argument("--report", default="conversation-report.json", help="Where to write the conversation report")

    status_parser = subparsers.add_parser("status", help="Refresh statuses for conversations in a report")
    status_parser.add_argument("report", help="Path to an existing conversation report")
    status_parser.add_argument("--base-url", default=None, help="Override the OpenHands Cloud base URL")

    demo_bootstrap_parser = subparsers.add_parser(
        "demo-bootstrap",
        help="Generate a local four-repo demo bundle and matching workflow config",
    )
    demo_bootstrap_parser.add_argument("--owner", required=True, help="GitHub owner or org name for demo repo slugs")
    demo_bootstrap_parser.add_argument(
        "--scope",
        default=None,
        help="Package scope for the shared library, defaults to @<owner>",
    )
    demo_bootstrap_parser.add_argument(
        "--output",
        default="demo-bundle",
        help="Output directory for the generated demo bundle",
    )
    demo_bootstrap_parser.add_argument(
        "--live-config",
        action="store_true",
        help="Write demo-config.json with dry_run=false",
    )

    demo_verify_parser = subparsers.add_parser(
        "demo-verify",
        help="Validate a generated demo bundle locally and run a dry-run workflow check",
    )
    demo_verify_parser.add_argument("bundle", help="Path to a generated demo bundle directory")

    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "start":
        config = load_config(args.config)
        runs = start_workflow(config)
        write_report(args.report, runs)
        for run in runs:
            print(f"[{run.status}] {run.repo_name}: {run.message}")
            if run.conversation_url:
                print(f"  {run.conversation_url}")
        return 0 if all(run.status != "failed" for run in runs) else 1

    if args.command == "status":
        runs = status_workflow(args.report, base_url=args.base_url)
        write_report(args.report, runs)
        for run in runs:
            print(
                f"[{run.status}] {run.repo_name}: execution_status={run.execution_status} sandbox_status={run.sandbox_status}"
            )
        return 0

    if args.command == "demo-bootstrap":
        result = bootstrap_demo_bundle(
            args.output,
            owner=args.owner,
            scope=args.scope,
            dry_run=not args.live_config,
        )
        print(f"Created demo bundle: {result.bundle_dir}")
        print(f"Config: {result.config_path}")
        for repo_name, repo_path in sorted(result.repo_paths.items()):
            print(f"- {repo_name}: {repo_path}")
        return 0

    verification = verify_demo_bundle(args.bundle)
    print(f"Verified demo bundle: {verification.bundle_dir}")
    print(f"Config: {verification.config_path}")
    print(f"Direct dependents: {', '.join(verification.direct_dependents)}")
    for repo_name, output in sorted(verification.repo_test_outputs.items()):
        print(f"- test {repo_name}: {output}")
    for repo_name, status in sorted(verification.run_statuses.items()):
        print(f"- dry-run {repo_name}: {status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
