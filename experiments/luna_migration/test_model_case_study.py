"""Offline tests: no TinyTroupe imports, API calls or credentials."""

import copy
import json
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from model_case_study import decode_key, digest, export_cases, replay_body, run_cases, validate_case


class ModelCaseTests(unittest.TestCase):
    def setUp(self):
        self.request = {
            "model": "gpt-6-luna",
            "messages": [{"role": "user", "content": "Keep 'response_format' literally."}],
            "reasoning_effort": "xhigh",
        }
        self.response = {
            "id": "test-response", "model": "gpt-6-luna",
            "choices": [{"finish_reason": "stop", "message": {"content": '{"answer":"No"}'}}],
        }
        self.case = {
            "case_id": "sample", "request": self.request,
            "original_response": self.response, "assessment": {},
            "provenance": {
                "request_sha256": digest(self.request),
                "response_sha256": digest(self.response),
            },
        }

    def test_literal_key_roundtrip(self):
        self.assertEqual(decode_key(str(("gpt-6-luna", self.request))), (self.request, None))

    def test_sdk_class_only_replaced_outside_messages(self):
        key = str(("gpt-6-luna", {
            **self.request, "response_format": "SCHEMA",
        })).replace("'SCHEMA'", "<class 'package.Response'>")
        request, name = decode_key(key)
        self.assertEqual(name, "package.Response")
        self.assertEqual(request["messages"], self.request["messages"])

    def test_unsafe_key_never_executes(self):
        with self.assertRaises((ValueError, SyntaxError)):
            decode_key("__import__('os').system('never')")

    def test_model_effort_overrides_do_not_mutate_source(self):
        result = replay_body(self.case, {"model": "gpt-5-mini", "reasoning_effort": "omit"})
        self.assertNotIn("reasoning_effort", result)
        self.assertEqual(self.case["request"], self.request)
        self.assertEqual(result["messages"], self.request["messages"])
        self.assertEqual(result["model"], "gpt-5-mini")

    def test_integrity_detects_modified_input_and_output(self):
        validate_case(self.case)
        for field in ("request", "original_response"):
            bad = copy.deepcopy(self.case)
            bad[field]["modified"] = True
            with self.assertRaises(ValueError):
                validate_case(bad)

    def test_export_and_dry_run_without_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "cache.json").write_text(
                json.dumps({str(("gpt-6-luna", self.request)): self.response}), encoding="utf-8"
            )
            (root / "schemas.json").write_text("{}", encoding="utf-8")
            selection = {
                "case_id": "sample", "cache": "cache.json", "response_id": "test-response",
                "phase": "extraction", "group": "test",
                "assessment": {"label": "positive", "finding": "Known answer", "criterion": "Public only"},
            }
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({"schema_file": "schemas.json", "cases": [selection]}),
                                encoding="utf-8")
            export_cases(manifest, root / "export")
            corpus = root / "export" / "cases.jsonl"
            saved = json.loads(corpus.read_text(encoding="utf-8"))
            self.assertEqual(saved["request"], self.request)
            self.assertEqual(saved["original_response"], self.response)
            conditions = root / "conditions.json"
            conditions.write_text('[{"id":"baseline","model":"gpt-5-mini"}]', encoding="utf-8")
            output = root / "result.jsonl"
            run_cases(corpus, conditions, output, [], 2, 120, False)
            self.assertFalse(output.exists())
            with self.assertRaises(ValueError):
                run_cases(corpus, conditions, output, ["missing"], 1, 120, False)

    def test_execution_records_success_refusal_and_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "cases.jsonl"
            corpus.write_text(json.dumps(self.case) + "\n", encoding="utf-8")
            conditions = root / "conditions.json"
            conditions.write_text('[{"id":"baseline","model":"gpt-5-mini"}]', encoding="utf-8")
            for status, refusal, error in [
                ("completed", None, None),
                ("incomplete_or_refused", "Cannot comply", None),
                ("error", None, RuntimeError("Explicit failure")),
            ]:
                output = root / (status + ".jsonl")
                response = types.SimpleNamespace(
                    choices=[types.SimpleNamespace(
                        finish_reason="stop",
                        message=types.SimpleNamespace(refusal=refusal),
                    )],
                    model_dump=lambda **kwargs: self.response,
                )
                create = unittest.mock.Mock(return_value=response, side_effect=error)
                constructor = unittest.mock.Mock(return_value=types.SimpleNamespace(
                    chat=types.SimpleNamespace(completions=types.SimpleNamespace(create=create))
                ))
                with patch.dict("sys.modules", {"openai": types.SimpleNamespace(OpenAI=constructor)}):
                    if status == "completed":
                        run_cases(corpus, conditions, output, [], 1, 120, True)
                    else:
                        with self.assertRaises(SystemExit):
                            run_cases(corpus, conditions, output, [], 1, 120, True)
                    with self.assertRaises(FileExistsError):
                        run_cases(corpus, conditions, output, [], 1, 120, True)
                result = json.loads(output.read_text(encoding="utf-8"))
                self.assertEqual(result["status"], status)
                self.assertEqual(result["request"]["messages"], self.request["messages"])
                self.assertNotIn("assessment", create.call_args.kwargs)
                if error:
                    self.assertEqual(result["error"]["message"], "Explicit failure")
                constructor.assert_called_once_with(timeout=120, max_retries=0)


if __name__ == "__main__":
    unittest.main()
