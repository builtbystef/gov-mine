import json
import logging
from typing import TYPE_CHECKING

from gov_mine.jobs.context import running
from gov_mine.shared.logs import ContextFilter, JsonFormatter, TextFormatter, request_id

if TYPE_CHECKING:
    from types import TracebackType

    ExcInfo = tuple[type[BaseException], BaseException, TracebackType | None]


def record(message: str, exc_info: ExcInfo | None = None) -> logging.LogRecord:
    rec = logging.LogRecord("gov_mine.tests", logging.INFO, __file__, 1, message, (), exc_info)
    ContextFilter().filter(rec)
    return rec


def test_text_lines_carry_a_utc_timestamp_and_the_request_id():
    token = request_id.set("report-1")
    try:
        line = TextFormatter().format(record("hello"))
    finally:
        request_id.reset(token)
    timestamp, rest = line.split(" ", 1)
    assert timestamp.endswith("Z")
    assert "T" in timestamp
    assert rest == "INFO [gov_mine.tests] [report-1] hello"


def test_json_lines_are_one_object_each():
    exc = ValueError("nope")
    rec = record("it broke", exc_info=(type(exc), exc, None))
    line = json.loads(JsonFormatter().format(rec))
    assert line["level"] == "INFO"
    assert line["logger"] == "gov_mine.tests"
    assert line["request_id"] == "-"
    assert line["message"] == "it broke"
    assert line["time"].endswith("Z")
    assert "ValueError: nope" in line["exception"]
    assert "\n" not in JsonFormatter().format(record("one\nline"))


def test_json_lines_inside_a_job_carry_its_ids():
    with running("crawl.fetch", 7, None, {"run_id": "run-1", "webpage_id": "page-1"}):
        line = json.loads(JsonFormatter().format(record("fetching")))
    assert (line["run_id"], line["job_id"], line["webpage_id"]) == ("run-1", 7, "page-1")


def test_json_lines_of_a_job_without_a_webpage_carry_no_webpage_id():
    with running("crawl.start", 8, None, {"run_id": "run-1"}):
        line = json.loads(JsonFormatter().format(record("starting")))
    assert (line["run_id"], line["job_id"]) == ("run-1", 8)
    assert "webpage_id" not in line


def test_json_lines_outside_a_job_carry_none_of_its_ids():
    with running("crawl.fetch", 7, None, {"run_id": "run-1", "webpage_id": "page-1"}):
        pass
    line = json.loads(JsonFormatter().format(record("idle")))
    assert not {"run_id", "job_id", "webpage_id"} & line.keys()
