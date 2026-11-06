"""Render audited notebook execution and explicit human quality decisions as HTML and CSV."""

import argparse
import csv
import html
import json
from datetime import datetime, timezone
from pathlib import Path


def main():
    """Keep execution evidence, quality judgments and repository promotion distinct."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--reviews", type=Path, required=True)
    parser.add_argument("--promotions", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    audit = json.loads(args.audit.read_text(encoding="utf-8"))
    reviews = json.loads(args.reviews.read_text(encoding="utf-8"))
    promotions = json.loads(args.promotions.read_text(encoding="utf-8"))
    inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
    decisions = {"accept", "accept_with_caveats", "pending", "reject"}
    if any(item.get("decision") not in decisions for item in reviews.values()):
        raise ValueError("Every review must have an explicit recognized decision.")

    rows = []
    for run in sorted(audit["runs"], key=lambda item: item["name"].casefold()):
        name = run["name"]
        review = reviews.get(name, {})
        review_is_current = (
            run.get("library_matches") is True
            and review.get("reviewed_started_at") == run.get("started_at")
        )
        status = run["status"]
        if status == "completed":
            status = "Complete" if run.get("execution_audit_passed") else "Rerun required"
        saved = "No"
        if name in promotions:
            receipt = promotions[name]
            saved = "Yes" if (
                run.get("execution_audit_passed")
                and receipt.get("started_at") == run.get("started_at")
                and receipt.get("library_sha256") == run.get("library_sha256")
            ) else "Prior output only"
        elapsed = run.get("elapsed_seconds")
        rows.append({
            "Example": name,
            "Execution": status,
            "Quality": review.get("verdict", "Not yet reviewed") if review_is_current else "Review pending for current implementation",
            "Findings": (
                review.get("findings", "Substantive quality review pending.")
                if review_is_current else
                "Prior-run evidence (not a decision for the repaired implementation): "
                + review.get("findings", "No earlier substantive review.")
            ),
            "Minutes": round(elapsed / 60, 2) if elapsed is not None else "",
            "Saved in repo": saved,
            "Decision": review.get("decision", "pending") if review_is_current else "pending",
            "Evidence": (args.audit.parent / run["folder"] / (name + ".txt")).resolve().as_uri(),
        })

    excluded = [item["name"] for item in inventory if item["excluded"]]
    fields = ["Example", "Execution", "Quality", "Findings", "Minutes", "Saved in repo", "Decision"]
    with args.output.with_suffix(".csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    reviewed = sum(row["Decision"] != "pending" for row in rows)
    saved = sum(row["Saved in repo"] == "Yes" for row in rows)
    state = "Complete" if reviewed == len(rows) else "In progress"
    if reviewed != len(rows) and any(row["Quality"].startswith("Blocked:") for row in rows):
        state = "Blocked"
    escape = html.escape
    table = []
    for row in rows:
        cells = [f'<td><a href="{row["Evidence"]}">{escape(row["Example"])}</a></td>']
        cells.extend(f"<td>{escape(str(row[key]))}</td>" for key in fields[1:-1])
        table.append(f'<tr class="{row["Decision"]}">{"".join(cells)}</tr>')
    report = f"""<!doctype html>
<html lang="en"><meta charset="utf-8"><title>Luna notebook quality sweep</title>
<style>
body{{font:15px/1.5 system-ui,sans-serif;margin:32px;color:#20262e}}
table{{border-collapse:collapse;width:100%;font-size:14px}}
th,td{{border:1px solid #d6dce2;padding:9px;text-align:left;vertical-align:top}}
th{{background:#edf1f5;position:sticky;top:0}}
.pending{{background:#f7f7f7}}.accept_with_caveats{{background:#fff9e8}}.reject{{background:#fff0f0}}
td:first-child{{min-width:210px}}td:nth-child(4){{min-width:420px}}
.scroll{{overflow-x:auto}}li{{margin:6px 0}}a{{color:#075aaf}}
</style>
<h1>Luna notebook quality sweep</h1>
<p><b>{state}.</b>
{reviewed}/{len(rows)} quality decisions finalized; {saved}/{len(rows)} reviewed notebooks saved in the repository.
Model: <code>gpt-6-luna</code>; API effort: <code>xhigh</code>, the highest accepted effort tested.</p>
<p>Generated {escape(datetime.now(timezone.utc).isoformat())}.
Execution audit updated {escape(audit["updated_at"])}.
Running-cell elapsed times are checkpoints, not live wall-clock durations.</p>
<h2>Interpretation</h2>
<ul>
<li>Execution success does not establish realism, insight quality, empirical fidelity or clinical validity.</li>
<li>Fresh GPT-5-mini comparisons exist for the first four evaluated examples. Other comparisons use preserved historical outputs with mixed model/version provenance.</li>
<li>GPT-5-mini receipts record the selected high-effort configuration, but the client did not explicitly forward that parameter for this model. Its effective API-default effort is unspecified; these are not effort-controlled comparisons with Luna xhigh.</li>
<li>Scenario and library repairs can improve outcomes without proving an isolated model advantage. Single qualitative rollouts are not statistically validated model rankings.</li>
<li>Shared repairs preserve full selected episodic memories and restore missing cognitive-state prompt fields, including reachable contacts, goals, attention and relevant semantic memories. Attention updates and contact removal are also corrected. Final decisions and saved status require the reviewed run and library fingerprint to match; earlier evidence remains provisional.</li>
<li>Document consultation now specifies its action fields and reports empty retrieval as a failure, not a successful read. Investment Firm is explicitly a historical October 2024 case matching its supplied reports; this scenario repair also confounds isolated model comparisons.</li>
<li>Contextual semantic-retrieval cues exclude repeated historical cognitive states and have a token budget separate from full agent-visible memory. Logged per-agent simulation exceptions invalidate execution even if a notebook cell finishes without raising.</li>
<li>Original population sizes and simulation steps are retained. Empirical mismatches are findings, not reasons to tune survey scores or thresholds.</li>
<li>Elapsed times were observed under concurrent shared-machine load and are not model performance benchmarks. Unknown model pricing is not interpreted as a dollar estimate.</li>
</ul>
<div class="scroll"><table><thead><tr>
{"".join(f"<th>{escape(key)}</th>" for key in fields[:-1])}
</tr></thead><tbody>{"".join(table)}</tbody></table></div>
<h2>Excluded archival/local notebooks</h2>
<p>{escape("; ".join(excluded))}</p>
</html>"""
    args.output.write_text(report, encoding="utf-8")
    print(f"Report saved: {len(rows)} examples, {reviewed} final decisions, {saved} promoted, {len(excluded)} exclusions.")


if __name__ == "__main__":
    main()
