#!/usr/bin/env python3
"""Read-only structural checks for a self-contained, editable SVG schematic.

This is not a renderer, a complete SVG validator, or a scientific/geometry audit.
Only UTF-8 XML and absolute canvas units are supported. No resources are loaded.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import sys
from xml.etree import ElementTree as ET


FORMAT = "rw-figures/svg-audit@1"
NUMBER = r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?"
LENGTH = re.compile(rf"^\s*({NUMBER})\s*(px|pt|pc|mm|cm|in)\s*$")
URL = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.IGNORECASE)
LIMITS = [
    "Does not certify scientific meaning or correspondence with sources.",
    "Does not detect layout collisions, arrow endpoints, final font size or color accessibility.",
    "Native text counts do not prove that every visible label is editable.",
    "Does not authenticate image data or execute/render SVG.",
]


def local(name: str) -> str:
    return name.rsplit("}", 1)[-1]


def result(path: str | None = None) -> dict:
    return {"format": FORMAT, "path": path, "status": "not-auditable",
            "findings": [], "counts": {}, "limitations": LIMITS.copy()}


def finding(report: dict, severity: str, code: str, message: str) -> None:
    report["findings"].append({"severity": severity, "code": code, "message": message})


def audit_svg(data: bytes, path: str | None = None) -> dict:
    """Inspect bytes in memory without loading resources or mutating anything."""
    report = result(path)
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        finding(report, "error", "xml.encoding", "Input must be UTF-8 XML.")
        return report
    # Reject before parsing: ElementTree may otherwise expand internal entities.
    if re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", text, re.IGNORECASE):
        finding(report, "error", "xml.declaration", "DTD and entity declarations are unsupported.")
        return report
    if re.search(r"<\?xml-stylesheet\b", text, re.IGNORECASE):
        finding(report, "error", "xml.stylesheet", "Stylesheet processing instructions are unsupported.")
        return report
    declaration = re.match(r"\s*<\?xml\s+[^?]*encoding\s*=\s*(['\"])(.*?)\1", text, re.IGNORECASE)
    if declaration and declaration.group(2).lower() not in {"utf-8", "utf8"}:
        finding(report, "error", "xml.encoding", "Only an UTF-8 encoding declaration is supported.")
        return report
    try:
        root = ET.fromstring(text)
    except (ET.ParseError, ValueError) as exc:
        finding(report, "error", "xml.parse", str(exc))
        return report
    if root.tag not in {"svg", "{http://www.w3.org/2000/svg}svg"}:
        finding(report, "error", "xml.root", "Root element must be SVG.")
        return report

    for name in ("width", "height"):
        match = LENGTH.fullmatch(root.get(name, ""))
        value = float(match.group(1)) if match else None
        if value is None or not math.isfinite(value) or value <= 0:
            finding(report, "error", "canvas." + name,
                    f"{name} must be finite and positive with an absolute px/pt/pc/mm/cm/in unit.")
    values = re.split(r"[\s,]+", root.get("viewBox", "").strip())
    try:
        box = [float(item) for item in values]
        valid_box = (len(box) == 4 and all(re.fullmatch(NUMBER, item) for item in values)
                     and all(math.isfinite(n) for n in box) and box[2] > 0 and box[3] > 0)
    except ValueError:
        valid_box = False
    if not valid_box:
        finding(report, "error", "canvas.viewBox", "viewBox needs four finite numbers with positive width and height.")

    ids: set[str] = set()
    references: list[tuple[str, str]] = []
    native_text = 0
    images = 0
    svg_prefix = "{http://www.w3.org/2000/svg}" if root.tag.startswith("{") else ""
    for element in root.iter():
        tag = local(element.tag)
        identifier = element.get("id")
        label = identifier or tag
        if identifier is not None:
            if not identifier.strip():
                finding(report, "error", "id.empty", "An id is empty.")
            elif identifier in ids:
                finding(report, "error", "id.duplicate", f"Repeated id: {identifier}")
            ids.add(identifier)
        if tag.lower() in {"script", "foreignobject", "animate", "animatetransform",
                           "animatemotion", "set", "discard"}:
            finding(report, "error", "content.active", f"Unsupported active content: {tag}")
        if element.tag == svg_prefix + "text" and "".join(element.itertext()).strip():
            native_text += 1
        if tag == "image":
            images += 1
        for key, value in element.attrib.items():
            attribute = local(key)
            if key == "{http://www.w3.org/XML/1998/namespace}base":
                finding(report, "error", "resource.xml-base", "XML base is unsupported; fragment references must stay in this document.")
            if re.fullmatch(r"on[a-z]+", attribute, re.IGNORECASE):
                finding(report, "error", "content.event", f"Event handler on {label}: {attribute}")
            if attribute in {"href", "src"}:
                value = value.strip()
                if value.startswith("#"):
                    references.append((label, value[1:]))
                else:
                    finding(report, "error", "resource.nonlocal", f"Non-local resource on {label} is unsupported.")
            if attribute in {"aria-labelledby", "aria-describedby"}:
                references.extend((label, target) for target in value.split())
            inspect_css(value, label, references, report)
        if tag == "style":
            inspect_css("".join(element.itertext()), label, references, report)
    for owner, target in references:
        if not target or target not in ids:
            finding(report, "error", "reference.dangling", f"{owner} references missing id: {target!r}")
    if not native_text:
        finding(report, "error", "text.missing", "No non-empty native SVG text element was found.")
    if images:
        finding(report, "warning", "content.image", "Image elements are present; their content and authenticity are not inspected.")
    for tag in ("title", "desc"):
        if not any(child.tag == svg_prefix + tag and "".join(child.itertext()).strip() for child in root):
            finding(report, "warning", "accessibility." + tag, f"No non-empty root {tag} was found.")
    report["counts"] = {"ids": len(ids), "local_references": len(references),
                        "native_text_elements": native_text, "image_elements": images}
    report["status"] = "fail" if any(item["severity"] == "error" for item in report["findings"]) else "pass"
    return report


def inspect_css(value: str, owner: str, references: list, report: dict) -> None:
    if "\\" in value:
        finding(report, "error", "resource.css-escape", f"Escaped resource or CSS values on {owner} are unsupported.")
    value = re.sub(r"/\*.*?\*/", "", value, flags=re.DOTALL)
    if re.search(r"@import\b", value, re.IGNORECASE):
        finding(report, "error", "resource.css-import", f"CSS import on {owner} is unsupported.")
    for match in URL.finditer(value):
        target = match.group(2).strip()
        if target.startswith("#"):
            references.append((owner, target[1:]))
        else:
            finding(report, "error", "resource.nonlocal", f"Non-local CSS resource on {owner} is unsupported.")


def exit_code(report: dict) -> int:
    return {"pass": 0, "fail": 1, "not-auditable": 2}[report["status"]]


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        report = result()
        finding(report, "error", "input.arguments", message)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        raise SystemExit(2)


def main(argv: list[str] | None = None) -> int:
    parser = JsonArgumentParser(description=__doc__)
    parser.add_argument("svg", type=Path, help="SVG file to inspect without modification")
    args = parser.parse_args(argv)
    try:
        data = args.svg.read_bytes()
    except OSError as exc:
        report = result(str(args.svg))
        finding(report, "error", "input.read", str(exc))
    else:
        report = audit_svg(data, str(args.svg))
    print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    return exit_code(report)


if __name__ == "__main__":
    sys.exit(main())
