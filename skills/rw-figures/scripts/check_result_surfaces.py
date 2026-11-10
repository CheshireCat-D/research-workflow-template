"""Check result-table excerpts on named manuscript, caption or figure surfaces."""
import argparse
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET


def digest(data):
    return hashlib.sha256(data).hexdigest()


def stream_hash(path, destination=None):
    checksum = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            checksum.update(chunk)
            if destination is not None:
                destination.write(chunk)
    return checksum.hexdigest()


def unique_fields(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError(f"Duplicate JSON key: {name}")
        result[name] = value
    return result


def local_file(base, name):
    if not isinstance(name, str) or not name.strip() or Path(name).is_absolute():
        raise ValueError("Expected a project-relative file path")
    base = base.resolve()
    path = (base / name).resolve()
    if not path.is_relative_to(base) or not path.is_file():
        raise ValueError(f"Missing file or path outside the project: {name}")
    return path


def read_rows(raw, key):
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""))
    names = reader.fieldnames or []
    if not key or key not in names or len(set(names)) != len(names) or "" in names:
        raise ValueError("The table needs distinct column names and an existing ID column")
    rows = {}
    for row in reader:
        if None in row or None in row.values():
            raise ValueError(f"Broken CSV row at line {reader.line_num}")
        identity = row[key].strip()
        if not identity or identity in rows:
            raise ValueError(f"Empty or duplicate row ID at line {reader.line_num}")
        rows[identity] = row
    return rows


# Only direct CSV column names and a small, bounded decimal display format.
FIELD = re.compile(r"\{([^{}:]+?)(?::(\+?\.(?:[0-9]|1[0-2])f))?\}")


def expected_text(template, row):
    if not isinstance(template, str) or not FIELD.search(template) or re.search(r"[{}]", FIELD.sub("", template)):
        raise ValueError("Expected a literal excerpt with {column} or {column:.2f}")
    def substitute(match):
        key, spec = match.groups()
        if key not in row or not row[key].strip():
            raise ValueError(f"Missing reference value for column {key}")
        value = row[key].strip()
        if spec:
            try:
                number = Decimal(value)
            except InvalidOperation as error:
                raise ValueError(f"Expected a decimal in {key}") from error
            if not number.is_finite() or abs(number.adjusted()) > 1000:
                raise ValueError(f"Unsupported decimal in {key}")
            return format(number, spec)
        return value
    return FIELD.sub(substitute, template)


def surface_lines(path, data):
    if path.suffix.lower() in {".md", ".txt", ".tex"}:
        return data.decode("utf-8-sig").splitlines()
    if path.suffix.lower() == ".svg":
        root = ET.fromstring(data)
        if root.tag.split("}")[-1] != "svg":
            raise ValueError("Expected an SVG document")
        return ["".join(el.itertext()) for el in root.iter() if el.tag.split("}")[-1] == "text"]
    return None


def normal(value):
    return " ".join(value.split())


def match_excerpt(lines, check, expected):
    anchor = normal(check["after"])
    if not anchor:
        raise ValueError("Each check needs a non-empty, unique after anchor")
    # An anchor selects a line, and optionally an explicitly delimited run of lines.
    text = "\n".join(normal(line) for line in lines)
    if text.count(anchor) != 1:
        return "mismatch", "Anchor missing or ambiguous"
    region = text.split(anchor, 1)[1]
    if "before" in check:
        end = normal(check["before"])
        if not end or end not in region:
            return "mismatch", "End anchor missing after the start"
        region = region.split(end, 1)[0]
    else:
        region = region.split("\n", 1)[0]
    literal = normal(expected)
    pattern = re.escape(literal)
    if literal[-1].isalnum():
        pattern += r"(?![\w]|\.\d)"
    # Match immediately after the anchor; a correct number in the sensitivity claim cannot rescue a stale headline.
    present = re.match(pattern, normal(region)) is not None
    return ("matched", "Expected excerpt located") if present else ("mismatch", "Expected excerpt absent from the selected region")


def preview_page(base, source, page, output):
    path = local_file(base, source)
    if path.suffix.lower() != ".pdf" or page < 1 or output.suffix.lower() != ".png":
        raise ValueError("Preview requires a project PDF, a positive page and a .png output")
    report = {"pdf": source, "page": page, "visual_review": "not_performed"}
    engine = shutil.which("pdftoppm")
    if engine is None:
        return {**report, "sha256": stream_hash(path), "status": "not_checked", "reason": "pdftoppm unavailable"}
    with tempfile.TemporaryDirectory() as dest:
        local = Path(dest)
        with (local / "input.pdf").open("wb") as pdf:
            report["sha256"] = stream_hash(path, pdf)
        result = subprocess.run([engine, "-f", str(page), "-l", str(page), "-singlefile",
                                 "-scale-to", "1400", "-png", "input.pdf", "page"],
                                cwd=local, capture_output=True, timeout=60)
        generated = local / "page.png"
        if result.returncode or not generated.is_file():
            return {**report, "status": "not_checked", "reason": "PDF page could not be rendered"}
        image = generated.read_bytes()
        if not image.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError("Renderer returned an invalid PNG header")
        with output.open("xb") as stream:
            try:
                stream.write(image)
                stream.flush()
            except OSError:
                stream.close()
                output.unlink(missing_ok=True)
                raise
    return {**report, "status": "rendered", "png": output.name, "png_sha256": digest(image)}


def audit(plan_file, render=None, page=1, output=None):
    base = plan_file.resolve().parent
    plan = json.loads(plan_file.read_text(encoding="utf-8-sig"), object_pairs_hook=unique_fields)
    if not isinstance(plan, dict) or set(plan) != {"table", "id_column", "checks"} or not isinstance(plan["checks"], list) or not plan["checks"]:
        raise ValueError("Supply at least one check")
    data = local_file(base, plan["table"]).read_bytes()
    rows = read_rows(data, plan["id_column"])
    report = {"table": plan["table"], "table_sha256": digest(data), "checks": []}
    surfaces = {}
    for check in plan["checks"]:
        if (not isinstance(check, dict) or set(check) - {"row", "file", "after", "expect", "before"}
                or not all(isinstance(check.get(k), str) for k in ("row", "file", "after", "expect"))
                or ("before" in check and not isinstance(check["before"], str))):
            raise ValueError("Each check needs row, file, after and expect strings")
        name = check["file"]
        if name not in surfaces:
            path = local_file(base, name)
            if path.suffix.lower() in {".svg", ".md", ".txt", ".tex"}:
                raw = path.read_bytes()
                surfaces[name] = (digest(raw), surface_lines(path, raw))
            else:
                surfaces[name] = (stream_hash(path), None)
        file_hash, lines = surfaces[name]
        expected = expected_text(check["expect"], rows[check["row"]])
        if lines is None:
            status, reason = "not_checked", "Text extraction unavailable for this format"
        else:
            status, reason = match_excerpt(lines, check, expected)
        report["checks"].append({"row": check["row"], "file": name, "sha256": file_hash, "after": check["after"],
                                 "expected": expected, "status": status, "reason": reason})
    if render:
        report["preview"] = preview_page(base, render, page, output)
    verdicts = [r["status"] for r in report["checks"]]
    if report.get("preview", {}).get("status") == "not_checked":
        verdicts.append("not_checked")
    report["status"] = "mismatch" if "mismatch" in verdicts else "not_checked" if "not_checked" in verdicts else "matched"
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--render", metavar="PROJECT_PDF", help="Render a PDF page for a reader")
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--output", type=Path, help="New output PNG; existing files are preserved")
    args = parser.parse_args()
    if bool(args.render) != bool(args.output):
        parser.error("--render and --output go together")
    try:
        response = audit(args.plan, args.render, args.page, args.output)
        code = {"matched": 0, "mismatch": 1, "not_checked": 2}[response["status"]]
    except (OSError, KeyError, TypeError, ValueError, AttributeError, csv.Error, ET.ParseError, subprocess.TimeoutExpired) as error:
        response, code = {"status": "error", "reason": str(error)}, 2
    print(json.dumps(response, ensure_ascii=True, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
