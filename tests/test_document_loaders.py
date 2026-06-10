"""Unit tests for WellMarkedLoader — the SDK client is faked, no network."""
from datetime import datetime, timezone

import pytest
from wellmarked import CrawlItem, CrawlJob, ExtractionMeta, ExtractResult

import langchain_wellmarked.document_loaders as mod
from langchain_wellmarked import WellMarkedLoader

RETRIEVED = datetime(2026, 6, 10, 12, 0, 0, tzinfo=timezone.utc)


class FakeWellMarked:
    """Stands in for wellmarked.WellMarked. Records calls, returns canned data."""

    calls: list = []

    def __init__(self, api_key=None, **kwargs):
        FakeWellMarked.calls.append(("init", api_key))

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        pass

    def extract(self, url, *, render_js=False):
        FakeWellMarked.calls.append(("extract", url, render_js))
        return ExtractResult(
            markdown="# Hello",
            metadata=ExtractionMeta(
                url=url, title="Hello", author="Ada", retrieved_at=RETRIEVED
            ),
            request_id="req_1",
        )

    def crawl(self, url, *, depth=1, render_js=False, **kwargs):
        FakeWellMarked.calls.append(("crawl", url, depth, render_js))
        return CrawlJob(job_id="job_1", status="queued", total=0, completed=0, results=[])

    def wait_for_job(self, job_id, *, timeout=300.0, **kwargs):
        FakeWellMarked.calls.append(("wait_for_job", job_id, timeout))
        return CrawlJob(
            job_id=job_id,
            status="done",
            total=2,
            completed=2,
            results=[
                CrawlItem(
                    url="https://docs.example.com",
                    depth=0,
                    markdown="# Root",
                    metadata=ExtractionMeta(url="https://docs.example.com", title="Root"),
                ),
                CrawlItem(url="https://docs.example.com/dead", depth=1, error="target_timeout"),
            ],
        )


@pytest.fixture(autouse=True)
def fake_client(monkeypatch):
    FakeWellMarked.calls = []
    monkeypatch.setattr(mod, "WellMarked", FakeWellMarked)


def test_extract_mode_yields_one_document():
    docs = WellMarkedLoader("https://example.com/article", api_key="wm_test").load()

    assert len(docs) == 1
    assert docs[0].page_content == "# Hello"
    assert docs[0].metadata == {
        "source": "https://example.com/article",
        "title": "Hello",
        "author": "Ada",
        "retrieved_at": RETRIEVED.isoformat(),
    }
    assert ("init", "wm_test") in FakeWellMarked.calls
    assert ("extract", "https://example.com/article", False) in FakeWellMarked.calls


def test_extract_mode_passes_render_js():
    WellMarkedLoader("https://example.com", render_js=True).load()

    assert ("extract", "https://example.com", True) in FakeWellMarked.calls


def test_crawl_mode_yields_ok_pages_and_skips_failures():
    docs = WellMarkedLoader(
        "https://docs.example.com", mode="crawl", depth=2, job_timeout=60.0
    ).load()

    assert ("crawl", "https://docs.example.com", 2, False) in FakeWellMarked.calls
    assert ("wait_for_job", "job_1", 60.0) in FakeWellMarked.calls
    assert len(docs) == 1  # the failed page is skipped
    assert docs[0].page_content == "# Root"
    assert docs[0].metadata == {
        "source": "https://docs.example.com",
        "title": "Root",
        "depth": 0,
    }


def test_invalid_mode_raises():
    with pytest.raises(ValueError, match="mode must be"):
        WellMarkedLoader("https://example.com", mode="bulk")


def test_lazy_load_is_lazy():
    it = WellMarkedLoader("https://example.com").lazy_load()
    assert FakeWellMarked.calls == []  # nothing happens until iteration
    next(it)
    assert ("extract", "https://example.com", False) in FakeWellMarked.calls
