from __future__ import annotations

import re
import unittest
from pathlib import Path


class DependencyPropagationSkillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = Path(__file__).resolve().parents[1]
        cls.skill_dir = cls.repo_root / ".agents" / "skills" / "dependency-propagation-analysis"
        cls.skill_path = cls.skill_dir / "SKILL.md"
        cls.skill_text = cls.skill_path.read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---\n(.*)$", cls.skill_text, re.DOTALL)
        if not match:
            raise AssertionError("SKILL.md is missing YAML frontmatter")
        cls.frontmatter = match.group(1)
        cls.body = match.group(2)

    def test_skill_files_exist(self) -> None:
        self.assertTrue(self.skill_dir.exists())
        self.assertTrue(self.skill_path.exists())
        self.assertTrue((self.skill_dir / "references" / "input-contract.md").exists())
        self.assertTrue((self.skill_dir / "references" / "analysis-patterns.md").exists())
        self.assertTrue((self.skill_dir / "references" / "cloud-ui-usage.md").exists())

    def test_frontmatter_contains_name_description_and_triggers(self) -> None:
        self.assertIn("name: dependency-propagation-analysis", self.frontmatter)
        self.assertIn("description:", self.frontmatter)
        self.assertIn("triggers:", self.frontmatter)
        self.assertIn('"analyze dependency impact"', self.frontmatter)
        self.assertIn('"propagate a dependency update"', self.frontmatter)

    def test_skill_body_emphasizes_direct_dependents_and_minimal_scope(self) -> None:
        self.assertIn("direct dependents only", self.body)
        self.assertIn("Keep downstream changes tightly scoped", self.body)
        self.assertIn("one PR per repo", self.body)
        self.assertIn("Prefer explicit blockers", self.body)

    def test_skill_references_existing_reference_files(self) -> None:
        referenced = re.findall(r"`(references/[^`]+)`", self.body)
        self.assertGreaterEqual(len(referenced), 3)
        for relative_path in referenced:
            self.assertTrue((self.skill_dir / relative_path).exists(), relative_path)

    def test_reference_docs_cover_inputs_patterns_and_cloud_usage(self) -> None:
        input_contract = (self.skill_dir / "references" / "input-contract.md").read_text(encoding="utf-8")
        patterns = (self.skill_dir / "references" / "analysis-patterns.md").read_text(encoding="utf-8")
        cloud_ui = (self.skill_dir / "references" / "cloud-ui-usage.md").read_text(encoding="utf-8")

        self.assertIn("candidate_repos", input_contract)
        self.assertIn("dependency_graph", input_contract)
        self.assertIn("next_action", input_contract)

        self.assertIn("Node.js / TypeScript", patterns)
        self.assertIn("Minimal-diff heuristics", patterns)
        self.assertIn("update-version-and-code", patterns)

        self.assertIn("dry-run analysis", cloud_ui)
        self.assertIn("OpenHands Cloud UI", cloud_ui)
        self.assertIn("unique branch naming suffix", cloud_ui)


if __name__ == "__main__":
    unittest.main()
