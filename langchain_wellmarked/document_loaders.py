"""WellMarked document loader for LangChain."""
from __future__ import annotations

from typing import Any, Iterator, Literal, Optional

from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document
from wellmarked import ExtractionMeta, WellMarked


def _metadata(meta: ExtractionMeta, source: str, depth: Optional[int] = None) -> dict[str, Any]:
    """Build JSON-serializable Document metadata from the SDK's ExtractionMeta."""
    out: dict[str, Any] = {"source": meta.url or source}
    if meta.title is not None:
        out["title"] = meta.title
    if meta.author is not None:
        out["author"] = meta.author
    if meta.date is not None:
        out["date"] = meta.date
    if meta.retrieved_at is not None:
        out["retrieved_at"] = meta.retrieved_at.isoformat()
    if depth is not None:
        out["depth"] = depth
    return out


class WellMarkedLoader(BaseLoader):
    """Load web pages as clean Markdown via the WellMarked API.

    Setup:
        Install ``langchain-wellmarked`` and set the ``WELLMARKED_API_KEY``
        environment variable (or pass ``api_key=``). Get a key at
        https://wellmarked.io.

        .. code-block:: bash

            pip install langchain-wellmarked

    Instantiate:
        .. code-block:: python

            from langchain_wellmarked import WellMarkedLoader

            loader = WellMarkedLoader("https://example.com/article")

            # Or crawl a whole site, one Document per page:
            loader = WellMarkedLoader(
                "https://docs.example.com", mode="crawl", depth=2
            )

    Load:
        .. code-block:: python

            docs = loader.load()
            docs[0].page_content   # clean Markdown
            docs[0].metadata       # {"source": ..., "title": ..., ...}

    In ``crawl`` mode the loader blocks until the crawl job finishes
    (up to ``job_timeout`` seconds) and yields only successfully
    extracted pages; failed pages (timeouts, robots-disallowed) are
    skipped. Crawling requires a Pro plan or above.
    """

    def __init__(
        self,
        url: str,
        *,
        api_key: Optional[str] = None,
        mode: Literal["extract", "crawl"] = "extract",
        depth: int = 1,
        render_js: bool = False,
        job_timeout: Optional[float] = 300.0,
    ) -> None:
        """Create the loader.

        Args:
            url: The URL to extract (``mode="extract"``) or the root URL
                to crawl from (``mode="crawl"``).
            api_key: WellMarked API key (``wm_...``). Falls back to the
                ``WELLMARKED_API_KEY`` environment variable.
            mode: ``"extract"`` loads the single page at ``url``;
                ``"crawl"`` BFS-crawls same-site links from ``url``.
            depth: Crawl depth (``mode="crawl"`` only).
            render_js: Render JS-heavy pages with a headless browser
                (Pro plan and above).
            job_timeout: Seconds to wait for a crawl job to finish.
                ``None`` waits forever.
        """
        if mode not in ("extract", "crawl"):
            raise ValueError(f"mode must be 'extract' or 'crawl', got {mode!r}")
        self.url = url
        self.api_key = api_key
        self.mode = mode
        self.depth = depth
        self.render_js = render_js
        self.job_timeout = job_timeout

    def lazy_load(self) -> Iterator[Document]:
        with WellMarked(api_key=self.api_key) as wm:
            if self.mode == "extract":
                result = wm.extract(self.url, render_js=self.render_js)
                yield Document(
                    page_content=result.markdown,
                    metadata=_metadata(result.metadata, self.url),
                )
            else:
                job = wm.crawl(self.url, depth=self.depth, render_js=self.render_js)
                job = wm.wait_for_job(job.job_id, timeout=self.job_timeout)
                for page in job.results:
                    if not page.ok:
                        continue
                    assert page.markdown is not None and page.metadata is not None
                    yield Document(
                        page_content=page.markdown,
                        metadata=_metadata(page.metadata, page.url, depth=page.depth),
                    )
