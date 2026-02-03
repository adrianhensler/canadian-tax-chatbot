{Edit Feb 2nd 2026 : Use this functional resource instead of my half-done AI slop:  https://taxgpt.ca/ }

# Canadian Tax Chatbot

A RAG-powered chatbot that answers Canadian income tax questions with citations to authoritative sources.

---

## Status

**Phase 1 Complete:** Corpus Ingestion ✓
**Phase 2 Complete:** LLM Integration ✓
**Phase 3 Complete:** CLI Interface ✓
**Phase 4:** Web UI & Advanced Features (Not Started)

### What's Working

- ✅ Income Tax Act XML parsing (774 sections)
- ✅ Section-aware chunking with metadata preservation (3,878 chunks)
- ✅ Local embeddings (MiniLM-L6-v2) and ChromaDB vector store
- ✅ Retrieval interface for finding relevant ITA sections
- ✅ LLM integration with OpenAI GPT-5.2
- ✅ Answer generation with automatic citation extraction
- ✅ Citation validation against retrieved sources
- ✅ Refusal detection for complex tax situations
- ✅ **CLI interface** with single-question and interactive modes
- ✅ Test suite: 73/74 tests passing (1 skipped)

### What's NOT Working

- ❌ No CRA Folios or guidance documents (ITA only)
- ❌ No web UI (CLI only)
- ❌ No evaluation against full dataset (only 15 questions currently)

**Note:** The chatbot is fully functional via CLI. Run `python scripts/cli.py --help` for usage.

**Future review:** CRA Income Tax Folios ingestion is deferred. These documents are
published as HTML on canada.ca with no structured API, so ingestion requires a
brittle scraper, ongoing maintenance as page layouts change, and careful
excerpt-only storage with attribution to satisfy Crown copyright guidelines.
We'll revisit this once we have a clear update/monitoring strategy and defined
scope (curated folios vs. full catalog).

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

### Phase 2: LLM Integration (✓ Complete)
- ✅ LLM interface with OpenAI provider (GPT-5.2)
- ✅ Prompt engineering for tax Q&A with citation requirements
- ✅ Citation extraction and validation
- ✅ Answer generation with retrieved context
- ✅ Refusal detection for professional advice cases
- ✅ Chatbot orchestration (retrieve → generate → validate)

### Phase 3: CLI Interface (✓ Complete)
- ✅ CLI with single-question and interactive modes
- ✅ JSON output for scripting
- ✅ Verbose mode for debugging
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

### Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -e .

# Run ingestion (takes ~15 minutes on 2 cores)
python scripts/ingest_corpus.py --download

# Run tests
pytest tests/ -v
```

### Using the CLI

```bash
# Set your OpenAI API key
export OPENAI_API_KEY=sk-...

# Ask a single question
python scripts/cli.py "What is the basic personal amount?"

# Interactive mode - continuous conversation
python scripts/cli.py --interactive

# JSON output for scripting
python scripts/cli.py "What is RRSP contribution limit?" --json

# Verbose mode - show retrieved chunks
python scripts/cli.py "What is TFSA?" -v
```

### Using the Python API

```python
from src.chat.chatbot import Chatbot
from src.retrieval.retriever import Retriever
from src.chat.providers.openai import OpenAIProvider
import os

# Initialize components
retriever = Retriever()
llm = OpenAIProvider(api_key=os.environ['OPENAI_API_KEY'])
chatbot = Chatbot(retriever, llm)

# Ask a question
response = chatbot.ask("What is the basic personal amount?")

print(response.answer)
print("\nCitations:")
for citation in response.citations:
    print(f"  - {citation.reference}: {citation.text[:50]}...")
```

### Evaluation

```bash
# Evaluate against dataset (requires OpenAI API key)
OPENAI_API_KEY=sk-... python scripts/evaluate_chatbot.py
```

**Note:** Phase 3 (user interface) is not yet implemented. The chatbot currently works via Python API only.

---

## Contributing

Contributions welcome! Phases 1 & 2 are complete. Phase 3+ need work:
- Phase 3: User interface (CLI or web)
- Phase 4: CRA Folios scraping, hybrid search, calculator module

See the [PRD](docs/PRD.md) for project scope and [Architecture](docs/architecture.md) for technical approach.
