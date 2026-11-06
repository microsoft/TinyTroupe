"""Print complete, selected notebook evidence without console display truncation."""

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path


def read_json(path):
    """Read a captured artifact with explicit decoding."""
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    """Select source, actual agent memories, traits, tables, or execution metadata."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("notebook", type=Path)
    parser.add_argument(
        "--mode", choices=["summary", "actions", "traits", "tables", "source"],
        default="summary",
    )
    parser.add_argument("--action-types", nargs="+", default=["TALK"])
    parser.add_argument("--speaker", action="append")
    parser.add_argument("--include-stimuli", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    path = args.notebook
    lines = []
    if args.mode != "source":
        receipt = read_json(path.with_suffix(".run.json"))
        if receipt.get("status") != "completed":
            raise RuntimeError(f"Cannot review an unfinished execution: {receipt.get('status', 'running')}")
        evidence_type = args.mode if args.mode in {"traits", "tables"} else "agents"
        evidence = path.with_suffix(f".{evidence_type}.json")
        if evidence.stat().st_mtime < datetime.fromisoformat(receipt["started_at"]).timestamp():
            raise RuntimeError(f"Evidence predates this execution: {evidence}")
    if args.mode in {"traits", "tables"}:
        lines.append(json.dumps(
            read_json(path.with_suffix(f".{args.mode}.json")),
            ensure_ascii=False, indent=2,
        ))
    elif args.mode == "source":
        for index, cell in enumerate(read_json(path)["cells"]):
            if cell["cell_type"] == "code":
                source = cell["source"]
                if isinstance(source, list):
                    source = "".join(source)
                lines.extend([f"\n=== CELL {index} ===", source])
    else:
        lines.append(json.dumps(receipt, ensure_ascii=False, indent=2))
        agents = read_json(path.with_suffix(".agents.json"))
        for name, events in agents.items():
            if args.speaker and name not in args.speaker:
                continue
            actions = [
                event["content"]["action"] for event in events
                if event.get("type") == "action"
            ]
            lines.append(f"\n=== {name}: {dict(Counter(a['type'] for a in actions))} ===")
            if args.mode == "summary":
                talks = [a["content"] for a in actions if a["type"] == "TALK"]
                lines.append(f"TALKs: {len(talks)}; exact unique TALKs: {len(set(talks))}")
                continue
            for index, event in enumerate(events):
                if event.get("type") == "action":
                    action = event["content"]["action"]
                    if action["type"] in args.action_types:
                        lines.extend([
                            f"\nEVENT {index} {action['type']} -> {action.get('target', '')}",
                            action["content"],
                        ])
                elif args.include_stimuli:
                    lines.extend([
                        f"\nEVENT {index} STIMULUS",
                        json.dumps(event["content"], ensure_ascii=False, indent=2),
                    ])
    result = "\n".join(lines)
    if args.output:
        args.output.write_text(result, encoding="utf-8")
        print(f"Saved {len(result)} characters to {args.output}")
    else:
        print(result)


if __name__ == "__main__":
    main()
