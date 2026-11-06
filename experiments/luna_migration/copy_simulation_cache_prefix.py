"""Copy a verified simulation-trace prefix without loading its large suffix."""

import argparse
import itertools
import json
from pathlib import Path

import ijson


def main():
    """Keep earlier sampling transactions while replaying later changed operations."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--events", type=int, required=True)
    parser.add_argument("--require-event-name", required=True)
    args = parser.parse_args()
    if args.events <= 0 or args.source.resolve() == args.output.resolve():
        raise ValueError("Use a positive prefix length and a distinct output path.")
    with args.source.open("rb") as stream:
        prefix = list(itertools.islice(
            ijson.items(stream, "item", use_float=True), args.events
        ))
    if len(prefix) != args.events:
        raise ValueError("The source has fewer events than requested.")
    for event in prefix:
        if (
            not isinstance(event, list) or len(event) != 4
            or not isinstance(event[1], str)
            or not event[1].startswith(f"('{args.require_event_name}',")
        ):
            raise ValueError("An event does not match the required transaction name.")
    args.output.write_text(json.dumps(prefix, indent=4), encoding="utf-8")
    print(f"Copied {len(prefix)} verified transactions; {args.output.stat().st_size} bytes.")


if __name__ == "__main__":
    main()
