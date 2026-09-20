#!/usr/bin/env python3

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
POLICY_DIR = ROOT / ".seventwos"
HEX_40 = re.compile(r"^[0-9a-f]{40}$")
HEX_64 = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_FILES = {
    "policy": POLICY_DIR / "upstream-policy.json",
    "state": POLICY_DIR / "upstream-state.json",
    "path_map": POLICY_DIR / "upstream-path-map.json",
    "invariants": POLICY_DIR / "upstream-invariants.json",
    "ledger": POLICY_DIR / "upstream-ledger.jsonl",
}


class ValidationError(Exception):
    pass


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValidationError(f"{path.relative_to(ROOT)}: {error}") from error
    if not isinstance(value, dict):
        raise ValidationError(f"{path.relative_to(ROOT)} must contain a JSON object")
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def validate_policy_files() -> tuple[dict, dict, dict]:
    for path in REQUIRED_FILES.values():
        require(path.is_file(), f"missing required policy file: {path.relative_to(ROOT)}")

    policy = load_json(REQUIRED_FILES["policy"])
    state = load_json(REQUIRED_FILES["state"])
    path_map = load_json(REQUIRED_FILES["path_map"])
    invariants = load_json(REQUIRED_FILES["invariants"])

    require(policy.get("schemaVersion") == 1, "unsupported upstream policy schemaVersion")
    require(state.get("schemaVersion") == 1, "unsupported upstream state schemaVersion")
    require(path_map.get("schemaVersion") == 1, "unsupported upstream path-map schemaVersion")
    require(invariants.get("schemaVersion") == 1, "unsupported upstream invariants schemaVersion")
    require(state.get("policyId") == policy.get("policyId"), "state policyId does not match policy")
    require(policy.get("integrationModel") == "desktop-shell-plus-separately-pinned-element-web-bundle", "unexpected integration model")
    require(not (ROOT / "apps" / "web").exists(), "apps/web must remain absent")

    mappings = path_map.get("mappings")
    require(isinstance(mappings, list), "path-map mappings must be an array")
    require(
        any(item.get("upstream") == "apps/web/**" and item.get("mode") == "forbidden" and item.get("local") is None for item in mappings),
        "path-map must forbid apps/web",
    )
    require(
        any(item.get("local") == "apps/desktop/seventwos.org/**" and item.get("mode") == "protected-divergence" for item in mappings),
        "path-map must protect Seventwos product configuration",
    )

    required_invariants = {
        "no-apps-web",
        "immutable-bundle-only",
        "verified-selection-evidence",
        "protect-seventwos-divergence",
        "assessment-only",
        "append-only-ledger",
    }
    actual_invariants = {item.get("id") for item in invariants.get("invariants", [])}
    require(required_invariants <= actual_invariants, "required upstream invariants are missing")

    evidence_path = ROOT / state.get("baselineCandidateEvidence", "")
    require(evidence_path.is_file() and evidence_path.is_relative_to(POLICY_DIR / "evidence"), "baseline candidate evidence must be under .seventwos/evidence")
    evidence = load_json(evidence_path)
    validate_evidence(evidence, policy)

    selected = state.get("selectedBundle")
    if selected is not None:
        validate_selection(selected, evidence, policy)
        require(state.get("humanReview", {}).get("status") == "approved", "selected bundle requires approved human review")

    validate_ledger()
    return policy, state, evidence


def validate_evidence(evidence: dict, policy: dict) -> None:
    require(evidence.get("schemaVersion") == 1, "unsupported evidence schemaVersion")
    require(evidence.get("immutable") is True, "baseline evidence must be immutable")
    candidate = evidence.get("candidate")
    require(isinstance(candidate, dict), "evidence candidate must be an object")

    tag = candidate.get("tag")
    url = candidate.get("url")
    digest = candidate.get("sha256")
    forbidden = set(policy["selection"]["movingRefsForbidden"])
    require(isinstance(tag, str) and tag not in forbidden and tag.startswith("v"), "candidate tag must be an immutable release tag")
    require(isinstance(url, str) and url.startswith(policy["upstream"]["bundleReleaseUrlPrefix"]), "candidate URL must be an upstream HTTPS release URL")
    require(urlparse(url).scheme == "https" and f"/download/{tag}/" in url, "candidate URL must embed the exact release tag")
    require(isinstance(digest, str) and HEX_64.fullmatch(digest) is not None, "candidate sha256 must be lowercase hexadecimal")

    signature = candidate.get("signature")
    provenance = candidate.get("provenance")
    rollback = candidate.get("rollback")
    require(isinstance(signature, dict) and HEX_64.fullmatch(signature.get("sha256", "")) is not None, "signature metadata and digest are required")
    require(isinstance(provenance, dict) and HEX_40.fullmatch(provenance.get("commitSha", "")) is not None, "provenance commit SHA is required")
    require(isinstance(provenance.get("annotatedTagSha"), str) and HEX_40.fullmatch(provenance["annotatedTagSha"]) is not None, "annotated tag SHA is required")
    require(isinstance(rollback, dict) and rollback.get("strategy"), "rollback strategy is required")

    required_evidence = set(policy["selection"]["requiredEvidence"])
    actual_evidence = evidence.get("evidence")
    require(isinstance(actual_evidence, dict) and required_evidence <= set(actual_evidence), "required evidence categories are missing")
    for category in required_evidence:
        require(actual_evidence[category].get("status") in {"pending", "passed", "failed"}, f"invalid {category} evidence status")

    product_intent = evidence.get("productIntent", {})
    require(product_intent.get("status") in {"unknown", "approved", "rejected"}, "invalid product intent status")
    if product_intent.get("status") == "unknown":
        require(product_intent.get("humanReviewRequired") is True, "unknown product intent must require human review")


def validate_selection(selected: dict, evidence: dict, policy: dict) -> None:
    candidate = evidence["candidate"]
    for field in ("tag", "url", "sha256"):
        require(selected.get(field) == candidate.get(field), f"selected bundle {field} must match its evidence")
    require(selected.get("evidenceId") == evidence.get("evidenceId"), "selected bundle must reference its evidence ID")
    require(candidate["signature"].get("status") == "passed", "selected bundle signature evidence has not passed")
    require(candidate["provenance"].get("status") == "passed", "selected bundle provenance evidence has not passed")
    require(candidate["rollback"].get("status") == "passed", "selected bundle rollback evidence has not passed")
    for category in policy["selection"]["requiredEvidence"]:
        require(evidence["evidence"][category].get("status") == "passed", f"selected bundle {category} evidence has not passed")
    require(evidence.get("productIntent", {}).get("status") == "approved", "selected bundle product intent is not approved")


def validate_ledger() -> None:
    entries = []
    for line_number, line in enumerate(REQUIRED_FILES["ledger"].read_text(encoding="utf-8").splitlines(), start=1):
        require(line.strip() != "", f"ledger line {line_number} must not be blank")
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValidationError(f"ledger line {line_number}: {error}") from error
        require(isinstance(entry, dict), f"ledger line {line_number} must be an object")
        require(entry.get("sequence") == line_number, f"ledger line {line_number} has a non-contiguous sequence")
        require(entry.get("schemaVersion") == 1 and entry.get("eventId"), f"ledger line {line_number} is missing required identity")
        entries.append(entry)
    require(entries, "upstream ledger must contain at least one entry")
    require(len({entry["eventId"] for entry in entries}) == len(entries), "ledger event IDs must be unique")


def validate_append_only(base_ref: str | None) -> None:
    if not base_ref:
        return
    result = subprocess.run(
        ["git", "show", f"{base_ref}:.seventwos/upstream-ledger.jsonl"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return
    current = REQUIRED_FILES["ledger"].read_text(encoding="utf-8")
    require(current.startswith(result.stdout), "upstream ledger is append-only; existing bytes changed or were removed")


def validate_requested_selection(url: str | None, sha256: str | None, state: dict) -> None:
    if url is None and sha256 is None:
        return
    require(url is not None and sha256 is not None, "bundle URL and SHA-256 must be provided together")
    selected = state.get("selectedBundle")
    require(isinstance(selected, dict), "no upstream bundle is selected; complete and approve all evidence first")
    require(url == selected.get("url"), "requested bundle URL is not the selected policy bundle")
    require(sha256.lower() == selected.get("sha256"), "requested bundle digest is not the selected policy bundle")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Seventwos selective upstream policy")
    parser.add_argument("--base-ref", help="Git ref used to enforce append-only ledger history")
    parser.add_argument("--selection-url", help="Bundle URL requested by packaging")
    parser.add_argument("--selection-sha256", help="Bundle SHA-256 requested by packaging")
    args = parser.parse_args()

    try:
        _, state, _ = validate_policy_files()
        validate_append_only(args.base_ref)
        validate_requested_selection(args.selection_url, args.selection_sha256, state)
    except ValidationError as error:
        print(f"upstream policy validation failed: {error}", file=sys.stderr)
        return 1

    print("upstream policy validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
