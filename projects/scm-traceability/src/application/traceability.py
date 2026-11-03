"""Evidence chains and process matrix over the SCM registry."""

import hashlib
from pathlib import Path

from .common import now, write_json
from .platform import Platform


class Traceability(Platform):
    def verify(self, baseline, root):
        base = self.get_baseline(baseline)
        root = Path(root).resolve()
        mismatches = []
        for item in base["items"]:
            path = (root / item["path"]).resolve()
            if not path.is_relative_to(root) or not path.is_file():
                mismatches.append({"item": item["id"], "reason": "missing or unsafe path"})
            elif hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
                mismatches.append({"item": item["id"], "reason": "sha256 mismatch"})
        return {"baseline": baseline, "passed": not mismatches, "mismatches": mismatches}

    def chains(self):
        result = []
        for request in self.requests():
            if request["status"] != "applied":
                continue
            matches = []
            for base in self.rows("SELECT id FROM baselines WHERE project=?", (request["project"],)):
                if any(
                    i["id"] == request["item"]
                    and i["sha256"] == request["sha256"]
                    and i["version"] == request["version"]
                    for i in self.get_baseline(base["id"])["items"]
                ):
                    matches.append(base["id"])
            result.append(
                {
                    "request": request["id"],
                    "decision": request["decision"],
                    "approver": request["approver"],
                    "commit": request["commit_hash"],
                    "baselines": matches,
                    "test": request["test"],
                }
            )
        return result

    def audit(self, output=None):
        chains = self.chains()
        events = self.rows("SELECT * FROM history WHERE event='change_applied'")
        missing = [
            c["request"] for c in chains if not c["baselines"] or not any(e["ref"] == c["request"] for e in events)
        ]
        result = {
            "time": now(),
            "passed": not missing,
            "chains": chains,
            "incomplete_requests": missing,
            "matrix": self.matrix(),
            "limitation": "Commit and test references are registered evidence; remote CI is verified separately.",
        }
        if output:
            write_json(output, result)
        return result

    def matrix(self):
        return [
            {
                "process": "Identification",
                "scmp": "SCMP 3",
                "function": "item/items",
                "test": "test_item_registration",
                "evidence": "items + item_versions",
                "status": "implemented",
                "limitation": "content hashes; no binary artifact repository",
            },
            {
                "process": "Change control",
                "scmp": "SCMP 4",
                "function": "request/decide/apply",
                "test": "test_unapproved_change",
                "evidence": "requests + history",
                "status": "partial",
                "limitation": "local approver role, no authentication or separation of duties",
            },
            {
                "process": "Baseline",
                "scmp": "SCMP 5",
                "function": "baseline/verify",
                "test": "test_baseline_detects_change",
                "evidence": "baselines + verification.json",
                "status": "implemented",
                "limitation": "SQLite triggers do not protect against a database administrator",
            },
            {
                "process": "Status accounting",
                "scmp": "SCMP 6",
                "function": "chains/report",
                "test": "test_chain",
                "evidence": "traceability.json",
                "status": "implemented",
                "limitation": "test identifiers are references, not signed attestations",
            },
            {
                "process": "Audit",
                "scmp": "SCMP 7",
                "function": "audit/verify",
                "test": "test_incomplete_chain",
                "evidence": "audit.json",
                "status": "partial",
                "limitation": "internal checks only, no independent external audit",
            },
            {
                "process": "Release",
                "scmp": "SCMP 8",
                "function": "release",
                "test": "test_release",
                "evidence": "releases + Git tag",
                "status": "partial",
                "limitation": "release registry; no production deployment",
            },
            {
                "process": "Formal certification",
                "scmp": "SCMP 1",
                "function": "none",
                "test": "not applicable",
                "evidence": "scope statement",
                "status": "not implemented",
                "limitation": "out of scope",
            },
        ]
