"""Wait a bounded time for a new terminal notebook receipt without rerunning work."""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path


def snapshot(root, manifest, library_sha):
    """Read matching receipts, tolerating only absent files or concurrent JSON writes."""
    result = {}
    for jobs in manifest.values():
        for job in jobs:
            path = (root / job["id"] / job["name"]).with_suffix(".run.json")
            try:
                receipt = json.loads(path.read_text(encoding="utf-8-sig"))
            except FileNotFoundError:
                continue
            except json.JSONDecodeError:
                print(f"Receipt currently incomplete: {path}", flush=True)
                continue
            if receipt.get("library_sha256") == library_sha:
                result[job["name"]] = receipt
    return result


def main():
    """Report new completed/error receipts and actual wall time for unfinished receipts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--library-sha", required=True)
    parser.add_argument("--reviews", type=Path)
    parser.add_argument("--seconds", type=float, default=540)
    args = parser.parse_args()
    if args.seconds <= 0:
        parser.error("--seconds must be positive")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    terminal = {"completed", "error", "failed"}
    key = lambda name, receipt: (name, receipt["started_at"], receipt.get("status"))
    initial = snapshot(args.artifact_root, manifest, args.library_sha)
    baseline = {key(name, r) for name, r in initial.items() if r.get("status") in terminal}
    if args.reviews:
        reviews = json.loads(args.reviews.read_text(encoding="utf-8"))
        baseline = {
            key(name, r) for name, r in initial.items()
            if reviews.get(Path(name).stem, {}).get("decision") in {
                "accept", "accept_with_caveats", "reject"
            }
            and reviews[Path(name).stem].get("reviewed_started_at") == r["started_at"]
        }
    print("Wait started", datetime.now().astimezone().isoformat(), flush=True)
    deadline = time.monotonic() + args.seconds
    while True:
        state = snapshot(args.artifact_root, manifest, args.library_sha)
        changed = [
            (name, r) for name, r in state.items()
            if r.get("status") in terminal and key(name, r) not in baseline
        ]
        if changed or time.monotonic() >= deadline:
            break
        time.sleep(min(15, max(0, deadline - time.monotonic())))
    print("Wait ended", datetime.now().astimezone().isoformat())
    for name, r in changed:
        print("NEW RESULT", name, r.get("status"), r.get("elapsed_seconds"), r.get("error"))
    if not changed:
        print("No new terminal receipt within this bounded wait.")
    for name, r in state.items():
        if not r.get("status"):
            minutes = (datetime.now().astimezone() - datetime.fromisoformat(r["started_at"])).total_seconds() / 60
            print("UNFINISHED RECEIPT", name, "wall minutes", round(minutes, 1), "cell", r.get("current_cell"))


if __name__ == "__main__":
    main()
