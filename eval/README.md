# Evaluation Dataset for Canadian Tax Q&A

This directory contains curated question-answer pairs for evaluating retrieval-augmented generation (RAG) systems on Canadian income tax questions.

---

## Dataset Structure

```
eval/
├── canadian-tax-qa-dataset/
│   ├── metadata.json              # Dataset metadata and sources
│   ├── basic_questions.jsonl      # Common tax questions (7 questions)
│   ├── tricky_questions.jsonl     # Edge cases and nuanced scenarios (5 questions)
│   └── should_refuse.jsonl        # Cases requiring professional advice (3 questions)
└── examples/
    └── initial-dataset-v1.zip     # Original dataset archive (reference/backup)
```

**Total:** 15 questions

---

## Format

Each `.jsonl` file contains one JSON object per line:

```json
{
  "question": "Who has to file a Canadian income tax return?",
  "answer": "You have to file a return if...",
  "source_section": "CRA – Who has to file a return",
  "source_url": ["https://www.canada.ca/..."],
  "tags": ["filing-requirements", "tax-return"],
  "difficulty": "basic"
}
```

**Fields:**
- `question` - Natural language question about Canadian tax
- `answer` - Authoritative answer with citations
- `source_section` - Reference to ITA section or CRA guidance
- `source_url` - Links to official sources
- `tags` - Keywords for categorization
- `difficulty` - `basic`, `tricky`, or `should-refuse`

---

## License

**CC0-1.0 (Public Domain)**

This dataset is dedicated to the public domain under the [Creative Commons Zero v1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/) license. You can copy, modify, distribute and use the dataset for any purpose without asking permission.

### Why Public Domain?

Public evaluation datasets accelerate research and ensure transparency in AI systems. Anyone can:
- Use this to benchmark their own Canadian tax chatbot
- Extend it with more questions
- Publish accuracy results
- Build upon it without restrictions

---

## Sources

Questions and answers derived from:
- [Canada Revenue Agency guidance](https://www.canada.ca/en/revenue-agency.html)
- [Justice Laws website](https://laws-lois.justice.gc.ca/)
- [Open Government Portal](https://open.canada.ca/)

All answers cite authoritative government sources.

---

## Can You Contribute?

**Yes!** This is a community resource.

### How to Add Questions

1. **Fork the repo** on GitHub
2. **Add questions** to the appropriate `.jsonl` file:
   - `basic_questions.jsonl` - Common questions most taxpayers ask
   - `tricky_questions.jsonl` - Edge cases, complex scenarios, nuanced situations
   - `should_refuse.jsonl` - Questions requiring professional tax advice

3. **Follow the format** (see above)
4. **Cite sources** - Every answer must link to CRA guidance or ITA sections
5. **Submit a PR** with your additions

### Quality Guidelines

✅ **Do:**
- Cite official CRA or Justice Laws sources
- Write clear, natural language questions
- Provide complete answers (not just "see section X")
- Include appropriate tags
- Test that source URLs are valid

❌ **Don't:**
- Copy/paste large blocks of copyrighted CRA text (use excerpts with citations)
- Include personal opinions or non-official interpretations
- Add questions about US tax, corporate tax (T2), or GST/HST (focus: personal income tax T1)
- Include identifying information about real taxpayers

---

## Usage in Testing

This dataset is intended for:

1. **Retrieval evaluation** - Does the RAG system retrieve correct ITA sections?
2. **Citation accuracy** - Do generated answers cite the right sources?
3. **Hallucination detection** - Does the system invent tax rules not in the corpus?
4. **Refusal behavior** - Does it correctly identify when to say "consult a professional"?

### Example Test

```python
import json

# Load evaluation set
with open('eval/canadian-tax-qa-dataset/basic_questions.jsonl') as f:
    questions = [json.loads(line) for line in f if line.startswith('{')]

# Test retrieval
for q in questions:
    result = chatbot.answer(q['question'])

    # Check: Does answer include correct source?
    expected_source = q['source_section']
    assert expected_source in result['citations']

    # Check: No hallucinated rules
    assert not contains_hallucination(result['answer'], corpus)
```

---

## Expansion Roadmap

Target: **100+ questions** covering:

- [ ] RRSP contributions and withdrawals (HBP, LLP)
- [ ] TFSA rules and limits
- [ ] Capital gains and losses
- [ ] Employment expenses (T2200)
- [ ] Self-employment income (T2125)
- [ ] Rental income and expenses
- [ ] Child care expenses
- [ ] Medical expenses
- [ ] Tuition and education credits
- [ ] Principal residence exemption
- [ ] Foreign income reporting
- [ ] Provincial tax differences
- [ ] Tax brackets and rates (2024, 2025)

**Want to help?** Pick a category and submit questions!

---

## Citation

If you use this dataset in research or publications:

```bibtex
@dataset{canadian_tax_qa_2026,
  title={Evaluation Dataset for Canadian Tax Question Answering},
  author={Canadian Tax Chatbot Contributors},
  year={2026},
  url={https://github.com/adrianhensler/canadian-tax-chatbot},
  license={CC0-1.0}
}
```

---

## Questions?

Open an issue on GitHub or contribute directly via pull request.
