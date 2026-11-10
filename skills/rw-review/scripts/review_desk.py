#!/usr/bin/env python3
"""Review registered project materials in a browser and save a versioned RWT decision."""
import argparse
import base64
from contextlib import contextmanager
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import json
import os
import posixpath
from pathlib import Path
import re
import secrets
import shutil
import sys
import tempfile
from urllib.parse import parse_qs, quote, unquote, urlsplit
from zipfile import ZIP_DEFLATED, ZipFile

sys.dont_write_bytecode = True
SKILLS = Path(__file__).resolve().parents[2]
RUNTIME = SKILLS / "_rw-runtime" if (SKILLS / "_rw-runtime").is_dir() else SKILLS.parent
sys.path.insert(0, str(RUNTIME))
from core import project
from core.storage import CoreError, FILE_LIMIT, ProjectFiles, object_sha, parse_json, sha

CHECK_STATUSES = {"checked", "pending", "not-run", "failed"}
REF = re.compile(r"(?:artifact|evidence):[A-Za-z][A-Za-z0-9_.-]{0,63}")
NATIVE_ID = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{0,63}")
IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
               ".svg": "image/svg+xml", ".webp": "image/webp", ".gif": "image/gif"}
PREVIEW_LIMIT = 4 * 1024 * 1024


def require(condition, message):
    if not condition:
        raise ValueError(message)


def nonblank(value):
    return isinstance(value, str) and bool(value.strip())


def parse_plan(raw):
    p = parse_json(raw)
    require(isinstance(p, dict) and set(p) <= {"id", "title", "candidates", "deliverables", "evidence",
                                               "supersedes", "checks"}, "Unknown field or invalid review plan")
    require(isinstance(p.get("id"), str) and NATIVE_ID.fullmatch(p["id"]), "Invalid decision ID")
    require(nonblank(p.get("title")), "A review title is required")
    for key in ("candidates", "deliverables", "evidence"):
        v = p.setdefault(key, [])
        require(isinstance(v, list) and all(isinstance(r, str) and REF.fullmatch(r) for r in v)
                and len(v) == len(set(v)), f"{key} must contain unique artifact/evidence references")
    require(p["candidates"] or p["deliverables"], "List at least one candidate or deliverable")
    s = p.setdefault("supersedes", {})
    require(isinstance(s, dict) and all(isinstance(v, str) and REF.fullmatch(k) and REF.fullmatch(v)
                                        and k != v for k, v in s.items()), "Invalid supersession references")
    for new in s:
        seen = set()
        current = new
        while current in s:
            require(current not in seen, "Cyclic supersession")
            seen.add(current)
            current = s[current]
    require(not set(s.values()).intersection(p["deliverables"]), "Superseded material cannot be a current deliverable")
    checks = p.setdefault("checks", [])
    require(isinstance(checks, list), "checks must be an array")
    for c in checks:
        require(isinstance(c, dict) and set(c) <= {"label", "status", "evidence", "note", "against"}
                and nonblank(c.get("label")) and isinstance(c.get("status"), str)
                and c["status"] in CHECK_STATUSES, "Invalid review check")
        if "evidence" in c:
            require(isinstance(c["evidence"], str) and REF.fullmatch(c["evidence"]), "Invalid check evidence")
        against = c.get("against", {})
        require(isinstance(against, dict) and all(REF.fullmatch(ref) and isinstance(digest, str)
                and re.fullmatch(r"[0-9a-f]{64}", digest) for ref, digest in against.items()),
                "Check baselines must map registered references to SHA-256 values")
        if "note" in c:
            require(nonblank(c["note"]), "Invalid check note")
        require(c["status"] != "checked" or "evidence" in c, "Checked items require a registered evidence file")
    return p


@contextmanager
def material_stream(files, relative):
    # Use the same no-follow regular-file opener as native SHA-256 checks, including on Windows.
    with os.fdopen(files._open(relative), "rb") as stream:
        yield stream


def copy_verified(files, material, destination):
    digest = hashlib.sha256()
    size = 0
    with material_stream(files, material["path"]) as source:
        while block := source.read(1024 * 1024):
            size += len(block)
            require(size <= FILE_LIMIT, "File exceeds the native project size limit")
            digest.update(block)
            destination.write(block)
    require(digest.hexdigest() == material["sha256"], "Material changed while reading: " + material["path"])
    return size


def state(files, metadata, registry, plan_path):
    raw = files.read(plan_path)
    plan = parse_plan(raw)
    refs = dict.fromkeys([*plan["candidates"], *plan["deliverables"], *plan["evidence"],
                          *plan["supersedes"], *plan["supersedes"].values(),
                          *(c["evidence"] for c in plan["checks"] if "evidence" in c),
                          *(r for c in plan["checks"] for r in c.get("against", {}))])
    materials = {}
    for ref in refs:
        entry = project.envelope(registry, ref)
        kind = ref.split(":", 1)[0]
        data = entry["data"]
        path = project.local_path(kind, data)
        require(path, f"{ref} does not identify a local file")
        expected = entry["bindings"]["files"][path] if entry.get("bindings") else None
        try:
            actual = files.fingerprint(path)
        except FileNotFoundError:
            actual = None
        materials[ref] = {"path": path, "description": data["description"], "version": entry["version"],
                           "sha256": actual, "registered_sha256": expected,
                           "state": "missing" if actual is None else "current" if actual == expected else "changed"}
    for new, old in plan["supersedes"].items():
        require(materials[new]["path"] != materials[old]["path"], f"{old} must retain its own file")
    saved = registry["records"]["decisions"].get(plan["id"])
    history = [h["previous"] for h in registry["history"] if h["kind"] == "decision"
               and h["id"] == plan["id"] and h["previous"]]
    decisions = []
    for envelope in history + ([saved] if saved else []):
        receipt = envelope["data"].get("extensions", {}).get("review_desk")
        require(isinstance(receipt, dict) and receipt.get("format") == 1,
                "Decision ID already belongs to another record. Use a different plan ID.")
        decisions.append({"version": envelope["version"], **{k: envelope["data"][k]
                          for k in ("choice", "rationale", "responsible", "decided_at")}, "receipt": receipt})
    scope = object_sha({"project": metadata["project_id"], "plan_sha256": sha(raw), "materials": materials})
    version = saved["version"] if saved else 0
    current = decisions[-1] if decisions else None
    decision_status = "awaiting decision"
    if current:
        if current["receipt"]["scope"] != scope:
            decision_status = "materials or plan changed since decision"
        elif current["choice"] in plan["supersedes"].values():
            decision_status = "historical candidate; choose a current version"
        elif current["choice"] == "request-changes":
            decision_status = "changes requested"
        else:
            decision_status = "selection saved"
    checks = []
    for item in plan["checks"]:
        result = dict(item, effective_status=item["status"])
        if item["status"] == "checked":
            against = item.get("against", {})
            evidence = item["evidence"]
            complete = evidence in against and any(ref != evidence for ref in against)
            result["effective_status"] = "checked (bound files match)" if complete else "reported check; file set unverified"
            if materials[item["evidence"]]["state"] != "current" or any(
                    materials[r]["sha256"] != digest or materials[r]["state"] != "current" for r, digest in against.items()):
                result["effective_status"] = "needs recheck"
        checks.append(result)
    return {"plan": plan, "project_id": metadata["project_id"], "materials": materials, "checks": checks,
            "history": decisions, "decision_status": decision_status, "scope": scope,
            "version": version, "token": object_sha([scope, version])}


def snapshot(root, plan_path):
    with ProjectFiles(root) as files:
        metadata, registry, _, _ = project.load(files)
        return state(files, metadata, registry, plan_path)


def save(root, plan_path, expected, choice, feedback, actor):
    view = snapshot(root, plan_path)
    p = view["plan"]
    require(view["token"] == expected, "Review changed. Reload and inspect current materials before saving.")
    eligible = [r for r in p["candidates"] if r not in p["supersedes"].values()]
    options = (eligible if p["candidates"] else ["accept-materials"]) + ["request-changes"]
    require(choice in options, "Select a listed candidate or request changes")
    require(nonblank(actor) and nonblank(feedback), "Record the reviewer and the actual reason or requested changes")
    require(len(actor) <= 200 and len(feedback) <= 8000, "Reviewer or feedback too long")
    require(all(m["state"] == "current" for m in view["materials"].values()),
            "Changed or missing material. Reconcile the registered files before saving.")
    old = view["history"][-1] if view["history"] else None
    if old and old["receipt"]["scope"] == view["scope"] and (old["choice"], old["responsible"], old["rationale"]) == (
            choice, actor.strip(), feedback.strip()):
        return {"registered": False, "already_saved": True, "version": old["version"]}
    evidence = [r.split(":", 1)[1] for r in view["materials"] if r.startswith("evidence:")]
    material_receipts = {ref: {k: m[k] for k in ("path", "version", "sha256")} for ref, m in view["materials"].items()}
    record = {"id": p["id"], "choice": choice, "responsible": actor.strip(), "rationale": feedback.strip(),
              "decided_at": project.now(), "alternatives": options, "evidence_refs": evidence,
              "extensions": {"review_desk": {"format": 1, "plan": plan_path, "scope": view["scope"],
                                              "materials": material_receipts, "supersedes": p["supersedes"]}}}

    def same_review(files, metadata, registry):
        require(state(files, metadata, registry, plan_path)["token"] == expected,
                "Review changed. Reload and inspect current materials before saving.")

    action = (f"Address the requested changes in decision:{p['id']}." if choice == "request-changes" else
              f"Use decision:{p['id']} for the next manuscript revision or delivery.")
    return project.register(root, "decision", record, replace=bool(view["version"]),
                            expected_version=view["version"] or None, next_action=action, precondition=same_review)


def preview(files, m):
    if m["state"] != "current":
        return ""
    ext = Path(m["path"]).suffix.lower()
    if ext not in IMAGE_TYPES and ext not in {".txt", ".md", ".csv", ".tex", ".pdf"}:
        return ""
    with material_stream(files, m["path"]) as stream:
        length = os.fstat(stream.fileno()).st_size
        if length > PREVIEW_LIMIT:
            return "<p>Open the registered file locally for a full-size preview.</p>"
        content = stream.read(PREVIEW_LIMIT + 1)
    if sha(content) != m["sha256"]:
        raise ValueError("File changed while generating preview. Reload the page.")
    if ext in IMAGE_TYPES:
        encoded = base64.b64encode(content).decode("ascii")
        return f'<img alt="{escape(m["description"])}" src="data:{IMAGE_TYPES[ext]};base64,{encoded}">'
    if ext == ".pdf":
        encoded = base64.b64encode(content).decode("ascii")
        name = escape(Path(m["path"]).name)
        return f'<p><a download="{name}" href="data:application/pdf;base64,{encoded}">Download PDF preview</a></p>'
    text = content.decode("utf-8", errors="replace")
    return "<details><summary>Read text</summary><pre>" + escape(text[:4000]) + (
        "\n…" if len(text) > 4000 else "") + "</pre></details>"


def html(root, view, *, nonce=None, notice=""):
    p, materials = view["plan"], view["materials"]
    parts = ['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
             '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src data:; style-src \'unsafe-inline\'; form-action \'self\'; base-uri \'none\'">',
             f'<title>{escape(p["title"])} · RWT</title>',
             """<style>
*{box-sizing:border-box}
body{max-width:66rem;margin:0 auto;padding:2.5rem 5%;color:#182831;background:#fff;font:16px/1.55 system-ui,sans-serif}
h1{font-size:clamp(2rem,5vw,3rem);line-height:1.1}
h2{margin-top:2.3rem}
small,code{overflow-wrap:anywhere}
small{color:#425560}
figure{margin:.9rem 0;padding:1rem;border:1px solid #bdced1;border-radius:.5rem}
img{display:block;max-width:100%;max-height:30rem;margin:1rem auto}
li{margin:.6rem 0}
pre{white-space:pre-wrap;overflow-wrap:anywhere}
label{display:block;margin:.8rem 0}
button{background:#12574f;color:white;font:inherit;border:0;border-radius:.4rem;padding:.55rem 1rem}
textarea,input[type=text]{width:100%;font:inherit;padding:.45rem}
fieldset{border:0;padding:0}
dt{font-weight:650}
dd{margin-left:0}
aside{padding:.6rem 1rem;background:#eff6f5}
</style>""",
             f'<main><h1>{escape(p["title"])}</h1><p>{escape(view["decision_status"])}</p>']
    if view["history"]:
        last = view["history"][-1]
        parts.append(f'<aside><strong>{escape(last["choice"])}</strong> · {escape(last["responsible"])}<br>'
                     f'{escape(last["rationale"])}</aside>')
    if notice:
        parts.append(f'<aside role="status">{escape(notice)}</aside>')
    def file_link(ref):
        if nonce and materials[ref]["state"] == "current":
            return f' <a href="/file/{quote(ref, safe="")}">Download file</a>'
        return ""

    if nonce:
        parts.append(f'<form method="post" action="/decision"><input type="hidden" name="nonce" value="{nonce}">'
                     f'<input type="hidden" name="version" value="{view["token"]}">')
    if p["candidates"]:
        parts.append("<h2>Candidates</h2>")
    with ProjectFiles(root) as files:
        for ref in p["candidates"]:
            m = materials[ref]
            previous = ref in p["supersedes"].values()
            version_label = "Earlier version" if previous else "Candidate"
            identity = "fingerprint verified" if m["state"] == "current" else m["state"]
            parts.append(f'<figure><strong>{escape(m["description"])}</strong>{preview(files,m)}'
                         f'<figcaption>{version_label} · {escape(m["path"])} · {identity}{file_link(ref)}</figcaption>')
            if nonce and not previous:
                parts.append(f'<label><input type="radio" required name="choice" value="{escape(ref)}"> Use this candidate</label>')
            parts.append("</figure>")
        if p["deliverables"]:
            parts.append("<h2>Current deliverables</h2>")
            for ref in p["deliverables"]:
                m = materials[ref]
                parts.append(f'<p><strong>{escape(m["description"])}</strong><br><code>{escape(m["path"])}</code>{file_link(ref)}</p>')
                if ref not in p["candidates"]:
                    parts.append(preview(files, m))
    if nonce:
        if not p["candidates"]:
            parts.append('<label><input type="radio" name="choice" value="accept-materials" required> Use these materials</label>')
        parts.extend(['<label><input type="radio" name="choice" value="request-changes" required> Request changes</label>',
                      '<label>Reviewer or delegated operator<input name="by" type="text" required maxlength="200"></label>',
                      '<label>Reason or revision feedback<textarea name="feedback" required maxlength="8000" rows="3"></textarea></label>',
                      '<button>Save decision to project</button></form>'])
    if p["supersedes"]:
        parts.append("<h2>Revisions</h2><ul>")
        for new, old in p["supersedes"].items():
            parts.append(f'<li>{escape(materials[old]["path"])} → {escape(materials[new]["path"])}</li>')
        parts.append("</ul>")
    parts.append("<h2>Checks</h2><ul>")
    for c in view["checks"]:
        desc = f' · {c["evidence"]}' if "evidence" in c else ""
        parts.append(f'<li>{escape(c["label"])} · {escape(c["effective_status"] + desc)} {escape(c.get("note",""))}</li>')
    parts.append("</ul>" if p["checks"] else "<li>No checks recorded.</li></ul>")
    parts.append("<h2>Decision history</h2><ol>")
    for d in view["history"]:
        parts.append(f'<li><strong>{escape(d["choice"])}</strong> · {escape(d["responsible"])} · {escape(d["decided_at"])}'
                     f'<br>{escape(d["rationale"])}</li>')
    parts.append("</ol>" if view["history"] else "<li>No decision saved yet.</li></ol>")
    parts.append("<details><summary>Registered files and current SHA-256</summary><dl>")
    for ref,m in materials.items():
        parts.append(f'<dt>{escape(ref)}</dt><dd>{escape(m["path"])} · {escape(m["state"])}<br>'
                     f'<small>{escape(m["sha256"] or "missing")}</small></dd>')
    parts.append("</dl></details></main></html>")
    return "".join(parts)


INLINE = re.compile(r"(!?)\[([^\]\n]+)\]\((?:<([^>\n]+)>|([^()\n]+))\)|\*\*([^*\n]+)\*\*|`([^`\n]+)`")
HEADING = re.compile(r"^(#{1,6})\s+(.+)$")
MANUSCRIPT_LIMIT = 256 * 1024


def markdown_preview(text, member, visible_files):
    """Render a small Markdown subset; only exact local archive members may become links."""
    def inline(source):
        out = []
        offset = 0
        for m in INLINE.finditer(source):
            out.append(escape(source[offset:m.start()]))
            offset = m.end()
            image, label, angle_url, url, strong, code = m.groups()
            if code is not None:
                out.append("<code>" + escape(code) + "</code>")
                continue
            if strong is not None:
                out.append("<strong>" + escape(strong) + "</strong>")
                continue
            label = escape(label)
            try:
                parsed = urlsplit((angle_url or url).strip())
                path = unquote(parsed.path)
            except ValueError:
                out.append(label)
                continue
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(member), path))
            if (not path or parsed.scheme or parsed.netloc or parsed.query or path.startswith("/")
                    or "\\" in path or resolved not in visible_files):
                out.append(label)
                continue
            href = escape(quote(resolved, safe="/"))
            if image and Path(resolved).suffix.lower() in IMAGE_TYPES:
                out.append(f'<img alt="{label}" src="{href}">')
            else:
                out.append(f'<a href="{href}" download>{label}</a>')
        out.append(escape(source[offset:]))
        return "".join(out)

    def cells(line):
        return [x.strip().replace(r"\|", "|") for x in re.split(r"(?<!\\)\|", line.strip().strip("|"))]

    def table_start(index):
        if index + 1 >= len(lines) or "|" not in lines[index]:
            return False
        divider = cells(lines[index+1])
        return len(cells(lines[index])) == len(divider) and all(re.fullmatch(r":?-{3,}:?", x) for x in divider)

    lines = text.splitlines()
    out = []
    paragraphs = []
    i = 0
    while i < len(lines):
        line = lines[i]
        heading = HEADING.match(line)
        fence = re.match(r"^\s*(`{3,}|~{3,})", line)
        table = table_start(i)
        if line.strip() and not (heading or fence or table):
            paragraphs.append(line)
            i += 1
            continue
        if paragraphs:
            out.append("<p>" + inline(" ".join(paragraphs)) + "</p>")
            paragraphs.clear()
        if heading:
            level = min(6, len(heading[1])+2)
            out.append(f"<h{level}>" + inline(heading[2]) + f"</h{level}>")
        elif fence:
            first = i + 1
            i = first
            while i < len(lines) and not lines[i].lstrip().startswith(fence[1]):
                i += 1
            out.append("<pre><code>" + escape("\n".join(lines[first:i])) + "</code></pre>")
        elif table:
            head = cells(line)
            out.append('<div class="table-scroll"><table><thead><tr>' +
                       "".join('<th scope="col">' + inline(c) + "</th>" for c in head) + "</tr></thead><tbody>")
            i += 2
            while i < len(lines) and "|" in lines[i] and len(cells(lines[i])) == len(head):
                out.append("<tr>" + "".join("<td>" + inline(c) + "</td>" for c in cells(lines[i])) + "</tr>")
                i += 1
            out.append("</tbody></table></div>")
            continue
        i += 1
    if paragraphs:
        out.append("<p>" + inline(" ".join(paragraphs)) + "</p>")
    return "".join(out)


def reader_page(view, package, archive):
    """A portable, offline entry point using only the files explicitly packed."""
    plan, materials = view["plan"], view["materials"]
    files = package["files"]

    def href(ref):
        return escape(quote(files[ref]["member"], safe="/"))

    def file_link(ref):
        item = materials[ref]
        return f'<a href="{href(ref)}">{escape(item["description"])}</a> <small>{escape(item["path"])}</small>'

    manuscript_suffixes = {".pdf", ".docx", ".doc", ".odt", ".rtf", ".md", ".markdown", ".txt", ".tex", ".html", ".htm", ".qmd"}
    reading_order = sorted(plan["deliverables"],
                           key=lambda ref: Path(materials[ref]["path"]).suffix.lower() not in manuscript_suffixes)
    parts = ['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" '
             'content="width=device-width,initial-scale=1">',
             """<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src 'self' file:; style-src 'unsafe-inline'; base-uri 'none'">""",
             f'<title>{escape(plan["title"])}</title>',
             '<style>body{max-width:54rem;margin:auto;padding:2rem;color:#172a32;font:16px/1.55 system-ui,sans-serif}'
             'a{color:#165d5a}h2{margin-top:2rem}li{margin:.55em 0}small{overflow-wrap:anywhere;color:#465b63}'
             'figure{margin:1rem 0}img{display:block;max-width:100%;max-height:34rem}blockquote{margin-left:0;white-space:pre-wrap}'
             'article{border-top:1px solid #bdced1;margin:2rem 0}pre{white-space:pre-wrap;overflow-wrap:anywhere}'
             '.table-scroll{overflow-x:auto}table{border-collapse:collapse}td,th{padding:.35rem .65rem;border-bottom:1px solid #bdced1;text-align:left}'
             '</style><main>', f'<h1>{escape(plan["title"])}</h1>']
    if reading_order:
        parts.append('<h2>Current deliverables</h2><ul>')
        parts.extend(f'<li>{file_link(ref)}</li>' for ref in reading_order)
        parts.append('</ul>')
    visible = {entry["member"] for entry in files.values()}
    for ref in reading_order:
        member = files[ref]["member"]
        ext = Path(member).suffix.lower()
        if ext not in (".md", ".markdown", ".txt") or archive.getinfo(member).file_size > MANUSCRIPT_LIMIT:
            continue
        try:
            text = archive.read(member).decode("utf-8-sig")
        except UnicodeDecodeError:
            continue
        body = "<pre>" + escape(text) + "</pre>" if ext == ".txt" else markdown_preview(text, member, visible)
        parts.append(f'<article><h2>{escape(materials[ref]["description"])}</h2>{body}'
                     f'<a href="{href(ref)}" download>Download original</a></article>')
    selected = package.get("selected_candidate")
    if selected:
        item = materials[selected]
        parts.append('<h2>Selected candidate</h2>')
        if Path(item["path"]).suffix.lower() in IMAGE_TYPES:
            parts.append(f'<figure><img src="{href(selected)}" alt="{escape(item["description"])}">'
                         f'<figcaption>{file_link(selected)}</figcaption></figure>')
        else:
            parts.append(f'<p>{file_link(selected)}</p>')
    parts.append(f'<p>Decision status · {escape(package["decision_status"])}</p>')
    if feedback := package.get("feedback"):
        parts.append('<h2>Latest recorded feedback</h2>'
                     f'<p>{escape(feedback["responsible"])} · {escape(feedback["decided_at"])}</p>'
                     f'<blockquote>{escape(feedback["rationale"])}</blockquote>')
    parts.append('<h2>Checks</h2><ul>')
    for check in package["checks"]:
        parts.append(f'<li>{escape(check["label"])} · {escape(check["effective_status"])}</li>')
    if not package["checks"]:
        parts.append('<li>No checks recorded.</li>')
    parts.append('</ul><p><a href="manifest.json">File manifest and SHA-256 values</a></p></main></html>')
    return ''.join(parts).encode("utf-8")


def pack(root, plan_path, output, *, include_feedback=False):
    view = snapshot(root, plan_path)
    plan, materials = view["plan"], view["materials"]
    require(all(m["state"] == "current" for m in materials.values()), "Refresh changed or missing materials before packing")
    refs = list(plan["deliverables"])
    if view["decision_status"] == "selection saved":
        chosen = view["history"][-1]["choice"]
        require(chosen not in plan["supersedes"].values(), "Archived material cannot be the current selection")
        if chosen in plan["candidates"] and chosen not in refs:
            refs.append(chosen)
    require(refs, "No current deliverables or selected candidate to pack")
    target = Path(output).absolute()
    require(not os.path.lexists(target), "Output already exists. Choose a fresh ZIP filename.")
    package = {"project_id": view["project_id"], "review": plan["id"], "decision_version": view["version"],
               "decision_status": view["decision_status"], "checks": view["checks"],
               "files": {r: {"member": "files/" + materials[r]["path"], "sha256": materials[r]["sha256"]} for r in refs}}
    if view["decision_status"] == "selection saved" and view["history"][-1]["choice"] in plan["candidates"]:
        package["selected_candidate"] = view["history"][-1]["choice"]
    if include_feedback and view["history"]:
        # Share only the latest explicitly requested handoff. Omit the private decision history.
        package["feedback"] = {field: view["history"][-1][field]
                               for field in ("version", "choice", "rationale", "responsible", "decided_at")}
    written = set()
    with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".rwt-review-", delete=False) as handle:
        tmp = Path(handle.name)
    try:
        with ProjectFiles(root) as files, ZipFile(tmp, "w", compression=ZIP_DEFLATED) as archive:
            for ref in refs:
                entry = package["files"][ref]
                if entry["member"] in written:
                    continue
                with archive.open(entry["member"], "w") as dest:
                    copy_verified(files, materials[ref], dest)
                written.add(entry["member"])
            reader = reader_page(view, package, archive)
            package["reader"] = {"member": "index.html", "sha256": sha(reader)}
            archive.writestr("index.html", reader)
            archive.writestr("manifest.json", json.dumps(package, ensure_ascii=False, indent=2) + "\n")
        require(snapshot(root, plan_path)["token"] == view["token"], "Review changed during packaging")
        try:
            os.link(tmp, target)  # Atomic exclusive publish; preserve any existing file.
        except FileExistsError:
            raise ValueError("Output already exists. Choose a fresh ZIP filename.") from None
        except OSError as exc:
            raise ValueError("This destination cannot publish the archive using a hard link. "
                             "Choose a directory on a hard-link-capable filesystem, then copy the finished ZIP.") from exc
    finally:
        tmp.unlink(missing_ok=True)
    return package


def serve(root, plan_path, port):
    snapshot(root, plan_path)
    nonce = secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        timeout = 20

        def log_message(self, *_):
            pass

        def respond(self, status, page):
            body = page.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def local(self):
            return self.headers.get("Host") == f"127.0.0.1:{self.server.server_port}"

        def do_GET(self):
            if not self.local():
                return self.respond(404, "Unknown review page")
            try:
                view = snapshot(root, plan_path)
                if self.path.startswith("/file/"):
                    ref = unquote(self.path.removeprefix("/file/"))
                    item = view["materials"].get(ref)
                    if not item or item["state"] != "current":
                        return self.respond(404, "No current file for this reference")
                    with tempfile.SpooledTemporaryFile(max_size=PREVIEW_LIMIT) as download:
                        with ProjectFiles(root) as files:
                            size = copy_verified(files, item, download)
                        download.seek(0)
                        self.send_response(200)
                        self.send_header("Content-Type", "application/octet-stream")
                        filename = quote(Path(item["path"]).name, safe="")
                        self.send_header("Content-Disposition", "attachment; filename*=UTF-8''" + filename)
                        self.send_header("Cache-Control", "no-store")
                        self.send_header("X-Content-Type-Options", "nosniff")
                        self.send_header("Content-Length", str(size))
                        self.end_headers()
                        shutil.copyfileobj(download, self.wfile)
                    return
                if self.path not in ("/", "/saved"):
                    return self.respond(404, "Unknown review page")
                self.respond(200, html(root, view, nonce=nonce,
                                       notice="Decision saved in the project registry." if self.path == "/saved" else ""))
            except (ValueError, OSError, CoreError) as exc:
                self.respond(409, escape(str(exc)))

        def do_POST(self):
            if not self.local() or self.path != "/decision":
                return self.respond(404, "Unknown review page")
            try:
                origin = self.headers.get("Origin")
                require(origin in (None, f"http://127.0.0.1:{self.server.server_port}"), "Unexpected origin")
                require(self.headers.get_content_type() == "application/x-www-form-urlencoded", "Unsupported form")
                size = int(self.headers.get("Content-Length", "0"))
                require(0 < size <= 100000, "Invalid form length")
                form = parse_qs(self.rfile.read(size).decode("utf-8"), keep_blank_values=True, max_num_fields=5)
                require(set(form) == {"version", "nonce", "choice", "feedback", "by"} and
                        all(len(v) == 1 for v in form.values()), "Incomplete form")
                require(secrets.compare_digest(form["nonce"][0], nonce), "Invalid review session")
                result = save(root, plan_path, form["version"][0], form["choice"][0], form["feedback"][0], form["by"][0])
                if result.get("recovery", {}).get("passed") is False:
                    view = snapshot(root, plan_path)
                    return self.respond(200, html(root, view, nonce=nonce,
                            notice="Decision saved. RWT recovery reports outstanding project changes. Run resume to inspect."))
                self.send_response(303)
                self.send_header("Location", "/saved")
                self.end_headers()
            except (ValueError, OSError, CoreError, TypeError) as exc:
                self.respond(409, '<p>' + escape(str(exc)) + '</p><a href="/">Reload review</a>')

    with ThreadingHTTPServer(("127.0.0.1", port), Handler) as server:
        print(f"http://127.0.0.1:{server.server_port}/", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    for mode in ("serve", "html", "manifest", "save", "pack"):
        cmd = modes.add_parser(mode)
        cmd.add_argument("--root", default=".")
        cmd.add_argument("--plan", default="review.json", help="project-relative review plan")
        if mode == "serve":
            cmd.add_argument("--port", type=int, default=0)
        elif mode == "pack":
            cmd.add_argument("--output", required=True)
            cmd.add_argument("--include-feedback", action="store_true",
                             help="share the latest recorded reviewer's name, feedback, choice and date")
        elif mode == "save":
            cmd.add_argument("--expect", required=True, help="token from the inspected manifest")
            cmd.add_argument("--choice", required=True)
            cmd.add_argument("--by", required=True)
            cmd.add_argument("--feedback", required=True)
    args = parser.parse_args(argv)
    try:
        if args.mode == "serve":
            serve(args.root, args.plan, args.port)
            return 0
        if args.mode == "pack":
            out = pack(args.root, args.plan, args.output, include_feedback=args.include_feedback)
        elif args.mode == "save":
            out = save(args.root, args.plan, args.expect, args.choice, args.feedback, args.by)
        else:
            out = snapshot(args.root, args.plan)
            if args.mode == "html":
                print(html(args.root, out))
                return 0
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 1 if out.get("recovery", {}).get("passed") is False else 0
    except (CoreError, ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
