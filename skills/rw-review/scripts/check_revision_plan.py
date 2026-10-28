#!/usr/bin/env python3
"""Read-only checks of a declared revision plan; standard library only."""

import argparse
from fractions import Fraction
import json
import math
from pathlib import Path, PureWindowsPath
import sys


SEVERITIES = {"blocking", "major", "minor", "optional"}
DECISIONS = {"accept", "partial", "clarify", "decline", "defer"}
STATUSES = {"planned", "in_progress", "blocked", "done"}
SCOPE = (
    "Checks only declared review-plan structure, dependencies, effort, and quoted "
    "UTF-8 file locations; it does not assess scientific correctness or submission readiness."
)


def _report(delivery):
    return {
        "passed": False,
        "mode": "delivery" if delivery else "plan",
        "scope": SCOPE,
        "errors": [],
        "batches": [],
        "dependency_order_complete": False,
        "known_effort_hours": 0,
        "unknown_effort_items": [],
        "budget": {"status": "not_provided", "available_hours": None},
        "unfinished": [],
        "deferred": [],
        "declined": [],
    }


def _nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def _hours(value):
    return (
        type(value) in (int, float)
        and value >= 0
        and (type(value) is int or math.isfinite(value))
    )


def validate_plan(plan, root, *, delivery=False):
    """Return a JSON-serializable report without changing the plan or any files."""
    result = _report(delivery)
    errors = result["errors"]

    def error(code, location, message):
        errors.append({"code": code, "location": location, "message": message})

    try:
        root_path = Path(root).resolve(strict=True)
        if not root_path.is_dir():
            raise ValueError("root must be an existing directory")
    except (OSError, ValueError, TypeError, RuntimeError) as exc:
        error("invalid_root", "root", str(exc))
        root_path = None

    def locator(value, location):
        if not isinstance(value, dict):
            error("invalid_locator", location, "Expected an object with path and quote.")
            return
        name, quote = value.get("path"), value.get("quote")
        if not _nonempty(name):
            error("invalid_path", location + ".path", "Path must be a nonempty relative string.")
            return
        windows = PureWindowsPath(name)
        relative = Path(name.replace("\\", "/"))
        if (relative.is_absolute() or windows.drive or windows.root
                or ".." in relative.parts or "\x00" in name):
            error("unsafe_path", location + ".path", "Absolute paths, drives, and .. are forbidden.")
            return
        if not _nonempty(quote):
            error("invalid_quote", location + ".quote", "Quote must be a nonempty exact string.")
            return
        if root_path is None:
            return
        try:
            target = (root_path / relative).resolve(strict=True)
            if not target.is_relative_to(root_path):
                error("unsafe_path", location + ".path", "Resolved path escapes root, including via symlinks.")
                return
            if not target.is_file():
                raise ValueError("Location must name a regular file.")
            with target.open(encoding="utf-8", newline="") as stream:
                content = stream.read()
        except (OSError, ValueError, RuntimeError) as exc:
            error("unreadable_location", location + ".path", str(exc))
            return
        first = content.find(quote)
        if first < 0:
            error("quote_not_found", location + ".quote", "Exact quote does not occur in the file.")
        elif content.find(quote, first + 1) >= 0:
            error("ambiguous_quote", location + ".quote", "Exact quote occurs more than once, including overlaps.")

    if not isinstance(plan, dict):
        error("invalid_plan", "$", "Plan must be a JSON object.")
        return result

    sources = plan.get("sources")
    if not isinstance(sources, list):
        error("invalid_sources", "sources", "Expected a list of source objects.")
        sources = []
    elif not sources:
        error("empty_sources", "sources", "At least one original review comment is required.")
    source_ids = set()
    for index, source in enumerate(sources):
        location = f"sources[{index}]"
        if not isinstance(source, dict):
            error("invalid_source", location, "Expected a source object.")
            continue
        source_id = source.get("id")
        if not _nonempty(source_id):
            error("invalid_source_id", location + ".id", "ID must be a nonempty string.")
        elif source_id in source_ids:
            error("duplicate_source_id", location + ".id", f"Duplicate source ID: {source_id}")
        else:
            source_ids.add(source_id)
        if not _nonempty(source.get("text")):
            error("invalid_source_text", location + ".text", "Original source text must be nonempty.")

    items = plan.get("items")
    if not isinstance(items, list):
        error("invalid_items", "items", "Expected a list of item objects.")
        items = []
    elif not items:
        error("empty_items", "items", "At least one revision item is required.")
    records, covered = {}, set()
    graph_valid, effort_valid = bool(sources) and bool(items), True
    known_efforts = []
    for index, item in enumerate(items):
        location = f"items[{index}]"
        if not isinstance(item, dict):
            error("invalid_item", location, "Expected an item object.")
            graph_valid = False
            continue
        item_id = item.get("id")
        unique_id = _nonempty(item_id) and item_id not in records
        if not _nonempty(item_id):
            error("invalid_item_id", location + ".id", "ID must be a nonempty string.")
            graph_valid = False
        elif not unique_id:
            error("duplicate_item_id", location + ".id", f"Duplicate item ID: {item_id}")
            graph_valid = False
        else:
            records[item_id] = item
        source_id = item.get("source_id")
        if not _nonempty(source_id):
            error("invalid_source_id", location + ".source_id", "Source ID must be a nonempty string.")
        elif source_id not in source_ids:
            error("unknown_source_id", location + ".source_id", f"Unknown source ID: {source_id}")
        else:
            covered.add(source_id)
        for field, allowed in (("severity", SEVERITIES), ("decision", DECISIONS), ("status", STATUSES)):
            value = item.get(field)
            if not isinstance(value, str) or value not in allowed:
                error("invalid_" + field, location + "." + field,
                      "Expected one of: " + ", ".join(sorted(allowed)))
        dependencies = item.get("depends_on")
        if not isinstance(dependencies, list):
            error("invalid_dependencies", location + ".depends_on", "Expected a list of item IDs.")
            graph_valid = False
        else:
            seen = set()
            for dep_index, dependency in enumerate(dependencies):
                dep_location = f"{location}.depends_on[{dep_index}]"
                if not _nonempty(dependency):
                    error("invalid_dependency_id", dep_location, "Dependency ID must be a nonempty string.")
                    graph_valid = False
                elif dependency in seen:
                    error("duplicate_dependency", dep_location, f"Repeated dependency: {dependency}")
                    graph_valid = False
                else:
                    seen.add(dependency)
        if "effort_hours" in item:
            if not _hours(item["effort_hours"]):
                error("invalid_effort_hours", location + ".effort_hours",
                      "Hours must be a finite nonnegative number, excluding booleans.")
                effort_valid = False
            elif unique_id:
                known_efforts.append(item["effort_hours"])
        elif unique_id:
            result["unknown_effort_items"].append(item_id)
        decision = item.get("decision")
        if delivery and isinstance(decision, str) and decision in {"clarify", "decline", "defer"}:
            if not _nonempty(item.get("reason")):
                error("missing_reason", location + ".reason", "This delivery decision requires a nonempty reason.")
        elif "reason" in item and not _nonempty(item["reason"]):
            error("invalid_reason", location + ".reason", "A supplied reason must be a nonempty string.")
        if "reply" in item:
            locator(item["reply"], location + ".reply")
        elif delivery:
            error("missing_reply", location + ".reply", "Each delivery item requires a reply location.")
        changes = item.get("changes", [])
        if not isinstance(changes, list):
            error("invalid_changes", location + ".changes", "Expected a list of change locations.")
        else:
            for change_index, change in enumerate(changes):
                locator(change, f"{location}.changes[{change_index}]")
            if (delivery and isinstance(decision, str) and decision in {"accept", "partial"}
                    and item.get("status") == "done" and not changes):
                error("missing_changes", location + ".changes", "A completed accepted item requires a change location.")

    for source_id in sorted(source_ids - covered):
        error("uncovered_source", "sources", f"Source has no item: {source_id}")
    for item_id, item in records.items():
        dependencies = item.get("depends_on")
        if not isinstance(dependencies, list):
            continue
        for dependency in dependencies:
            if not _nonempty(dependency):
                continue
            if dependency == item_id:
                error("self_dependency", f"item:{item_id}.depends_on", "An item cannot depend on itself.")
                graph_valid = False
            elif dependency not in records:
                error("unknown_dependency", f"item:{item_id}.depends_on", f"Unknown item ID: {dependency}")
                graph_valid = False
            elif item.get("status") == "done" and records[dependency].get("status") != "done":
                error("incomplete_dependency", f"item:{item_id}.depends_on",
                      f"Completed item still has an unfinished prerequisite: {dependency}")
    if graph_valid:
        remaining = {key: set(value["depends_on"]) for key, value in records.items()}
        batches = []
        while remaining:
            batch = [key for key, dependencies in remaining.items() if not dependencies]
            if not batch:
                error("dependency_cycle", "items", "A cycle prevents ordering these items: " + ", ".join(remaining))
                graph_valid = False
                break
            batches.append(batch)
            for item_id in batch:
                del remaining[item_id]
            for dependencies in remaining.values():
                dependencies.difference_update(batch)
        if graph_valid:
            result["batches"] = batches
            result["dependency_order_complete"] = True

    try:
        exact_total = sum((Fraction(str(value)) for value in known_efforts), Fraction())
        total = float(exact_total) if any(type(value) is float for value in known_efforts) else int(exact_total)
        if type(total) is float and not math.isfinite(total):
            raise OverflowError("Known effort total exceeds finite numeric range.")
        json.dumps(total, allow_nan=False)
    except (OverflowError, ValueError) as exc:
        total, effort_valid = None, False
        error("invalid_effort_total", "items", str(exc))
    result["known_effort_hours"] = total
    if "available_hours" in plan:
        available = plan["available_hours"]
        if not _hours(available):
            error("invalid_available_hours", "available_hours",
                  "Hours must be a finite nonnegative number, excluding booleans.")
            result["budget"]["status"] = "invalid"
        else:
            result["budget"]["available_hours"] = available
            if not effort_valid:
                result["budget"]["status"] = "invalid"
            elif exact_total > Fraction(str(available)):
                result["budget"]["status"] = "over_budget"
                error("over_budget", "available_hours", "Known effort already exceeds available hours.")
            elif result["unknown_effort_items"]:
                result["budget"]["status"] = "undetermined"
                error("budget_unknown_effort", "items", "Budget cannot be confirmed while item effort is unknown.")
            else:
                result["budget"]["status"] = "within_budget"
    for item_id, item in records.items():
        summary = {key: item.get(key) if isinstance(item.get(key), str) else None
                   for key in ("id", "source_id", "severity", "decision", "status")}
        if _nonempty(item.get("reason")):
            summary["reason"] = item["reason"]
        if item.get("status") != "done":
            result["unfinished"].append(summary)
        if item.get("decision") == "defer":
            result["deferred"].append(summary)
        if item.get("decision") == "decline":
            result["declined"].append(summary)
    result["passed"] = not errors
    return result


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


def main(argv=None):
    parser = _Parser(add_help=False)
    parser.add_argument("plan", nargs="?")
    parser.add_argument("--root")
    parser.add_argument("--delivery", action="store_true")
    parser.add_argument("--help", action="store_true")
    delivery = False
    try:
        args = parser.parse_args(argv)
        delivery = args.delivery
        if args.help:
            print(json.dumps({"passed": True, "usage": "python check_revision_plan.py PLAN.json [--root DIR] [--delivery]",
                              "scope": SCOPE}))
            return 0
        if not args.plan:
            raise ValueError("PLAN.json is required.")
    except ValueError as exc:
        result = _report(delivery)
        result["errors"].append({"code": "arguments_error", "location": "cli", "message": str(exc)})
    else:
        try:
            plan_path = Path(args.plan)
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, RuntimeError) as exc:
            result = _report(delivery)
            result["errors"].append({"code": "plan_read_error", "location": "plan", "message": str(exc)})
        else:
            result = validate_plan(plan, args.root if args.root is not None else plan_path.parent,
                                   delivery=delivery)
    print(json.dumps(result, allow_nan=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
