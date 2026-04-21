from __future__ import annotations

import json
import os
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path

from dep_propagator.client import OpenHandsV1Client
from dep_propagator.config import RepoTarget, UpstreamChange, WorkflowConfig
from dep_propagator.prompts import render_prompt
from dep_propagator.workflow import (
    ConversationRun,
    _normalize_start_response,
    build_branch_name,
    build_pr_title,
    resolve_direct_dependents,
    start_workflow,
    status_workflow,
)


class FakeClient:
    def __init__(self) -> None:
        self.seen_task_ids: list[str] = []
        self.seen_conversation_ids: list[str] = []

    def poll_start_task_until_ready(self, task_id: str, *, timeout_s: int = 600) -> dict[str, str]:
        self.seen_task_ids.append(task_id)
        return {"status": "READY", "app_conversation_id": "conv-123"}

    def app_conversation_get(self, conversation_id: str) -> dict[str, str]:
        self.seen_conversation_ids.append(conversation_id)
        return {"execution_status": "running", "sandbox_status": "running"}


class WorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = WorkflowConfig(
            source_repo="acme/shared-lib",
            dependency_name="@acme/shared-lib",
            dependency_graph={
                "acme/service-a": ["acme/shared-lib"],
                "acme/service-b": ["acme/shared-lib", "other-lib"],
                "acme/service-c": ["other-lib"],
            },
            upstream_change=UpstreamChange(
                summary="Renamed LegacyClient to ApiClient",
                old_version="2.3.1",
                new_version="2.4.0",
                usage_notes=["Rename LegacyClient imports to ApiClient if needed."],
            ),
            repositories={
                "acme/service-a": RepoTarget(
                    name="acme/service-a",
                    selected_repository="acme/service-a",
                    selected_branch="main",
                    dependency_hints=["package.json", "src/client.ts"],
                    validation_commands=["npm test"],
                )
            },
        )

    def test_resolve_direct_dependents_infers_from_graph(self) -> None:
        self.assertEqual(
            resolve_direct_dependents(self.config),
            ["acme/service-a", "acme/service-b"],
        )

    def test_build_branch_name_slugifies_dependency_and_version(self) -> None:
        self.assertEqual(
            build_branch_name(self.config),
            "deps/propagate/acme-shared-lib-2-4-0",
        )

    def test_render_prompt_includes_required_sections(self) -> None:
        repo = self.config.repositories["acme/service-a"]
        prompt = render_prompt(
            self.config,
            repo,
            branch_name="deps/propagate/acme-shared-lib-2-4-0",
            pr_title=build_pr_title(self.config),
        )
        self.assertIn("Open a pull request", prompt)
        self.assertIn("npm test", prompt)
        self.assertIn("@acme/shared-lib", prompt)
        self.assertIn("ApiClient", prompt)

    def test_normalize_start_response_polls_when_conversation_id_missing(self) -> None:
        client = FakeClient()
        task_id, conversation_id, task = _normalize_start_response(
            response={"id": "task-1"},
            client=client,
            timeout_s=123,
        )
        self.assertEqual(task_id, "task-1")
        self.assertEqual(conversation_id, "conv-123")
        self.assertEqual(task["status"], "READY")
        self.assertEqual(client.seen_task_ids, ["task-1"])

    def test_start_workflow_dry_run_requires_no_api_key(self) -> None:
        self.config.dry_run = True
        runs = start_workflow(self.config)
        self.assertEqual([run.status for run in runs], ["dry_run", "failed"])
        self.assertTrue(runs[0].prompt)
        self.assertIn("Missing repository configuration", runs[1].message)

    def test_client_from_env_loads_dotenv(self) -> None:
        original_cloud = os.environ.pop("OPENHANDS_CLOUD_API_KEY", None)
        original_legacy = os.environ.pop("OPENHANDS_API_KEY", None)
        cwd = Path.cwd()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                (temp_path / ".env").write_text("OPENHANDS_CLOUD_API_KEY='demo-key'\n", encoding="utf-8")
                os.chdir(temp_path)
                client = OpenHandsV1Client.from_env(base_url="https://example.com")
                self.assertEqual(client.api_key, "demo-key")
                self.assertEqual(client.base_url, "https://example.com")
        finally:
            os.chdir(cwd)
            if original_cloud is None:
                os.environ.pop("OPENHANDS_CLOUD_API_KEY", None)
            else:
                os.environ["OPENHANDS_CLOUD_API_KEY"] = original_cloud
            if original_legacy is None:
                os.environ.pop("OPENHANDS_API_KEY", None)
            else:
                os.environ["OPENHANDS_API_KEY"] = original_legacy



    def test_status_workflow_refreshes_report(self) -> None:
        client = FakeClient()
        run = ConversationRun(
            repo_name="acme/service-a",
            selected_repository="acme/service-a",
            selected_branch="main",
            branch_name="deps/propagate/acme-shared-lib-2-4-0",
            title="Propagate @acme/shared-lib 2.4.0 to acme/service-a",
            prompt="hello",
            app_conversation_id="conv-123",
            conversation_url="https://app.all-hands.dev/conversations/conv-123",
            status="started",
            message="Conversation started.",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            report = Path(temp_dir) / "report.json"
            report.write_text(json.dumps([asdict(run)]), encoding="utf-8")
            refreshed = status_workflow(report, client=client)
        self.assertEqual(refreshed[0].execution_status, "running")
        self.assertEqual(refreshed[0].sandbox_status, "running")
        self.assertEqual(client.seen_conversation_ids, ["conv-123"])

    def test_status_workflow_dry_run_report_requires_no_api_key(self) -> None:
        run = ConversationRun(
            repo_name="acme/service-a",
            selected_repository="acme/service-a",
            selected_branch="main",
            branch_name="deps/propagate/acme-shared-lib-2-4-0",
            title="Propagate @acme/shared-lib 2.4.0 to acme/service-a",
            prompt="hello",
            status="dry_run",
            message="Prompt rendered; no conversation started because dry_run=true.",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            report = Path(temp_dir) / "report.json"
            report.write_text(json.dumps([asdict(run)]), encoding="utf-8")
            refreshed = status_workflow(report)
        self.assertEqual(refreshed[0].status, "dry_run")
        self.assertIsNone(refreshed[0].app_conversation_id)


if __name__ == "__main__":
    unittest.main()
