"""Regression checks for the notebook execution gate, without making API calls."""

import json
import io
import contextlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from audit_notebook_runs import audit, library_fingerprint
from inspect_notebook_evidence import main as inspect_evidence


class NotebookAuditTests(unittest.TestCase):
    """Completed cells must not conceal failed agent simulations."""

    def test_logged_agent_exception_invalidates_completed_notebook(self):
        with tempfile.TemporaryDirectory(prefix="notebook-audit-") as temporary:
            root = Path(temporary)
            source = root / "examples"
            package = root / "tinytroupe"
            case = root / "case"
            for folder in (source, package, case):
                folder.mkdir()
            (package / "sample.py").write_text("pass\n", encoding="utf-8")
            body = {
                "cell_type": "code", "source": ["pass"], "execution_count": 2,
                "outputs": [{
                    "output_type": "stream", "name": "stderr",
                    "text": ["ERROR - Agent Sample Person generated an exception: API failure\n"],
                }],
            }
            (source / "Sample.ipynb").write_text(
                json.dumps({"cells": [body]}), encoding="utf-8"
            )
            notebook = {"cells": [
                {"cell_type": "code", "source": ["COMPARISON_MODEL"]},
                body,
                {"cell_type": "code", "source": ["COMPARISON_USAGE"]},
            ]}
            destination = case / "Sample.ipynb"
            destination.write_text(json.dumps(notebook), encoding="utf-8")
            (case / "Sample.run.json").write_text(json.dumps({
                "status": "completed", "model": "sample-model", "effort": "sample-effort",
                "library_sha256": library_fingerprint(package),
                "library_unchanged_during_run": True,
            }), encoding="utf-8")

            def inspect():
                return audit(source, root, {"Sample": "case"}, "sample-model", "sample-effort")["runs"][0]

            result = inspect()
            self.assertEqual(result["errors"], [])
            self.assertEqual(len(result["simulation_errors"]), 1)
            self.assertFalse(result["execution_audit_passed"])

            body["outputs"] = []
            destination.write_text(json.dumps(notebook), encoding="utf-8")
            result = inspect()
            self.assertEqual(result["simulation_errors"], [])
            self.assertTrue(result["execution_audit_passed"])

    def test_inspector_rejects_running_receipt(self):
        with tempfile.TemporaryDirectory(prefix="notebook-evidence-") as temporary:
            notebook = Path(temporary) / "Sample.ipynb"
            notebook.with_suffix(".run.json").write_text(
                json.dumps({"status": "running"}), encoding="utf-8"
            )
            with patch("sys.argv", ["inspect", str(notebook)]):
                with self.assertRaisesRegex(RuntimeError, "unfinished execution"):
                    inspect_evidence()

    def test_inspector_rejects_old_evidence_and_accepts_current_evidence(self):
        with tempfile.TemporaryDirectory(prefix="notebook-evidence-") as temporary:
            notebook = Path(temporary) / "Sample.ipynb"
            notebook.with_suffix(".agents.json").write_text("{}", encoding="utf-8")
            receipt = notebook.with_suffix(".run.json")
            receipt.write_text(json.dumps({
                "status": "completed", "started_at": "2099-01-01T00:00:00+00:00",
            }), encoding="utf-8")
            with patch("sys.argv", ["inspect", str(notebook)]):
                with self.assertRaisesRegex(RuntimeError, "predates"):
                    inspect_evidence()
                receipt.write_text(json.dumps({
                    "status": "completed", "started_at": "1970-01-01T00:00:00+00:00",
                }), encoding="utf-8")
                with contextlib.redirect_stdout(io.StringIO()) as output:
                    inspect_evidence()
                self.assertIn('"status": "completed"', output.getvalue())


if __name__ == "__main__":
    unittest.main()
