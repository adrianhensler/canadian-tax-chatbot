# Canadian Tax Chatbot

A RAG-powered chatbot that answers Canadian income tax questions with citations to authoritative sources.

---

## Status

**Phase:** Planning / Pre-implementation

This project is in the documentation and design phase. No code has been written yet. The architecture and requirements are documented; implementation will follow.

---

## What This Does

Ask a question about Canadian personal income tax. The chatbot retrieves relevant passages from the Income Tax Act, Regulations, and CRA guidance, then generates an answer grounded in those sources. Every answer includes citations so you can verify the information.

**This tool does not:**
- File tax returns
- Provide professional tax advice
- Replace consultation with a qualified accountant

---

## Planned Features

- **Q&A with Citations** - Ask questions, get answers with source references
- **Local Mode** - Run entirely on your machine via Docker + Ollama (no data leaves your device)
- **Hosted Mode** - Web service using GPT-4 for higher quality answers
- **Hybrid Retrieval** - Vector search + keyword matching for accurate document retrieval
- **Deterministic Calculations** - Tax math handled by code, not the LLM

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

## Contributing

Contributions welcome once implementation begins. See the [PRD](docs/PRD.md) for project scope and [Architecture](docs/architecture.md) for technical approach.
