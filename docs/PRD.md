# Product Requirements Document: Canadian Tax Chatbot

**Version:** 0.1
**Last Updated:** January 2025
**Status:** Planning

---

## Product Overview

A retrieval-augmented generation (RAG) chatbot that answers Canadian income tax questions by citing authoritative sources (Income Tax Act, Regulations, CRA guidance). The product does not file tax returns or provide professional advice. It explains rules, estimates amounts, and helps users understand what documents they need.

---

## Problem Statement

Canadian taxpayers face a complex tax system with thousands of pages of legislation and CRA guidance. Finding answers requires navigating multiple government websites, interpreting legal language, and understanding which rules apply to specific situations. Existing tax software focuses on filing, not explanation. There is no accessible tool that answers tax questions with citations to authoritative sources.

---

## Target Users

**Primary:** Individual Canadian taxpayers who want to understand their tax obligations before or during tax season.

**Secondary:**
- Tax preparers and accountants seeking quick reference lookup
- Developers interested in RAG applications for legal/regulatory domains
- Privacy-conscious users who want local-only processing

---

## Goals

1. Answer common Canadian tax questions accurately with source citations
2. Provide two deployment options: local (privacy-first) and hosted (convenience)
3. Never hallucinate tax rules - refuse when uncertain rather than guess
4. Separate factual retrieval from deterministic calculations
5. Comply with Canadian privacy law (PIPEDA) and Crown copyright requirements

## Non-Goals

1. Filing tax returns (NETFILE/EFILE integration)
2. Replacing professional tax advice for complex situations
3. Covering provincial-specific rules beyond basic federal/provincial tax
4. GST/HST or corporate tax (T2) - focus is personal income tax (T1)
5. Real-time CRA account integration

---

## Core Features (v0.1)

### Q&A with Citations
- User asks a natural language question about Canadian tax
- System retrieves relevant passages from the corpus (ITA, Regulations, CRA Folios)
- LLM generates an answer grounded in retrieved context
- Response includes citations with section references and links

### Two Deployment Modes

**Local Mode (Plan #1)**
- Docker-based, runs entirely on user's machine
- Uses Ollama with open-source models (Qwen 2.5 72B, Llama 3.3 70B, or DeepSeek-R1-Distill-32B)
- No data leaves the device
- Labeled as "experimental" due to model quality constraints

**Hosted Mode (Plan #2)**
- Web service using Claude Opus 4.5, GPT-5.2, or other models via OpenRouter/direct APIs
- OpenRouter provides unified access to multiple providers with fallback support
- Higher quality answers with better citation handling
- Privacy policy and data minimization
- Potential for fine-tuning on behavior (not knowledge)

### Corpus
- Income Tax Act (XML consolidations from Justice Laws)
- Income Tax Regulations
- CRA Income Tax Folios (excerpts with citations, not full reproduction)
- Updated every ~2 weeks to match Justice Laws consolidation schedule

---

## Future Features (Deferred)

| Feature | Description | Phase |
|---------|-------------|-------|
| Interview Mode | Guided Q&A that asks clarifying questions (province, year, income type) | v0.2 |
| Calculator Mode | Deterministic tax calculations separate from LLM | v0.3 |
| Export JSON | Structured output for integration with other tools | v0.4 |
| Document Upload | User uploads T4, NOA for personalized answers | v0.5 |

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Citation accuracy | >90% | Eval set: Does cited source support the answer? |
| Hallucination rate | <5% | Eval set: Did the answer invent rules not in corpus? |
| Retrieval recall | >85% | Eval set: Did retrieval find the relevant section? |
| User satisfaction | >4/5 | Post-answer feedback thumbs up/down |

---

## Technical Constraints

### Architecture
- RAG-first: Knowledge comes from retrieval, not model weights
- Hybrid retrieval: Vector similarity + BM25 keyword search
- Section-aware chunking: Respect ITA structure (sections, subsections)
- Deterministic calculator: LLM never performs final tax math

### Legal
- Federal law reproduction allowed under Reproduction of Federal Law Order
- CRA content: Excerpts only with citations; full reproduction requires permission if commercial
- Must display "not an official version" disclaimer
- Must state "informational purposes only, not tax advice"

### Privacy (PIPEDA)
- Minimize data collection - don't ask for SIN
- Local mode: No data transmission
- Hosted mode: Redact PII before API calls, no persistent storage of user queries
- Clear privacy policy required

---

## Open Questions

| Question | Options | Decision Needed By |
|----------|---------|-------------------|
| Corpus format | XML consolidations (see [Ingestion Spec](./ingestion-spec.md)) | ✅ Specified |
| Embedding model | Mistral Embed, text-embedding-3-large, or BGE-large | During chunking prototype |
| Vector store | ChromaDB, FAISS, or pgvector | During RAG pipeline build |
| Hosted model | Claude Opus 4.5, GPT-5.2 Instant, or o3-mini | Before hosted launch |
| API provider | Direct (Anthropic/OpenAI) vs OpenRouter | Before hosted launch |
| Local model | Qwen 2.5 72B, Llama 3.3 70B, or DeepSeek-R1-Distill-32B | During local prototype |
| Monetization | Free vs paid tier | After demand validation |

---

## References

- [Architecture Document](./architecture.md) - Technical implementation details (includes TDD methodology)
- [Ingestion Specification](./ingestion-spec.md) - Document ingestion implementation guide
- [Research Notes](./research-notes.md) - Strategic analysis and background research
