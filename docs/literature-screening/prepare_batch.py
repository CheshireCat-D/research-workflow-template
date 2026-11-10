#!/usr/bin/env python3
"""Convert a reviewed screening sheet into a first-time RWT register-batch file."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


def fields(value, required, optional=()):
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object")
    missing = set(required) - value.keys()
    extra = value.keys() - set(required) - set(optional)
    if missing or extra:
        raise ValueError(f"Missing fields: {sorted(missing)}; unexpected fields: {sorted(extra)}")


def string(value, choices=()):
    if not isinstance(value, str) or not value.strip() or (choices and value not in choices):
        raise ValueError("Expected nonempty text" + (f" from {choices}" if choices else ""))
    return value


def unique_fields(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Repeated JSON field: {key}")
        result[key] = value
    return result


def identifier(value):
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{0,63}", string(value)):
        raise ValueError(f"Invalid or overlong RWT record ID: {value}")
    return value


def prepare(sheet, path, digest):
    fields(sheet, ("id", "question", "search", "criterion", "claim", "reports"))
    group = identifier(sheet["id"])
    fields(sheet["search"], ("date", "channel", "query", "coverage"))
    for text in sheet["search"].values():
        string(text)
    statement = sheet["claim"]
    fields(statement, ("text", "type", "scope"))
    string(statement["text"])
    string(statement["scope"])
    string(statement["type"], ("formal", "empirical", "interpretive", "normative", "design", "question"))
    if not isinstance(sheet["reports"], list) or not sheet["reports"]:
        raise ValueError("Supply at least one screened report")
    batch = []
    def add(kind, **record):
        batch.append({"kind": kind, "record": record})

    add("statement", id=group, **statement)
    sources, relations, locators = set(), [], set()
    for row in sheet["reports"]:
        fields(row, ("key", "title", "locator", "version", "access", "read_at", "position",
                     "decision", "reason"), ("relation",))
        source_id = identifier(group + "." + identifier(row["key"]))
        locator = string(row["locator"])
        if source_id in sources or locator in locators:
            raise ValueError("Repeated report ID or locator; review duplicate entries first")
        decision = string(row["decision"], ("include", "exclude", "defer"))
        access = string(row["access"], ("not-read", "metadata-only", "partial", "full"))
        position = string(row["position"])
        reason = string(row["reason"])
        read_at = string(row["read_at"])
        sources.add(source_id)
        locators.add(locator)
        add("source", id=source_id, title=string(row["title"]), locator=locator,
            version=string(row["version"]), content_access=access,
            extensions={"screening": {"decision": decision, "reason": reason,
                                      "read_at": read_at, "position": position}})
        if decision != "include":
            if "relation" in row:
                raise ValueError(f"{source_id}: only included reports may supply a claim relation")
            continue
        if access not in ("partial", "full") or "relation" not in row:
            raise ValueError(f"{source_id}: include requires checked material and a reviewed relation")
        link = row["relation"]
        fields(link, ("kind", "rationale", "scope"))
        relation = string(link["kind"], ("supports", "qualifies", "challenges", "contextualizes", "derived_from"))
        add("evidence", id=source_id, type="source-reading", source_ids=[source_id],
            description=position, provenance=string(row["title"]),
            location={"kind": "external", "locator": read_at, "access_note": position})
        add("relation", id=source_id, evidence_id=source_id, statement_id=group,
            relation=relation, rationale=string(link["rationale"]), scope=string(link["scope"]))
        relations.append("relation:" + source_id)

    add("evidence", id=group, type="screening-decisions", description=string(sheet["criterion"]),
        location={"kind": "local", "path": path}, provenance=string(sheet["question"]),
        source_ids=sorted(sources), extensions={"search": sheet["search"], "prepared_sha256": digest})
    unresolved = [r["key"] for r in sheet["reports"] if r["decision"] == "defer"]
    add("activity", id=group, title="Screen selected reports: " + sheet["question"], status="done",
        inputs=["evidence:" + group, "statement:" + group], outputs=relations,
        note="Deferred reports: " + (", ".join(unresolved) if unresolved else "none"))
    if unresolved:
        add("activity", id=identifier(group + ".followup"), title="Review deferred reports", status="pending",
            depends_on=[group], inputs=["source:" + group + "." + key for key in unresolved],
            note="Use each source's screening reason to resolve the outstanding question.")
    return batch


def register(runtime, root, sheet, path, digest, data, next_action):
    """Submit checked bytes, then inspect the actual binding through RWT's public CLI."""
    cli = [sys.executable, "-I", "-X", "utf8", "-B", str(runtime)]
    group = sheet["id"]
    followup = any(row["decision"] == "defer" for row in sheet["reports"])
    saved = subprocess.run([*cli, "register-batch", "--root", str(root), "--file", "-",
                            "--activity", group + (".followup" if followup else ""),
                            "--next-action", next_action], input=data, stdout=subprocess.PIPE)
    if not saved.stdout:
        return saved.returncode or 2
    result = json.loads(saved.stdout)
    if not result.get("registered"):
        sys.stdout.buffer.write(saved.stdout)
        return saved.returncode or 2
    show = subprocess.run([*cli, "show", "--root", str(root), "--kind", "evidence", "--id", group],
                          stdout=subprocess.PIPE)
    bound_digest = None
    if show.returncode == 0:
        bound_digest = json.loads(show.stdout)["envelope"]["bindings"]["files"].get(path)
    result["screening_sheet_verified"] = bound_digest == digest
    if not result["screening_sheet_verified"]:
        result["passed"] = False
        result["screening_error"] = "Batch saved. Review the registered sheet binding before continuing."
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="Existing research project")
    parser.add_argument("--sheet", required=True, help="Project-relative screening sheet (use /)")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--output", type=Path, help="New batch file")
    action.add_argument("--register", type=Path, help="Verify and submit a previously prepared batch")
    parser.add_argument("--next-action", help="Next task to save with --register")
    parser.add_argument("--runtime", type=Path, help="Path to RWT tools/research.py (defaults to this checkout)")
    args = parser.parse_args()
    if args.register and (not args.next_action or not args.next_action.strip()):
        parser.error("--register requires a nonempty --next-action")
    if args.output and (args.next_action or args.runtime):
        parser.error("--next-action and --runtime apply to --register")
    try:
        parts = args.sheet.split("/")
        if any(p in ("", ".", "..") for p in parts) or "\\" in args.sheet or ":" in args.sheet:
            raise ValueError("Use a project-relative file path with / separators")
        root = args.root.resolve(strict=True)
        path = root.joinpath(*parts)
        if not path.is_file() or path.resolve(strict=True) != path:
            raise ValueError("The screening sheet must be an ordinary file inside the project")
        limit = 8 * 1024 * 1024
        with path.open("rb") as source:
            raw = source.read(limit + 1)
        if len(raw) > limit:
            raise ValueError("Screening sheet exceeds the 8 MiB input limit")
        sheet = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_fields)
        digest = hashlib.sha256(raw).hexdigest()
        batch = prepare(sheet, args.sheet, digest)
        data = (json.dumps(batch, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        if len(data) > limit:
            raise ValueError("Prepared batch exceeds the RWT 8 MiB input limit")
        if args.register:
            with args.register.open("rb") as existing:
                if existing.read(limit + 1) != data:
                    raise ValueError("Sheet or batch changed; review the sheet and prepare a fresh batch")
            runtime = args.runtime or Path(__file__).resolve().parents[2] / "tools/research.py"
            return register(runtime, root, sheet, args.sheet, digest, data, args.next_action)
        with args.output.open("xb") as target:
            target.write(data)
    except (OSError, ValueError, TypeError, RecursionError) as error:
        parser.exit(2, f"Screening batch: {error}\n")
    print(f"Prepared {len(batch)} records in {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
