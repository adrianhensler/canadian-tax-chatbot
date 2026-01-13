# Research Notes: Canadian Tax Chatbot

**Last Updated:** January 2025

Background research, strategic analysis, and design rationale for the Canadian Tax Chatbot project.

---

## Table of Contents

1. [Why RAG First, Not Fine-Tuning](#why-rag-first-not-fine-tuning)
2. [Product Phases](#product-phases)
3. [Canonical Source Set](#canonical-source-set)
4. [Security Best Practices](#security-best-practices)
5. [Local vs Hosted Models](#local-vs-hosted-models)
6. [Technical Stack Recommendations](#technical-stack-recommendations)
7. [UI/UX Guidelines](#uiux-guidelines)
8. [Distribution Strategy](#distribution-strategy)
9. [Evaluation and Iteration](#evaluation-and-iteration)
10. [OpenAI Agents Integration](#openai-agents-integration)
11. [Legal Considerations](#legal-considerations)

---

## Why RAG First, Not Fine-Tuning

For Canadian tax, fine-tuning the model on legal text is rarely the best first move:
- Tax rules change frequently
- Interpretations shift with new CRA guidance
- Users need source-backed answers they can verify

**The practical rule:**
- **RAG supplies "what is true"** - Retrieval grounds answers in current law
- **Fine-tuning supplies "how to behave"** - Question-asking style, output structure, refusal patterns

Fine-tuning can help with:
- Asking the right follow-up questions (province, residency, income type, year)
- Outputting consistent JSON (`{assumptions, questions, answer, citations}`)
- Following a "tax-safety" style: informational, cite sources, recommend accountant for edge cases

But fine-tuning should not be used to bake in tax knowledge - that's what retrieval is for.

---

## Product Phases

### Phase 1: Tax Explainer + Checklist Builder (MVP)

**Goal:** Answer questions with citations, generate document checklists

**Features:**
- RAG over ITA + Regulations + CRA Folios
- "Interview mode" asking 5-15 questions
- Output: likely credits/deductions, documents needed (T4, RRSP slips), warnings

**No filing. Minimal liability surface.**

### Phase 2: Calculation Assistant

Add deterministic calculator layer:
- LLM never computes final tax
- LLM fills structured schema → code computes
- Model explains reasoning and cites sources

Shows transparent calculation trace with unit tests.

### Phase 3: Return Builder (Export, Not Transmit)

Generate T1-like internal representation:
- Summary PDF for user
- JSON export for import into other software

**Still not filing.**

### Phase 4: Electronic Filing (Hard Mode)

Requires CRA certification:
- NETFILE (individuals filing own return)
- EFILE (professional filers)

This is feasible but shifts from "LLM product" to "regulated integration + compliance + QA."

**Recommendation:** Keep MVP as non-filing until demand is validated.

---

## Canonical Source Set

### Primary Sources (High Signal)

| Source | URL | Update Frequency |
|--------|-----|------------------|
| Income Tax Act | [laws-lois.justice.gc.ca](https://laws-lois.justice.gc.ca/eng/acts/I-3.3/) | ~2 weeks |
| Income Tax Regulations | [laws-lois.justice.gc.ca](https://laws-lois.justice.gc.ca/eng/regulations/C.R.C.,_c._945/) | ~2 weeks |
| CRA Income Tax Folios | [canada.ca](https://www.canada.ca/en/revenue-agency/services/tax/technical-information/income-tax/income-tax-folios-index.html) | Varies |

**Note:** CRA Income Tax Folios were introduced in 2013 to gradually replace older interpretation bulletins.

### Corpus Acquisition Strategy

**Format decision:** XML consolidations from Justice Laws
- Structured, stable, easier to parse than HTML
- Includes version dates and section metadata
- Less brittle than web scraping

**Update strategy:**
- Scheduled fetch (cron/Celery) every ~2 weeks
- Compare current corpus to latest feeds
- Re-index only changed sections

**Error handling:**
- Log parsing failures
- Alert maintainers
- Don't silently skip documents

---

## Security Best Practices

### Data Handling Defaults

- **Local-first storage:** Keep tax inputs on-device by default
- **Redaction layer:** Strip SIN, names, addresses before API calls
- **No training on user data:** Explicitly stated in product

### App Architecture

Separate services/modules:
- **Retriever** - Builds citations pack
- **Reasoner** - LLM answers using pack only
- **Calculator** - Deterministic math
- **UI** - Local web app / desktop

### Quality Gates

Build evaluation set of ~100 questions:
- 70 "basic" questions
- 20 "tricky" edge cases
- 10 "should refuse / recommend accountant"

Score on:
- Citation correctness
- Hallucination rate
- "Asked-needed-questions" rate

---

## Local vs Hosted Models

### Trade-offs

| Aspect | Hosted API (2025) | Local (Ollama) |
|--------|-------------------|----------------|
| Answer quality | State-of-the-art (Claude Opus 4.5, GPT-5.2) | Excellent with modern models (Qwen 2.5 72B, Llama 3.3 70B) |
| Privacy | Queries leave device | Everything local |
| Cost | Per-token charges (~$0.015/1K) | Free (user provides hardware) |
| Setup | API key only | Docker + model download (~20-50GB) |
| Hardware needed | None | 48GB+ VRAM or 128GB RAM for 70B models |

### Recommended Approach

**Default:** Claude Opus 4.5 or GPT-5.2 Instant + RAG + redaction layer

**Optional "Private Mode":** Local model (Qwen 2.5 72B or DeepSeek-R1-Distill-32B) with same retrieval index

**Budget/Testing:** Qwen 2.5 7B for laptop development

This avoids stalling MVP waiting for perfect local model quality.

### Local Model Expectations

Label local mode as "High Quality" or "Experimental" depending on model:
- **Qwen 2.5 72B / Llama 3.3 70B**: Production-quality for most questions
- **DeepSeek-R1-Distill-32B**: Good reasoning, efficient for mid-range hardware
- **Qwen 2.5 7B**: Budget option, may miss nuanced edge cases
- Hosted Claude/GPT-5.2 still provides highest quality for complex situations

---

## Technical Stack Recommendations

### Frontend

**MVP:** Streamlit - Fast iteration, interactive, good enough for validation

**Future:** Next.js - More control over UX, user accounts, theming

### Backend

**Recommended:** FastAPI (Python)
- Lightweight, high-performance
- Auto-generated API docs
- Integrates with Python ML ecosystem
- Async support for concurrency

**Alternative:** Node/NestJS if preferring single-language stack

### LLM Integration

**Hosted (Recommended for production):**
- **Claude Opus 4.5** (Anthropic API or OpenRouter) - Best instruction-following, 200K+ context
- **GPT-5.2 Instant** (OpenAI API or OpenRouter) - Fast, improved tool-calling, Aug 2025 knowledge
- **o3-mini / o4-mini** (OpenAI API or OpenRouter) - Specialized reasoning for calculations

**OpenRouter Benefits:**
- Single API key for multiple providers (Anthropic, OpenAI, DeepSeek, etc.)
- Automatic fallbacks if primary model is unavailable
- Often more competitive pricing than direct APIs
- Access to models that may be region-restricted
- Unified interface simplifies `LLMClient` implementation

**Local (Privacy-focused):**
- **Qwen 2.5 72B** - Best RAG performance (requires 48GB+ VRAM or 128GB RAM)
- **Llama 3.3 70B** - Clean, controllable prose
- **DeepSeek-R1-Distill-32B** - Efficient reasoning (24GB VRAM or 64GB RAM)
- **Qwen 2.5 7B** - Budget/laptop option (8GB VRAM or 16GB RAM)

All via `LLMClient` abstraction to swap implementations

### Hardware Requirements (Local Models)

| Model | Size | VRAM (GPU) | RAM (CPU-only) | Use Case |
|-------|------|------------|----------------|----------|
| Qwen 2.5 72B | 72B | 48GB+ | 128GB+ | Production quality, best RAG |
| Llama 3.3 70B | 70B | 48GB+ | 128GB+ | Clean prose, general quality |
| DeepSeek-R1-Distill-32B | 32B | 24GB | 64GB+ | Mid-range, good reasoning |
| Qwen 2.5 7B | 7B | 8GB | 16GB+ | Budget/laptop, testing |

**Inference speed:**
- With GPU (NVIDIA RTX 4090, A100): 20-50 tokens/sec
- CPU-only (high-end workstation): 2-10 tokens/sec
- Apple Silicon (M2 Max/Ultra): 15-30 tokens/sec

### Retrieval Stack

- **Embedding:** Mistral Embed (top 2025 accuracy), text-embedding-3-large (OpenAI), or BGE-large (open source)
- **Vector Store:** ChromaDB or FAISS with SQLite persistence
- **Hybrid Search:** Vector similarity + BM25 via LangChain or LlamaIndex
- **Re-ranking:** Cross-encoder for top results
- **Advanced techniques (2025):** Self-RAG (52% less hallucination), GraphRAG (for hierarchical ITA structure), Adaptive RAG

### Deployment

Docker Compose setup:
- FastAPI server
- Vector database
- Ollama server (optional)

One-command launch: `docker compose up`

---

## UI/UX Guidelines

### Chat Interface

- Familiar chat bubble layout (user right, bot left)
- Markdown rendering for rich text and code blocks
- Streaming responses for immediate feedback
- Loading indicator while generating

### Citations

- Superscript numbers in answer text: "...certain conditions[1]"
- Source list at end: "[1] CRA Guide T4044, p. 3"
- Clickable links to official sources
- Hover preview of cited text (optional)

### Document Upload

- Drag-and-drop or button upload
- Confirmation message in chat
- Progress indicator during indexing
- Privacy reassurance: "Your documents are processed locally"

### Structured Output

- JSON rendered with syntax highlighting
- "Copy JSON" button for export
- Table rendering for tabular data

### General

- Professional but approachable aesthetic
- Example queries as placeholder text
- Graceful error messages
- Accessible design (readable fonts, good contrast, keyboard navigation)

---

## Distribution Strategy

### Channels

- **GitHub:** Open-source repository with clear README
- **Hacker News:** "Show HN" post emphasizing problem solved
- **Reddit:** r/MachineLearning, r/PersonalFinanceCanada
- **LinkedIn:** Professional angle for accountants/tax preparers
- **Product Hunt:** For broader consumer visibility

### Content Strategy

**Blog posts that double as marketing:**

1. "Why We Didn't Fine-Tune on the Tax Act (At First)"
   - Explain freshness + citations + evals
   - Screenshot of "answer with sources"

2. "RAG You Can Trust: Building a Citation-First Tax Assistant"
   - Source list and chunking strategy
   - Examples with links

3. "LLM + Deterministic Calculator: The Hybrid Pattern"
   - JSON schema
   - Unit test examples
   - Calculation trace

4. "Privacy & Threat Model for DIY Tax Software"
   - What's stored locally
   - What's sent to APIs and how it's redacted
   - Encryption and secrets handling

### Tailoring to Audiences

**Developers:** Technical deep-dives, architecture diagrams, code quality

**Tax professionals:** Accuracy, time-saving, cite-ability for verification

**Everyday users:** Ease of use, trustworthiness, friendly tone

---

## Evaluation and Iteration

### Test Set Construction

Collect ~100 representative questions:
- Common scenarios from CRA FAQs
- Real confusion points from tax forums
- Synthetic edge cases for stress testing

Each question needs:
- Ground truth answer
- Relevant citations
- Expected behavior (answer, ask clarifying question, or refuse)

### Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| Citation accuracy | >90% | Does cited source support the answer? |
| Hallucination rate | <5% | Did the answer invent rules? |
| Retrieval recall | >85% | Did retrieval find relevant section? |
| Faithfulness | High | Is answer consistent with retrieved context? |

### Iteration Process

1. Implement feature or tweak
2. Run eval set
3. Compare metrics to baseline
4. Manual testing of realistic conversations
5. Analyze failures (retrieval issue vs generation issue)
6. Add edge cases to eval set

### Staged Feature Releases

- **v0.1:** Q&A with citations only - validate demand
- **v0.2:** Interview mode - guided question flow
- **v0.3:** Calculator mode - deterministic tax math
- **v0.4:** Export JSON - structured output

Ship v0.1 first. Observe usage. Then decide on next phase.

---

## OpenAI Agents Integration

### Tool-Oriented Design

Structure functions as discrete, callable tools:
- `lookup_tax_law(query: str) -> str` - Search vector store
- `calculate_income_tax(data: dict) -> dict` - Deterministic calculation
- `ask_clarifying_question(topic: str) -> str` - Interview flow

Each tool should:
- Do one thing clearly
- Have clear docstring describing purpose and parameters
- Return structured JSON

### JSON Schemas

Define Pydantic models for tool inputs/outputs:
```python
class TaxCalculationInput(BaseModel):
    income: float
    rrsp_contribution: float
    province: str

class TaxCalculationOutput(BaseModel):
    federal_tax: float
    provincial_tax: float
    total_tax: float
    effective_rate: float
```

### API Endpoints for Tools

Design REST endpoints that map to tools:
- `GET /taxlaw?query=...` - Lookup
- `POST /calculate` - Calculation

Clear paths, appropriate HTTP methods, JSON responses.

### Future Integration

With tool-oriented design, the chatbot can later be:
- ChatGPT plugin
- MCP server for Claude or other agents
- LangChain agent tool

---

## Legal Considerations

### Reproducing Federal Law

**Allowed** under [Reproduction of Federal Law Order](https://laws-lois.justice.gc.ca/eng/regulations/SI-97-5/page-1.html):
- Income Tax Act
- Income Tax Regulations
- Court decisions

**Requirements:**
- Exercise due diligence for accuracy
- State "not an official version"
- Cite source (Justice Laws)

### CRA Publications

**Crown copyright applies.** Non-commercial personal use allowed with:
- Citation of authoring organization
- Statement that not endorsed by Government of Canada

**Commercial use requires permission.** Strategy:
- Keep excerpts only, not full documents
- Link to official CRA pages
- If monetizing, seek licensing guidance

### Privacy (PIPEDA)

If commercial activity (charging, ads), PIPEDA applies:
- Clear privacy policy
- Data minimization (no SINs)
- Local-first storage defaults
- Explicit consent for any logging
- Disclose if queries sent to third-party API

### Filing Software (If Ever)

NETFILE/EFILE certification required for actual filing:
- CRA has certified software lists
- Significant compliance/QA requirements
- Different product category entirely

**Recommendation:** Stay as "research + explain + estimate" until demand proven.

---

## References

- [Justice Laws - Income Tax Act](https://laws-lois.justice.gc.ca/eng/acts/I-3.3/)
- [CRA Income Tax Folios](https://www.canada.ca/en/revenue-agency/services/tax/technical-information/income-tax/income-tax-folios-index.html)
- [Reproduction of Federal Law Order](https://laws-lois.justice.gc.ca/eng/regulations/SI-97-5/page-1.html)
- [PIPEDA Fair Information Principles](https://www.priv.gc.ca/en/privacy-topics/privacy-laws-in-canada/the-personal-information-protection-and-electronic-documents-act-pipeda/p_principle/)
- [CRA NETFILE Program](https://www.canada.ca/en/revenue-agency/services/e-services/e-services-individuals/netfile-overview.html)
