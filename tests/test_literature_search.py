"""Crossref adapter behavior with local synthetic HTTP responses; no network."""

from contextlib import redirect_stdout
import hashlib
from http.client import HTTPResponse, IncompleteRead
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/rw-literature/scripts/search_crossref.py"
SPEC = importlib.util.spec_from_file_location("rw_search_crossref", SCRIPT)
SEARCH = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SEARCH)


def response(items, *, total=10, cursor="next+cursor/=", **updates):
    message = {"items": items, "total-results": total}
    if cursor is not None:
        message["next-cursor"] = cursor
    return json.dumps({"status": "ok", "message": message, **updates}).encode("utf-8")


class Response(io.BytesIO):
    def __init__(self, body, url):
        super().__init__(body)
        self.status = 200
        self.headers = {"Content-Type": "application/json", "X-API-Pool": "public"}
        self.url = url

    def geturl(self):
        return self.url


class Opener:
    def __init__(self, *results):
        self.results = list(results)
        self.calls = []

    def __call__(self, request, *, timeout):
        self.calls.append((request, timeout))
        if not self.results:
            raise AssertionError("Unexpected extra network request")
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return Response(result, request.full_url)


class Clock:
    def __init__(self):
        self.now = 0
        self.waits = []

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.waits.append(seconds)
        self.now += seconds


def http_opener(body, *, extra_declared_bytes=0):
    """Real HTTPResponse parser over an in-memory socket, including read1 semantics."""
    wire = (b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: "
            + str(len(body) + extra_declared_bytes).encode("ascii") + b"\r\n\r\n" + body)

    class Socket:
        def makefile(self, mode):
            return io.BytesIO(wire)

    def open_response(request, *, timeout):
        result = HTTPResponse(Socket(), method="GET")
        result.begin()
        result.url = request.full_url
        return result

    return open_response


class LiteratureSearchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="rw-crossref-tests-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.output = self.base / "检索结果 with spaces"
        self.clock = Clock()

    def search(self, opener, **kwargs):
        result = SEARCH.search("rough paths & probability", self.output, opener=opener,
                               sleep=self.clock.sleep, clock=self.clock, **kwargs)
        saved = json.loads((self.output / "search.json").read_text(encoding="utf-8"))
        self.assertEqual(result, saved)
        for page in result["pages"]:
            if page["raw_response"]:
                raw = (self.output / page["raw_response"]).read_bytes()
                self.assertEqual(page["response_sha256"], hashlib.sha256(raw).hexdigest())
                self.assertEqual(page["response_bytes"], len(raw))
        return result

    def test_cursor_pagination_deduplicates_doi_and_retains_metadata_origins(self):
        opener = Opener(
            response([{"DOI": "10.1000/ABC", "title": ["First title"]},
                      {"DOI": "https://doi.org/10.1000/abc", "title": ["Duplicate"]}], total=8),
            response([{"DOI": "doi:10.1000/DEF"}], total=9, cursor=None))
        report = self.search(opener, rows=2)
        self.assertTrue(report["passed"])
        self.assertEqual([record["doi"] for record in report["records"]], ["10.1000/abc", "10.1000/def"])
        self.assertEqual(report["records"][0]["metadata"]["title"], ["First title"])
        self.assertEqual(report["pagination"]["returned_items"], 3)
        self.assertEqual(report["pagination"]["duplicate_items"], 1)
        self.assertEqual(report["pagination"]["reported_totals_by_page"], [8, 9])
        self.assertFalse(report["pagination"]["truncated"])
        self.assertEqual(report["pagination"]["pages_completed"], 2)
        first, second = [parse_qs(urlsplit(call[0].full_url).query) for call in opener.calls]
        self.assertEqual(first["cursor"], ["*"])
        self.assertEqual(second["cursor"], ["next+cursor/="])
        self.assertEqual(first["query"], ["rough paths & probability"])
        self.assertEqual(opener.calls[0][0].get_header("Accept-encoding"), "identity")
        self.assertEqual(report["access"]["content_access"], "metadata-only")
        self.assertFalse(report["access"]["full_text_accessed"])
        self.assertEqual(self.clock.waits, [1.0])

    def test_default_paging_never_exceeds_public_one_request_per_second(self):
        request_times = []
        bodies = iter([response([{"DOI": "10.1/A"}]), response([], total=1)])

        def public_opener(request, *, timeout):
            request_times.append(self.clock())
            if len(request_times) > 1 and request_times[-1] - request_times[-2] < 1.0:
                raise HTTPError(request.full_url, 429, "public works-list rate exceeded", {}, None)
            result = Response(next(bodies), request.full_url)
            result.headers.update({"X-Rate-Limit-Limit": "1", "X-Rate-Limit-Interval": "1s"})
            return result

        report = self.search(public_opener, rows=1)
        self.assertTrue(report["passed"])
        self.assertEqual(request_times, [0, 1.0])
        self.assertTrue(all(len(page["attempts"]) == 1 for page in report["pages"]))

    def test_duplicates_across_pages_preserve_page_locations(self):
        opener = Opener(response([{"DOI": "10.1/A"}]),
                        response([{"DOI": "10.1/a"}]), response([], total=10))
        report = self.search(opener, rows=1)
        self.assertEqual(report["records"][0]["source_pages"], [1, 2])
        self.assertEqual(report["pagination"]["duplicate_items"], 1)
        self.assertEqual(len(opener.calls), 3)

    def test_repeated_cursor_is_not_mistaken_for_exhaustion(self):
        opener = Opener(response([{"DOI": "10.1/A"}], cursor="same"),
                        response([{"DOI": "10.1/B"}], cursor="same"),
                        response([], cursor="same"))
        report = self.search(opener, rows=1)
        self.assertTrue(report["pagination"]["cursor_exhausted"])
        self.assertEqual(len(report["records"]), 2)

    def test_max_pages_stops_without_claiming_complete_coverage(self):
        opener = Opener(response([{"DOI": "10.1/A"}], total=12345))
        report = self.search(opener, rows=1, max_pages=1)
        self.assertTrue(report["passed"])
        self.assertTrue(report["pagination"]["truncated"])
        self.assertEqual(report["pagination"]["stop_reason"], "max_pages")
        self.assertEqual(report["pagination"]["reported_total_results"], 12345)
        self.assertEqual(len(opener.calls), 1)

    def test_record_cap_accounts_for_unretained_items_even_on_last_page(self):
        opener = Opener(response([{"DOI": "10.1/A"}, {"DOI": "10.1/B"}], cursor=None))
        report = self.search(opener, rows=2, max_records=1)
        self.assertEqual(report["pagination"]["unretained_items"], 1)
        self.assertTrue(report["pagination"]["truncated"])
        self.assertTrue(report["pagination"]["cursor_exhausted"])
        self.assertEqual(report["pagination"]["stop_reason"], "max_records")
        self.assertEqual(len(report["records"]), 1)

    def test_record_cap_still_deduplicates_omitted_dois(self):
        opener = Opener(response([{"DOI": "10.1/A"}, {"DOI": "10.1/B"}, {"DOI": "10.1/b"}], cursor=None))
        report = self.search(opener, rows=3, max_records=1)
        self.assertEqual(report["pagination"]["unretained_items"], 1)
        self.assertEqual(report["pagination"]["duplicate_items"], 1)

    def test_missing_doi_uses_metadata_identity_without_dropping_distinct_records(self):
        opener = Opener(response([{"title": ["A"]}, {"title": ["A"]}, {"title": ["B"]}], cursor=None))
        report = self.search(opener, rows=3)
        self.assertEqual(report["pagination"]["items_without_doi"], 3)
        self.assertEqual(report["pagination"]["duplicate_items"], 1)
        self.assertEqual(len(report["records"]), 2)
        self.assertTrue(all(record["doi"] is None for record in report["records"]))

    def test_retry_429_honors_retry_after_and_records_attempts(self):
        failure = HTTPError(SEARCH.ENDPOINT, 429, "too many", {"Retry-After": "3"}, io.BytesIO(b"limited"))
        opener = Opener(failure, response([], total=0))
        report = self.search(opener)
        self.assertTrue(report["passed"])
        self.assertEqual(self.clock.waits, [3.0])
        self.assertEqual(len(report["pages"][0]["attempts"]), 2)
        self.assertEqual(report["pages"][0]["attempts"][0]["http_status"], 429)
        self.assertEqual(opener.calls[0][1], 15)

    def test_retry_budget_is_bounded_and_does_not_return_false_success(self):
        opener = Opener(*(HTTPError(SEARCH.ENDPOINT, 503, "unavailable", {}, None) for _ in range(3)))
        report = self.search(opener, retries=2)
        self.assertFalse(report["passed"])
        self.assertEqual(len(opener.calls), 3)
        self.assertEqual(self.clock.waits, [1.0, 2.0])
        self.assertEqual(report["errors"][0]["code"], "http_error")
        self.assertEqual(report["pagination"]["pages_completed"], 0)
        self.assertIsNone(report["pages"][0]["response_sha256"])

    def test_nonretryable_failure_preserves_completed_page(self):
        opener = Opener(response([{"DOI": "10.1/A"}]),
                        HTTPError(SEARCH.ENDPOINT, 403, "forbidden", {}, None))
        report = self.search(opener, rows=1)
        self.assertFalse(report["passed"])
        self.assertEqual(len(opener.calls), 2)
        self.assertEqual(report["pagination"]["pages_completed"], 1)
        self.assertEqual(len(report["records"]), 1)
        self.assertTrue(report["pagination"]["truncated"])

    def test_network_timeout_retries_then_recovers(self):
        report = self.search(Opener(URLError("synthetic timeout"), response([], total=0)), retries=1)
        self.assertTrue(report["passed"])
        self.assertEqual(report["pages"][0]["attempts"][0]["error"], "network_error")

    def test_interrupted_http_body_is_a_recorded_failure(self):
        report = self.search(Opener(IncompleteRead(b"partial", 10)), retries=0)
        self.assertFalse(report["passed"])
        self.assertEqual(report["errors"][0]["code"], "network_error")

    def test_real_http_response_silent_short_read_preserves_partial_and_fails(self):
        body = response([], total=0, cursor=None)  # Valid JSON despite missing transport bytes.
        report = self.search(http_opener(body, extra_declared_bytes=50), retries=0)
        self.assertFalse(report["passed"])
        self.assertEqual(report["errors"][0]["code"], "network_short_read")
        self.assertEqual(report["pagination"]["pages_completed"], 0)
        self.assertTrue(report["pagination"]["truncated"])
        self.assertFalse(report["pagination"]["cursor_exhausted"])
        self.assertEqual(report["records"], [])
        page = report["pages"][0]
        self.assertFalse(page["response_complete"])
        self.assertEqual(page["incomplete_reason"], "network_short_read")
        self.assertEqual(page["response_headers"]["content-length"], str(len(body) + 50))
        self.assertTrue(page["raw_response"].endswith(".partial"))
        self.assertEqual((self.output / page["raw_response"]).read_bytes(), body)

    def test_real_http_response_matching_content_length_completes(self):
        report = self.search(http_opener(response([], total=0, cursor=None)), retries=0)
        self.assertTrue(report["passed"])
        self.assertTrue(report["pages"][0]["response_complete"])
        self.assertFalse(report["pagination"]["truncated"])

    def test_main_exits_failed_for_real_http_response_short_read(self):
        transport = mock.Mock(open=http_opener(response([], total=0, cursor=None), extra_declared_bytes=50))
        stdout = io.StringIO()
        with mock.patch.object(SEARCH, "build_opener", return_value=transport), redirect_stdout(stdout):
            code = SEARCH.main(["--query", "synthetic", "--output", str(self.output), "--retries", "0"])
        self.assertEqual(code, 2)
        self.assertFalse(json.loads(stdout.getvalue())["passed"])
        saved = json.loads((self.output / "search.json").read_text(encoding="utf-8"))
        self.assertFalse(saved["pages"][0]["response_complete"])

    def test_excessive_retry_after_stops_without_early_retry(self):
        opener = Opener(HTTPError(SEARCH.ENDPOINT, 429, "limited", {"Retry-After": "3600"}, None))
        report = self.search(opener)
        self.assertFalse(report["passed"])
        self.assertEqual(report["errors"][0]["code"], "retry_after_limit")
        self.assertEqual(len(opener.calls), 1)
        self.assertEqual(self.clock.waits, [])

    def test_overall_time_budget_prevents_retry(self):
        opener = Opener(TimeoutError("timeout"))
        report = self.search(opener, max_seconds=0.5)
        self.assertFalse(report["passed"])
        self.assertEqual(report["errors"][0]["code"], "time_limit")
        self.assertEqual(opener.calls[0][1], 0.5)
        self.assertEqual(len(opener.calls), 1)

    def test_read_returning_after_deadline_preserves_partial_body_without_success(self):
        body = response([], total=0, cursor=None)
        for delayed_read in ('body', 'eof'):
            with self.subTest(delayed_read=delayed_read):
                self.output = self.base / ('delayed-' + delayed_read)
                self.clock.now = 0
                clock = self.clock

                class DelayedResponse(Response):
                    def read1(self, size=-1):
                        chunk = super().read1(size)
                        if bool(chunk) == (delayed_read == 'body'):
                            clock.now = 2
                        return chunk

                def delayed_opener(request, *, timeout):
                    return DelayedResponse(body, request.full_url)

                report = self.search(delayed_opener, max_seconds=1, retries=0)
                self.assertFalse(report['passed'])
                self.assertEqual(report['errors'][0]['code'], 'time_limit')
                self.assertEqual(report['pagination']['pages_completed'], 0)
                self.assertEqual(report['records'], [])
                page = report['pages'][0]
                self.assertFalse(page['response_complete'])
                self.assertEqual(page['incomplete_reason'], 'time_limit')
                self.assertTrue(page['raw_response'].endswith('.partial'))
                self.assertEqual((self.output / page['raw_response']).read_bytes(), body)

    def test_eof_deadline_boundary_uses_the_existing_exhaustion_rule(self):
        body = response([], total=0, cursor=None)
        for ended_at, expected_passed in ((0.999, True), (1.0, False)):
            with self.subTest(ended_at=ended_at):
                self.output = self.base / ('deadline-' + str(ended_at))
                self.clock.now = 0
                clock = self.clock

                class BoundaryResponse(Response):
                    def read1(self, size=-1):
                        chunk = super().read1(size)
                        if not chunk:
                            clock.now = ended_at
                        return chunk

                def boundary_opener(request, *, timeout):
                    return BoundaryResponse(body, request.full_url)

                report = self.search(boundary_opener, max_seconds=1, retries=0)
                self.assertEqual(report['passed'], expected_passed)
                if not expected_passed:
                    self.assertEqual(report['errors'][0]['code'], 'time_limit')

    def test_oversized_response_saves_only_bounded_prefix_and_hash(self):
        report = self.search(Opener(b"x" * 1000), max_response_bytes=100)
        self.assertFalse(report["passed"])
        self.assertEqual(report["errors"][0]["code"], "response_size_limit")
        self.assertEqual(report["pagination"]["response_bytes_saved"], 100)
        self.assertFalse(report["pages"][0]["response_complete"])
        self.assertEqual(report["records"], [])

    def test_total_byte_cap_applies_across_pages(self):
        first = response([{"DOI": "10.1/A"}])
        opener = Opener(first, response([{"DOI": "10.1/B"}]))
        report = self.search(opener, rows=1, max_total_bytes=len(first) + 10)
        self.assertFalse(report["passed"])
        self.assertEqual(report["pagination"]["response_bytes_saved"], len(first) + 10)
        self.assertEqual(report["pagination"]["pages_completed"], 1)

    def test_invalid_json_is_not_reported_as_an_empty_success(self):
        report = self.search(Opener(b"not json"))
        self.assertFalse(report["passed"])
        self.assertEqual(report["errors"][0]["code"], "invalid_response")
        self.assertTrue(report["pages"][0]["response_complete"])
        self.assertIsNotNone(report["pages"][0]["response_sha256"])

    def test_existing_output_is_untouched_and_makes_no_request(self):
        self.output.mkdir()
        original = self.output / "keep.txt"
        original.write_bytes(b"keep exactly")
        opener = Opener()
        with self.assertRaises(SEARCH.SearchError) as caught:
            self.search(opener)
        self.assertEqual(caught.exception.code, "output_unavailable")
        self.assertEqual(original.read_bytes(), b"keep exactly")
        self.assertEqual(list(self.output.iterdir()), [original])
        self.assertEqual(opener.calls, [])

    def test_empty_existing_output_is_also_refused(self):
        self.output.mkdir()
        with self.assertRaises(SEARCH.SearchError):
            self.search(Opener())
        self.assertEqual(list(self.output.iterdir()), [])

    def test_existing_symlink_is_not_followed_to_create_output(self):
        target = self.base / "absent target"
        try:
            self.output.symlink_to(target, target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"Symlinks unavailable: {exc}")
        with self.assertRaises(SEARCH.SearchError):
            self.search(Opener())
        self.assertFalse(target.exists())
        self.assertTrue(self.output.is_symlink())

    def test_redirected_response_is_not_accepted_as_metadata(self):
        opener = mock.Mock(return_value=Response(response([], total=0), "https://example.org/fulltext"))
        report = self.search(opener)
        self.assertFalse(report["passed"])
        self.assertEqual(report["errors"][0]["code"], "unexpected_redirect")
        self.assertEqual(report["records"], [])

    def test_invalid_arguments_do_not_create_output(self):
        for kwargs in ({"rows": 0}, {"retries": 4}, {"timeout": float("nan")},
                       {"max_seconds": 601}, {"mailto": "bad\r\nheader@example.org"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(SEARCH.SearchError):
                self.search(Opener(), **kwargs)
            self.assertFalse(self.output.exists())

    def test_optional_mailto_is_explicit_and_traceable(self):
        opener = Opener(response([], total=0))
        report = self.search(opener, mailto="researcher@example.org")
        self.assertTrue(report["query"]["mailto_included"])
        self.assertEqual(parse_qs(urlsplit(opener.calls[0][0].full_url).query)["mailto"], ["researcher@example.org"])

    def test_cli_failure_exit_and_json_do_not_claim_success(self):
        self.output.mkdir()
        proc = subprocess.run([sys.executable, "-B", str(SCRIPT), "--query", "synthetic",
                               "--output", str(self.output)], capture_output=True, text=True, timeout=10)
        self.assertEqual(proc.returncode, 2)
        self.assertFalse(json.loads(proc.stdout)["passed"])
        self.assertEqual(list(self.output.iterdir()), [])

    def test_main_success_and_failed_retrieval_exit_codes(self):
        for passed in (True, False):
            fake = {"passed": passed, "status": "completed" if passed else "failed",
                    "pagination": {}, "errors": [] if passed else [{"code": "http_error"}]}
            stdout = io.StringIO()
            with mock.patch.object(SEARCH, "search", return_value=fake), redirect_stdout(stdout):
                code = SEARCH.main(["--query", "synthetic", "--output", str(self.output)])
            self.assertEqual(code, 0 if passed else 2)
            self.assertEqual(json.loads(stdout.getvalue())["passed"], passed)


if __name__ == "__main__":
    unittest.main()
