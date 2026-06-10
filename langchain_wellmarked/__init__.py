"""Official LangChain integration for the WellMarked API.

    from langchain_wellmarked import WellMarkedLoader

    loader = WellMarkedLoader("https://example.com/article")
    docs = loader.load()

See https://wellmarked.io/docs for the full API reference.
"""
from langchain_wellmarked.document_loaders import WellMarkedLoader

__all__ = ["WellMarkedLoader"]
