import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/desktop-validation.yaml"


class DesktopValidationWorkflowTests(unittest.TestCase):
    def test_resolved_electron_is_installed_before_parallel_unit_tests(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        install = workflow.index(
            "run: pnpm install --frozen-lockfile --filter seventwos-workspace-desktop"
        )
        prepare = workflow.index(
            "run: pnpm --filter seventwos-workspace-desktop exec install-electron"
        )
        tests = workflow.index(
            "run: pnpm --filter seventwos-workspace-desktop test:unit --run"
        )
        self.assertLess(install, prepare)
        self.assertLess(prepare, tests)
        step = workflow[:prepare].rsplit("            - name:", 1)[1]
        self.assertNotIn("if:", step)
        self.assertNotIn("continue-on-error:", step)
        self.assertNotIn("--maxWorkers", workflow)
        self.assertNotIn("--no-file-parallelism", workflow)


if __name__ == "__main__":
    unittest.main()
