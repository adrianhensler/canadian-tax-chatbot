# Canadian Tax Chatbot

A RAG-powered chatbot that answers Canadian income tax questions with citations to authoritative sources.

---

## Status

**Phase 1 Complete:** Corpus Ingestion ✓
**Phase 2:** LLM Integration & UI (Not Started)

### What's Working

- ✅ Income Tax Act XML parsing (774 sections)
- ✅ Section-aware chunking with metadata preservation (3,878 chunks)
- ✅ Local embeddings (MiniLM-L6-v2) and ChromaDB vector store
- ✅ Retrieval interface for finding relevant ITA sections
- ✅ Test suite: 31/32 tests passing

### What's NOT Working

- ❌ No chatbot interface (no LLM integration yet)
- ❌ No answer generation from retrieved chunks
- ❌ No CRA Folios or guidance documents (ITA only)
- ❌ No UI (CLI or web)
- ❌ Cannot actually answer tax questions yet

**This is infrastructure only.** The retrieval pipeline works, but there's no user-facing chatbot.

---

## What This Does

Ask a question about Canadian personal income tax. The chatbot retrieves relevant passages from the Income Tax Act, Regulations, and CRA guidance, then generates an answer grounded in those sources. Every answer includes citations so you can verify the information.

**This tool does not:**
- File tax returns
- Provide professional tax advice
- Replace consultation with a qualified accountant

---

## Implementation Progress

### Phase 1: Corpus Ingestion (✓ Complete)
- ✅ XML parser for Justice Laws format
- ✅ Section-aware chunking respecting ITA structure
- ✅ Embedding generation (local + API support)
- ✅ ChromaDB vector store with persistence
- ✅ Full ITA ingestion pipeline

### Phase 2: LLM Integration (Not Started)
- ⏳ LLM interface (Claude/GPT/local models)
- ⏳ Prompt engineering for tax Q&A
- ⏳ Citation extraction and formatting
- ⏳ Answer generation with retrieved context

### Phase 3: User Interface (Not Started)
- ⏳ CLI interface
- ⏳ Web UI (Streamlit or Next.js)
- ⏳ Docker deployment

### Phase 4: Advanced Features (Not Started)
- ⏳ CRA Folios scraping and ingestion
- ⏳ Hybrid search (BM25 + vector)
- ⏳ Deterministic tax calculator
- ⏳ Interview mode (guided questions)

---

## Architecture

The system uses Retrieval-Augmented Generation (RAG):

```
User Question
     │
     ▼
┌─────────────┐
│  Retriever  │ ← Hybrid search (vector + BM25)
└─────────────┘
     │
     ▼
┌─────────────┐
│   Corpus    │ ← Income Tax Act, Regulations, CRA Folios
└─────────────┘
     │
     ▼
┌─────────────┐
│     LLM     │ ← Generates answer from retrieved context
└─────────────┘
     │
     ▼
Answer + Citations
```

See [docs/architecture.md](docs/architecture.md) for full technical details.

---

## Documentation

| Document | Description |
|----------|-------------|
| [PRD](docs/PRD.md) | Product requirements, goals, constraints |
| [Architecture](docs/architecture.md) | Technical implementation plan (includes TDD methodology) |
| [Ingestion Specification](docs/ingestion-spec.md) | How to ingest Justice Laws XML and CRA content |
| [Research Notes](docs/research-notes.md) | Background research and strategic analysis |
| [Evaluation Dataset](eval/README.md) | Q&A pairs for testing (CC0 public domain - contributions welcome!) |

---

## Legal Disclaimer

This software provides **informational content only** and does not constitute tax, legal, or financial advice. The information retrieved and presented is not an official version of Canadian law. Always consult a qualified professional for advice specific to your situation.

Tax law reproduced under the [Reproduction of Federal Law Order](https://laws-lois.justice.gc.ca/eng/regulations/SI-97-5/page-1.html). CRA content used as excerpts with citations under Crown copyright guidelines.

---

## License

[MIT](LICENSE)

---

## Development

To run the existing ingestion pipeline:

```bash
# Setup
python3 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -e .

# Run ingestion (takes ~15 minutes on 2 cores)
python scripts/ingest_corpus.py --download

# Run tests
pytest tests/ -v
```

**Note:** This only sets up the retrieval infrastructure. There's no chatbot to interact with yet.

---

## Contributing

Contributions welcome! Phase 1 is complete, but Phase 2+ need work. See the [PRD](docs/PRD.md) for project scope and [Architecture](docs/architecture.md) for technical approach.
