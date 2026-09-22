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
        with mock.patch.object(
            VALIDATOR,
            "verify_selection_cryptography",
            side_effect=VALIDATOR.ValidationError("cryptographic verification failed"),
        ):
            with self.assertRaisesRegex(VALIDATOR.ValidationError, "cryptographic verification failed"):
                VALIDATOR.validate_selection(selected, self.evidence)

    def test_editable_passed_statuses_do_not_bypass_cryptography(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["candidate"]["signature"]["status"] = "passed"
        evidence["candidate"]["provenance"]["status"] = "passed"
        evidence["candidate"]["rollback"] |= {"status": "passed", "knownGoodEvidenceId": "previous"}
        evidence["productIntent"]["status"] = "approved"
        for category in VALIDATOR.MANDATORY_EVIDENCE:
            evidence["evidence"][category] |= {"status": "passed", "artifacts": ["reviewed.json"]}
        selected = {
            "evidenceId": evidence["evidenceId"],
            "tag": evidence["candidate"]["tag"],
            "url": evidence["candidate"]["url"],
            "sha256": evidence["candidate"]["sha256"],
        }
        with mock.patch.object(
            VALIDATOR,
            "verify_selection_cryptography",
            side_effect=VALIDATOR.ValidationError("bad detached signature"),
        ) as verification:
            with self.assertRaisesRegex(VALIDATOR.ValidationError, "bad detached signature"):
                VALIDATOR.validate_selection(selected, evidence)
        verification.assert_called_once_with(selected, evidence)

    def test_wrong_detached_signature_identity_is_rejected(self) -> None:
        selected = self.selection_for(self.evidence)
        hashes = [
            selected["sha256"],
            self.evidence["candidate"]["signature"]["sha256"],
            VALIDATOR.TRUSTED_KEY_SHA256,
        ]
        key_details = subprocess_result(
            0,
            f"fpr:::::::::{VALIDATOR.TRUSTED_PRIMARY_FINGERPRINT}:\n"
            f"fpr:::::::::{VALIDATOR.TRUSTED_SIGNING_FINGERPRINT}:\n",
        )
        wrong_signature = subprocess_result(
            0,
            "[GNUPG:] VALIDSIG 0000000000000000000000000000000000000000 2026-09-01 1788272737 0 4 0 1 10 00 "
            f"{VALIDATOR.TRUSTED_PRIMARY_FINGERPRINT}\n",
        )
        with (
            mock.patch.object(VALIDATOR, "download"),
            mock.patch.object(VALIDATOR, "sha256", side_effect=hashes),
            mock.patch.object(
                VALIDATOR,
                "run_checked",
                side_effect=[key_details, subprocess_result(0), wrong_signature],
            ),
        ):
            with self.assertRaisesRegex(VALIDATOR.ValidationError, "pinned trusted signing key"):
                VALIDATOR.verify_selection_cryptography(selected, self.evidence)

    def test_downloaded_bundle_digest_must_match_selection(self) -> None:
        selected = self.selection_for(self.evidence)
        with (
            mock.patch.object(VALIDATOR, "download"),
            mock.patch.object(VALIDATOR, "sha256", return_value="0" * 64),
        ):
            with self.assertRaisesRegex(VALIDATOR.ValidationError, "bundle digest"):
                VALIDATOR.verify_selection_cryptography(selected, self.evidence)

    def test_verified_tag_object_must_match_recorded_provenance(self) -> None:
        selected = self.selection_for(self.evidence)
        hashes = [
            selected["sha256"],
            self.evidence["candidate"]["signature"]["sha256"],
            VALIDATOR.TRUSTED_KEY_SHA256,
        ]
        key_details = subprocess_result(
            0,
            f"fpr:::::::::{VALIDATOR.TRUSTED_PRIMARY_FINGERPRINT}:\n"
            f"fpr:::::::::{VALIDATOR.TRUSTED_SIGNING_FINGERPRINT}:\n",
        )
        valid_signature = subprocess_result(
            0,
            f"[GNUPG:] VALIDSIG {VALIDATOR.TRUSTED_SIGNING_FINGERPRINT} 2026-09-01 1788272737 0 4 0 1 10 00 "
            f"{VALIDATOR.TRUSTED_PRIMARY_FINGERPRINT}\n",
        )
        command_results = [
            key_details,
            subprocess_result(0),
            valid_signature,
            subprocess_result(0),
            subprocess_result(0),
            subprocess_result(0),
            subprocess_result(0, "b" * 40 + "\n"),
            subprocess_result(0, self.evidence["candidate"]["provenance"]["commitSha"] + "\n"),
        ]
        with (
            mock.patch.object(VALIDATOR, "download"),
            mock.patch.object(VALIDATOR, "sha256", side_effect=hashes),
            mock.patch.object(VALIDATOR, "run_checked", side_effect=command_results),
        ):
            with self.assertRaisesRegex(VALIDATOR.ValidationError, "tag object SHA"):
                VALIDATOR.verify_selection_cryptography(selected, self.evidence)

    def test_verified_tag_commit_must_match_recorded_provenance(self) -> None:
        selected = self.selection_for(self.evidence)
        hashes = [
            selected["sha256"],
            self.evidence["candidate"]["signature"]["sha256"],
            VALIDATOR.TRUSTED_KEY_SHA256,
        ]
        key_details = subprocess_result(
            0,
            f"fpr:::::::::{VALIDATOR.TRUSTED_PRIMARY_FINGERPRINT}:\n"
            f"fpr:::::::::{VALIDATOR.TRUSTED_SIGNING_FINGERPRINT}:\n",
        )
        valid_signature = subprocess_result(
            0,
            f"[GNUPG:] VALIDSIG {VALIDATOR.TRUSTED_SIGNING_FINGERPRINT} 2026-09-01 1788272737 0 4 0 1 10 00 "
            f"{VALIDATOR.TRUSTED_PRIMARY_FINGERPRINT}\n",
        )
        command_results = [
            key_details,
            subprocess_result(0),
            valid_signature,
            subprocess_result(0),
            subprocess_result(0),
            subprocess_result(0),
            subprocess_result(0, self.evidence["candidate"]["provenance"]["annotatedTagSha"] + "\n"),
            subprocess_result(0, "c" * 40 + "\n"),
        ]
        with (
            mock.patch.object(VALIDATOR, "download"),
            mock.patch.object(VALIDATOR, "sha256", side_effect=hashes),
            mock.patch.object(VALIDATOR, "run_checked", side_effect=command_results),
        ):
            with self.assertRaisesRegex(VALIDATOR.ValidationError, "tag commit SHA"):
                VALIDATOR.verify_selection_cryptography(selected, self.evidence)

    def test_moving_tag_is_rejected(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["candidate"]["tag"] = "develop"
        with self.assertRaisesRegex(VALIDATOR.ValidationError, "immutable release tag"):
            VALIDATOR.validate_evidence(evidence, VALIDATOR.load_json(VALIDATOR.REQUIRED_FILES["policy"]))

    def test_empty_required_evidence_policy_is_rejected(self) -> None:
        policy = VALIDATOR.load_json(VALIDATOR.REQUIRED_FILES["policy"])
        state = VALIDATOR.load_json(VALIDATOR.REQUIRED_FILES["state"])
        path_map = VALIDATOR.load_json(VALIDATOR.REQUIRED_FILES["path_map"])
        invariants = VALIDATOR.load_json(VALIDATOR.REQUIRED_FILES["invariants"])
        policy["selection"]["requiredEvidence"] = []
        with self.assertRaisesRegex(VALIDATOR.ValidationError, "mandatory evidence categories"):
            VALIDATOR.validate_policy_semantics(policy, state, path_map, invariants)

    def test_weakened_protected_mapping_is_rejected(self) -> None:
        policy = VALIDATOR.load_json(VALIDATOR.REQUIRED_FILES["policy"])
        state = VALIDATOR.load_json(VALIDATOR.REQUIRED_FILES["state"])
        path_map = VALIDATOR.load_json(VALIDATOR.REQUIRED_FILES["path_map"])
        invariants = VALIDATOR.load_json(VALIDATOR.REQUIRED_FILES["invariants"])
        for mapping in path_map["mappings"]:
            if mapping.get("local") == "apps/desktop/seventwos.org/**":
                mapping["mode"] = "selective-review"
        with self.assertRaisesRegex(VALIDATOR.ValidationError, "path-map protection"):
            VALIDATOR.validate_policy_semantics(policy, state, path_map, invariants)

    def test_weakened_invariant_statement_is_rejected(self) -> None:
        policy = VALIDATOR.load_json(VALIDATOR.REQUIRED_FILES["policy"])
        state = VALIDATOR.load_json(VALIDATOR.REQUIRED_FILES["state"])
        path_map = VALIDATOR.load_json(VALIDATOR.REQUIRED_FILES["path_map"])
        invariants = VALIDATOR.load_json(VALIDATOR.REQUIRED_FILES["invariants"])
        invariants["invariants"][0]["statement"] = "apps/web is usually absent."
        with self.assertRaisesRegex(VALIDATOR.ValidationError, "removed or weakened"):
            VALIDATOR.validate_policy_semantics(policy, state, path_map, invariants)

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

    def test_append_only_requires_base_ref(self) -> None:
        with self.assertRaisesRegex(VALIDATOR.ValidationError, "base ref is required"):
            VALIDATOR.validate_append_only(None)

    def test_append_only_fails_closed_when_base_ledger_cannot_be_read(self) -> None:
        resolved = subprocess_result(returncode=0, stdout="a" * 40 + "\n")
        missing = subprocess_result(returncode=128, stderr="fatal: path does not exist")
        with mock.patch.object(VALIDATOR.subprocess, "run", side_effect=[resolved, missing]):
            with self.assertRaisesRegex(VALIDATOR.ValidationError, "refusing to bypass"):
                VALIDATOR.validate_append_only("base-sha")

    def test_ledger_introduction_requires_explicit_flag_and_absence_on_base(self) -> None:
        resolved = subprocess_result(returncode=0, stdout="a" * 40 + "\n")
        missing = subprocess_result(returncode=128, stderr="fatal: path does not exist")
        absent = subprocess_result(returncode=0, stdout="")
        with mock.patch.object(VALIDATOR.subprocess, "run", side_effect=[resolved, missing, absent]):
            VALIDATOR.validate_append_only("base-sha", allow_ledger_introduction=True)

    @staticmethod
    def selection_for(evidence: dict) -> dict:
        return {
            "evidenceId": evidence["evidenceId"],
            "tag": evidence["candidate"]["tag"],
            "url": evidence["candidate"]["url"],
            "sha256": evidence["candidate"]["sha256"],
        }


def subprocess_result(returncode: int, stdout: str = "", stderr: str = ""):
    return VALIDATOR.subprocess.CompletedProcess([], returncode, stdout, stderr)


if __name__ == "__main__":
    unittest.main()
