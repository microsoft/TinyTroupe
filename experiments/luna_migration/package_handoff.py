"""Package selected local migration artifacts without copying bulk workspaces."""

import argparse
import ast
import hashlib
import json
import re
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
DESTINATION = Path(__file__).resolve().parent
PRIVATE = re.compile(
    r"sk-[A-Za-z0-9_-]{20,}|Bearer\s+[A-Za-z0-9._-]{20,}"
    r"|https?://[^\s<>\"']*pickfu\.com/[^\s<>\"']+"
    r"|gh[pousr]_[A-Za-z0-9]{30,}",
    re.IGNORECASE,
)
ARTIFACT_SUFFIXES = {".json", ".jsonl", ".mustache", ".csv"}
SMALL_TRIALS = {
    "cf5-reextraction", "cf6-coherent-dimensions", "cf6-comprehension-screen",
    "demographic-coverage-budget", "demographic-coverage-budget-r2",
    "demographic-coverage-budget-r3", "demographic-coverage-budget-r4",
    "integrated-coverage-plan", "marginal-choices-integration",
    "generator-example-ablation", "generator-example-ablation-json-mode",
    "population-scope-actor-replays", "population-scope-test-diagnostics",
    "population-scope-trial", "realized-behavior-coverage",
    "realized-behavior-coverage-compact", "realized-behavior-coverage-r2",
    "realized-coverage-pipeline", "investment-retention-replay",
}
REVIEWED_RUNS = {"cf5-inv", "cf5-kids", "cf5-gaz", "cf6-gaz"}
CORE_LOGS = {
    "comprehension-options-core.log", "marginal-choices-core.log",
    "marginal-choices-targeted.log", "sampling-coverage-core.log",
    "comprehension-targeted.log", "opposing-options-targeted.log",
}


def select(path, source):
    """Select helpers, small evidence, and the latest synthetic response caches."""
    relative = path.relative_to(source)
    if any(part in {"workspace", "attempts", "__pycache__", ".pytest_cache",
                    "published-updates", "originals"} for part in relative.parts):
        return False
    if path.suffix == ".py":
        return len(relative.parts) == 1 or relative.parts[0] == "model-study"
    if len(relative.parts) == 1:
        return path.suffix in ARTIFACT_SUFFIXES or path.name in {
            "cf5-quality-report.html", *CORE_LOGS,
            "comprehension-options-core-source.txt", "marginal-choices-core-source.txt",
        }
    folder = relative.parts[0]
    if folder == "cf7-gaz":
        return len(relative.parts) == 2 and path.name in {
            "recovery-response-snapshot.json",
        }
    if folder == "model-study":
        return (
            len(relative.parts) == 2
            and (path.suffix in ARTIFACT_SUFFIXES or path.name == "requirements.txt")
        ) or (
            path.suffix == ".json" and path.stat().st_size < 2_000_000
            and "expanded-execution-corpus" not in relative.parts
        )
    if folder in REVIEWED_RUNS:
        return len(relative.parts) == 2 and (
            path.name.endswith((".agents.json", ".traits.json", ".factories.json",
                                ".personas.json", ".run.json"))
            or folder == "cf6-gaz" and path.name == "api.cache.json"
        )
    return (
        folder in SMALL_TRIALS or folder.startswith("fixed-persona-")
        or folder.startswith("crossed-")
    ) and len(relative.parts) == 2 and path.suffix in ARTIFACT_SUFFIXES


def portable_helper(text):
    """Replace historical checkout constants without changing experiment semantics."""
    text = re.sub(
        r'(REPO|ROOT) = Path\(r"C:\\Users\\[^"\n]+\\TinyTroupe"\)',
        lambda match: f"{match[1]} = Path(__file__).resolve().parents[2]",
        text,
    )
    return re.sub(
        r'PACKAGE = Path\(r"C:\\Users\\[^"\n]+\\TinyTroupe\\tinytroupe"\)',
        'PACKAGE = Path(__file__).resolve().parents[2] / "tinytroupe"',
        text,
    )


def main():
    """Copy an explicitly selected artifact root and record omissions and hashes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    old_manifest = DESTINATION / "handoff-manifest.json"
    old_hashes = {}
    if args.refresh:
        old_hashes = {
            row["path"]: row["sha256"]
            for row in json.loads(old_manifest.read_text(encoding="utf-8"))["included"]
        }
    included, excluded = [], []
    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(source)
        if not select(path, source):
            excluded.append({"path": relative.as_posix(), "reason": "bulk_or_out_of_scope"})
            continue
        data = path.read_bytes()
        if path.suffix in {".json", ".jsonl", ".py", ".mustache", ".csv", ".html",
                           ".txt", ".log"}:
            text = data.decode("utf-8-sig")
            if PRIVATE.search(text):
                excluded.append({"path": relative.as_posix(), "reason": "private_reference_or_secret"})
                continue
            if path.suffix == ".py":
                text = portable_helper(text)
                ast.parse(text, filename=str(relative))
                data = text.encode("utf-8")
            if path.suffix == ".json":
                json.loads(text)
        # Captured tables can contain respondent-level human data: ship only synthetic
        # public-evidence records, not mixed human/simulation dataframe exports.
        if path.name.endswith(".tables.json"):
            excluded.append({"path": relative.as_posix(), "reason": "mixed_human_tables"})
            continue
        target = DESTINATION / relative
        if target.exists():
            if target.read_bytes() != data:
                actual = hashlib.sha256(target.read_bytes()).hexdigest()
                if not args.refresh or old_hashes.get(relative.as_posix()) != actual:
                    raise FileExistsError(f"Refusing to overwrite differing handoff file: {relative}")
                target.write_bytes(data)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        included.append({
            "path": relative.as_posix(),
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "portable_checkout_constant": path.suffix == ".py" and data != path.read_bytes(),
        })
    manifest = {
        "purpose": "Temporary branch-local migration handoff; remove or curate before merging.",
        "included": included,
        "excluded": excluded,
        "excluded_policy": "No copied workspaces, images, zip bundles, large execution corpus, "
                           "private report URLs, mixed human tables, or automatic bulk-cache transfer.",
        "total_bytes": sum(row["bytes"] for row in included),
        "source_path": "Original desktop session artifact directory (not required at runtime).",
    }
    (DESTINATION / "handoff-manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(json.dumps({
        "files": len(included), "bytes": manifest["total_bytes"],
        "helpers": sum(row["path"].endswith(".py") for row in included),
        "private_files_excluded": sum(
            row["reason"] == "private_reference_or_secret" for row in excluded
        ),
    }))


if __name__ == "__main__":
    main()
