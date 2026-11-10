"""Check a project-specific Chinese thesis handoff. Print a read-only JSON report."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from zipfile import BadZipFile, ZipFile

WORD = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
CONTENT_TYPES = "{http://schemas.openxmlformats.org/package/2006/content-types}"


def fields(obj, required, optional=()):
    if not isinstance(obj, dict):
        raise ValueError("Expected a JSON object")
    missing = set(required) - obj.keys()
    unknown = obj.keys() - set(required) - set(optional)
    if missing or unknown:
        raise ValueError(f"Missing fields {sorted(missing)}, unknown fields {sorted(unknown)}")


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def text(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Expected nonempty text")
    return value.strip()


def local(root, value):
    relative = Path(text(value))
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"Expected a project-relative file: {value}")
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"File resolves outside this project: {value}")
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"File is missing or empty: {value}")
    return path


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def paragraphs(path):
    with ZipFile(path) as archive:
        kinds = ET.fromstring(archive.read("[Content_Types].xml"))
        if not any(t.get("PartName") == "/word/document.xml" and
                   t.get("ContentType") == "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"
                   for t in kinds.findall(CONTENT_TYPES + "Override")):
            raise ValueError("Not a DOCX main document")
        body = ET.fromstring(archive.read("word/document.xml")).find(WORD + "body")
        if body is None:
            raise ValueError("DOCX has no Word document body")
        result = []
        for p in body.iter(WORD + "p"):
            words = "".join(t.text or "" for t in p.iter(WORD + "t"))
            style = p.find(WORD + "pPr/" + WORD + "pStyle")
            result.append((" ".join(words.split()), style.get(WORD + "val") if style is not None else None))
        return result


def pdf_pages(path):
    with path.open("rb") as stream:
        if b"%PDF-" not in stream.read(1024):
            raise ValueError("PDF signature is missing")
    if shutil.which("pdftotext"):
        proc = subprocess.run(["pdftotext", "-enc", "UTF-8", str(path), "-"],
                              capture_output=True, timeout=90)
        if proc.returncode:
            return None, "pdftotext could not extract the document"
        pages = proc.stdout.decode("utf-8").split("\f")
        if pages and not pages[-1].strip():
            pages.pop()
        return pages, "pdftotext"
    try:
        from pypdf import PdfReader
    except ImportError:
        return None, "Install pdftotext or use a Python interpreter with pypdf"
    try:
        with path.open("rb") as stream:
            reader = PdfReader(stream)
            pages = [page.extract_text() or "" for page in reader.pages]
        return pages, "pypdf"
    except Exception as exc:
        return None, f"pypdf could not extract the document: {type(exc).__name__}"


def page_coverage(spec, page_count):
    covered = set()
    for token in text(spec).split(","):
        match = re.fullmatch(r"\s*([0-9]+)(?:-([0-9]+))?\s*", token)
        if not match:
            raise ValueError("pages must use one-based numbers or ranges")
        first = int(match[1])
        last = int(match[2] or first)
        if not 1 <= first <= last <= page_count:
            raise ValueError("review page outside the current PDF")
        covered.update(range(first, last + 1))
    return len(covered) == page_count


def check_numbered(config, body, record):
    fields(config, ["body_heading", "reference_heading"], ["end_heading", "sources"])
    words = [paragraph for paragraph, _style in body]
    indices = []
    for key in ("body_heading", "reference_heading", "end_heading"):
        if key not in config:
            break
        heading = text(config[key])
        hits = [i for i, paragraph in enumerate(words) if paragraph == heading]
        if len(hits) != 1:
            record("citations/scope", "pending", f"Expected one exact heading: {heading}")
            return
        indices.append(hits[0])
    if len(indices) == 2:
        indices.append(len(words))
    start, split, end = indices
    if not start < split < end:
        raise ValueError("Citation section headings out of order")

    numbered = re.compile(r"^[\[［]([0-9]+)[\]］]\s*\S")
    reference_ids = [int(match[1]) for line in words[split + 1:end] if (match := numbered.match(line))]
    if not reference_ids:
        record("citations/bibliography", "pending", "No explicit bracket-numbered bibliography entries in range")
        return
    reference_set = set(reference_ids)
    seq_ok = reference_ids == list(range(1, len(reference_ids) + 1))
    record("citations/bibliography", "pass" if seq_ok else "mismatch", {"printed_numbers": reference_ids})
    cited = {}
    invalid = []
    brackets = re.compile(r"[\[［]([0-9][0-9\s,，、\-–—]*)[\]］]")
    for line in words[start + 1:split]:
        for expression in brackets.findall(line):
            for item in re.split("[,，、]", expression):
                pair = re.fullmatch(r"\s*([0-9]+)(?:\s*[-–—]\s*([0-9]+))?\s*", item)
                if not pair:
                    invalid.append(item)
                    continue
                first, last = int(pair[1]), int(pair[2] or pair[1])
                if first < 1 or last < first or last - first >= len(reference_ids):
                    invalid.append(item)
                    continue
                for number in range(first, last + 1):
                    cited[number] = None
    missing = sorted(cited.keys() - reference_set)
    unused = sorted(reference_set - cited.keys())
    order_ok = list(cited) == sorted(cited)
    if invalid or missing or not order_ok:
        status = "mismatch"
    elif not cited or unused:
        status = "pending"
    else:
        status = "pass"
    record("citations/body", status, {"first_use": list(cited), "missing_references": missing,
                                     "unseen_in_body": unused, "invalid_tokens": invalid})
    if "sources" not in config:
        return
    ledger = config["sources"]
    if not isinstance(ledger, list):
        raise ValueError("sources must be an array")
    mapped = set()
    for entry in ledger:
        fields(entry, ["number", "origin", "status", "location"])
        n = entry["number"]
        if type(n) is not int or n < 1 or n in mapped:
            raise ValueError("Source ledger numbers must be positive and unique")
        mapped.add(n)
        state = entry["status"]
        if state not in ("original_checked", "metadata_only", "unavailable"):
            raise ValueError("Unknown source ledger status")
        record(f"source/{n}", "pass" if state == "original_checked" else "pending",
               {"recorded_status": state, "origin": text(entry["origin"]), "location": text(entry["location"])})
    record("citations/ledger", "pass" if mapped == reference_set else "pending",
           {"unmapped_entries": sorted(reference_set - mapped), "outside_bibliography": sorted(mapped - reference_set)})


def check(manifest):
    cfg = json.loads(manifest.read_text(encoding="utf-8"), object_pairs_hook=unique_keys)
    fields(cfg, ["institution", "degree", "basis", "docx", "pdf", "anchors"], ["materials", "visual_review", "numbered_references", "section_order"])
    root = manifest.parent
    basis = cfg["basis"]
    fields(basis, ["file", "locator"])
    report = {"institution": text(cfg["institution"]), "degree": text(cfg["degree"]),
              "requirements": {"file": basis["file"], "locator": text(basis["locator"]),
                               "sha256": sha(local(root, basis["file"]))},
              "files": {}, "checks": []}

    def record(name, status, detail):
        report["checks"].append({"name": name, "status": status, "detail": detail})

    docx, pdf = (local(root, cfg[key]) for key in ("docx", "pdf"))
    for key, path in (("docx", docx), ("pdf", pdf)):
        report["files"][key] = {"path": cfg[key], "sha256": sha(path)}
    body = paragraphs(docx)
    pages, engine = pdf_pages(pdf)
    report["pdf_extractor"] = engine
    report["page_count"] = len(pages) if pages is not None else None
    pagetext = [" ".join(page.split()) for page in pages or []]
    searchable = any(pagetext)
    if not searchable:
        record("pdf_text", "pending", "No searchable PDF text available; review the export visually")

    if not isinstance(cfg["anchors"], list) or not cfg["anchors"]:
        raise ValueError("Supply at least one real passage to check across editions")
    labels = set()
    for anchor in cfg["anchors"]:
        fields(anchor, ["label", "text"], ["style"])
        label, snippet = text(anchor["label"]), " ".join(text(anchor["text"]).split())
        if label in labels:
            raise ValueError(f"Duplicate anchor label: {label}")
        labels.add(label)
        matches = [style for words, style in body if snippet in words]
        record(f"{label}/docx", "pass" if matches else "mismatch", "Body paragraph text")
        if "style" in anchor:
            style = text(anchor["style"])
            record(f"{label}/style", "pass" if style in matches else "mismatch", f"Explicit Word paragraph style ID: {style}")
        locations = [i for i, value in enumerate(pagetext, 1) if snippet in value]
        status = "pass" if locations else ("mismatch" if searchable and all(pagetext) else "pending")
        record(f"{label}/pdf", status, {"matched_pages": locations})

    if "section_order" in cfg:
        order = cfg["section_order"]
        if not isinstance(order, list) or not order or any(not isinstance(v, str) or not v.strip() for v in order):
            raise ValueError("section_order must list nonempty heading texts")
        if len(set(order)) != len(order):
            raise ValueError("section_order headings must be distinct")
        positions = {h: [i for i, (words, _style) in enumerate(body, 1) if words == h] for h in order}
        if any(not hits for hits in positions.values()):
            status = "mismatch"
        elif any(len(hits) != 1 for hits in positions.values()):
            status = "pending"
        else:
            sequence = [v[0] for v in positions.values()]
            status = "pass" if sequence == sorted(sequence) else "mismatch"
        record("sections/docx", status, positions)

    if "numbered_references" in cfg:
        check_numbered(cfg["numbered_references"], body, record)

    materials = cfg.get("materials", [])
    if not isinstance(materials, list):
        raise ValueError("materials must be an array")
    for item in materials:
        fields(item, ["file", "use", "applies", "basis"])
        name = text(item["file"])
        reason = {"use": text(item["use"]), "basis": text(item["basis"])}
        if item["applies"] is None:
            record(name, "pending", reason)
        elif type(item["applies"]) is not bool:
            raise ValueError("applies must be true, false or null")
        elif item["applies"]:
            try:
                reason["sha256"] = sha(local(root, name))
                record(name, "pass", reason)
            except (OSError, ValueError) as exc:
                record(name, "mismatch", {**reason, "finding": str(exc)})
        else:
            record(name, "not_applicable", reason)

    review = cfg.get("visual_review")
    if review is None:
        record("visual_review", "pending", "No version-bound page inspection recorded")
    else:
        fields(review, ["note", "renderer", "docx_sha256", "pdf_sha256", "pages", "outcome"])
        note = local(root, review["note"])
        detail = {"renderer": text(review["renderer"]), "note": review["note"], "note_sha256": sha(note)}
        if review["outcome"] not in ("clear", "issues"):
            raise ValueError("outcome must be clear or issues")
        if any(review[key + "_sha256"] != report["files"][key]["sha256"] for key in ("pdf", "docx")):
            record("visual_review", "pending", {**detail, "finding": "Review belongs to another version"})
        elif review["outcome"] == "issues":
            record("visual_review", "mismatch", {**detail, "finding": "Page inspection recorded unresolved issues"})
        elif not pages or not page_coverage(review["pages"], len(pages)):
            record("visual_review", "pending", {**detail, "finding": "Full page coverage not established"})
        else:
            record("visual_review", "pass", {**detail, "scope": "Supplied inspection record covers these file versions and pages"})
    states = {c["status"] for c in report["checks"]}
    code = 1 if "mismatch" in states else 2 if "pending" in states else 0
    report["status"] = {0: "configured_checks_pass", 1: "mismatch", 2: "needs_review"}[code]
    return report, code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    try:
        report, code = check(parser.parse_args().manifest.resolve())
    except (OSError, ValueError, KeyError, RuntimeError, ET.ParseError, BadZipFile, subprocess.TimeoutExpired) as exc:
        report, code = {"status": "invalid_input", "detail": str(exc)}, 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
