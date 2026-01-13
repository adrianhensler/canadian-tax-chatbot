# Document Ingestion Specification

**Version:** 0.1
**Last Updated:** January 2026
**Status:** Implementation Guide

This document specifies how to ingest Canadian tax law documents into the RAG system, including federal legislation from Justice Laws and CRA guidance materials.

---

## Table of Contents

1. [Justice Laws - Federal Legislation](#justice-laws---federal-legislation)
2. [CRA Income Tax Folios](#cra-income-tax-folios)
3. [XML Parsing and Structure](#xml-parsing-and-structure)
4. [Chunking Strategy](#chunking-strategy)
5. [Update Detection](#update-detection)
6. [Corpus Versioning](#corpus-versioning)
7. [Custom Document Ingestion](#custom-document-ingestion)
8. [Implementation Checklist](#implementation-checklist)

---

## Justice Laws - Federal Legislation

### Source Documents

Primary sources from [Justice Laws Website](https://laws-lois.justice.gc.ca/):
- **Income Tax Act** - R.S.C., 1985, c. 1 (5th Supp.)
- **Income Tax Regulations** - C.R.C., c. 945

### Access Methods

Justice Canada provides **three methods** to access XML consolidations:

#### Method 1: GitHub Repository (Recommended for Development)

**Repository:** [justicecanada/laws-lois-xml](https://github.com/justicecanada/laws-lois-xml)

**Pros:**
- Complete bulk download of all Acts and Regulations
- Git history for change tracking
- Easy to clone and version control
- No rate limiting concerns

**Cons:**
- Large download (~1GB+)
- Includes all federal laws, not just tax

**Implementation:**
```bash
# Clone the repo
git clone https://github.com/justicecanada/laws-lois-xml.git

# Find Income Tax Act
cd laws-lois-xml/eng/acts
ls -la I-3.3*  # Income Tax Act files

# Find Income Tax Regulations
cd ../regulations
ls -la C.R.C.,_c._945*  # Income Tax Regulations
```

#### Method 2: Open Government Portal (Recommended for Production)

**Dataset:** [Consolidated federal Acts and regulations - Bulk XML](https://open.canada.ca/data/en/dataset/ff56de85-f8b9-4719-8dff-ecf362adf0af)

**Pros:**
- Official government data portal
- Updated regularly
- Metadata about last consolidation date

**Cons:**
- Large bulk download
- Less granular than individual file access

**Implementation:**
Download the complete XML bundle from the Open Government Portal, extract Income Tax Act (I-3.3.xml) and Regulations (C.R.C.,_c._945.xml).

#### Method 3: Direct XML URLs (Recommended for Selective Updates)

**Index file:** [Legis.xml](https://laws-lois.justice.gc.ca/eng/XML/Legis.xml)

The Legis.xml file is a master index containing:
- List of all Acts and Regulations
- Consolidation dates
- Direct links to XML files

**Income Tax Act direct URL:**
```
https://laws-lois.justice.gc.ca/eng/XML/I-3.3.xml
```

**Income Tax Regulations direct URL:**
```
https://laws-lois.justice.gc.ca/eng/XML/C.R.C.,_c._945.xml
```

**Pros:**
- Fetch only what you need
- Can check Legis.xml for updates before downloading
- Lower bandwidth for incremental updates

**Implementation:**
```python
import requests
from datetime import datetime

# Fetch master index
legis = requests.get("https://laws-lois.justice.gc.ca/eng/XML/Legis.xml")

# Parse to find Income Tax Act entry
# Check consolidation date
# Download if newer than local copy

ita_xml = requests.get("https://laws-lois.justice.gc.ca/eng/XML/I-3.3.xml")
```

### Recommended Approach

**Initial setup:** Method 1 (GitHub clone) for quick start

**Production updates:** Method 3 (direct URLs)
1. Fetch Legis.xml every 2 weeks
2. Compare consolidation dates with local corpus
3. Download only changed files (ITA, Regulations)
4. Re-index changed documents

---

## CRA Income Tax Folios

### Source

[Income Tax Folios Index](https://www.canada.ca/en/revenue-agency/services/tax/technical-information/income-tax/income-tax-folios-index.html)

### Challenge

**No API or structured data available.** Must scrape HTML from canada.ca website.

### Structure

Folios are organized as:
- **Series** (S1-S6) - Broad categories
  - S1: Individuals
  - S2: Business and Professional Income
  - S3: Property, Investments, Savings Plans
  - S4: Businesses
  - S5: International
  - S6: Trusts
- **Chapters** - Specific topics within each series
- **Sections** - Subsections within chapters

### Implementation Strategy

#### Step 1: Scrape Folio Index

```python
import requests
from bs4 import BeautifulSoup

index_url = "https://www.canada.ca/en/revenue-agency/services/tax/technical-information/income-tax/income-tax-folios-index.html"
response = requests.get(index_url)
soup = BeautifulSoup(response.content, 'html.parser')

# Extract links to individual folios
folio_links = soup.find_all('a', href=True)
folio_urls = [link['href'] for link in folio_links if '/income-tax/income-tax-folios-index/' in link['href']]
```

#### Step 2: Prioritize Key Folios

Start with most relevant for personal tax:
- **S1-F1-C1:** Medical Expense Tax Credit
- **S1-F2-C1:** Education Tax Credit
- **S1-F2-C3:** Tuition Tax Credit
- **S1-F3-C1:** Child Care Expense Deduction
- **S1-F3-C2:** Principal Residence
- **S1-F4-C2:** Basic Personal and Dependant Tax Credits
- **S3-F10-C1:** Qualified Investments - RRSPs, RESPs, RRIFs, etc.

**Strategy:** Create a curated list of ~20-30 key folios instead of scraping all 100+.

#### Step 3: Extract Content

```python
def scrape_folio(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find main content area (varies by page structure)
    content = soup.find('main') or soup.find('div', class_='container')

    # Extract metadata
    title = soup.find('h1').get_text() if soup.find('h1') else ""

    # Extract text, preserving section structure
    sections = []
    for heading in content.find_all(['h2', 'h3']):
        section_title = heading.get_text()
        # Get text until next heading
        section_text = []
        for sibling in heading.find_next_siblings():
            if sibling.name in ['h2', 'h3']:
                break
            if sibling.get_text():
                section_text.append(sibling.get_text())

        sections.append({
            'title': section_title,
            'content': '\n'.join(section_text),
            'source_url': url
        })

    return {
        'title': title,
        'url': url,
        'sections': sections,
        'scraped_at': datetime.now().isoformat()
    }
```

#### Step 4: Store as Excerpts with Citations

Per legal requirements (Crown copyright), store only excerpts:
- Extract individual sections (2-5 paragraphs each)
- Preserve section headings
- Include source URL
- Add disclaimer metadata

### Update Strategy

CRA updates folios irregularly. Check "What's New" page:
- [What's new in income tax folios](https://www.canada.ca/en/revenue-agency/services/tax/technical-information/income-tax/whats-new-income-tax-folios.html)

**Implementation:**
1. Scrape "What's New" page monthly
2. Parse for recently updated folios
3. Re-scrape only changed folios
4. Compare scraped dates to local copies

---

## XML Parsing and Structure

### Justice Laws XML Schema

**Data Dictionary:** [https://laws-lois.justice.gc.ca/eng/XML/index.html](https://laws-lois.justice.gc.ca/eng/XML/index.html)

### Key XML Elements

```xml
<Statute>
  <Identification>
    <InstrumentNumber>I-3.3</InstrumentNumber>
    <ShortTitle>Income Tax Act</ShortTitle>
    <ConsolidatedDate>2025-01-15</ConsolidatedDate>
  </Identification>

  <Body>
    <Section>
      <MarginalNote>Basic personal amount</MarginalNote>
      <Label>118</Label>
      <Subsection>
        <Label>(1)</Label>
        <Text>For the purpose of computing...</Text>
        <Paragraph>
          <Label>(a)</Label>
          <Text>...</Text>
        </Paragraph>
      </Subsection>
    </Section>
  </Body>
</Statute>
```

### Parsing Strategy

```python
import xml.etree.ElementTree as ET

def parse_justice_xml(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Extract metadata
    metadata = {
        'title': root.find('.//ShortTitle').text,
        'number': root.find('.//InstrumentNumber').text,
        'consolidated_date': root.find('.//ConsolidatedDate').text
    }

    # Extract sections
    sections = []
    for section in root.findall('.//Section'):
        label = section.find('Label').text if section.find('Label') is not None else ""
        marginal = section.find('MarginalNote').text if section.find('MarginalNote') is not None else ""

        # Recursively extract subsections, paragraphs, etc.
        section_text = extract_text_recursive(section)

        sections.append({
            'section_number': label,
            'title': marginal,
            'content': section_text,
            'metadata': metadata
        })

    return sections

def extract_text_recursive(element, level=0):
    """Recursively extract text while preserving structure"""
    output = []

    for child in element:
        if child.tag == 'Text':
            output.append(child.text)
        elif child.tag == 'Label':
            output.append(f"\n{'  ' * level}({child.text})")
        elif child.tag in ['Subsection', 'Paragraph', 'Subparagraph']:
            output.append(extract_text_recursive(child, level + 1))

    return '\n'.join(output)
```

---

## Chunking Strategy

### Section-Aware Chunking

**Goal:** Respect legal document structure while creating retrievable chunks.

### Rules

1. **Primary boundary:** Section level
   - Each `<Section>` becomes at least one chunk
   - Include section number (e.g., "118") and marginal note in metadata

2. **Subsection handling:**
   - If section > 2000 tokens, split at subsection boundaries
   - Keep subsection label with content (e.g., "118(1)")

3. **Paragraph handling:**
   - If subsection > 2000 tokens, split at paragraph boundaries
   - Preserve paragraph labels (e.g., "118(1)(a)")

4. **Cross-reference preservation:**
   - When chunking, include parent context in metadata
   - Example: Chunk "118(1)(a)" includes metadata: `parent_section: "118", parent_subsection: "118(1)"`

5. **Overlapping windows:**
   - Add 200-token overlap between chunks
   - Helps capture cross-references that span boundaries

### Implementation

```python
def chunk_section(section_element, max_tokens=1500, overlap_tokens=200):
    """
    Section-aware chunking with overlap
    """
    chunks = []

    section_num = section_element.find('Label').text
    marginal_note = section_element.find('MarginalNote').text or ""

    # Try to keep entire section together
    full_text = extract_text_recursive(section_element)
    token_count = estimate_tokens(full_text)

    if token_count <= max_tokens:
        # Section fits in one chunk
        chunks.append({
            'text': full_text,
            'metadata': {
                'section': section_num,
                'title': marginal_note,
                'type': 'section',
                'reference': f"ITA s.{section_num}"
            }
        })
    else:
        # Split at subsection boundaries
        for subsection in section_element.findall('Subsection'):
            subsection_num = subsection.find('Label').text
            subsection_text = extract_text_recursive(subsection)

            chunks.append({
                'text': subsection_text,
                'metadata': {
                    'section': section_num,
                    'subsection': subsection_num,
                    'title': marginal_note,
                    'type': 'subsection',
                    'reference': f"ITA s.{section_num}({subsection_num})"
                }
            })

    # Add overlap between chunks
    chunks = add_overlapping_context(chunks, overlap_tokens)

    return chunks
```

### Metadata Schema

Each chunk includes:

```json
{
  "text": "Full text content...",
  "metadata": {
    "source": "Income Tax Act",
    "source_abbreviation": "ITA",
    "section": "118",
    "subsection": "1",
    "paragraph": "a",
    "title": "Basic personal amount",
    "reference": "ITA s.118(1)(a)",
    "url": "https://laws-lois.justice.gc.ca/eng/acts/I-3.3/page-...",
    "consolidated_date": "2025-01-15",
    "chunk_id": "ITA-118-1-a-001",
    "parent_section": "118",
    "document_type": "federal_statute"
  }
}
```

---

## Update Detection

### Strategy

Compare consolidation dates to determine if re-indexing is needed.

### Implementation

```python
import json
from datetime import datetime

def check_for_updates():
    """
    Check if Justice Laws corpus has updates
    """
    # Fetch current Legis.xml
    response = requests.get("https://laws-lois.justice.gc.ca/eng/XML/Legis.xml")
    legis_xml = ET.fromstring(response.content)

    # Find Income Tax Act entry
    for act in legis_xml.findall('.//Statute'):
        if act.find('InstrumentNumber').text == 'I-3.3':
            remote_date = act.find('ConsolidatedDate').text

            # Compare with local stored date
            with open('corpus_metadata.json', 'r') as f:
                local_meta = json.load(f)

            local_date = local_meta.get('ITA_consolidated_date')

            if remote_date > local_date:
                return {
                    'update_available': True,
                    'document': 'Income Tax Act',
                    'local_date': local_date,
                    'remote_date': remote_date
                }

    return {'update_available': False}
```

### Scheduled Task

```bash
# Cron job to check for updates every 2 weeks (Monday morning)
0 6 * * 1 /path/to/venv/bin/python /path/to/check_updates.py

# check_updates.py
if check_for_updates()['update_available']:
    download_updated_files()
    reindex_corpus()
    send_notification("Corpus updated and re-indexed")
```

---

## Corpus Versioning

### Why Versioning Matters

- **Reproducibility:** Eval results are meaningless without knowing which corpus was tested
- **Debugging:** Wrong answer reports require tracing back to corpus version
- **Rollback:** Bad ingest (parsing error, corrupted data) needs quick recovery
- **Comparison:** Isolate whether quality changes come from model tuning or corpus changes

### Version Naming

Use date-based naming tied to the primary source consolidation date:

```
corpus-YYYY-MM-DD
```

Examples:
- `corpus-2025-01-15` - Corpus built from Jan 15, 2025 consolidation
- `corpus-2025-02-01` - Corpus built from Feb 1, 2025 consolidation

### Manifest File

Each corpus version includes a `corpus_manifest.json`:

```json
{
  "version": "corpus-2025-01-15",
  "created_at": "2025-01-15T06:00:00Z",
  "sources": {
    "ITA": {
      "file": "I-3.3.xml",
      "consolidated_date": "2025-01-10",
      "sha256": "a1b2c3d4e5f6..."
    },
    "ITR": {
      "file": "C.R.C.,_c._945.xml",
      "consolidated_date": "2025-01-10",
      "sha256": "f6e5d4c3b2a1..."
    },
    "CRA_Folios": {
      "count": 25,
      "scraped_at": "2025-01-14T12:00:00Z",
      "folio_list": ["S1-F1-C1", "S1-F2-C1", "..."]
    }
  },
  "processing": {
    "chunk_count": 4521,
    "embedding_model": "mistral-embed-v1",
    "chunking_config": {
      "max_tokens": 1500,
      "overlap_tokens": 200
    }
  },
  "checksums": {
    "chunks_file": "sha256:abc123...",
    "vector_index": {
      "vectors.faiss": "sha256:def456...",
      "vectors.faiss.meta": "sha256:987abc..."
    }
  }
}
```

### Directory Structure

```
data/
├── corpus/
│   ├── current -> corpus-2025-01-15/    # Symlink to active version
│   ├── corpus-2025-01-15/
│   │   ├── corpus_manifest.json
│   │   ├── chunks.jsonl
│   │   ├── vectors.faiss (or chroma/)
│   │   └── sources/
│   │       ├── I-3.3.xml
│   │       └── C.R.C.,_c._945.xml
│   ├── corpus-2025-01-01/
│   │   └── ...
│   └── corpus-2024-12-15/
│       └── ...
└── archive/                              # Cold storage for older versions
```

### Retention Policy

- **Active:** Keep last 3 corpus versions on disk
- **Archive:** Move older versions to cold storage (S3 Glacier, etc.)
- **Minimum:** Always keep at least one known-good version for rollback

### Rollback Procedure

```bash
# List available versions
./scripts/corpus-manager list

# Output:
# * corpus-2025-01-15 (current)
#   corpus-2025-01-01
#   corpus-2024-12-15

# Rollback to previous version
./scripts/corpus-manager rollback corpus-2025-01-01

# This:
# 1. Verifies checksums of target version (source XML + derived artifacts)
# 2. Updates 'current' symlink
# 3. Restarts retrieval service to load new index
# 4. Logs rollback event
```

### Implementation

```python
import hashlib
import json
from pathlib import Path
from datetime import datetime

def create_corpus_version(
    sources_dir: Path,
    output_dir: Path,
    consolidation_date: str,
    chunks_path: Path,
    vector_index_paths: list[Path],
) -> dict:
    """
    Create a new versioned corpus with manifest.
    """
    version = f"corpus-{consolidation_date}"
    version_dir = output_dir / version
    version_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "version": version,
        "created_at": datetime.now().isoformat(),
        "sources": {},
        "processing": {},
        "checksums": {}
    }

    # Copy sources and compute checksums
    for source_file in sources_dir.glob("*.xml"):
        content = source_file.read_bytes()
        sha256 = hashlib.sha256(content).hexdigest()

        # Copy to version directory
        dest = version_dir / "sources" / source_file.name
        dest.parent.mkdir(exist_ok=True)
        dest.write_bytes(content)

        manifest["sources"][source_file.stem] = {
            "file": source_file.name,
            "sha256": sha256
        }

    manifest["checksums"]["chunks_file"] = (
        f"sha256:{hashlib.sha256(chunks_path.read_bytes()).hexdigest()}"
    )
    manifest["checksums"]["vector_index"] = {
        artifact.name: f"sha256:{hashlib.sha256(artifact.read_bytes()).hexdigest()}"
        for artifact in vector_index_paths
    }

    manifest_path = version_dir / "corpus_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    return manifest

def verify_corpus_integrity(version_dir: Path) -> bool:
    """
    Verify checksums match manifest.
    """
    manifest_path = version_dir / "corpus_manifest.json"
    manifest = json.loads(manifest_path.read_text())

    for source_name, source_info in manifest["sources"].items():
        if "sha256" not in source_info:
            continue

        file_path = version_dir / "sources" / source_info["file"]
        actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()

        if actual_hash != source_info["sha256"]:
            print(f"Checksum mismatch: {source_name}")
            return False

    chunks_path = version_dir / "chunks.jsonl"
    chunks_hash = hashlib.sha256(chunks_path.read_bytes()).hexdigest()
    if f"sha256:{chunks_hash}" != manifest["checksums"].get("chunks_file"):
        print("Checksum mismatch: chunks.jsonl")
        return False

    vector_checksums = manifest["checksums"].get("vector_index", {})
    for artifact_name, expected_hash in vector_checksums.items():
        artifact_path = version_dir / artifact_name
        actual_hash = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
        if f"sha256:{actual_hash}" != expected_hash:
            print(f"Checksum mismatch: {artifact_name}")
            return False

    return True
```

### Linking Evals to Corpus Version

When running evaluations, always record the corpus version:

```python
eval_result = {
    "eval_run_id": "eval-2025-01-16-001",
    "corpus_version": "corpus-2025-01-15",  # From manifest
    "model": "claude-opus-4-5",
    "metrics": {
        "citation_accuracy": 0.92,
        "hallucination_rate": 0.03,
        "retrieval_recall": 0.87
    },
    "timestamp": "2025-01-16T10:30:00Z"
}
```

This enables queries like:
- "Show all eval runs for corpus-2025-01-15"
- "Compare retrieval recall across corpus versions"
- "Which corpus version had the regression?"

---

## Custom Document Ingestion

### User-Provided Documents

Allow users to add their own documents (e.g., CRA notices, accountant memos, provincial tax guides).

### Supported Formats

- **PDF** - Extract with `pdfplumber` or `pypdf`
- **Text** - Plain .txt files
- **HTML** - Parse with BeautifulSoup
- **Markdown** - Parse with `markdown` library

### Upload Interface

```python
def ingest_custom_document(file_path, metadata):
    """
    Ingest user-uploaded document

    metadata should include:
    - title: Document title
    - source: Source description
    - date: Document date
    - tags: List of tags (e.g., ["RRSP", "2024"])
    """
    # Detect format
    ext = file_path.suffix.lower()

    if ext == '.pdf':
        text = extract_pdf(file_path)
    elif ext in ['.txt', '.md']:
        text = file_path.read_text()
    elif ext in ['.html', '.htm']:
        text = extract_html(file_path)
    else:
        raise ValueError(f"Unsupported format: {ext}")

    # Chunk document
    chunks = chunk_generic_document(text, max_tokens=1500)

    # Add metadata to each chunk
    for i, chunk in enumerate(chunks):
        chunk['metadata'].update({
            'source': metadata['title'],
            'custom_document': True,
            'upload_date': datetime.now().isoformat(),
            'tags': metadata.get('tags', []),
            'chunk_id': f"CUSTOM-{hash(file_path)}-{i:03d}"
        })

    # Index chunks
    index_chunks(chunks)

    return len(chunks)
```

### Security Considerations

- **Scan uploads** for malware
- **Validate file types** against whitelist
- **Limit file size** (e.g., 10MB max)
- **Sanitize filenames** to prevent path traversal
- **Isolate storage** - custom docs in separate directory
- **Mark clearly** in UI that custom docs are user-provided, not official sources

---

## Implementation Checklist

### Phase 1: Core Ingestion

- [ ] Set up Python environment with dependencies (requests, BeautifulSoup, lxml, sentence-transformers)
- [ ] Clone GitHub repo or download from Open Government Portal
- [ ] Parse Income Tax Act XML with section-aware chunking
- [ ] Parse Income Tax Regulations XML
- [ ] Generate embeddings using Mistral Embed or BGE-large
- [ ] Store in vector database (ChromaDB/FAISS/pgvector)
- [ ] Test retrieval with sample queries

### Phase 2: CRA Folios

- [ ] Build web scraper for CRA Folios index
- [ ] Create curated list of priority folios (~20)
- [ ] Scrape individual folio pages
- [ ] Extract sections as excerpts with citations
- [ ] Add disclaimer metadata (Crown copyright, excerpts only)
- [ ] Index folio excerpts alongside federal law

### Phase 3: Updates and Versioning

- [ ] Implement Legis.xml parser to check consolidation dates
- [ ] Create update detection script
- [ ] Set up scheduled task (cron/Celery) to check bi-weekly
- [ ] Implement incremental re-indexing for changed documents
- [ ] Add logging and notifications for update events
- [ ] Implement corpus versioning (manifest, checksums, directory structure)
- [ ] Create rollback script (`./scripts/corpus-manager`)
- [ ] Add integrity verification on startup
- [ ] Link eval results to corpus version

### Phase 4: Custom Documents

- [ ] Build document upload interface (CLI or web form)
- [ ] Implement PDF/HTML/text parsers
- [ ] Add metadata form for user-provided context
- [ ] Implement security validations
- [ ] Store custom docs in isolated storage
- [ ] Display "user-provided" badge in search results

### Phase 5: Testing & Validation (TDD Approach)

**Use Test-Driven Development for ingestion pipeline:**

1. **Write tests before implementation:**
   ```python
   # Test XML parsing before writing parser
   def test_parse_section_118():
       xml_sample = load_fixture('ita_section_118.xml')
       sections = parse_justice_xml(xml_sample)

       assert len(sections) == 1
       assert sections[0]['section_number'] == '118'
       assert sections[0]['title'] == 'Basic personal amount'
       assert 'For the purpose of computing' in sections[0]['content']
   ```

2. **Test chunking logic:**
   ```python
   def test_chunk_preserves_section_numbers():
       section_text = load_fixture('long_section.xml')
       chunks = chunk_section(section_text, max_tokens=1500)

       # All chunks should have section metadata
       for chunk in chunks:
           assert 'section' in chunk['metadata']
           assert 'reference' in chunk['metadata']

   def test_chunk_respects_boundaries():
       # Section 118(1) shouldn't be split from 118
       section_118 = load_fixture('section_118.xml')
       chunks = chunk_section(section_118)

       # Find chunk with subsection (1)
       subsection_chunks = [c for c in chunks if '(1)' in c['metadata']['reference']]
       assert len(subsection_chunks) > 0
   ```

3. **Test update detection:**
   ```python
   def test_detects_new_consolidation():
       old_meta = {'ITA_consolidated_date': '2024-12-01'}
       new_legis_xml = load_fixture('legis_2025_01_15.xml')

       result = check_for_updates(old_meta, new_legis_xml)

       assert result['update_available'] == True
       assert result['remote_date'] == '2025-01-15'
   ```

**Validation checklist:**

- [ ] Write test: Parse ITA Section 118 XML → extract section number, title, content
- [ ] Write test: Chunk section 118 → verify metadata preserved
- [ ] Write test: Detect updates → compare consolidation dates
- [ ] Create test queries for each document type
- [ ] Verify citation accuracy (does retrieved section support answer?)
- [ ] Check cross-reference handling (e.g., "as defined in subsection 248(1)")
- [ ] Test with edge cases (very long sections, nested paragraphs, French/English bilingual)
- [ ] Validate CRA folio scraping doesn't break on page structure changes

**Test fixtures:**

Create `tests/fixtures/` directory with:
- `ita_section_118.xml` - Real XML from Justice Laws
- `ita_section_248.xml` - Definitions section (tests cross-refs)
- `legis_2025_01_15.xml` - Sample Legis.xml for update tests
- `cra_folio_s1_f4_c2.html` - Sample CRA folio HTML

**Run tests before each commit:**
```bash
pytest tests/test_ingestion.py -v
```

---

## Resources

### Official Sources
- [Justice Laws Website](https://laws-lois.justice.gc.ca/eng/)
- [Justice Laws XML Data Dictionary](https://laws-lois.justice.gc.ca/eng/XML/index.html)
- [Consolidated Acts and Regulations - Open Government Portal](https://open.canada.ca/data/en/dataset/eb0dee21-9123-4d0d-b11d-0763fa1fb403)
- [GitHub: justicecanada/laws-lois-xml](https://github.com/justicecanada/laws-lois-xml)
- [Income Tax Folios Index](https://www.canada.ca/en/revenue-agency/services/tax/technical-information/income-tax/income-tax-folios-index.html)
- [What's New in Income Tax Folios](https://www.canada.ca/en/revenue-agency/services/tax/technical-information/income-tax/whats-new-income-tax-folios.html)

### Python Libraries
- `requests` - HTTP requests for downloading files
- `beautifulsoup4` - HTML parsing for CRA folios
- `lxml` - Fast XML parsing for Justice Laws
- `sentence-transformers` - Generate embeddings
- `chromadb` or `faiss-cpu` - Vector storage
- `pdfplumber` - PDF text extraction
- `python-magic` - File type detection

---

## Next Steps

After reading this specification, developers should:

1. Choose an initial ingestion method (recommend GitHub clone for quick start)
2. Implement XML parser with section-aware chunking
3. Generate embeddings and populate vector database
4. Test retrieval quality with sample queries
5. Iterate on chunking strategy based on retrieval performance
6. Add CRA Folios scraping once core federal law ingestion works
7. Build update detection for production deployment
