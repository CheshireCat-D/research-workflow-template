#!/usr/bin/env python3
"""Bounded Crossref metadata search; Python 3.11+ standard library only.

Does not fetch linked articles, verify source claims, or assess novelty.
"""

import argparse
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
from http.client import HTTPException
import json
import math
from pathlib import Path
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener


ENDPOINT = "https://api.crossref.org/v1/works"
USER_AGENT = "research-workflow-template-crossref/1.0 (metadata search)"
RETRYABLE = {429, 500, 502, 503, 504}
MIB = 1024 * 1024


class SearchError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalize_doi(value):
    if not isinstance(value, str):
        return None
    value = value.strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/",
                   "http://dx.doi.org/", "doi:"):
        if value.lower().startswith(prefix):
            value = value[len(prefix):].strip()
            break
    return value.casefold() if value else None


def _validate(query, mailto, limits):
    if not isinstance(query, str) or not query.strip() or len(query) > 4096:
        raise SearchError("invalid_query", "Query must contain 1 to 4096 characters.")
    if mailto is not None and (not isinstance(mailto, str) or not mailto.strip()
                               or len(mailto) > 254 or "@" not in mailto
                               or any(char.isspace() for char in mailto)):
        raise SearchError("invalid_mailto", "mailto must be an email address without whitespace.")
    integer_bounds = {"rows": (1, 1000), "max_pages": (1, 50),
                      "max_records": (1, 10000), "retries": (0, 3),
                      "max_response_bytes": (1, 8 * MIB),
                      "max_total_bytes": (1, 64 * MIB)}
    for name, (minimum, maximum) in integer_bounds.items():
        value = limits[name]
        if type(value) is not int or not minimum <= value <= maximum:
            raise SearchError("invalid_limits", f"{name} must be an integer in [{minimum}, {maximum}].")
    for name, maximum in (("timeout", 60), ("max_seconds", 600)):
        value = limits[name]
        if type(value) not in (int, float) or not math.isfinite(value) or not 0 < value <= maximum:
            raise SearchError("invalid_limits", f"{name} must be finite, positive and at most {maximum}.")


def _remaining(deadline, clock):
    remaining = deadline - clock()
    if remaining <= 0:
        raise SearchError("time_limit", "Search time budget exhausted.")
    return remaining


def _pause(seconds, deadline, clock, sleep):
    if seconds >= _remaining(deadline, clock):
        raise SearchError("time_limit", "Required wait exceeds the remaining search time budget.")
    sleep(seconds)


def _retry_wait(header, retry_index):
    delay = float(2 ** retry_index)
    if header:
        try:
            requested = float(header)
        except ValueError:
            try:
                date = parsedate_to_datetime(header)
                if date.tzinfo is None:
                    date = date.replace(tzinfo=timezone.utc)
                requested = (date - datetime.now(timezone.utc)).total_seconds()
            except (ValueError, TypeError, OverflowError):
                raise SearchError("invalid_retry_after", "Server returned an invalid Retry-After header.")
        if not math.isfinite(requested) or requested > 30:
            raise SearchError("retry_after_limit", "Server Retry-After exceeds the 30 second wait limit.")
        delay = max(delay, requested)
    return delay


def _body(response, limit, deadline, clock):
    """Read at most limit+1 bytes; read1 lets the overall deadline be rechecked."""
    chunks, length = [], 0
    expected = getattr(response, "length", None)
    if not getattr(response, "chunked", False) and expected is None:
        declared = response.headers.get("Content-Length")
        if declared is not None and declared.strip().isdecimal():
            expected = int(declared)
    reader = getattr(response, "read1", response.read)
    try:
        while length <= limit:
            _remaining(deadline, clock)
            chunk = reader(min(65536, limit + 1 - length))
            chunks.append(chunk)
            length += len(chunk)
            # A final read (including EOF) can consume the remaining budget.
            # Retain received bytes, but never report that response as timely.
            _remaining(deadline, clock)
            if not chunk:
                # HTTPResponse.read1() can silently return EOF with length remaining.
                # Syntactically valid JSON is insufficient to establish transport completion.
                if type(expected) is int and length < expected:
                    return b"".join(chunks), False, "network_short_read"
                return b"".join(chunks), True, None
    except SearchError as exc:
        if exc.code != "time_limit":
            raise
        return b"".join(chunks)[:limit], False, "time_limit"
    return b"".join(chunks)[:limit], False, "response_size_limit"


def _fetch(url, page, limits, deadline, clock, sleep, opener):
    request = Request(url, headers={"Accept": "application/json", "Accept-Encoding": "identity",
                                    "User-Agent": USER_AGENT})
    for retry_index in range(limits["retries"] + 1):
        attempt = {"started_at": utc_now(), "attempt": retry_index + 1}
        page["attempts"].append(attempt)
        try:
            timeout = min(limits["timeout"], _remaining(deadline, clock))
            with opener(request, timeout=timeout) as response:
                status = response.status
                attempt["http_status"] = status
                if status != 200:
                    raise HTTPError(url, status, "Unexpected HTTP status", response.headers, None)
                if response.geturl() != url:
                    raise SearchError("unexpected_redirect", "Metadata endpoint redirected; response was not accepted.")
                encoding = response.headers.get("Content-Encoding", "identity").lower()
                if encoding not in ("", "identity"):
                    raise SearchError("unsupported_encoding", "Expected uncompressed metadata response.")
                page["response_headers"] = {
                    key.lower(): response.headers.get(key) for key in
                    ("Content-Type", "Content-Length", "Date", "X-Rate-Limit-Limit", "X-Rate-Limit-Interval", "X-API-Pool")
                    if response.headers.get(key) is not None
                }
                return _body(response, page["byte_limit"], deadline, clock)
        except HTTPError as exc:
            attempt.update(http_status=exc.code, error="http_error", message=str(exc.reason))
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            exc.close()
            if exc.code not in RETRYABLE or retry_index == limits["retries"]:
                raise SearchError("http_error", f"Crossref returned HTTP {exc.code}; retry budget exhausted or status is not retryable.")
        except (URLError, TimeoutError, OSError, HTTPException) as exc:
            attempt.update(error="network_error", message=str(exc))
            retry_after = None
            if retry_index == limits["retries"]:
                raise SearchError("network_error", f"Network request failed after {retry_index + 1} attempts: {exc}")
        delay = _retry_wait(retry_after, retry_index)
        attempt["retry_wait_seconds"] = delay
        _pause(delay, deadline, clock, sleep)
    raise AssertionError("unreachable retry loop")


def _message(body):
    try:
        data = json.loads(body)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise SearchError("invalid_response", f"Response is not valid JSON: {exc}")
    message = data.get("message") if isinstance(data, dict) else None
    if (not isinstance(data, dict) or data.get("status") != "ok" or not isinstance(message, dict)
            or not isinstance(message.get("items"), list)
            or any(not isinstance(item, dict) for item in message["items"])
            or type(message.get("total-results")) is not int or message["total-results"] < 0):
        raise SearchError("invalid_response", "Expected an ok Crossref works list with items and nonnegative total-results.")
    cursor = message.get("next-cursor")
    if cursor is not None and (not isinstance(cursor, str) or not cursor):
        raise SearchError("invalid_response", "next-cursor must be a nonempty string when present.")
    return message


def search(query, output, *, rows=20, max_pages=5, max_records=100, mailto=None,
           timeout=15, retries=2, max_seconds=120, max_response_bytes=2 * MIB,
           max_total_bytes=20 * MIB, opener=None, sleep=None, clock=None):
    """Create a new output directory and return a saved, possibly failed report.

    Invalid arguments/existing destinations raise SearchError without a request.
    A failed retrieval keeps partial evidence with passed=false and errors.
    """
    limits = {"rows": rows, "max_pages": max_pages, "max_records": max_records,
              "timeout": timeout, "retries": retries, "max_seconds": max_seconds,
              "max_response_bytes": max_response_bytes, "max_total_bytes": max_total_bytes}
    _validate(query, mailto, limits)
    destination = Path(output).expanduser().absolute()
    try:
        destination = destination.parent.resolve(strict=True) / destination.name
        destination.mkdir()  # Deliberately refuses even an empty directory or symlink.
    except (OSError, RuntimeError) as exc:
        raise SearchError("output_unavailable", f"Output must be a new directory in an existing parent: {exc}")
    opener = opener or build_opener(_NoRedirect()).open
    sleep, clock = sleep or time.sleep, clock or time.monotonic
    deadline = clock() + max_seconds
    report = {
        "schema_version": 1, "provider": "Crossref", "passed": False, "status": "failed",
        "started_at": utc_now(), "finished_at": None,
        "query": {"text": query, "endpoint": ENDPOINT, "parameters": {"query": query, "rows": rows},
                  "limits": limits, "mailto_included": mailto is not None},
        "access": {"content_access": "metadata-only", "full_text_accessed": False,
                   "claim_support_checked": False, "novelty_assessed": False,
                   "scope": "Crossref-registered metadata matching this API query; not all research literature."},
        "pagination": {"pages_completed": 0, "reported_total_results": None,
                       "reported_totals_by_page": [], "returned_items": 0,
                       "retained_records": 0, "duplicate_items": 0, "items_without_doi": 0,
                       "unretained_items": 0, "response_bytes_saved": 0,
                       "truncated": True, "cursor_exhausted": False, "stop_reason": None},
        "pages": [], "records": [], "errors": [],
    }
    pagination = report["pagination"]
    records, seen, cursor = {}, set(), "*"
    try:
        (destination / "pages").mkdir()
        for page_index in range(1, max_pages + 1):
            if page_index > 1:
                # Public works-list requests are limited to 1/s (Crossref, July 2026).
                _pause(1.0, deadline, clock, sleep)
            parameters = {"query": query, "rows": rows, "cursor": cursor}
            if mailto:
                parameters["mailto"] = mailto
            url = ENDPOINT + "?" + urlencode(parameters)
            page = {"page": page_index, "url": url, "requested_cursor": cursor,
                    "status": "failed", "attempts": [], "raw_response": None,
                    "response_sha256": None, "response_complete": False,
                    "byte_limit": min(max_response_bytes, max_total_bytes - pagination["response_bytes_saved"])}
            report["pages"].append(page)
            if page["byte_limit"] <= 0:
                raise SearchError("total_size_limit", "Total raw response byte budget exhausted.")
            body, complete, incomplete_reason = _fetch(url, page, limits, deadline, clock, sleep, opener)
            raw_name = f"pages/page-{page_index:04d}." + ("json" if complete else "partial")
            with (destination / raw_name).open("xb") as stream:
                stream.write(body)
            page.update(raw_response=raw_name, response_sha256=hashlib.sha256(body).hexdigest(),
                        response_bytes=len(body), response_complete=complete)
            pagination["response_bytes_saved"] += len(body)
            if not complete:
                page["incomplete_reason"] = incomplete_reason
                if incomplete_reason == "time_limit":
                    raise SearchError("time_limit", "Response exceeded the search time budget; saved partial body only.")
                if incomplete_reason == "network_short_read":
                    raise SearchError("network_short_read", "Response ended before its declared Content-Length; saved partial body only.")
                raise SearchError("response_size_limit", "Page exceeded its per-response or remaining total byte budget; saved prefix only.")
            message = _message(body)
            items, next_cursor = message["items"], message.get("next-cursor")
            if len(items) > rows:
                raise SearchError("invalid_response", "Crossref returned more items than the requested rows.")
            page.update(status="completed", returned_items=len(items),
                        reported_total_results=message["total-results"], next_cursor=next_cursor)
            pagination["pages_completed"] += 1
            pagination["reported_totals_by_page"].append(message["total-results"])
            if pagination["reported_total_results"] is None:
                pagination["reported_total_results"] = message["total-results"]
            pagination["returned_items"] += len(items)
            for item in items:
                doi = normalize_doi(item.get("DOI"))
                if doi is None:
                    pagination["items_without_doi"] += 1
                key = ("doi:" + doi) if doi else "metadata:" + hashlib.sha256(
                    json.dumps(item, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
                if key in seen:
                    pagination["duplicate_items"] += 1
                    if key in records and page_index not in records[key]["source_pages"]:
                        records[key]["source_pages"].append(page_index)
                    continue
                seen.add(key)
                if len(records) < max_records:
                    records[key] = {"doi": doi, "metadata": item, "source_pages": [page_index]}
                else:
                    pagination["unretained_items"] += 1
            exhausted = len(items) < rows or next_cursor is None
            if exhausted:
                pagination.update(cursor_exhausted=True,
                                  truncated=pagination["unretained_items"] > 0,
                                  stop_reason="max_records" if pagination["unretained_items"] else "cursor_exhausted")
                break
            if len(records) >= max_records:
                pagination["stop_reason"] = "max_records"
                break
            # Crossref cursors may remain identical across pages; item count ends pagination.
            cursor = next_cursor
        else:
            pagination["stop_reason"] = "max_pages"
        report.update(passed=True, status="completed")
    except SearchError as exc:
        pagination["stop_reason"] = exc.code
        report["errors"].append({"code": exc.code, "message": str(exc)})
    except (OSError, ValueError, RuntimeError) as exc:
        pagination["stop_reason"] = "io_error"
        report["errors"].append({"code": "io_error", "message": str(exc)})
    report["records"] = list(records.values())
    pagination["retained_records"] = len(records)
    report["finished_at"] = utc_now()
    try:
        with (destination / "search.json").open("x", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=False, allow_nan=False, indent=2)
            stream.write("\n")
    except (OSError, ValueError) as exc:
        raise SearchError("report_write_failed", f"Could not save search.json; partial output may remain: {exc}")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True, help="Crossref query text (sent to the external API)")
    parser.add_argument("--output", required=True, help="New output directory; parent must exist")
    parser.add_argument("--mailto", help="Optional contact email sent to Crossref and saved in request URLs")
    parser.add_argument("--rows", type=int, default=20, help="Items per page, 1..1000 (default: 20)")
    parser.add_argument("--max-pages", type=int, default=5, help="Maximum pages, 1..50 (default: 5)")
    parser.add_argument("--max-records", type=int, default=100, help="Maximum retained records, 1..10000 (default: 100)")
    parser.add_argument("--timeout", type=float, default=15, help="Socket timeout seconds, at most 60 (default: 15)")
    parser.add_argument("--retries", type=int, default=2, help="Retries per page, 0..3 (default: 2)")
    parser.add_argument("--max-seconds", type=float, default=120, help="Overall time budget, at most 600 (default: 120)")
    parser.add_argument("--max-response-bytes", type=int, default=2 * MIB, help="Per-page byte cap, at most 8 MiB")
    parser.add_argument("--max-total-bytes", type=int, default=20 * MIB, help="Total saved response cap, at most 64 MiB")
    args = parser.parse_args(argv)
    try:
        report = search(**vars(args))
        result = {"passed": report["passed"], "status": report["status"],
                  "report": str(Path(args.output).expanduser().absolute() / "search.json"),
                  "content_access": "metadata-only", "pagination": report["pagination"],
                  "errors": report["errors"]}
    except SearchError as exc:
        result = {"passed": False, "status": "failed", "errors": [{"code": exc.code, "message": str(exc)}]}
    # Portable console JSON even when a Windows terminal cannot encode the path.
    print(json.dumps(result, ensure_ascii=True, allow_nan=False, indent=2))
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
