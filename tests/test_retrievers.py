"""Unit tests for WellMarkedRetriever — the SDK client is faked, no network."""
import pytest
from wellmarked import SearchResult, SearchResults

import langchain_wellmarked.retrievers as mod
from langchain_wellmarked import WellMarkedRetriever


class FakeWellMarked:
    """Stands in for wellmarked.WellMarked. Records calls, returns canned data."""

    calls: list = []

    def __init__(self, api_key=None, **kwargs):
        FakeWellMarked.calls.append(("init", api_key))

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        pass

    def search(self, query, *, num_results=5, render_js=False):
        FakeWellMarked.calls.append(("search", query, num_results, render_js))
        return SearchResults(
            query=query,
            results=[
                SearchResult(
                    url="https://a.test/1", status="ok", title="A",
                    snippet="s1", markdown="# A",
                ),
                SearchResult(
                    url="https://b.test/2", status="error", title="B",
                    snippet="s2", error="target_timeout",
                ),
            ],
            request_id="req_1",
        )


@pytest.fixture(autouse=True)
def fake_client(monkeypatch):
    FakeWellMarked.calls = []
    monkeypatch.setattr(mod, "WellMarked", FakeWellMarked)


def test_retriever_returns_ok_results_as_documents():
    docs = WellMarkedRetriever(api_key="wm_test", num_results=3).invoke("vector databases")

    assert ("init", "wm_test") in FakeWellMarked.calls
    assert ("search", "vector databases", 3, False) in FakeWellMarked.calls
    # The errored result is skipped — only extractable pages become Documents.
    assert len(docs) == 1
    assert docs[0].page_content == "# A"
    assert docs[0].metadata == {
        "source": "https://a.test/1", "title": "A", "snippet": "s1",
    }


def test_retriever_passes_render_js():
    WellMarkedRetriever(render_js=True).invoke("q")
    assert ("search", "q", 5, True) in FakeWellMarked.calls
