import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

MODULE_PATH = Path(__file__).with_name("validate_policy.py")
SPEC = importlib.util.spec_from_file_location("validate_policy", MODULE_PATH)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class ValidatePolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _, cls.state, cls.evidence = VALIDATOR.validate_policy_files()

    def test_repository_policy_is_valid(self) -> None:
        VALIDATOR.validate_ledger()

    def test_pending_evidence_cannot_be_selected(self) -> None:
        selected = {
            "evidenceId": self.evidence["evidenceId"],
            "tag": self.evidence["candidate"]["tag"],
            "url": self.evidence["candidate"]["url"],
            "sha256": self.evidence["candidate"]["sha256"],
        }
        with self.assertRaisesRegex(VALIDATOR.ValidationError, "signature evidence has not passed"):
            VALIDATOR.validate_selection(selected, self.evidence, VALIDATOR.load_json(VALIDATOR.REQUIRED_FILES["policy"]))

    def test_moving_tag_is_rejected(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["candidate"]["tag"] = "develop"
        with self.assertRaisesRegex(VALIDATOR.ValidationError, "immutable release tag"):
            VALIDATOR.validate_evidence(evidence, VALIDATOR.load_json(VALIDATOR.REQUIRED_FILES["policy"]))

    def test_requested_bundle_requires_selection(self) -> None:
        with self.assertRaisesRegex(VALIDATOR.ValidationError, "no upstream bundle is selected"):
            VALIDATOR.validate_requested_selection(
                self.evidence["candidate"]["url"],
                self.evidence["candidate"]["sha256"],
                self.state,
            )

    def test_ledger_rejects_rewritten_history(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "ledger.jsonl"
            ledger.write_text(
                json.dumps({"schemaVersion": 1, "sequence": 2, "eventId": "rewritten"}) + "\n",
                encoding="utf-8",
            )
            with mock.patch.dict(VALIDATOR.REQUIRED_FILES, {"ledger": ledger}):
                with self.assertRaisesRegex(VALIDATOR.ValidationError, "non-contiguous sequence"):
                    VALIDATOR.validate_ledger()


if __name__ == "__main__":
    unittest.main()
