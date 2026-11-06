"""Verify text edits preserve envelope structure and reject invalid recipes."""

import json
import tempfile
import unittest
from pathlib import Path

from model_case_study import digest
from prompt_variants import build_variants, transform_content


class VariantTests(unittest.TestCase):
    def test_json_nested_stimulus_is_edited_without_modifying_other_values(self):
        value = {"stimuli": [{"type": "CONVERSATION", "content": 'Say "Yes" only', "source": "Person"}]}
        text, count = transform_content(json.dumps(value), {
            "kind": "replace", "old": 'Say "Yes" only', "new": "Give an answer and a reason.",
        })
        self.assertEqual(count, 1)
        self.assertEqual(json.loads(text)["stimuli"][0], {
            "type": "CONVERSATION", "content": "Give an answer and a reason.", "source": "Person",
        })

    def test_no_match_preserves_exact_bytes(self):
        text = '{"stimuli":  [{"content": "unchanged"}]}'
        self.assertEqual(transform_content(text, {
            "kind": "replace", "old": "absent", "new": "anything",
        }), (text, 0))

    def test_parent_chain_and_original_provenance(self):
        request = {"model": "gpt-6-luna", "messages": [{"role": "user", "content": "first"}]}
        response = {"choices": [{"finish_reason": "stop"}]}
        case = {"case_id": "sample", "request": request, "original_response": response,
                "assessment": {}, "provenance": {
                    "request_sha256": digest(request), "response_sha256": digest(response),
                }}
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            corpus = root / "source.jsonl"
            corpus.write_text(json.dumps(case) + "\n", encoding="utf-8")
            manifest = root / "manifest.json"
            recipe = {"order_seed": 1, "protocol": "test", "variants": [
                {"id": "a", "cases": ["sample"], "hypothesis": "test", "operations": [
                    {"kind": "replace", "message": 0, "old": "first", "new": "second", "max_matches": 1},
                ]},
                {"id": "b", "parent": "a", "phase": "persona_generation_plan",
                 "response_format": {"type": "json_schema", "json_schema": {
                     "name": "test", "strict": True,
                     "schema": {"type": "object", "properties": {}, "additionalProperties": False},
                 }},
                 "cases": ["sample"], "hypothesis": "test", "operations": [
                    {"kind": "replace", "message": 0, "old": "second", "new": "third", "max_matches": 1},
                ]},
            ]}
            manifest.write_text(json.dumps(recipe), encoding="utf-8")
            build_variants(corpus, manifest, root / "output")
            saved = {c["case_id"]: c for c in map(
                json.loads, (root / "output" / "cases.jsonl").read_text(encoding="utf-8").splitlines()
            )}
            self.assertEqual(saved["sample::baseline"]["request"], request)
            self.assertEqual(saved["sample::b"]["request"]["messages"][0]["content"], "third")
            self.assertEqual(saved["sample::b"]["experiment"]["parent_case_id"], "sample::a")
            self.assertEqual(saved["sample::b"]["phase"], "persona_generation_plan")
            self.assertEqual(saved["sample::b"]["request"]["response_format"], recipe["variants"][1]["response_format"])
            self.assertNotIn("response_format", saved["sample::a"]["request"])
            self.assertEqual(json.loads(corpus.read_text(encoding="utf-8")), case)
            recipe["variants"][0]["operations"][0]["old"] = "missing"
            manifest.write_text(json.dumps(recipe), encoding="utf-8")
            with self.assertRaises(ValueError):
                build_variants(corpus, manifest, root / "invalid")


if __name__ == "__main__":
    unittest.main()
