#!/usr/bin/env python3

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def upstream_develop_sha() -> str:
    result = subprocess.run(
        ["git", "ls-remote", "https://github.com/element-hq/element-web.git", "refs/heads/develop"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.split()[0]


def main() -> int:
    parser = argparse.ArgumentParser(description="Produce a read-only upstream assessment report")
    parser.add_argument("--output", type=Path, help="Optional report path")
    args = parser.parse_args()

    state = json.loads((ROOT / ".seventwos/upstream-state.json").read_text(encoding="utf-8"))
    evidence_path = ROOT / state["baselineCandidateEvidence"]
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    report = {
        "schemaVersion": 1,
        "mode": "report-only",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "upstream": {
            "repository": "element-hq/element-web",
            "branch": "develop",
            "observedCommit": upstream_develop_sha(),
        },
        "repositoryBase": state["repositoryBase"],
        "selectedBundle": state["selectedBundle"],
        "baselineCandidate": {
            "evidenceId": evidence["evidenceId"],
            "tag": evidence["candidate"]["tag"],
            "selectionStatus": evidence["selection"]["status"],
            "blockers": evidence["selection"]["blockers"],
        },
        "actions": {
            "changesApplied": False,
            "bundleSelectionModified": False,
            "mergeAttempted": False,
        },
    }
    rendered = json.dumps(report, indent=2) + "\n"
    print(rendered, end="")
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
