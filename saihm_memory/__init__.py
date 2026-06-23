"""SAIHM memory for Python — owned, portable, provably-erasable agent memory.

The core :class:`SaihmMemoryClient` needs only the ``mcp`` package. The framework
adapters are imported lazily, so you install only what you use:

    from saihm_memory import SaihmMemoryClient        # core (mcp only)
    from saihm_memory import SaihmChatMessageHistory   # LangChain  (needs langchain-core)
    from saihm_memory import SaihmMemory               # LlamaIndex (needs llama-index-core)
"""
from .client import Memory, SaihmMemoryClient, SaihmTimeout

__all__ = ["SaihmMemoryClient", "Memory", "SaihmTimeout", "SaihmChatMessageHistory", "SaihmMemory"]


def __getattr__(name):  # PEP 562 — lazy adapter imports
    if name == "SaihmChatMessageHistory":
        from .langchain_memory import SaihmChatMessageHistory

        return SaihmChatMessageHistory
    if name == "SaihmMemory":
        from .llamaindex_memory import SaihmMemory

        return SaihmMemory
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
