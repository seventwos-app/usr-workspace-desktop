import os
import subprocess
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/upstream-assessment.yml"


class AssessmentWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.triggers = cls.workflow.split("\non:\n", 1)[1].split("\npermissions:", 1)[0]
        step = cls.workflow.split("            - name: Validate selective upstream policy\n", 1)[1]
        script = step.split("              run: |\n", 1)[1].split("\n            - name:", 1)[0]
        cls.base_script = textwrap.dedent(script).split("python3 scripts/upstream/validate_policy.py", 1)[0]

    def test_required_check_runs_for_all_develop_pull_requests(self) -> None:
        self.assertRegex(self.triggers, r"(?m)^    pull_request:\n        branches:\n            - develop$")
        self.assertNotRegex(self.triggers, r"(?m)^\s+(paths|paths-ignore):")
        self.assertNotRegex(self.workflow, r"(?m)^\s+if:")
        self.assertIn("name: Validate policy and report upstream tip", self.workflow)

    def test_merge_queue_requests_run_the_same_check(self) -> None:
        self.assertRegex(self.triggers, r"(?m)^    merge_group:\n        types:\n            - checks_requested$")

    def test_manual_and_weekly_assessments_remain_available(self) -> None:
        self.assertIn("    workflow_dispatch: {}", self.triggers)
        self.assertIn('    schedule:\n        - cron: "17 6 * * 1"', self.triggers)

    def resolve_base(self, event: str, pr_base: str = "", merge_base: str = "") -> subprocess.CompletedProcess:
        return subprocess.run(
            ["bash", "-e", "-c", self.base_script + 'printf "%s" "$BASE_REF"'],
            cwd=ROOT,
            env=os.environ | {
                "EVENT_NAME": event,
                "PR_BASE_SHA": pr_base,
                "MERGE_GROUP_BASE_SHA": merge_base,
            },
            text=True,
            capture_output=True,
        )

    def test_pull_request_and_merge_group_use_their_event_base(self) -> None:
        for event, expected in [("pull_request", "a" * 40), ("merge_group", "b" * 40)]:
            with self.subTest(event=event):
                result = self.resolve_base(event, pr_base="a" * 40, merge_base="b" * 40)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, expected)

    def test_missing_event_base_fails_closed(self) -> None:
        for event in ["pull_request", "merge_group"]:
            with self.subTest(event=event):
                self.assertNotEqual(self.resolve_base(event).returncode, 0)

    def test_non_pr_assessments_keep_the_previous_commit_baseline(self) -> None:
        expected = subprocess.check_output(["git", "rev-parse", "HEAD^"], cwd=ROOT, text=True).strip()
        for event in ["workflow_dispatch", "schedule"]:
            with self.subTest(event=event):
                result = self.resolve_base(event)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, expected)


if __name__ == "__main__":
    unittest.main()
