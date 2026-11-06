"""Check fresh Markdown/JSON/DOCX exports against a completed notebook receipt."""

import argparse
import json
import os
import re
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from pathlib import Path

import markdown
from bs4 import BeautifulSoup


def main():
    """Validate complete visible text without counting exports from older attempts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--folder", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--text-output", type=Path)
    args = parser.parse_args()
    receipt = json.loads(args.run.read_text(encoding="utf-8"))
    if receipt.get("status") != "completed":
        raise RuntimeError("Export review requires a completed notebook execution.")
    started = datetime.fromisoformat(receipt["started_at"]).timestamp()
    folder = str(args.folder.resolve())
    if os.name == "nt" and not folder.startswith("\\\\?\\"):
        folder = "\\\\?\\UNC\\" + folder[2:] if folder.startswith("\\\\") else "\\\\?\\" + folder

    documents = []
    contents = []
    for path in sorted(Path(folder).rglob("*.json")):
        if path.stat().st_mtime < started:
            continue
        document = json.loads(path.read_text(encoding="utf-8"))
        content = document["content"]
        for suffix in (".md", ".docx"):
            if path.with_suffix(suffix).stat().st_mtime < started:
                raise RuntimeError(f"Export format predates this execution: {path.with_suffix(suffix)}")
        if path.with_suffix(".md").read_text(encoding="utf-8") != content:
            raise AssertionError(f"Markdown differs from JSON content: {path.name}")
        with zipfile.ZipFile(path.with_suffix(".docx")) as archive:
            xml = ET.fromstring(archive.read("word/document.xml"))
        docx_text = " ".join(node.text or "" for node in xml.iter(
            "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"
        ))
        visible = BeautifulSoup(markdown.markdown(content), "html.parser").get_text(" ")
        expected_words = re.findall(r"\w+", visible)
        actual_words = re.findall(r"\w+", docx_text)
        if expected_words != actual_words:
            raise AssertionError(f"DOCX visible word tokens differ from Markdown: {path.name}")
        documents.append({
            "file": path.name, "title": document.get("title"),
            "characters": len(content), "visible_word_tokens": len(actual_words),
            "markdown_equals_json": True, "docx_word_tokens_match": True,
        })
        contents.extend([f"\n=== {path.name} ===", content])
    if not documents:
        raise RuntimeError("No document exports were written during this execution.")
    report = {"started_at": receipt["started_at"], "documents": documents}
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.text_output:
        args.text_output.write_text("\n".join(contents), encoding="utf-8")
    print(f"Validated {len(documents)} complete fresh Markdown/JSON/DOCX export sets.")


if __name__ == "__main__":
    main()
