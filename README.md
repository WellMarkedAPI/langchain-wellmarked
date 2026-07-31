# langchain-wellmarked

The official [LangChain](https://www.langchain.com/) integration for **[WellMarked](https://wellmarked.io)** — load any URL as clean Markdown `Document`s, or retrieve them straight from a web search.

```bash
pip install langchain-wellmarked
```

## Quick start

Set your API key (get one at [wellmarked.io](https://wellmarked.io)):

```bash
export WELLMARKED_API_KEY="wm_..."
```

Load a single page:

```python
from langchain_wellmarked import WellMarkedLoader

loader = WellMarkedLoader("https://example.com/article")
docs = loader.load()

docs[0].page_content   # clean Markdown
docs[0].metadata       # {"source": ..., "title": ..., "author": ..., "retrieved_at": ...}
```

Or crawl a whole site BFS-style — one `Document` per successfully extracted page (Pro plan and above):

```python
loader = WellMarkedLoader("https://docs.example.com", mode="crawl", depth=2)
docs = loader.load()

docs[0].metadata["depth"]   # how far from the root URL this page sits
```

`lazy_load()` works too, and the loader passes `render_js=True` through to the API for JS-heavy pages.

## Options

| Parameter     | Default     | Description                                                        |
|---------------|-------------|--------------------------------------------------------------------|
| `url`         | (required)  | Page to extract, or root URL to crawl from                          |
| `api_key`     | env var     | WellMarked API key; falls back to `WELLMARKED_API_KEY`              |
| `mode`        | `"extract"` | `"extract"` (single page) or `"crawl"` (same-site BFS)              |
| `depth`       | `1`         | Crawl depth (`mode="crawl"` only)                                   |
| `render_js`   | `False`     | Render JS-heavy pages with a headless browser (Pro and above)       |
| `job_timeout` | `300.0`     | Seconds to wait for a crawl job; `None` waits forever               |

In `crawl` mode, pages that fail to extract (timeouts, robots-disallowed, no content) are skipped; only successful pages become `Document`s.

## Retriever

`WellMarkedRetriever` is the natural surface for RAG chains where the context should come from the live web: each retrieval searches the web, extracts the top results to clean Markdown, and returns them as `Document`s — search and extraction in one round trip, no URLs to wrangle. Search requires a Pro plan or above.

```python
from langchain_wellmarked import WellMarkedRetriever

retriever = WellMarkedRetriever(num_results=5)
docs = retriever.invoke("best open-source vector databases")

docs[0].page_content   # clean Markdown of a result page
docs[0].metadata       # {"source": ..., "title": ..., "snippet": ...}
```

| Parameter     | Default   | Description                                                    |
|---------------|-----------|----------------------------------------------------------------|
| `api_key`     | env var   | WellMarked API key; falls back to `WELLMARKED_API_KEY`         |
| `num_results` | `5`       | How many results to fetch + extract (clamped to 1..10)        |
| `render_js`   | `False`   | Render JS-heavy result pages with a headless browser (Pro and above) |

Only successfully extracted results become `Document`s; a result whose page timed out or was blocked is skipped.

## Related

- [`wellmarked`](https://pypi.org/project/wellmarked/) — the underlying Python SDK (this package wraps it)
- [LangChain integration docs](https://wellmarked.io/docs/sdks/langchain) — this package, on the WellMarked docs site
- [WellMarked API docs](https://wellmarked.io/docs)
- [`llama-index-readers-wellmarked`](https://github.com/WellMarkedAPI/llama-index-readers-wellmarked) — the LlamaIndex equivalent
