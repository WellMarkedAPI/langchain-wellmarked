"""WellMarked retriever for LangChain."""
from __future__ import annotations

from typing import Any, List, Optional

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from wellmarked import WellMarked


class WellMarkedRetriever(BaseRetriever):
    """Retrieve web documents for a query via WellMarked search.

    Each retrieval searches the web, extracts the top results to clean Markdown,
    and returns them as LangChain ``Document`` objects — search and extraction
    in one round trip, no crawling or URL wrangling. This is the natural
    LangChain surface for WellMarked: drop it into any RAG chain where the
    context should come from the live web.

    Search requires a Pro plan or above (it is a paid feature); Free keys get
    ``plan_not_supported``.

    Setup:
        Install ``langchain-wellmarked`` and set ``WELLMARKED_API_KEY`` (or pass
        ``api_key=``). Get a key at https://wellmarked.io.

        .. code-block:: bash

            pip install langchain-wellmarked

    Example:
        .. code-block:: python

            from langchain_wellmarked import WellMarkedRetriever

            retriever = WellMarkedRetriever(num_results=5)
            docs = retriever.invoke("best open-source vector databases")
            docs[0].page_content   # clean Markdown of a result page
            docs[0].metadata       # {"source": ..., "title": ..., "snippet": ...}

    Only successfully extracted results are returned; a result whose page timed
    out or was blocked is skipped (its snippet stays in the API response but
    there's no content to embed).
    """

    api_key: Optional[str] = None
    """WellMarked API key (``wm_...``). Falls back to ``WELLMARKED_API_KEY``."""
    num_results: int = 5
    """How many results to fetch + extract. Clamped to 1..10 server-side."""
    render_js: bool = False
    """Render JS-heavy result pages with a headless browser (Pro plan and above)."""

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun,
    ) -> List[Document]:
        with WellMarked(api_key=self.api_key) as wm:
            results = wm.search(
                query, num_results=self.num_results, render_js=self.render_js,
            ).results

        docs: List[Document] = []
        for r in results:
            if not r.ok or not r.markdown:
                continue
            metadata: dict[str, Any] = {"source": r.url}
            if r.title:
                metadata["title"] = r.title
            if r.snippet:
                metadata["snippet"] = r.snippet
            docs.append(Document(page_content=r.markdown, metadata=metadata))
        return docs
