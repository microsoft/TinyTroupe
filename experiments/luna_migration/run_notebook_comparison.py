"""Execute unchanged example cells with model overrides and preserve all results.

An output directory's execution-settings.json may override cell_timeout_seconds.
"""

import argparse
import asyncio
import hashlib
import json
import re
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import nbformat
from bs4 import BeautifulSoup
from jupyter_client import KernelManager
from nbclient import NotebookClient


def library_fingerprint(package_dir):
    """Identify the Python and prompt implementation used by an isolated run."""
    paths = sorted(
        path for path in package_dir.rglob("*")
        if path.is_file() and path.suffix in {".py", ".mustache"}
    )
    if not paths:
        raise ValueError(f"No library implementation files found: {package_dir}")
    digest = hashlib.sha256()
    for path in paths:
        digest.update("\0".join(path.relative_to(package_dir).parts).encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def transcript(notebook):
    """Extract readable source and outputs without duplicate HTML renderings."""
    lines = []
    for index, cell in enumerate(notebook.cells):
        lines.extend([f"\n=== Cell {index} ({cell.cell_type}) ===", cell.source])
        for output in cell.get("outputs", []):
            if output.output_type == "stream":
                lines.append(output.text)
            elif output.output_type == "error":
                lines.append(f"{output.ename}: {output.evalue}")
            else:
                plain = output.get("data", {}).get("text/plain")
                markup = output.get("data", {}).get("text/html")
                if markup and (not plain or "IPython.core.display.HTML" in plain):
                    document = BeautifulSoup(markup, "html.parser")
                    for element in document(["style", "script"]):
                        element.decompose()
                    lines.append(document.get_text(" ", strip=True))
                elif plain:
                    lines.append(plain)
    return re.sub(r"\x1b\[[0-9;]*m", "", "\n".join(lines))


def main():
    """Run notebooks in individual py310 kernels and checkpoint after every cell."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--model", required=True)
    parser.add_argument("--reasoning-model", required=True)
    parser.add_argument("--effort", required=True)
    parser.add_argument("--api-timeout", type=int, help="Explicit API deadline override; preserves model effort.")
    parser.add_argument("--timeout", type=int, default=600, help="Default per-cell timeout in seconds.")
    parser.add_argument("--startup-timeout", type=int, default=300, help="Kernel readiness timeout in seconds.")
    parser.add_argument("--use-cache", action="store_true")
    parser.add_argument(
        "--reuse-simulation-cache", action="store_true",
        help="Retain controlled-simulation caches for hash-checked replay with the same library.",
    )
    parser.add_argument("notebooks", nargs="+")
    args = parser.parse_args()
    if args.api_timeout is not None and args.api_timeout <= 0:
        raise ValueError("API timeout must be a positive number of seconds.")
    source_dir = args.source_dir.resolve()
    output_dir = args.output_dir.resolve()
    settings_path = output_dir / "execution-settings.json"
    settings = json.loads(settings_path.read_text(encoding="utf-8")) if settings_path.exists() else {}
    if not isinstance(settings, dict) or set(settings) - {"cell_timeout_seconds"}:
        raise ValueError(f"Invalid execution settings: {settings_path}")
    cell_timeout = settings.get("cell_timeout_seconds", args.timeout)
    if type(cell_timeout) is not int or cell_timeout <= 0:
        raise ValueError("cell_timeout_seconds must be a positive integer.")
    originals = output_dir.parent / "originals"
    output_dir.mkdir(parents=True, exist_ok=True)
    originals.mkdir(parents=True, exist_ok=True)
    for source in source_dir.glob("*.ipynb"):
        target = originals / source.name
        if not target.exists():
            shutil.copy2(source, target)
            notebook = nbformat.read(source, as_version=4)
            target.with_suffix(".txt").write_text(transcript(notebook), encoding="utf-8")
    workspace = output_dir / "workspace"
    working_examples = workspace / "examples"
    shutil.copytree(
        source_dir, working_examples, dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(
            "*.ipynb", "*.log", "*cache*", "__pycache__", "extractions"
        ),
    )
    source_data = source_dir.parent / "data"
    if source_data.is_dir():
        shutil.copytree(
            source_data, workspace / "data", dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("extractions", "*.log", "*cache*"),
        )
        (workspace / "data" / "extractions").mkdir(parents=True, exist_ok=True)
    summary = []
    for name in args.notebooks:
        source = source_dir / name
        notebook = nbformat.read(source, as_version=4)
        source_code_hash = hashlib.sha256(
            json.dumps(
                [cell.source for cell in notebook.cells if cell.cell_type == "code"],
                ensure_ascii=False,
            ).encode("utf-8")
        ).hexdigest()
        for cell in notebook.cells:
            if cell.cell_type == "code":
                cell.outputs = []
                cell.execution_count = None
        setup = (
            "import sys\n"
            f"sys.path.insert(0, {str(source_dir.parent)!r})\n"
            "from tinytroupe import config_manager\n"
            "from tinytroupe.clients import force_api_cache\n"
            f"config_manager.update('model', {args.model!r})\n"
            f"config_manager.update('reasoning_model', {args.reasoning_model!r})\n"
            f"config_manager.update('reasoning_effort', {args.effort!r})\n"
            + (f"config_manager.update('timeout', {args.api_timeout!r})\n" if args.api_timeout is not None else "")
            +
            f"force_api_cache({args.use_cache!r}, {str(output_dir / 'api.cache.json')!r})\n"
            "print('COMPARISON_MODEL', config_manager.get('model'))\n"
            "print('COMPARISON_EFFORT', config_manager.get('reasoning_effort'))\n"
        )
        notebook.cells.insert(0, nbformat.v4.new_code_cell(setup))
        diagnostics = (
            "import json\n"
            "from pathlib import Path\n"
            "from tinytroupe.agent import TinyPerson\n"
            "from tinytroupe.factory import TinyPersonFactory\n"
            "from tinytroupe.extraction import ResultsExtractor\n"
            "from tinytroupe.clients import client\n"
            "print('COMPARISON_USAGE', json.dumps(client().get_cost_stats()))\n"
            f"Path({str(output_dir / (Path(name).stem + '.agents.json'))!r}).write_text(\n"
            "    json.dumps({name: agent.episodic_memory.retrieve_all()\n"
            "                for name, agent in TinyPerson.all_agents.items()},\n"
            "               ensure_ascii=False, indent=2, default=str), encoding='utf-8')\n"
            f"Path({str(output_dir / (Path(name).stem + '.personas.json'))!r}).write_text(\n"
            "    json.dumps({name: agent.minibio() for name, agent in TinyPerson.all_agents.items()},\n"
            "               ensure_ascii=False, indent=2), encoding='utf-8')\n"
            f"Path({str(output_dir / (Path(name).stem + '.traits.json'))!r}).write_text(\n"
            "    json.dumps({name: {field: agent.get(field) for field in\n"
            "        ['age', 'nationality', 'occupation', 'preferences', 'personality',\n"
            "         'beliefs', 'skills', 'goals', 'relationships', 'context']}\n"
            "        for name, agent in TinyPerson.all_agents.items()},\n"
            "        ensure_ascii=False, indent=2, default=str), encoding='utf-8')\n"
            f"Path({str(output_dir / (Path(name).stem + '.factories.json'))!r}).write_text(\n"
            "    json.dumps({name: {field: getattr(value, field) for field in\n"
            "        ['context_text', 'population_size', 'enforce_usage_of_all_dimensions',\n"
            "         'sampling_dimensions', 'sampling_plan']}\n"
            "        for name, value in list(globals().items())\n"
            "        if isinstance(value, TinyPersonFactory)},\n"
            "        ensure_ascii=False, indent=2, default=str), encoding='utf-8')\n"
            f"Path({str(output_dir / (Path(name).stem + '.extractions.json'))!r}).write_text(\n"
            "    json.dumps({key: {'agent_extraction': value.agent_extraction,\n"
            "                      'world_extraction': value.world_extraction}\n"
            "        for key, value in list(globals().items())\n"
            "        if isinstance(value, ResultsExtractor)},\n"
            "        ensure_ascii=False, indent=2, default=str), encoding='utf-8')\n"
            "import pandas as pd\n"
            f"Path({str(output_dir / (Path(name).stem + '.tables.json'))!r}).write_text(\n"
            "    json.dumps({key: json.loads(value.to_json(orient='split', force_ascii=False, default_handler=str))\n"
            "                for key, value in list(globals().items()) if isinstance(value, pd.DataFrame)},\n"
            "               ensure_ascii=False, indent=2), encoding='utf-8')\n"
        )
        notebook.cells.append(nbformat.v4.new_code_cell(diagnostics))
        notebook.nbformat_minor = max(notebook.nbformat_minor, 5)
        _, notebook = nbformat.validator.normalize(notebook)
        destination = output_dir / name
        if destination.exists():
            archive = output_dir / "attempts" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            archive.mkdir(parents=True)
            for suffix in (".ipynb", ".txt", ".run.json", ".agents.json", ".personas.json", ".traits.json", ".factories.json", ".tables.json", ".extractions.json"):
                previous = destination.with_suffix(suffix)
                if previous.exists():
                    shutil.copy2(previous, archive / previous.name)
            for cache in working_examples.glob("*.cache.json"):
                if args.reuse_simulation_cache:
                    shutil.copy2(cache, archive / cache.name)
                else:
                    shutil.move(str(cache), str(archive / cache.name))
        started = time.monotonic()
        record = {
            "notebook": name, "model": args.model, "effort": args.effort,
            "api_timeout_override_seconds": args.api_timeout,
            "started_at": datetime.now(timezone.utc).isoformat(), "cells": [],
            "source_code_sha256": source_code_hash, "cache_enabled": args.use_cache,
            "simulation_cache_reused": args.reuse_simulation_cache,
            "cell_timeout_seconds": cell_timeout,
            "library_sha256": library_fingerprint(source_dir.parent / "tinytroupe"),
        }

        def save():
            nbformat.write(notebook, destination)
            destination.with_suffix(".txt").write_text(transcript(notebook), encoding="utf-8")
            destination.with_suffix(".run.json").write_text(json.dumps(record, indent=2), encoding="utf-8")

        def cell_done(cell, cell_index, execute_reply):
            record["cells"].append({
                "index": cell_index, "elapsed_seconds": round(time.monotonic() - started, 2),
                "status": execute_reply["content"]["status"],
            })
            save()
            print(json.dumps({"notebook": name, **record["cells"][-1]}), flush=True)

        def cell_start(cell, cell_index):
            record["current_cell"] = cell_index
            record["elapsed_seconds"] = round(time.monotonic() - started, 2)
            save()
            print(f"CELL_START {name}: {cell_index} ({cell.cell_type})", flush=True)

        manager = KernelManager(kernel_name="python3")
        manager.kernel_spec.argv[0] = sys.executable
        executor = NotebookClient(
            notebook, km=manager, timeout=cell_timeout, startup_timeout=args.startup_timeout,
            resources={"metadata": {"path": str(working_examples)}},
            on_cell_executed=cell_done,
            on_cell_start=cell_start,
        )
        print(f"START {args.model}: {name}", flush=True)
        try:
            executor.execute()
            record["status"] = "completed"
        except Exception as exc:
            record["status"] = "error"
            record["error"] = f"{type(exc).__name__}: {exc}"
            print(record["error"], flush=True)
        finally:
            if manager.has_kernel:
                manager.shutdown_kernel(now=True)
            record["elapsed_seconds"] = round(time.monotonic() - started, 2)
            record["library_unchanged_during_run"] = (
                library_fingerprint(source_dir.parent / "tinytroupe") == record["library_sha256"]
            )
            save()
        summary.append(record)
        (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"END {name}: {record['status']} ({record['elapsed_seconds']}s)", flush=True)
    if any(record["status"] == "error" for record in summary):
        raise SystemExit(1)


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    main()
