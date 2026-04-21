from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from dep_propagator.demo import bootstrap_demo_bundle, verify_demo_bundle


class DemoBundleTestCase(unittest.TestCase):
    def test_bootstrap_demo_bundle_creates_expected_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = bootstrap_demo_bundle(Path(temp_dir) / "bundle", owner="octocat")
            payload = json.loads(result.config_path.read_text(encoding="utf-8"))

            self.assertEqual(payload["source_repo"], "octocat/demo-shared-lib")
            self.assertEqual(payload["dependency_name"], "@octocat/demo-shared-lib")
            self.assertTrue((result.bundle_dir / "repos" / "demo-service-a" / "src" / "client.ts").exists())
            self.assertTrue((result.bundle_dir / "repos" / "demo-service-b" / "src" / "service.ts").exists())
            self.assertTrue((result.bundle_dir / "repos" / "demo-service-c" / "package.json").exists())

    @unittest.skipUnless(shutil.which("node"), "node is required for demo bundle verification")
    def test_verify_demo_bundle_runs_repo_checks_and_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = bootstrap_demo_bundle(Path(temp_dir) / "bundle", owner="octocat")
            verification = verify_demo_bundle(result.bundle_dir)

        self.assertEqual(
            verification.direct_dependents,
            ["octocat/demo-service-a", "octocat/demo-service-b"],
        )
        self.assertEqual(verification.run_statuses["octocat/demo-service-a"], "dry_run")
        self.assertEqual(verification.run_statuses["octocat/demo-service-b"], "dry_run")
        self.assertIn("demo-service-a test passed", verification.repo_test_outputs["demo-service-a"])
        self.assertIn("demo-service-b test passed", verification.repo_test_outputs["demo-service-b"])
        self.assertIn("demo-service-c test passed", verification.repo_test_outputs["demo-service-c"])

    @unittest.skipUnless(shutil.which("node"), "node is required for demo bundle verification")
    def test_service_test_script_accepts_post_propagation_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = bootstrap_demo_bundle(Path(temp_dir) / "bundle", owner="octocat")
            repo_path = result.repo_paths["demo-service-a"]
            package_path = repo_path / "package.json"
            package_payload = json.loads(package_path.read_text(encoding="utf-8"))
            package_payload["dependencies"]["@octocat/demo-shared-lib"] = "1.1.0"
            package_path.write_text(json.dumps(package_payload, indent=2) + "\n", encoding="utf-8")
            (repo_path / "src" / "client.ts").write_text(
                "import { ApiClient } from '@octocat/demo-shared-lib';\n\n"
                "export function fetchMessage(): string {\n"
                "  return new ApiClient().getMessage();\n"
                "}\n",
                encoding="utf-8",
            )

            completed = subprocess.run(
                ["node", "test.js"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
            )

        self.assertIn("demo-service-a test passed", completed.stdout)

    @unittest.skipUnless(shutil.which("node"), "node is required for demo bundle verification")
    def test_cli_demo_bootstrap_and_verify(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_path = Path(temp_dir) / "bundle"
            bootstrap = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "dep_propagator",
                    "demo-bootstrap",
                    "--owner",
                    "octocat",
                    "--output",
                    str(bundle_path),
                ],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True,
            )
            verify = subprocess.run(
                [sys.executable, "-m", "dep_propagator", "demo-verify", str(bundle_path)],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True,
            )

        self.assertIn("Created demo bundle", bootstrap.stdout)
        self.assertIn("Verified demo bundle", verify.stdout)
        self.assertIn("octocat/demo-service-a", verify.stdout)
