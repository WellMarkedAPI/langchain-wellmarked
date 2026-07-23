"""Official LangChain integration for the WellMarked API.

    from langchain_wellmarked import WellMarkedLoader, WellMarkedRetriever

    # Load specific URLs (or crawl a site) as Documents:
    loader = WellMarkedLoader("https://example.com/article")
    docs = loader.load()

    # Or retrieve from the live web by query (search + extract):
    retriever = WellMarkedRetriever(num_results=5)
    docs = retriever.invoke("best open-source vector databases")

See https://wellmarked.io/docs for the full API reference.
"""
from langchain_wellmarked.document_loaders import WellMarkedLoader
from langchain_wellmarked.retrievers import WellMarkedRetriever

__all__ = ["WellMarkedLoader", "WellMarkedRetriever"]
