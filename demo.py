#!/usr/bin/env python3
"""SAIHM memory for Python — one owned store, opened from the core client, LangChain, and
LlamaIndex, with erasure you can prove.

    npm install                 # the Node sidecar that does the client-side sealing
    python3 -m venv .venv && . .venv/bin/activate
    pip install -r requirements.txt
    python demo.py              # runs offline against a local blind sandbox; no account

Go live (paid membership, no free tier) by pointing it at the hosted, blind endpoint:
    export SAIHM_ENDPOINT_URL=https://saihm.coti.global/mcp
    export SAIHM_AUTH_HEADER="Bearer <your-onboard-JWT>"
    export SAIHM_MASTER_SECRET_HEX=<at least 64 hex chars, generated and held only by you>
Your master secret never leaves your machine; the endpoint only ever sees ciphertext.
"""
import json
import os

from llama_index.core.llms import ChatMessage, MessageRole

from saihm_memory import SaihmChatMessageHistory, SaihmMemory, SaihmMemoryClient


def rule():
    print("-" * 72)


def render(text):
    """Show a framework message's JSON envelope readably; pass plain facts through as-is."""
    try:
        o = json.loads(text)
        if isinstance(o, dict) and o.get("_saihm"):
            return f'[{o["role"]}] {o["content"]}'
    except (json.JSONDecodeError, TypeError):
        pass
    return text


def main():
    live = bool(os.environ.get("SAIHM_ENDPOINT_URL"))
    client = SaihmMemoryClient()  # one store; reads SAIHM_* env for live mode automatically
    try:
        rule(); print("SAIHM memory for Python"); rule()
        print("endpoint :", "hosted SAIHM (LIVE)" if live else "local blind sandbox")
        print("status   :", client.status())
        print("note     : Python holds no keys — the Node sidecar seals every cell client-side.\n")

        # 1) Seal three personal facts via the core client — this is your portable store.
        facts = [
            "My name is Dana Okafor.",
            "I am allergic to penicillin.",
            "I am building a Rust ray tracer called Lumen.",
        ]
        ids = {f: client.remember(f) for f in facts}
        print(f"Sealed {len(facts)} facts. The store now holds:")
        for m in client.recall():
            print("   -", render(m.text))
        print()

        # 2) The SAME store, opened through LangChain — it sees your memory, and adds to it.
        rule(); print("(1) LangChain — BaseChatMessageHistory on the same store:"); rule()
        hist = SaihmChatMessageHistory(client=client)
        print("LangChain opens your store and reads", len(hist.messages), "messages.")
        hist.add_user_message("Remind me what I'm allergic to.")
        print("After one turn, it holds", len(hist.messages), "messages.\n")

        # 3) The SAME store, opened through LlamaIndex.
        rule(); print("(2) LlamaIndex — BaseMemory on the same store:"); rule()
        mem = SaihmMemory.from_defaults(client=client)
        print("LlamaIndex opens the same store and reads", len(mem.get_all()), "messages.")
        mem.put(ChatMessage(role=MessageRole.USER, content="Note: prefers metric units."))
        print("After one put, it holds", len(mem.get_all()), "messages.\n")

        # 4) Provable erasure — forget the medical fact; it's gone for every consumer at once.
        rule(); print("(3) Provable erasure — forget the allergy, across all of them:"); rule()
        ok = client.forget(ids["I am allergic to penicillin."])
        print(f'forget("I am allergic to penicillin.")  ->  crypto-shredded: {ok}')
        remaining = client.recall()
        print("the store now holds:")
        for m in remaining:
            print("   -", render(m.text))
        assert not any("penicillin" in m.text for m in remaining), "erasure failed"
        print()

        rule()
        print("One store. Core, LangChain, and LlamaIndex — and erasure you can prove.")
        print("Go live (paid): https://saihm.coti.global/join")
        rule()
    finally:
        client.close()


if __name__ == "__main__":
    main()
