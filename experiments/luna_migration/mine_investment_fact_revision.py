"""Recover the exact final customer-summary request for source-revision diagnosis."""

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "model-study"))
from model_case_study import decode_key

cache = json.loads((ROOT / "cf4-inv" / "api.cache.json").read_text(encoding="utf-8"))
matches = []
for key, response in cache.items():
    choices = response.get("choices") or []
    if not choices:
        continue
    content = choices[0]["message"].get("content")
    if not isinstance(content, str) or "O que aprendemos até aqui:" not in content:
        continue
    request, schema_class = decode_key(key)
    payload = json.loads(content)
    if any(
        action["type"] == "TALK"
        and action["content"].startswith("O que aprendemos até aqui:")
        for action in payload.get("actions", [])
    ):
        matches.append({
            "request": request,
            "schema_class": schema_class,
            "response": response,
            "source": "Final CF4 Investment Firm customer-summary actor request.",
        })
if len(matches) != 1:
    raise ValueError(f"Expected one final actor request, found {len(matches)}.")
case = matches[0]
(ROOT / "investment-fact-revision-case.json").write_text(
    json.dumps(case, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("MODEL", case["request"]["model"])
print("EFFORT", case["request"].get("reasoning_effort"))
print("SCHEMA", case["schema_class"])
for i, message in enumerate(case["request"]["messages"]):
    content = message.get("content")
    if not isinstance(content, str):
        raise ValueError("Unexpected non-text message in actor case.")
    print("MESSAGE", i, message["role"], "CHARS", len(content))
    for match in re.finditer(r"90[,.]6|[78]%|81[,.]8|179|3[,.]74|ponte", content):
        print("EVIDENCE", re.sub(r"\s+", " ", content[max(0, match.start()-160):match.end()+200]))
    if i == len(case["request"]["messages"]) - 1:
        print("LATEST STIMULUS", content[-3500:])
