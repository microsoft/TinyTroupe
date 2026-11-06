"""Verify bundled evidence hashes and executable helper portability without API calls."""

import ast
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def staged_audit(manifest):
    """Check actual Git blobs, not just files in the current checkout."""
    repo = ROOT.parents[1]
    names = subprocess.check_output(
        ["git", "diff", "--cached", "--name-only", "-z"], cwd=repo
    ).split(b"\0")
    names = [name.decode("utf-8") for name in names if name]
    expected = {
        (ROOT / row["path"]).relative_to(repo).as_posix(): row
        for row in manifest["included"]
    }
    secrets = re.compile(
        rb"sk-[A-Za-z0-9_-]{20,}|Bearer\s+[A-Za-z0-9._-]{20,}"
        rb"|gh[pousr]_[A-Za-z0-9]{30,}"
        rb"|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
    )
    problems = []
    with subprocess.Popen(
        ["git", "cat-file", "--batch"], cwd=repo,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
    ) as process:
        for name in names:
            process.stdin.write(f":{name}\n".encode("utf-8"))
            process.stdin.flush()
            header = process.stdout.readline().split()
            if len(header) != 3 or header[1] != b"blob":
                raise ValueError(f"Cannot read staged blob: {name}")
            data = process.stdout.read(int(header[2]))
            if process.stdout.read(1) != b"\n":
                raise ValueError(f"Invalid Git batch framing: {name}")
            if secrets.search(data):
                problems.append(f"Credential-shaped content: {name}")
            if name in expected:
                row = expected.pop(name)
                matches = (
                    len(data) == row["bytes"]
                    and hashlib.sha256(data).hexdigest() == row["sha256"]
                )
                pointer = re.fullmatch(
                    rb"version https://git-lfs.github.com/spec/v1\n"
                    rb"oid sha256:([0-9a-f]{64})\nsize ([0-9]+)\n", data,
                )
                if pointer:
                    matches = (
                        pointer[1].decode() == row["sha256"]
                        and int(pointer[2]) == row["bytes"]
                    )
                if not matches:
                    problems.append(f"Staged evidence differs from manifest: {name}")
            if name.endswith(".py"):
                ast.parse(data.decode("utf-8-sig"), filename=name)
        process.stdin.close()
        if process.wait() != 0:
            raise RuntimeError("Git staged-blob reader failed.")
    if expected:
        problems.append(f"Bundled files absent from staged diff: {len(expected)}")
    if problems:
        raise ValueError("\n".join(problems))
    print(f"Checked {len(names)} staged files: evidence hashes, Python syntax, "
          "and credential-shaped content.")


def main():
    """Reject missing/changed bundled evidence and machine-bound executable helpers."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staged", action="store_true")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "handoff-manifest.json").read_text(encoding="utf-8"))
    for row in manifest["included"]:
        path = ROOT / row["path"]
        if not path.resolve().is_relative_to(ROOT):
            raise ValueError(f"Manifest path escapes the bundle: {row['path']}")
        data = path.read_bytes()
        if len(data) != row["bytes"] or hashlib.sha256(data).hexdigest() != row["sha256"]:
            raise ValueError(f"Bundle file changed or incomplete: {row['path']}")
        if path.suffix == ".py":
            text = data.decode("utf-8")
            ast.parse(text, filename=str(path))
            if "C:" + chr(92) + "Users" in text:
                raise ValueError(f"Machine-bound helper remains: {row['path']}")
    print(f"Verified {len(manifest['included'])} bundled files "
          f"({manifest['total_bytes']:,} bytes); no model calls.")
    if args.staged:
        staged_audit(manifest)


if __name__ == "__main__":
    main()
