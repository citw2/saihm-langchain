# saihm-langchain

**SAIHM memory for Python — LangChain & LlamaIndex adapters. One store you own. Erasure you can prove.**

> ⭐ **Star this repo and share it** — help every agent get portable, provable memory. [Share on X](https://x.com/intent/tweet?text=Python%20LangChain%20%26%20LlamaIndex%20with%20a%20memory%20you%20own%20-%20portable%2C%20encrypted%2C%20provably%20erasable%20-%20via%20SAIHM.&url=https%3A%2F%2Fgithub.com%2Fcitw2%2Fsaihm-langchain).

A runnable demo of [SAIHM](https://saihm.coti.global) for Python. It gives **LangChain** and **LlamaIndex** a single, client-side-encrypted memory that you own: portable across models *and* frameworks, non-custodial, and **provably erasable** (GDPR Art. 17). The same store opens from the core client, from LangChain, and from LlamaIndex — and one `forget` removes a memory from all of them at once.

**No Python cryptography.** All sealing happens in a small bundled **Node sidecar** (`server.mjs`, built on the same sealing client [`@saihm/mcp-server-pro`](https://www.npmjs.com/package/@saihm/mcp-server-pro) as [demo-claude-code](https://github.com/citw2/demo-claude-code)). Python drives it over [MCP](https://modelcontextprotocol.io) stdio and never holds a key — one audited crypto implementation, not a second one ported to Python.

## Run it

```
git clone https://github.com/citw2/saihm-langchain
cd saihm-langchain

npm install                                  # the Node sidecar (does the sealing)

python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

python demo.py                               # offline blind sandbox; no account
```

You'll see three facts sealed into one store, that same store opened from LangChain and from LlamaIndex, and then a `forget` that crypto-shreds one fact for every consumer at once.

## Use it in your code

The core client needs only the `mcp` package; the framework adapters are imported lazily, so you install only what you use. Run these from inside the cloned repo (the package locates its bundled Node sidecar relative to itself), or add the repo to your `PYTHONPATH`. The client is synchronous and blocking — inside an async app, call it from a thread, e.g. `await loop.run_in_executor(None, client.remember, text)`.

**Core**
```python
from saihm_memory import SaihmMemoryClient

mem = SaihmMemoryClient()                     # local blind sandbox by default
cell = mem.remember("My name is Dana Okafor.")
mem.recall()                                  # -> [Memory(cell_id=..., text="My name is Dana Okafor.")]
mem.forget(cell)                              # crypto-shred (irreversible)
```

**LangChain** — a `BaseChatMessageHistory`, drop-in for `RunnableWithMessageHistory`:
```python
from saihm_memory import SaihmChatMessageHistory

history = SaihmChatMessageHistory()
history.add_user_message("My name is Dana.")
history.messages                              # -> [HumanMessage("My name is Dana.")]
history.clear()                               # crypto-shreds the messages this history added
```

**LlamaIndex** — a `BaseMemory`, drop-in for chat engines / agents (`memory=...`):
```python
from saihm_memory import SaihmMemory
from llama_index.core.llms import ChatMessage, MessageRole

memory = SaihmMemory.from_defaults()
memory.put(ChatMessage(role=MessageRole.USER, content="My name is Dana."))
memory.get_all()                             # -> [ChatMessage(USER, "My name is Dana.")]
memory.reset()                               # crypto-shreds the messages this memory added
```

The adapters **read the whole store** (open your memory from any framework), but `clear()` / `reset()` only crypto-shred the messages that instance added — so a `reset()` never wipes the rest of your memory by surprise. For targeted erasure, call `forget(cell_id)` with the id returned by `remember` (or any id from `recall()`, which returns full, forgettable ids).

Framework messages are stored as a small JSON envelope (`{"_saihm":1,"role":…,"content":…}`); facts you store directly are kept as-is. When an adapter reads the store it only applies a message's **role** to cells it wrote — every other cell (including arbitrary facts) is read as opaque user content, so memorized untrusted text can't forge a privileged `system`/`assistant` turn.

## Why this matters

A per-vendor or per-framework "memory" locks your context in one place. SAIHM gives you memory that is:

1. **Yours / portable.** One live store grounds every model (Claude, GPT, DeepSeek, Qwen, Kimi, GLM, your own agent) **and** every framework here — no per-tool export, no lossy import.
2. **Non-custodial.** Every cell is sealed client-side by the Node sidecar; the endpoint only ever holds ciphertext and never sees your keys. Python does no crypto.
3. **Provably erasable.** `forget` crypto-shreds the cell (its wrapped key is destroyed). It returns nothing afterward and every consumer loses access at once — not a soft "hidden" flag. This is what GDPR Art. 17 actually asks for.

## Go live against the real SAIHM service

The local sandbox is a throwaway stand-in so you can try the protocol offline — it is **not** the SAIHM service and stores nothing beyond the current process. To run against the real, hosted, blind endpoint:

1. **Join SAIHM** at **[saihm.coti.global/join](https://saihm.coti.global/join)** and onboard to obtain your JWT. (Going live requires a paid membership — there is no free tier.)
2. Set the environment before running, and the same code goes live:

   ```
   export SAIHM_ENDPOINT_URL=https://saihm.coti.global/mcp
   export SAIHM_AUTH_HEADER="Bearer <your-onboard-JWT>"
   export SAIHM_MASTER_SECRET_HEX=<at least 64 hex chars, generated and held only by you>
   python demo.py
   ```

Your master secret never leaves your machine; the endpoint only ever receives ciphertext.

## How it works

- The bundled **Node sidecar** (`server.mjs`) exposes four MCP tools — `saihm_remember`, `saihm_recall`, `saihm_forget`, `saihm_status` — and seals every cell with [`@saihm/client-pro`](https://www.npmjs.com/package/@saihm/client-pro): an **ML-DSA-65** identity signs it, a per-cell **AES-256-GCM** key encrypts it, and that key is wrapped under a key-encryption key derived from *your* master secret. Sharing uses **ML-KEM-768**.
- [`SaihmMemoryClient`](./saihm_memory/client.py) spawns that sidecar once and keeps a single long-lived MCP session, exposing blocking `remember` / `recall` / `forget` / `status`. The LangChain and LlamaIndex adapters are thin wrappers over it.
- Only opaque ciphertext leaves the sidecar. [`sandbox.mjs`](./sandbox.mjs) is a complete, readable *blind operator* for offline use: it stores and returns ciphertext and **never holds a key**.

## Built on / see also

- **[demo-cross-model-memory](https://github.com/citw2/demo-cross-model-memory)** — one memory across Claude, DeepSeek, Qwen, Kimi, GLM, and GPT.
- **[demo-claude-code](https://github.com/citw2/demo-claude-code)** — the same sidecar as an MCP server for Claude Code, Cursor, and any MCP host.
- **[All demos + landing page](https://citw2.github.io/saihm-demos/)**.
- **[`@saihm/mcp-server-pro`](https://github.com/SAIHM-Admin/saihm-mcp-server-pro)** ([npm](https://www.npmjs.com/package/@saihm/mcp-server-pro)) · **[`@saihm/client-pro`](https://github.com/SAIHM-Admin/saihm-client-pro)** ([npm](https://www.npmjs.com/package/@saihm/client-pro)).
- **Learn more:** [AI memory needs a standard](https://saihm.coti.global/blog/2026-05-18-ai-memory-needs-a-standard) · [What makes SAIHM different](https://saihm.coti.global/blog/2026-05-31-what-makes-saihm-different).
- **Join the protocol:** [saihm.coti.global/join](https://saihm.coti.global/join).

## License

Apache-2.0 © SAIHM
