# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Status

**Phases 1-3 Complete:** Core RAG pipeline is functional with CLI interface.

- ✅ **Phase 1 (Document Ingestion):** XML parsing, chunking, embeddings, vector store
- ✅ **Phase 2 (LLM Integration):** Answer generation, citation extraction/validation
- ✅ **Phase 3 (CLI Interface):** Single-question and interactive modes
- ⏳ **Phase 4 (Advanced Features):** Web UI, CRA Folios, hybrid search, tax calculator

See README.md for detailed implementation status and usage instructions.

---

## Quick Start (For Testing)

```bash
# Install dependencies
pip install -e .

# Run ingestion (one-time, ~15 minutes)
python scripts/ingest_corpus.py --download

# Set API key
export OPENAI_API_KEY=sk-...

# Ask a question
python scripts/cli.py "What is the basic personal amount?"

# Interactive mode
python scripts/cli.py --interactive

# Run tests
pytest tests/ -v
```

See README.md for detailed usage instructions.

---

## Architecture Overview

RAG-powered Canadian tax law chatbot with mandatory citations. Three-layer architecture:

1. **Document Ingestion Layer**
   - Fetches Income Tax Act XML from [github.com/justicecanada/laws-lois-xml](https://github.com/justicecanada/laws-lois-xml)
   - Section-aware chunking respects ITA structure (e.g., keeps section 118(1)(a)(i) together)
   - Metadata preservation: section numbers, headings, dates, cross-references
   - See `docs/ingestion-spec.md` for XML parsing and chunking algorithms

2. **Retrieval Layer**
   - Hybrid search: Vector similarity (Mistral Embed / BGE-large) + BM25 keyword matching
   - Cross-reference handling for ITA structure ("as defined in subsection 248(1)")
   - Must retrieve correct sections with >85% recall (tested via eval set)

3. **Generation Layer**
   - LLM generates answers ONLY from retrieved context
   - Every answer must include ITA/Regulation citations with links
   - Deterministic `TaxCalculator` module for math (LLM never does final calculations)
   - Refusal behavior: Say "I don't know" rather than hallucinate

---

## Two Deployment Modes

**Local Mode (Docker + Ollama):** ⏳ *Planned for Phase 4*
- Qwen 2.5 72B / Llama 3.3 70B / DeepSeek-R1-Distill-32B
- All processing on-device (privacy-first)
- Labeled "experimental" due to model quality vs hosted
- Embeddings run locally (all-MiniLM-L6-v2) today

**Hosted Mode (Web Service):** ✅ *Current Implementation*
- OpenAI GPT-5.2 for generation
- Local embeddings (all-MiniLM-L6-v2) or OpenAI embeddings (optional)
- Vector store persisted locally (ChromaDB)
- PIPEDA-compliant data handling (no PII storage, redaction layer - see docs/architecture.md)

---

## Test-Driven Development (Required)

### ✅ Already Tested (Phases 1-3)
- **Document Chunking:** 90%+ coverage - Section structure preserved, metadata maintained
- **Citation Extraction:** 100% coverage - Citations extracted and validated
- **Retrieval Quality:** Tested - Retrieves relevant ITA sections with good recall
- **LLM Integration:** End-to-end tests for generation, validation, refusal detection

Current test suite: **73/74 tests passing** (1 skipped)

### ⏳ Write Tests BEFORE Implementing (Phase 4)

1. **Tax Calculator** (100% coverage required) - *NOT YET IMPLEMENTED*
   - Test against CRA examples and 2024 tax brackets
   - Example: `test_basic_personal_amount_2024()` before `calculate_bpa()`

2. **Hybrid Search (BM25 + Vector)** - *NOT YET IMPLEMENTED*
   - Test: BM25 retrieves keyword-heavy queries better than vector-only
   - Test: Hybrid fusion ranks results better than either alone

3. **CRA Folios Scraping** - *NOT YET IMPLEMENTED*
   - Test: Extracts sections with proper citations
   - Test: Respects Crown copyright (excerpts only, with attribution)

**TDD Workflow:**
```bash
# 1. Write failing test
pytest tests/test_calculator.py::test_calculate_federal_tax_2024

# 2. Implement minimal code to pass
# 3. Refactor, repeat
```

---

## Module Organization

Current structure:

```
src/
├── loaders/          # ✅ XMLParser, Chunker - parse Justice Laws XML
├── retrieval/        # ✅ Embedder, VectorStore, Retriever
├── chat/             # ✅ Chatbot, LLMInterface, CitationValidator, Prompts
│   └── providers/    # ✅ OpenAI provider (extensible for Claude, etc.)
├── calculator/       # ⏳ TaxCalculator - deterministic tax math (NOT IMPLEMENTED)
└── ui/               # ⏳ Web UI (NOT IMPLEMENTED - CLI exists as script)

scripts/
├── cli.py            # ✅ CLI interface (single-question + interactive modes)
├── ingest_corpus.py  # ✅ Full ingestion pipeline
└── evaluate_chatbot.py  # ✅ Evaluation against test dataset

tests/
├── fixtures/         # ✅ Sample ITA XML for testing
├── test_xml_parser.py   # ✅ XML parsing tests
├── test_chunker.py      # ✅ Chunking tests
├── test_embedder.py     # ✅ Embedding tests
├── test_vector_store.py # ✅ Vector store tests
├── test_retriever.py    # ✅ Retrieval tests
├── test_llm_interface.py # ✅ LLM integration tests
├── test_citations.py    # ✅ Citation extraction/validation tests
└── test_chatbot.py      # ✅ End-to-end chatbot tests
```

**Test Coverage:** 73/74 tests passing (1 skipped), comprehensive coverage of Phases 1-3.

---

## Legal Requirements

1. **Federal Law Reproduction:**
   - ITA/Regulations freely reproducible under [Reproduction of Federal Law Order](https://laws-lois.justice.gc.ca/eng/regulations/SI-97-5/page-1.html)
   - Must include "not an official version" disclaimer

2. **CRA Content (Crown Copyright):**
   - Store only excerpts with citations, NOT full documents
   - Commercial use requires permission
   - Always cite: "Source: CRA Income Tax Folio S1-F4-C2"

3. **PIPEDA Privacy:**
   - Never ask for SINs
   - Redact PII before sending to hosted LLM APIs
   - Local mode: No data transmission
   - Hosted mode: No persistent storage of user queries
   - See `docs/architecture.md` → "PII Handling for Hosted Mode" for detailed spec

4. **Disclaimers Required:**
   - "Not legal or tax advice"
   - "Consult a qualified professional for complex situations"

---

## Key Design Principles

1. **Trust First:** Citations and transparency before convenience
2. **Never Hallucinate:** Refuse to answer rather than invent tax rules
3. **Privacy by Design:** Local mode as first-class feature
4. **RAG for Knowledge, Fine-tuning for Behavior:**
   - Retrieval supplies "what is true" (tax law changes frequently)
   - Fine-tuning supplies "how to behave" (question-asking style, JSON output format)
5. **Deterministic Calculations:** Code handles math, not LLM

---

## Success Metrics (v0.1)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Citation accuracy | >90% | Does cited source support answer? |
| Hallucination rate | <5% | Did answer invent rules not in corpus? |
| Retrieval recall | >85% | Did retrieval find relevant section? |

**Evaluation Dataset:** `eval/canadian-tax-qa-dataset/`
- 15 curated questions (7 basic, 5 tricky, 3 should-refuse)
- CC0 public domain - contributions welcome
- See `eval/README.md` for format and contribution guidelines

---

## Corpus Sources

1. **Income Tax Act XML:**
   - Clone: `git clone https://github.com/justicecanada/laws-lois-xml.git`
   - Or download: [Open Canada Portal](https://open.canada.ca/data/en/dataset/eb0dee21-9123-4d0d-b11d-0763fa1fb403)
   - Or fetch directly: `https://laws-lois.justice.gc.ca/eng/XML/I-3.3.xml`

2. **Update Detection:**
   - Check `https://laws-lois.justice.gc.ca/eng/XML/Legis.xml` for consolidation dates
   - Re-index only changed documents (incremental updates)
   - Schedule: Every ~2 weeks (cron/Celery)
   - **Versioning:** Each corpus is versioned (`corpus-YYYY-MM-DD`) with manifest and checksums
   - See `docs/ingestion-spec.md` → "Corpus Versioning" for rollback procedures

3. **CRA Folios (scrape, no API exists):**
   - Start with curated list of 20-30 priority folios
   - Extract sections as excerpts with citations
   - See `docs/ingestion-spec.md` for scraping implementation

---

## Documentation

| Document | Purpose |
|----------|---------|
| `docs/PRD.md` | Product requirements, goals, success metrics |
| `docs/architecture.md` | Two deployment modes, component specs, TDD methodology |
| `docs/ingestion-spec.md` | Justice Laws XML parsing, CRA scraping, chunking algorithms |
| `docs/research-notes.md` | Model recommendations, RAG techniques, tech stack |
| `docs/private/` | Internal planning docs (not public) |

---

## When Writing Code

### For Existing Code (Phases 1-3)
1. **Read existing code first** - Understand patterns before modifying (e.g., `src/loaders/`, `src/retrieval/`, `src/chat/`)
2. **Run tests** - Ensure `pytest tests/ -v` passes before changes
3. **Follow established patterns** - Match existing style (dataclasses, type hints, error handling)
4. **Update tests** - Modify tests when changing behavior, add tests for new features
5. **Check dependencies** - Use what's in `pyproject.toml`, avoid adding unnecessary deps

### For New Code (Phase 4+)
1. **Read `docs/architecture.md` first** - Contains TDD requirements and module structure
2. **Read `docs/ingestion-spec.md`** - Before adding CRA scraping or new document loaders
3. **Test first** - Write tests BEFORE implementing (especially calculator, hybrid search)
4. **Use type annotations** - Python 3.10+, full type hints (mypy enforced)
5. **Follow PEP 8** - Use `black` for formatting (100 char line length), `ruff` for linting
6. **Write docstrings** - Module, class, and function level
7. **Never store PII** - Redact before API calls, no logs with sensitive data

---

## Tools and Dependencies

### Implemented (Phases 1-3)
- **Backend:** Python 3.10+ with type annotations
- **LLM (Hosted):** OpenAI GPT-5.2 via OpenAI API
- **Embeddings (Local):** `all-MiniLM-L6-v2` (sentence-transformers) - default
- **Embeddings (API):** `text-embedding-3-small/large` (OpenAI) - optional
- **Vector Store:** ChromaDB with persistence
- **Testing:** pytest with coverage (73/74 passing)
- **Linting:** ruff
- **Formatting:** black
- **Type Checking:** mypy
- **UI:** CLI (single-question + interactive modes)

### Planned (Phase 4+)
- **LLM (Local):** Ollama with Qwen 2.5 72B / Llama 3.3 70B / DeepSeek-R1-Distill-32B
- **Search:** Hybrid (BM25 + vector) - currently vector-only
- **Tax Calculator:** Deterministic module for calculations
- **Web UI:** Streamlit (MVP) or Next.js / FastAPI + Jinja (production)
- **Backend API:** FastAPI for web UI

---

## Decisions Made & Open Questions

### ✅ Decided (Phases 1-3)
- **Embedding model (local):** `all-MiniLM-L6-v2` - Fast, good quality for local use
- **Embedding model (API):** OpenAI `text-embedding-3-small/large` - Optional upgrade
- **Vector store:** ChromaDB - Good balance of features and simplicity
- **Hosted LLM:** OpenAI GPT-5.2 - High quality, reliable API
- **API provider:** Direct (OpenAI) - Simple, well-documented

### ⏳ Still Open (Phase 4+)
- **Local LLM:** Qwen 2.5 72B vs Llama 3.3 70B vs DeepSeek-R1-Distill-32B - Depends on hardware availability and quality testing
- **Hybrid search:** BM25 implementation strategy - Needs benchmarking vs vector-only
- **Web UI framework:** Streamlit (fast) vs Next.js (production-grade) vs FastAPI + Jinja - Depends on deployment requirements
- **Embedding upgrade:** Should we switch to Mistral Embed or BGE-large for better accuracy? - Needs evaluation against current dataset

See `docs/PRD.md` for evaluation criteria and decision framework.
