"""Schema source and bounded structural validation for the workflow core.

This module is not a general JSON Schema implementation.  Its validator supports
only the keywords emitted by :func:`export_schemas`.  Cross-record references,
catalog membership, paths, checkpoint freshness and scientific judgments belong
to other layers.  The same schema dictionaries drive validation and export.
"""

from __future__ import annotations

from copy import deepcopy
import json
import math
from pathlib import Path
import re
from typing import Any


SCHEMA_VERSION = "0.1"
RECORD_KINDS = (
    "source", "statement", "evidence", "relation", "activity", "decision",
    "artifact", "method-binding",
)
COLLECTIONS = {
    "source": "sources",
    "statement": "statements",
    "evidence": "evidence",
    "relation": "relations",
    "activity": "activities",
    "decision": "decisions",
    "artifact": "artifacts",
    "method-binding": "method_bindings",
}
# The final lookahead forbids the trailing-newline exception of regex ``$``.
# Both Python re and the exported ECMA-compatible JSON Schema pattern support it.
ID_PATTERN = r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$(?![\s\S])"
TYPED_REF_PATTERN = (
    r"^(?:source|statement|evidence|relation|activity|decision|artifact|method-binding):"
    r"[A-Za-z][A-Za-z0-9_.-]{0,63}$(?![\s\S])"
)
SHA256_PATTERN = r"^[0-9a-f]{64}$(?![\s\S])"
_DRAFT = "https://json-schema.org/draft/2020-12/schema"
_SCHEMA_BASE = "https://research-workflow-template.invalid/schemas/"


def _string(*, blank: bool = False, pattern: str | None = None) -> dict[str, Any]:
    schema: dict[str, Any] = {"type": "string"}
    if not blank:
        schema["minLength"] = 1
        # Whitespace alone is not a meaningful required/identifier value.
        schema["pattern"] = r"\S"
    if pattern is not None:
        schema["pattern"] = pattern
    return schema


def _enum(*values: str) -> dict[str, Any]:
    return {"type": "string", "enum": list(values)}


def _array(item: dict[str, Any]) -> dict[str, Any]:
    return {"type": "array", "items": item}


def _nullable(schema: dict[str, Any]) -> dict[str, Any]:
    return {"anyOf": [{"type": "null"}, schema]}


def _object(
    properties: dict[str, Any], required: tuple[str, ...] | list[str],
    *, extensions: bool = True,
) -> dict[str, Any]:
    props = dict(properties)
    if extensions:
        props["extensions"] = {"type": "object"}
    return {
        "type": "object", "properties": props, "required": list(required),
        "additionalProperties": False,
    }


def _map(value: dict[str, Any], key: dict[str, Any]) -> dict[str, Any]:
    return {"type": "object", "propertyNames": key, "additionalProperties": value}


def _id() -> dict[str, Any]:
    return _string(pattern=ID_PATTERN)


def _refs() -> dict[str, Any]:
    return _array(_string(pattern=TYPED_REF_PATTERN))


def _ids() -> dict[str, Any]:
    return _array(_id())


def _sha() -> dict[str, Any]:
    return _string(pattern=SHA256_PATTERN)


def _record_definitions() -> dict[str, Any]:
    """Construct the canonical record definitions; do not mutate returned leaves."""
    source = _object({
        "id": _id(), "title": _string(), "locator": _string(),
        "version": _string(),
        "content_access": _enum("not-read", "metadata-only", "partial", "full"),
        "rights": _enum("unknown", "public", "restricted"),
        "limitations": _string(blank=True), "notes": _string(blank=True),
    }, ("id", "title", "locator", "version", "content_access"))
    assessment = _object({
        "status": _enum("not-assessed", "supported-in-scope", "mixed", "challenged",
                        "insufficient", "not-applicable"),
        "scope": _string(), "rationale": _string(), "reviewer": _string(),
    }, ("status", "scope", "rationale", "reviewer"))
    formal = _object({
        "status": _enum("not-applicable", "not-started", "partial", "complete-in-scope"),
        "scope": _string(), "tool": _string(),
    }, ("status", "scope", "tool"))
    statement = _object({
        "id": _id(), "text": _string(),
        "type": _enum("question", "formal", "empirical", "interpretive", "normative", "design"),
        "scope": _string(), "role": _string(),
        "work_status": _enum("draft", "in-progress", "reviewed", "archived"),
        "use": _enum("included", "background", "excluded"),
        "depends_on": _ids(), "assessment": assessment,
        "formal_verification": formal, "notes": _string(blank=True),
    }, ("id", "text", "type", "scope"))
    location = {"oneOf": [
        _object({"kind": {"const": "local"}, "path": _string()}, ("kind", "path")),
        _object({"kind": {"const": "external"}, "locator": _string(),
                 "access_note": _string()}, ("kind", "locator", "access_note")),
        _object({"kind": {"const": "controlled"}, "reference": _string(),
                 "access_note": _string()}, ("kind", "reference", "access_note")),
    ]}
    evidence = _object({
        "id": _id(), "type": _string(), "description": _string(),
        "provenance": _string(), "location": location, "source_ids": _ids(),
        "limitations": _string(blank=True), "notes": _string(blank=True),
    }, ("id", "type", "description", "provenance", "location"))
    relation = _object({
        "id": _id(), "statement_id": _id(), "evidence_id": _id(),
        "relation": _enum("supports", "qualifies", "challenges", "contextualizes", "derived_from"),
        "rationale": _string(), "scope": _string(),
        "limitations": _string(blank=True), "notes": _string(blank=True),
    }, ("id", "statement_id", "evidence_id", "relation", "rationale", "scope"))
    activity = _object({
        "id": _id(), "title": _string(),
        "status": _enum("pending", "in-progress", "done", "failed", "skipped"),
        "depends_on": _ids(), "inputs": _refs(), "outputs": _refs(),
        "note": _string(blank=True),
    }, ("id", "title", "status"))
    decision = _object({
        "id": _id(), "choice": _string(), "rationale": _string(),
        "responsible": _string(), "decided_at": _string(),
        "alternatives": _array(_string()), "evidence_refs": _ids(),
        "revisit_when": _string(), "notes": _string(blank=True),
    }, ("id", "choice", "rationale", "responsible", "decided_at"))
    artifact = _object({
        "id": _id(), "type": _string(), "description": _string(),
        "path": _string(), "derived_from": _refs(), "notes": _string(blank=True),
    }, ("id", "type", "description", "path"))
    binding = _object({
        "id": _id(), "method_id": _string(), "profile_version": _string(),
        "reason": _string(), "applies_to": _refs(), "variant": _string(),
        "notes": _string(blank=True),
    }, ("id", "method_id", "profile_version", "reason", "applies_to"))
    return dict(zip(RECORD_KINDS, (
        source, statement, evidence, relation, activity, decision, artifact, binding,
    )))


def _document(name: str, schema: dict[str, Any], defs: dict[str, Any] | None = None) -> dict[str, Any]:
    result = {"$schema": _DRAFT, "$id": _SCHEMA_BASE + name + ".schema.json", **schema}
    if defs is not None:
        result["$defs"] = defs
    return result


_RECORD_DEFS = _record_definitions()

PROJECT_SCHEMA = _document("project", _object({
    "schema_version": {"const": SCHEMA_VERSION}, "project_id": _id(),
    "title": _string(), "interest": _string(),
    "disciplines": _array(_string()), "methods": _array(_string()),
    "entry_activity": _string(), "workflow_mode": _string(),
    "deliverable": _object({
        "kind": _string(), "language": _string(), "venue": _nullable(_string()),
        "contribution_benchmarks": _array(_string()),
    }, ("kind", "language", "venue", "contribution_benchmarks")),
    "resources": _object({
        "deadline": _nullable(_string()), "budget": _nullable(_string()),
        "available_capabilities": _array(_string()),
    }, ("deadline", "budget", "available_capabilities")),
    "governance": _object({
        "applicability": _enum("unknown", "applicable", "not-applicable"),
        "relevant_requirements": _array(_string()),
    }, ("applicability", "relevant_requirements")),
}, ("schema_version", "project_id", "title", "interest", "disciplines", "methods",
    "entry_activity", "workflow_mode", "deliverable", "resources", "governance")))

_BINDINGS = _nullable(_object({
    "records": _map(_sha(), _string(pattern=TYPED_REF_PATTERN)),
    "files": _map(_sha(), _string()),
}, ("records", "files")))


def _envelope(data: dict[str, Any]) -> dict[str, Any]:
    return _object({
        "version": {"type": "integer", "minimum": 1},
        "registered_at": _string(), "data": data, "bindings": deepcopy(_BINDINGS),
    }, ("version", "registered_at", "data", "bindings"))


_REGISTRY_DEFS = deepcopy(_RECORD_DEFS)
for _kind in RECORD_KINDS:
    _REGISTRY_DEFS["envelope-" + _kind] = _envelope({"$ref": "#/$defs/" + _kind})
_REGISTRY_DEFS["envelope"] = _envelope({
    "anyOf": [{"$ref": "#/$defs/" + kind} for kind in RECORD_KINDS],
})

REGISTRY_SCHEMA = _document("registry", _object({
    "schema_version": {"const": SCHEMA_VERSION}, "project_id": _id(),
    "revision": {"type": "integer", "minimum": 0},
    "records": _object({
        COLLECTIONS[kind]: _map({"$ref": "#/$defs/envelope-" + kind}, _id())
        for kind in RECORD_KINDS
    }, list(COLLECTIONS.values()), extensions=False),
    "cursor": _object({
        "activity_id": _nullable(_id()), "next_action": _string(),
    }, ("activity_id", "next_action")),
    "checkpoint": _nullable(_object({
        "created_at": _string(), "config_sha256": _sha(), "records_sha256": _sha(),
        "files": _map(_sha(), _string()), "note": _string(),
    }, ("created_at", "config_sha256", "records_sha256", "files", "note"))),
    "history": _array(_object({
        "revision": {"type": "integer", "minimum": 0}, "at": _string(),
        "action": _string(), "kind": _nullable(_string()),
        "id": _nullable(_id()),
        "previous": _nullable({"$ref": "#/$defs/envelope"}),
    }, ("revision", "at", "action", "kind", "id", "previous"))),
}, ("schema_version", "project_id", "revision", "records", "cursor", "checkpoint", "history")),
    _REGISTRY_DEFS)

RECORD_SCHEMAS = {
    kind: _document(kind, deepcopy(schema)) for kind, schema in _RECORD_DEFS.items()
}
SCHEMAS = {"project": PROJECT_SCHEMA, "registry": REGISTRY_SCHEMA, **RECORD_SCHEMAS}


def _path(parent: str, key: str | int) -> str:
    if isinstance(key, int):
        return f"{parent}[{key}]"
    return f"{parent}[{json.dumps(key, ensure_ascii=False)}]"


def _json_errors(value: Any, path: str = "$", ancestors: frozenset[int] = frozenset()) -> list[str]:
    """Reject Python-only values and non-finite extension data before schemas."""
    if value is None or isinstance(value, (str, bool, int)):
        return []
    if isinstance(value, float):
        return [] if math.isfinite(value) else [f"{path}: non-finite numbers are not JSON values"]
    if isinstance(value, (dict, list)):
        if id(value) in ancestors:
            return [f"{path}: cyclic containers are not JSON values"]
        seen = ancestors | {id(value)}
        errors = []
        entries = value.items() if isinstance(value, dict) else enumerate(value)
        for key, item in entries:
            if isinstance(value, dict) and not isinstance(key, str):
                errors.append(f"{path}: object key must be a string")
            else:
                errors.extend(_json_errors(item, _path(path, key), seen))
        return errors
    return [f"{path}: unsupported JSON value type {type(value).__name__}"]


def _matches_type(value: Any, expected: str) -> bool:
    return {
        "null": value is None,
        "boolean": isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "string": isinstance(value, str),
        "array": isinstance(value, list),
        "object": isinstance(value, dict),
    }[expected]


def _validate(value: Any, schema: dict[str, Any], root: dict[str, Any], path: str) -> list[str]:
    """Evaluate only this module's emitted structural schema keywords."""
    errors: list[str] = []
    if "$ref" in schema:
        ref = schema["$ref"]
        if not ref.startswith("#/"):
            raise ValueError(f"unsupported internal schema reference: {ref}")
        resolved = root
        for token in ref[2:].split("/"):
            resolved = resolved[token.replace("~1", "/").replace("~0", "~")]
        errors.extend(_validate(value, resolved, root, path))
    for keyword in ("anyOf", "oneOf"):
        if keyword in schema:
            results = [_validate(value, branch, root, path) for branch in schema[keyword]]
            matched = sum(not result for result in results)
            if (keyword == "anyOf" and matched == 0) or (keyword == "oneOf" and matched != 1):
                expectation = "at least one" if keyword == "anyOf" else "exactly one"
                errors.append(f"{path}: must match {expectation} {keyword} branch (matched {matched})")
                if matched == 0:
                    # The nearest branch makes malformed nested data actionable.
                    nearest = min(results, key=len)
                    errors.extend(nearest)
    expected = schema.get("type")
    if expected is not None and not _matches_type(value, expected):
        return errors + [f"{path}: expected {expected}, got {type(value).__name__}"]
    if "const" in schema and (type(value) is not type(schema["const"]) or value != schema["const"]):
        errors.append(f"{path}: expected constant {schema['const']!r}")
    if "enum" in schema and not any(type(value) is type(item) and value == item for item in schema["enum"]):
        errors.append(f"{path}: value is not one of {schema['enum']!r}")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{path}: string is shorter than {schema['minLength']}")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            errors.append(f"{path}: string does not match {schema['pattern']!r}")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: number must be at least {schema['minimum']}")
    if isinstance(value, list) and "items" in schema:
        for index, item in enumerate(value):
            errors.extend(_validate(item, schema["items"], root, _path(path, index)))
    if isinstance(value, dict):
        for key in schema.get("required", ()):
            if key not in value:
                errors.append(f"{_path(path, key)}: required field is missing")
        props = schema.get("properties", {})
        for key, item in value.items():
            if "propertyNames" in schema:
                errors.extend(_validate(key, schema["propertyNames"], root, _path(path, key) + " (key)"))
            if key in props:
                errors.extend(_validate(item, props[key], root, _path(path, key)))
            elif schema.get("additionalProperties") is False:
                errors.append(f"{_path(path, key)}: unknown field")
            elif isinstance(schema.get("additionalProperties"), dict):
                errors.extend(_validate(item, schema["additionalProperties"], root, _path(path, key)))
    return errors


def _run(value: Any, schema: dict[str, Any]) -> list[str]:
    errors = _json_errors(value)
    return errors if errors else _validate(value, schema, schema, "$")


def validate_project(obj: Any) -> list[str]:
    """Return structural errors; catalog membership is checked by the caller."""
    return _run(obj, PROJECT_SCHEMA)


def validate_record(kind: str, obj: Any) -> list[str]:
    """Validate one record, without resolving IDs, files or scientific support."""
    if kind not in RECORD_SCHEMAS:
        return [f"$: unknown record kind {kind!r}"]
    return _run(obj, RECORD_SCHEMAS[kind])


def validate_registry(obj: Any) -> list[str]:
    """Validate registry shape only, without checking references or file state."""
    return _run(obj, REGISTRY_SCHEMA)


def export_schemas(directory: str | Path) -> list[Path]:
    """Write the ten generated draft2020-12 schemas and return their paths.

    This is an explicit schema-build operation.  The read-only validators never
    call it and never modify these files.
    """
    destination = Path(directory)
    destination.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, schema in SCHEMAS.items():
        path = destination / f"{name}.schema.json"
        path.write_text(json.dumps(schema, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        paths.append(path)
    return paths
