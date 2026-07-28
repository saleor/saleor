"""Analyze Django queryset performance: EXPLAIN ANALYZE, detect issues, upload to Dalibo.

Usage from Django shell:

    import sys; sys.path.insert(0, ".claude/skills/filter-benchmark")
    from analyze_query import analyze, report

    # Analyze one or more querysets
    analyze(filtered_qs, "created_at range")
    analyze(another_qs, "events by type")

    # Print the full report with Dalibo links
    report()
"""

import json
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from django.db import connection

PLANS_DIR = Path("/tmp")


@dataclass
class PlanResult:
    title: str
    plan_default: list
    plan_no_seqscan: list
    execution_time_ms: float
    planning_time_ms: float
    warnings: list[str]
    scan_types: list[str]
    dalibo_url: str | None = None
    file_path: str = ""


_results: list[PlanResult] = []


def _run_explain(sql: str, params: tuple, *, seqscan: bool = True) -> list:
    """Run EXPLAIN ANALYZE with FORMAT JSON."""
    with connection.cursor() as cursor:
        if not seqscan:
            cursor.execute("SET enable_seqscan = OFF;")
        cursor.execute(
            f"EXPLAIN (ANALYZE, COSTS, VERBOSE, BUFFERS, FORMAT JSON) {sql}",
            params,
        )
        plan = cursor.fetchone()[0]
        if not seqscan:
            cursor.execute("SET enable_seqscan = ON;")
    return plan


def _extract_nodes(node: dict, out: list | None = None) -> list[dict]:
    """Recursively extract all plan nodes."""
    if out is None:
        out = []
    out.append(node)
    for child in node.get("Plans", []):
        _extract_nodes(child, out)
    return out


def _analyze_plan(plan: list) -> tuple[list[str], list[str], float, float]:
    """Analyze a JSON plan for warnings and scan types.

    Returns:
        (warnings, scan_types, execution_time_ms, planning_time_ms)

    """
    root = plan[0]
    top_node = root["Plan"]
    execution_time = root.get("Execution Time", 0.0)
    planning_time = root.get("Planning Time", 0.0)

    nodes = _extract_nodes(top_node)
    warnings = []
    scan_types = []

    for node in nodes:
        node_type = node.get("Node Type", "")
        relation = node.get("Relation Name", "")
        actual_rows = node.get("Actual Rows", 0)
        plan_rows = node.get("Plan Rows", 0)
        label = f"{node_type} on {relation}" if relation else node_type
        scan_types.append(label)

        # Red flag: Seq Scan on large tables
        if node_type == "Seq Scan" and actual_rows > 1000:
            warnings.append(
                f"Seq Scan on '{relation}' ({actual_rows} rows) — "
                f"consider adding an index"
            )

        # Red flag: large estimate mismatch
        if plan_rows > 0 and actual_rows > 0:
            ratio = max(actual_rows, plan_rows) / max(min(actual_rows, plan_rows), 1)
            if ratio > 10:
                warnings.append(
                    f"Row estimate mismatch on '{label}': "
                    f"planned {plan_rows}, actual {actual_rows} "
                    f"(ratio {ratio:.0f}x) — run ANALYZE on the table"
                )

        # Red flag: Sort node (may indicate missing index for ORDER BY)
        if node_type == "Sort":
            warnings.append(
                "Explicit Sort node detected — "
                "check if an index could eliminate the sort"
            )

        # Red flag: Nested Loop with Seq Scan inner
        if node_type == "Nested Loop":
            children = node.get("Plans", [])
            for child in children:
                if child.get("Node Type") == "Seq Scan":
                    child_rel = child.get("Relation Name", "?")
                    warnings.append(
                        f"Nested Loop with Seq Scan on inner '{child_rel}' — "
                        f"add index on join/filter columns"
                    )

    return warnings, scan_types, execution_time, planning_time


def _upload_to_dalibo(plan: list, title: str) -> str:
    """Upload a JSON plan to explain.dalibo.com, return the URL."""
    payload = json.dumps(
        {
            "plan": json.dumps(plan),
            "title": title,
            "query": "",
        }
    ).encode()

    req = urllib.request.Request(
        "https://explain.dalibo.com/new",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    resp = urllib.request.urlopen(req, timeout=10)
    return resp.url


def analyze(qs, title: str, *, upload: bool = True) -> PlanResult:
    """Run EXPLAIN ANALYZE on a queryset (both with and without seqscan).

    Detects red flags, saves the JSON plan to /tmp, and optionally uploads
    to explain.dalibo.com.

    Args:
        qs: A Django QuerySet to analyze.
        title: A short descriptive title for this plan.
        upload: Whether to upload the plan to Dalibo (default True).

    Returns:
        PlanResult with all analysis data.

    """
    sql, params = qs.query.sql_with_params()

    # Run with default planner settings
    plan_default = _run_explain(sql, params, seqscan=True)
    # Run with seqscan disabled to check index availability
    plan_no_seqscan = _run_explain(sql, params, seqscan=False)

    warnings, scan_types, exec_time, plan_time = _analyze_plan(plan_default)

    # Check if the planner uses different scan with seqscan off
    _, scan_types_forced, _, _ = _analyze_plan(plan_no_seqscan)
    if scan_types != scan_types_forced:
        warnings.append(
            f"Planner chooses different scan with enable_seqscan=OFF: "
            f"{scan_types_forced} vs default {scan_types}"
        )

    # Save JSON plan to /tmp
    slug = title.lower().replace(" ", "_").replace(":", "")
    fpath = PLANS_DIR / f"explain_{slug}.json"
    with open(fpath, "w") as f:
        json.dump(plan_default, f, indent=2)

    # Upload to Dalibo
    dalibo_url = None
    if upload:
        try:
            dalibo_url = _upload_to_dalibo(plan_default, title)
        except Exception as e:
            print(f"Warning: Dalibo upload failed: {e}")  # noqa: T201

    result = PlanResult(
        title=title,
        plan_default=plan_default,
        plan_no_seqscan=plan_no_seqscan,
        execution_time_ms=exec_time,
        planning_time_ms=plan_time,
        warnings=warnings,
        scan_types=scan_types,
        dalibo_url=dalibo_url,
        file_path=str(fpath),
    )
    _results.append(result)

    # Print quick summary
    status = "OK" if not warnings else f"{len(warnings)} warning(s)"
    print(  # noqa: T201
        f"[{title}] {exec_time:.2f}ms exec, {plan_time:.2f}ms plan — {status}"
    )
    if dalibo_url:
        print(f"  Dalibo: {dalibo_url}")  # noqa: T201
    for w in warnings:
        print(f"  ⚠ {w}")  # noqa: T201

    return result


def report() -> str:
    """Print a full markdown report of all analyzed queries.

    Returns:
        The report as a markdown string.

    """
    if not _results:
        print("No results. Use analyze(qs, title) first.")  # noqa: T201
        return ""

    lines = ["# Filter Benchmark Report", ""]

    # Summary table
    lines.append("## Summary")
    lines.append("")
    lines.append("| Filter | Exec (ms) | Plan (ms) | Warnings | Dalibo |")
    lines.append("|--------|-----------|-----------|----------|--------|")
    for r in _results:
        dalibo = f"[link]({r.dalibo_url})" if r.dalibo_url else "n/a"
        lines.append(
            f"| {r.title} | {r.execution_time_ms:.2f} | "
            f"{r.planning_time_ms:.2f} | {len(r.warnings)} | {dalibo} |"
        )
    lines.append("")

    # Details per query
    for r in _results:
        lines.append(f"## {r.title}")
        lines.append("")
        lines.append(f"- **Execution time**: {r.execution_time_ms:.2f} ms")
        lines.append(f"- **Planning time**: {r.planning_time_ms:.2f} ms")
        lines.append(f"- **Scan types**: {', '.join(r.scan_types)}")
        if r.dalibo_url:
            lines.append(f"- **Dalibo**: {r.dalibo_url}")
        lines.append("")

        if r.warnings:
            lines.append("### Warnings")
            for w in r.warnings:
                lines.append(f"- {w}")
            lines.append("")
        else:
            lines.append("No issues detected.")
            lines.append("")

    text = "\n".join(lines)
    print(text)  # noqa: T201
    return text
