#!/usr/bin/env python3

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[2]
POLICY_DIR = ROOT / ".seventwos"
HEX_40 = re.compile(r"^[0-9a-f]{40}$")
HEX_64 = re.compile(r"^[0-9a-f]{64}$")
MANDATORY_EVIDENCE = (
    "capabilityDenial",
    "networkDestinations",
    "visual",
    "existingProfileMigration",
)
MANDATORY_MAPPINGS = (
    ("apps/web/**", None, "forbidden"),
    ("apps/desktop/**", "apps/desktop/**", "selective-review"),
    ("packages/**", "packages/**", "selective-review"),
    ("modules/**", "modules/**", "protected-divergence"),
    (".github/workflows/**", ".github/workflows/**", "protected-divergence"),
    ("none", "apps/desktop/seventwos.org/**", "protected-divergence"),
    ("none", ".seventwos/**", "protected-divergence"),
)
MANDATORY_INVARIANTS = {
    "no-apps-web": "apps/web must remain absent from the repository.",
    "immutable-bundle-only": "A selected bundle must use an immutable release tag, exact HTTPS URL, and SHA-256 digest.",
    "verified-selection-evidence": "Signature, provenance, rollback, capability-denial, network-destination, visual, and existing-profile migration evidence must pass before selection.",
    "protect-seventwos-divergence": "Seventwos UI, product, auth, storage, profile migration, configuration, and release paths require repository ownership review.",
    "assessment-only": "Upstream assessment automation may report candidates but may not apply changes, merge, publish, or update bundle selection.",
    "append-only-ledger": "Existing upstream ledger entries may not be edited, reordered, or removed.",
}
UPSTREAM_REPOSITORY = "element-hq/element-web"
UPSTREAM_URL = "https://github.com/element-hq/element-web"
BUNDLE_URL_PREFIX = f"{UPSTREAM_URL}/releases/download/"
TRUSTED_KEY_URL = "https://packages.riot.im/element-release-key.asc"
TRUSTED_KEY_SHA256 = "b6683a2383d6dd34ab571622c90e71fb05451af4310421ec15327a8b04347b98"
TRUSTED_PRIMARY_FINGERPRINT = "712BFBEE92DCA45252DB17D7C7BE97EFA179B100"
TRUSTED_SIGNING_FINGERPRINT = "E95B7699E80B68A9EAD9A19A2BAA9B8552BD9047"
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
    validate_policy_semantics(policy, state, path_map, invariants)

    evidence_path = ROOT / state.get("baselineCandidateEvidence", "")
    require(evidence_path.is_file() and evidence_path.is_relative_to(POLICY_DIR / "evidence"), "baseline candidate evidence must be under .seventwos/evidence")
    evidence = load_json(evidence_path)
    validate_evidence(evidence, policy)

    selected = state.get("selectedBundle")
    if selected is not None:
        validate_selection(selected, evidence)
        require(state.get("humanReview", {}).get("status") == "approved", "selected bundle requires approved human review")

    validate_ledger()
    return policy, state, evidence


def validate_policy_semantics(policy: dict, state: dict, path_map: dict, invariants: dict) -> None:
    require(state.get("policyId") == policy.get("policyId"), "state policyId does not match policy")
    require(policy.get("integrationModel") == "desktop-shell-plus-separately-pinned-element-web-bundle", "unexpected integration model")
    require(policy.get("upstream", {}).get("repository") == UPSTREAM_REPOSITORY, "upstream repository is not the pinned Element Web repository")
    require(policy.get("upstream", {}).get("sourceUrl") == UPSTREAM_URL, "upstream source URL is not pinned")
    require(policy.get("upstream", {}).get("bundleReleaseUrlPrefix") == BUNDLE_URL_PREFIX, "bundle release URL prefix is not pinned")
    require(
        {"develop", "main", "master", "latest", "nightly"}
        <= set(policy.get("selection", {}).get("movingRefsForbidden", ())),
        "moving bundle references must remain forbidden",
    )
    require(tuple(policy.get("selection", {}).get("requiredEvidence", ())) == MANDATORY_EVIDENCE, "mandatory evidence categories may not be changed")
    require(policy.get("selection", {}).get("humanApprovalRequired") is True, "human approval must remain mandatory")
    require(policy.get("protectedDivergence", {}).get("pathMap") == ".seventwos/upstream-path-map.json", "protected divergence must use the pinned path map")
    require(policy.get("protectedDivergence", {}).get("codeowners") == "CODEOWNERS", "protected divergence must require CODEOWNERS")
    require(policy.get("ledger", {}).get("path") == ".seventwos/upstream-ledger.jsonl", "ledger path must remain pinned")
    require(policy.get("ledger", {}).get("appendOnly") is True, "ledger must remain append-only")
    require(not (ROOT / "apps" / "web").exists(), "apps/web must remain absent")

    mappings = path_map.get("mappings")
    require(isinstance(mappings, list), "path-map mappings must be an array")
    actual_mappings = {(item.get("upstream"), item.get("local"), item.get("mode")) for item in mappings}
    require(set(MANDATORY_MAPPINGS) <= actual_mappings, "mandatory path-map protection was removed or weakened")

    actual_invariants = {
        item.get("id"): item
        for item in invariants.get("invariants", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    for invariant_id, statement in MANDATORY_INVARIANTS.items():
        invariant = actual_invariants.get(invariant_id, {})
        require(
            invariant.get("severity") == "error" and invariant.get("statement") == statement,
            f"mandatory invariant {invariant_id} was removed or weakened",
        )


def validate_evidence(evidence: dict, policy: dict) -> None:
    require(evidence.get("schemaVersion") == 1, "unsupported evidence schemaVersion")
    require(evidence.get("immutable") is True, "baseline evidence must be immutable")
    candidate = evidence.get("candidate")
    require(isinstance(candidate, dict), "evidence candidate must be an object")

    tag = candidate.get("tag")
    url = candidate.get("url")
    digest = candidate.get("sha256")
    forbidden = {"develop", "main", "master", "latest", "nightly"}
    require(isinstance(tag, str) and tag not in forbidden and tag.startswith("v"), "candidate tag must be an immutable release tag")
    require(isinstance(url, str) and url.startswith(BUNDLE_URL_PREFIX), "candidate URL must be an upstream HTTPS release URL")
    require(urlparse(url).scheme == "https" and f"/download/{tag}/" in url, "candidate URL must embed the exact release tag")
    require(isinstance(digest, str) and HEX_64.fullmatch(digest) is not None, "candidate sha256 must be lowercase hexadecimal")

    signature = candidate.get("signature")
    provenance = candidate.get("provenance")
    rollback = candidate.get("rollback")
    require(isinstance(signature, dict) and HEX_64.fullmatch(signature.get("sha256", "")) is not None, "signature metadata and digest are required")
    require(signature.get("url") == f"{url}.asc", "detached signature URL must match the exact bundle URL")
    require(signature.get("keyUrl") == TRUSTED_KEY_URL, "signature key URL is not pinned")
    require(signature.get("keySha256") == TRUSTED_KEY_SHA256, "signature key digest is not pinned")
    require(isinstance(provenance, dict) and HEX_40.fullmatch(provenance.get("commitSha", "")) is not None, "provenance commit SHA is required")
    require(isinstance(provenance.get("annotatedTagSha"), str) and HEX_40.fullmatch(provenance["annotatedTagSha"]) is not None, "annotated tag SHA is required")
    require(isinstance(rollback, dict) and rollback.get("strategy"), "rollback strategy is required")

    actual_evidence = evidence.get("evidence")
    require(isinstance(actual_evidence, dict) and set(MANDATORY_EVIDENCE) <= set(actual_evidence), "required evidence categories are missing")
    for category in MANDATORY_EVIDENCE:
        require(actual_evidence[category].get("status") in {"pending", "passed", "failed"}, f"invalid {category} evidence status")

    product_intent = evidence.get("productIntent", {})
    require(product_intent.get("status") in {"unknown", "approved", "rejected"}, "invalid product intent status")
    if product_intent.get("status") == "unknown":
        require(product_intent.get("humanReviewRequired") is True, "unknown product intent must require human review")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, destination: Path) -> None:
    try:
        with urlopen(url, timeout=60) as response, destination.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
    except OSError as error:
        raise ValidationError(f"failed to download cryptographic verification input: {url}: {error}") from error


def run_checked(command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, cwd=cwd or ROOT, env=env, text=True, capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError) as error:
        detail = error.stderr.strip() if isinstance(error, subprocess.CalledProcessError) and error.stderr else str(error)
        raise ValidationError(f"cryptographic verification command failed: {' '.join(command)}: {detail}") from error


def verify_selection_cryptography(selected: dict, evidence: dict) -> None:
    candidate = evidence["candidate"]
    signature = candidate["signature"]
    provenance = candidate["provenance"]
    require(signature.get("keyUrl") == TRUSTED_KEY_URL, "signature key URL is not the pinned trusted key")
    require(signature.get("keySha256") == TRUSTED_KEY_SHA256, "signature key digest is not the pinned trusted key")

    with tempfile.TemporaryDirectory(prefix="seventwos-upstream-") as directory:
        temporary = Path(directory)
        bundle = temporary / "bundle.tar.gz"
        detached_signature = temporary / "bundle.tar.gz.asc"
        trusted_key = temporary / "trusted-key.asc"
        keyring = temporary / "gnupg"
        repository = temporary / "element-web.git"
        keyring.mkdir(mode=0o700)

        download(selected["url"], bundle)
        download(signature["url"], detached_signature)
        download(TRUSTED_KEY_URL, trusted_key)
        require(sha256(bundle) == selected["sha256"], "downloaded bundle digest does not match selection")
        require(sha256(detached_signature) == signature["sha256"], "downloaded signature digest does not match evidence")
        require(sha256(trusted_key) == TRUSTED_KEY_SHA256, "downloaded trusted key digest does not match pin")

        environment = os.environ | {"GNUPGHOME": str(keyring)}
        key_details = run_checked(["gpg", "--batch", "--with-colons", "--show-keys", "--fingerprint", str(trusted_key)], env=environment)
        fingerprints = {line.split(":")[9] for line in key_details.stdout.splitlines() if line.startswith("fpr:")}
        require(TRUSTED_PRIMARY_FINGERPRINT in fingerprints, "trusted key primary fingerprint does not match pin")
        require(TRUSTED_SIGNING_FINGERPRINT in fingerprints, "trusted key signing fingerprint does not match pin")
        run_checked(["gpg", "--batch", "--import-options", "import-minimal", "--import", str(trusted_key)], env=environment)
        verification = run_checked(
            ["gpg", "--batch", "--status-fd", "1", "--verify", str(detached_signature), str(bundle)],
            env=environment,
        )
        valid_signatures = [line.split() for line in verification.stdout.splitlines() if line.startswith("[GNUPG:] VALIDSIG ")]
        require(
            any(
                fields[2] == TRUSTED_SIGNING_FINGERPRINT
                and len(fields) >= 12
                and fields[-1] == TRUSTED_PRIMARY_FINGERPRINT
                for fields in valid_signatures
            ),
            "bundle detached signature was not made by the pinned trusted signing key",
        )

        run_checked(["git", "init", "--bare", str(repository)])
        tag = selected["tag"]
        run_checked(
            ["git", "fetch", "--no-tags", UPSTREAM_URL, f"refs/tags/{tag}:refs/tags/{tag}"],
            cwd=repository,
            env=environment,
        )
        run_checked(["git", "verify-tag", tag], cwd=repository, env=environment)
        tag_sha = run_checked(["git", "rev-parse", f"{tag}^{{tag}}"], cwd=repository, env=environment).stdout.strip()
        commit_sha = run_checked(["git", "rev-parse", f"{tag}^{{commit}}"], cwd=repository, env=environment).stdout.strip()
        require(tag_sha == provenance["annotatedTagSha"], "verified upstream tag object SHA does not match evidence")
        require(commit_sha == provenance["commitSha"], "verified upstream tag commit SHA does not match evidence")


def validate_selection(selected: dict, evidence: dict) -> None:
    candidate = evidence["candidate"]
    for field in ("tag", "url", "sha256"):
        require(selected.get(field) == candidate.get(field), f"selected bundle {field} must match its evidence")
    require(selected.get("evidenceId") == evidence.get("evidenceId"), "selected bundle must reference its evidence ID")
    verify_selection_cryptography(selected, evidence)
    require(candidate["rollback"].get("status") == "passed", "selected bundle rollback evidence has not passed")
    require(candidate["rollback"].get("knownGoodEvidenceId"), "selected bundle rollback must name known-good evidence")
    for category in MANDATORY_EVIDENCE:
        require(evidence["evidence"][category].get("status") == "passed", f"selected bundle {category} evidence has not passed")
        require(evidence["evidence"][category].get("artifacts"), f"selected bundle {category} evidence must contain artifacts")
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


def validate_append_only(base_ref: str | None, allow_ledger_introduction: bool = False) -> None:
    require(bool(base_ref), "a base ref is required for append-only validation")
    base_commit = subprocess.run(
        ["git", "rev-parse", "--verify", f"{base_ref}^{{commit}}"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    require(base_commit.returncode == 0, f"cannot resolve append-only base ref {base_ref}")
    result = subprocess.run(
        ["git", "show", f"{base_ref}:.seventwos/upstream-ledger.jsonl"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        require(allow_ledger_introduction, "cannot read ledger from base ref; refusing to bypass append-only validation")
        tree = subprocess.run(
            ["git", "ls-tree", "--name-only", base_ref, ".seventwos/upstream-ledger.jsonl"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        require(tree.returncode == 0 and not tree.stdout.strip(), "ledger introduction is allowed only when the base has no ledger")
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
    parser.add_argument("--allow-ledger-introduction", action="store_true", help="Allow the ledger only when a valid base ref has no ledger")
    parser.add_argument("--selection-url", help="Bundle URL requested by packaging")
    parser.add_argument("--selection-sha256", help="Bundle SHA-256 requested by packaging")
    args = parser.parse_args()

    try:
        _, state, _ = validate_policy_files()
        if args.base_ref or args.allow_ledger_introduction:
            validate_append_only(args.base_ref, args.allow_ledger_introduction)
        validate_requested_selection(args.selection_url, args.selection_sha256, state)
    except ValidationError as error:
        print(f"upstream policy validation failed: {error}", file=sys.stderr)
        return 1

    print("upstream policy validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
