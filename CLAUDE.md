# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Status

**Pre-implementation phase.** No code exists yet - only documentation and architecture specs. Implementation will follow these docs.

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

**Local Mode (Docker + Ollama):**
- Qwen 2.5 72B / Llama 3.3 70B / DeepSeek-R1-Distill-32B
- All processing on-device (privacy-first)
- Labeled "experimental" due to model quality vs hosted

**Hosted Mode (Web Service):**
- Claude Opus 4.5, GPT-5.2 Instant, or via OpenRouter
- Higher quality, centrally managed
- PIPEDA-compliant data handling (no PII storage, redaction layer)

---

## Test-Driven Development (Required)

Write tests BEFORE implementing these critical components:

1. **Tax Calculator** (100% coverage required)
   - Test against CRA examples and 2024 tax brackets
   - Example: `test_basic_personal_amount_2024()` before `calculate_bpa()`

2. **Document Chunking** (90%+ coverage)
   - Test: "Section 118(1)(a) should stay together"
   - Test: Metadata preserved (section numbers, references)

3. **Citation Extraction** (mandatory)
   - Test: Every answer includes ITA reference
   - Test: Links are valid and point to correct sections

4. **Retrieval Quality** (85%+ recall)
   - Test: "Query 'RRSP deduction' retrieves section 146"
   - Run against eval set before tuning

**TDD Workflow:**
```bash
# 1. Write failing test
pytest tests/test_calculator.py::test_calculate_federal_tax_2024

# 2. Implement minimal code to pass
# 3. Refactor, repeat
```

---

## Module Organization

Planned structure (when implementation begins):

```
src/
├── loaders/          # DocumentLoader class - parse Justice Laws XML
├── retrieval/        # Retriever, TaxKnowledgeBase (vector store wrapper)
├── chat/             # Chatbot class - LLM interface, prompt management
├── calculator/       # TaxCalculator - deterministic tax math (NO AI)
├── ui/               # Streamlit/FastAPI+Jinja/Next.js interface
└── tests/
    ├── fixtures/     # Sample ITA XML, CRA HTML for testing
    └── test_*.py     # Test modules (write these FIRST)
```

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

1. **Read `docs/architecture.md` first** - Contains TDD requirements and module structure
2. **Read `docs/ingestion-spec.md`** - Before implementing document loaders
3. **Use type annotations** - Python 3.10+, full type hints
4. **Follow PEP 8** - Use `black` for formatting, `ruff` for linting
5. **Write docstrings** - Module, class, and function level
6. **Test first** - Especially for calculator, chunking, citations, retrieval
7. **Never store PII** - Redact before API calls, no logs with sensitive data

---

## Tools and Dependencies (Planned)

- **Backend:** FastAPI (Python)
- **LLM (Hosted):** Claude Opus 4.5, GPT-5.2 Instant, or OpenRouter
- **LLM (Local):** Ollama with Qwen 2.5 72B / Llama 3.3 70B / DeepSeek-R1-Distill-32B
- **Embeddings:** Mistral Embed (top 2025 accuracy), text-embedding-3-large, or BGE-large
- **Vector Store:** ChromaDB, FAISS, or pgvector
- **Testing:** pytest
- **Linting:** ruff or pylint
- **Formatting:** black
- **Type Checking:** mypy
- **UI (MVP):** Streamlit (fast iteration)
- **UI (Future):** Next.js or FastAPI + Jinja

---

## Open Questions (Check `docs/PRD.md` for latest)

- Embedding model: Mistral Embed vs text-embedding-3-large vs BGE-large
- Vector store: ChromaDB vs FAISS vs pgvector
- Local model: Qwen 2.5 72B vs Llama 3.3 70B vs DeepSeek-R1-Distill-32B
- Hosted model: Claude Opus 4.5 vs GPT-5.2 Instant vs o3-mini
- API provider: Direct (Anthropic/OpenAI) vs OpenRouter

Decide during implementation based on benchmarks and hardware availability.
