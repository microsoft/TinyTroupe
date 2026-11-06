"""Run explicitly bounded shards with the existing no-retry standalone replay runner."""

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from mine_execution_cases import load_lines
from model_case_study import replay_body, run_cases, validate_case


def run(corpus, conditions, output, workers=3, timeout=300, execute=False):
    """Preserve each shard's attempts and an aggregate, with no silent retries or lost API errors."""
    if workers < 1:
        raise ValueError("workers must be positive")
    if output.exists():
        raise FileExistsError(f"Use a new result directory: {output}")
    cases = list(load_lines(corpus))
    if not cases or len({case["case_id"] for case in cases}) != len(cases):
        raise ValueError("Require nonempty distinct case IDs.")
    settings = json.loads(conditions.read_text(encoding="utf-8"))
    for case in cases:
        validate_case(case)
        for condition in settings:
            replay_body(case, condition)
    if not execute:
        print(f"DRY RUN: {len(cases) * len(settings)} calls, up to {workers} concurrent; no API calls.")
        return
    output.mkdir(parents=True)
    shards = []
    for index in range(min(workers, len(cases))):
        path = output / f"shard-{index}.jsonl"
        path.write_text("".join(json.dumps(c, ensure_ascii=False) + "\n"
                                for c in cases[index::workers]), encoding="utf-8")
        shards.append((path, output / f"results-{index}.jsonl"))

    def worker(paths):
        try:
            run_cases(paths[0], conditions, paths[1], [], 1, timeout, True)
            return None
        except SystemExit as error:
            return str(error)

    errors = []
    try:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for error in pool.map(worker, shards):
                if error:
                    errors.append(error)
    finally:
        with (output / "results.jsonl").open("x", encoding="utf-8") as aggregate:
            for _, path in shards:
                if path.exists():
                    aggregate.write(path.read_text(encoding="utf-8"))
    records = list(load_lines(output / "results.jsonl"))
    expected = len(cases) * len(settings)
    if len(records) != expected or errors:
        raise RuntimeError(f"{len(records)}/{expected} attempts saved; shard failures: {errors}")
    print(f"Saved {len(records)} completed attempts without retries.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--conditions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=300)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    run(args.corpus, args.conditions, args.output, args.workers, args.timeout, args.execute)
