# Architecture Document: Canadian Tax Chatbot

**Last Updated:** January 2025

---

## Overview

This document describes the technical architecture for a Canadian tax Q&A assistant. The system uses retrieval-augmented generation (RAG) to answer questions by citing authoritative sources. It does not file tax returns or perform NETFILE/EFILE functions.

Two deployment modes are supported:
- **Plan #1 - Local:** Docker-based, runs on user's machine, uses open-source models via Ollama
- **Plan #2 - Hosted:** Web service using Claude Opus 4.5 or GPT-5.2, managed by project maintainer

Both modes share core components: document ingestion, vector search, language model interface, and answer formatting.

**Language scope (v0.1):** English-only UI and responses. The ingestion pipeline targets English consolidations and English CRA guidance, so citations are English-only and do not reflect the official French wording. Users who need French-language legal text must consult the bilingual sources directly.

---

## Table of Contents

1. [Legal and Ethical Considerations](#legal-and-ethical-considerations)
2. [Coding Guidelines](#coding-guidelines)
3. [Plan #1 - Local Docker-Based Tool](#plan-1---local-docker-based-tool)
4. [Plan #2 - Hosted Web Service](#plan-2---hosted-web-service)
5. [Comparison](#comparison)

---

## Legal and Ethical Considerations

### Reproducing Canadian Tax Law

**Federal statutes and regulations** are freely reproducible under the [Reproduction of Federal Law Order](https://laws-lois.justice.gc.ca/eng/regulations/SI-97-5/page-1.html). Requirements:
- Exercise due diligence to ensure accuracy
- Do not represent the reproduction as an official version

**CRA publications** (folios, guides, forms) are covered by Crown copyright:
- Personal/non-commercial reproduction allowed with citation
- Commercial reproduction requires written permission
- Approach: Store only excerpts with citations, not full documents

### Privacy (PIPEDA)

The [Personal Information Protection and Electronic Documents Act](https://www.priv.gc.ca/en/privacy-topics/privacy-laws-in-canada/the-personal-information-protection-and-electronic-documents-act-pipeda/) applies to private-sector organizations collecting personal information.

**Key principles:**
- **Consent:** Only collect data necessary for the service
- **Limiting collection:** Do not ask for SINs; store minimal information
- **Safeguards:** Implement security measures against unauthorized access
- **Openness:** Provide clear privacy policy

**Both versions must include:**
- Privacy notice explaining data handling
- Disclaimer: "Not legal or tax advice - consult a professional for complex situations"

### Intellectual Property

**Original (protectable):** Code, prompts, document processing logic, UI/UX, evaluation framework

**Not original:** Legal texts themselves (reproducible under federal law)

**Risk mitigation:** Cap verbatim quotation length; summarize rather than copy large sections

---

## Coding Guidelines

### Structure and Readability
- Clear variable names, PEP 8 formatting
- Short, focused functions with docstrings
- Modules organized by responsibility: `loaders/`, `retrieval/`, `chat/`, `ui/`
- Configuration separated from code

### Documentation and Types
- Module and function docstrings
- Type annotations for static analysis
- Helps both human developers and AI assistants understand intent

### Testing and Tooling
- Linting: `ruff` or `pylint`
- Formatting: `black`
- Type checking: `mypy`
- Testing: `pytest`
- Pre-commit hooks to enforce standards

### Test-Driven Development (TDD)

This project strongly benefits from TDD methodology, especially for:

**Critical components requiring TDD:**

1. **Tax Calculator Module**
   - Write tests first for known tax scenarios (2024 tax brackets, credits)
   - Test against CRA examples and publications
   - Ensure deterministic, reproducible calculations
   - Example: `test_basic_personal_amount_2024()` before implementing `calculate_bpa()`

2. **Document Chunking Logic**
   - Test section-aware splitting with sample ITA XML
   - Verify metadata preservation (section numbers, references)
   - Ensure cross-reference handling works
   - Example: Write test for "Section 118(1)(a) should stay together" before implementing chunker

3. **Citation Extraction**
   - Test that every answer includes source references
   - Verify citation format matches requirements
   - Ensure links are valid and point to correct sections
   - Example: Test "answer must include ITA reference" before building citation system

4. **Retrieval Quality**
   - Test with known question-answer pairs
   - Verify correct sections are retrieved for sample queries
   - Measure recall and precision on evaluation set
   - Example: "Query 'RRSP deduction' should retrieve section 146" before tuning retrieval

**TDD Workflow:**

```python
# 1. Write failing test first
def test_calculate_federal_tax_2024():
    """Test federal tax calculation for 2024 tax year"""
    income = 50000
    result = calculate_federal_tax(income, year=2024)

    # Expected: First $55,867 at 15%
    expected = 50000 * 0.15
    assert result['federal_tax'] == expected
    assert result['marginal_rate'] == 0.15

# 2. Run test (it fails - function doesn't exist)
# $ pytest tests/test_calculator.py::test_calculate_federal_tax_2024

# 3. Implement minimal code to pass
def calculate_federal_tax(income, year):
    if year == 2024:
        if income <= 55867:
            return {
                'federal_tax': income * 0.15,
                'marginal_rate': 0.15
            }
    raise NotImplementedError()

# 4. Test passes, refactor if needed, repeat
```

**Benefits for this project:**

- **Accuracy validation:** Tax calculations must be correct - tests prove it
- **Regression prevention:** RAG changes shouldn't break working features
- **Documentation:** Tests show how components should behave
- **Confidence:** Refactor chunking/retrieval without fear of breaking things
- **Evaluation baseline:** Tests become part of the eval set

**Test Coverage Targets:**

- Calculator module: **100%** (money is involved)
- Document ingestion: **90%+** (core functionality)
- Retrieval logic: **85%+** (quality-critical)
- API endpoints: **80%+** (user-facing)
- UI components: **60%+** (lower risk, harder to test)

### Object-Oriented Design
Use classes where behavior is encapsulated:
- `DocumentLoader` - Parse and chunk documents
- `TaxKnowledgeBase` - Vector store wrapper
- `Retriever` - Hybrid search (vector + BM25)
- `Chatbot` - LLM interface and prompt management
- `Calculator` - Deterministic tax calculations

### Modularity for AI Integration
Build core functions as discrete callable tools with JSON inputs/outputs. This enables future integration with:
- OpenAI function calling
- LangChain agents
- Plugin frameworks (MCP)

---

## Plan #1 - Local Docker-Based Tool

### Objectives

1. Self-contained Q&A assistant running entirely on user's machine
2. RAG grounding in up-to-date tax legislation
3. Deterministic calculations via separate calculator module
4. No data transmitted to third parties

### Components

#### Corpus Ingestion and Indexing

**Sources:**
- Income Tax Act and Regulations from [Justice Laws](https://laws-lois.justice.gc.ca/) (English XML consolidations)
- CRA Folios (English excerpts only)
- Update frequency: Every ~2 weeks (matches Justice Laws consolidation schedule)

**Processing:**
- `DocumentLoader` class parses PDF/HTML/XML
- Section-aware chunking respects ITA structure (e.g., 118(1)(a)(i))
- Metadata preserved: section numbers, headings, dates
- **See [Ingestion Specification](./ingestion-spec.md) for detailed implementation guide**

**Vector Store:**
- Embedding model: Mistral Embed (top 2025 accuracy), text-embedding-3-large (OpenAI), or BGE-large (open source)
- Storage: ChromaDB or FAISS with SQLite persistence
- Alternative: pgvector in PostgreSQL container

**Retrieval:**
- Hybrid search: vector similarity + BM25 keyword matching
- Cross-encoder re-ranking for top results
- Metadata filtering by section or document type

#### Language Model Interface

**Model:**
- Recommended: Qwen 2.5 72B (best RAG performance), Llama 3.3 70B (clean prose), or DeepSeek-R1-Distill-32B (efficient reasoning)
- Budget option: Qwen 2.5 7B for laptop/low-resource environments
- Optional: User-supplied API key for Claude Opus 4.5 or GPT-5.2
- Abstraction: `LLMClient` class to swap implementations

**Prompt Template:**
- System prompt: Answer only from provided context, cite sources, refuse when uncertain
- Few-shot examples: Clarifying questions (year, province, income type)

**Output Format:**
```json
{
  "assumptions": ["..."],
  "questions": ["..."],
  "answer": "...",
  "citations": [
    {"source": "ITA s.118(1)", "text": "..."}
  ]
}
```

#### Calculator Module

Separate `TaxCalculator` module with no AI dependencies:
- Taxable income computation
- Federal/provincial tax brackets
- Basic personal amount and common credits
- Unit tested against known scenarios

LLM calls calculator via function calling - never performs final math itself.

#### API and Backend

**Framework:** FastAPI

**Endpoints:**
- `POST /query` - Ask a question, return JSON answer
- `POST /upload` - Ingest local document
- `POST /calc` - Deterministic calculation

**Validation:** Pydantic models for request/response schemas

#### User Interface

**Options:**
- Streamlit (fastest for MVP)
- FastAPI + Jinja templates
- Next.js (future upgrade)

**Features:**
- Chat interface with streaming responses
- Citations as clickable links
- Document upload area
- Toggle for raw JSON output
- Mobile-responsive
- English-only labels and system messages in v0.1

#### Deployment

**Docker Compose:**
- FastAPI server
- Vector database (Chroma or PostgreSQL + pgvector)
- Ollama server (optional, for local models)

**Commands:**
```bash
docker compose up        # Start all services
./scripts/update-corpus  # Fetch latest law consolidations
./scripts/reindex        # Rebuild vector index
```

**Security:**
- Bind to localhost by default
- No persistent storage of user input
- Sessions expire on browser close

---

## Plan #2 - Hosted Web Service

### Objectives

1. Publicly accessible web service for tax Q&A
2. Scalable cloud infrastructure
3. PIPEDA-compliant data handling
4. Higher quality answers via Claude Opus 4.5 or GPT-5.2

### Components

#### Backend

**Framework:** FastAPI (or Node/NestJS for single-language stack)

**Features:**
- Async request handling
- User authentication (optional, for conversation history)
- Rate limiting and request validation

**Vector Store:**
- Managed PostgreSQL with pgvector, or hosted service (Pinecone)
- Encryption at rest
- No persistent storage of user queries

**Task Queue:**
- Celery or FastAPI background tasks
- Handles corpus updates and re-indexing

#### Document Ingestion

- Scheduled job fetches Justice Laws consolidations every ~2 weeks
- Same `DocumentLoader` and indexing logic as Plan #1
- Admin interface for monitoring ingestion status

#### Language Model

**Recommended options:**
- **Claude Opus 4.5** (Anthropic API or OpenRouter) - Excellent instruction-following and citation handling, 200K+ context window
- **GPT-5.2 Instant** (OpenAI API or OpenRouter) - Fast responses, improved tool-calling, August 2025 knowledge cutoff
- **o3-mini / o4-mini** (OpenAI API or OpenRouter) - Specialized reasoning for calculation tasks

**API Access:**
- **Direct APIs:** Anthropic, OpenAI - Direct billing, full feature access
- **OpenRouter:** Unified API for multiple providers, automatic fallbacks, competitive pricing, access to models from multiple vendors

**Fine-tuning (optional):**
- Train on curated Q&A pairs for behavior (not knowledge)
- Objectives: ask clarifying questions, follow "not advice" style, output JSON with citations
- Format: JSONL chat format per provider spec (OpenAI) or prompt library (Anthropic)

**Optimizations:**
- Cache retrieval results to reduce latency and cost
- Stream partial responses to client

#### API Design

**Endpoints:**
- `POST /api/query` - Chat query
- `POST /api/calc` - Deterministic calculation
- `POST /api/feedback` - User feedback (thumbs up/down)
- `GET /api/docs` - API documentation

**Security:**
- Input validation and size limits
- Sanitize user input before prompt insertion
- Authentication tokens for restricted access

#### Frontend

**Framework:** Next.js or SvelteKit

**Features:**
- Chat interface with streaming
- Clickable citations
- Consent banner for data handling
- Privacy policy link
- Optional user accounts (minimize data collection)

#### Security and Privacy

- HTTPS everywhere (Let's Encrypt certificates)
- No personal data in logs; anonymize IP addresses
- User can delete conversation history
- Regular security audits

##### PII Handling for Hosted Mode

User queries are sent to third-party LLM APIs (Anthropic, OpenAI, or via OpenRouter). The following rules apply:

**Always redact before API call:**
- Social Insurance Number (SIN) - pattern: `\d{3}-\d{3}-\d{3}`
- Full legal names (if detected)
- Street addresses
- Phone numbers, email addresses
- Bank account numbers, credit card numbers

**Not considered PII for this purpose:**
- Income amounts (required for tax questions)
- Province of residence (required for provincial tax)
- Tax year
- Employment type, deduction categories

**Implementation:**
```
User Input → Redaction Layer → LLM API → Response → User
                  ↓
            [Redacted values stored in session memory]
            [Restored in response if needed]
```

**Logging policy:**
- Request logs: Timestamp, session ID, response latency only
- No query content in logs
- No financial amounts in logs
- IP addresses anonymized (last octet zeroed)

**Retention:**
- User queries: Zero persistent storage
- Session data: Memory only, cleared on session end
- Conversation history (if enabled): User-controlled, deletable

**Transparency:**
- Privacy banner on first use explaining data flow
- Link to full privacy policy
- Clear indication when query is sent to external API

#### Operations

**Deployment:** AWS, Azure, or GCP with container orchestration

**Monitoring:** Prometheus + Grafana

**Cost management:**
- Request quotas
- Response caching
- Tiered plans if monetized

---

## Comparison

| Aspect | Plan #1 (Local) | Plan #2 (Hosted) |
|--------|-----------------|------------------|
| **Privacy** | All processing on user's device | User queries go to server; strict privacy policy required |
| **Deployment** | Docker on user hardware | Cloud infrastructure managed centrally |
| **Model Quality** | Open models (Qwen 2.5, Llama 3.3, DeepSeek); labeled "experimental" | Claude Opus 4.5 or GPT-5.2 with optional fine-tuning; highest quality |
| **Maintenance** | User updates corpus and software | Centralized updates by maintainer |
| **Scaling** | Single user | Multi-user with horizontal scaling |
| **Cost** | Free (user provides hardware) | API costs; potential subscription model |
| **Legal** | Minimal copyright concern for personal use | Must ensure CRA content compliance if commercial |

---

## Conclusion

Both plans share a modular architecture with clear separation of concerns:
- **Retrieval** provides factual grounding
- **LLM** generates natural language answers
- **Calculator** handles deterministic math
- **UI** presents results with citations

Plan #1 prioritizes privacy for individuals who want local-only processing. Plan #2 prioritizes convenience and quality for broader accessibility. The shared codebase allows starting with one mode and adding the other later.
