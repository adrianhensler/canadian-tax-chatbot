#!/usr/bin/env python3
"""
Full corpus ingestion pipeline.

Usage:
    python scripts/ingest_corpus.py --source path/to/I-3.3.xml
    python scripts/ingest_corpus.py --download  # Download from Justice Laws
"""

import argparse
import json
import hashlib
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.loaders.xml_parser import parse_justice_xml
from src.loaders.chunker import chunk_section
from src.retrieval.vector_store import VectorStore
from src.retrieval.embedder import EmbedderConfig


def main():
    parser = argparse.ArgumentParser(description="Ingest ITA into vector store")
    parser.add_argument("--source", type=Path, help="Path to ITA XML")
    parser.add_argument("--download", action="store_true", help="Download from Justice Laws")
    parser.add_argument("--output", type=Path, default=Path("data/corpus"))
    parser.add_argument("--use-api", action="store_true", help="Use OpenAI API for embeddings")
    parser.add_argument("--model", default="all-MiniLM-L6-v2", help="Embedding model")
    args = parser.parse_args()

    # Download if requested
    if args.download:
        xml_path = download_ita(args.output / "sources")
    elif args.source:
        xml_path = args.source
    else:
        # Default to existing downloaded file
        xml_path = Path("data/corpus/sources/I-3.3.xml")
        if not xml_path.exists():
            print("Error: No ITA XML found. Use --download or --source")
            return 1

    # Normalize embedding model selection
    if args.use_api and args.model == "all-MiniLM-L6-v2":
        args.model = "text-embedding-3-small"
        print("Note: --use-api set; defaulting embedding model to text-embedding-3-small")

    # Parse XML
    print(f"Parsing {xml_path}...")
    sections = parse_justice_xml(xml_path)
    print(f"✓ Parsed {len(sections)} sections")

    # Chunk sections
    print("Chunking sections...")
    all_chunks = []
    for i, section in enumerate(sections):
        if i % 100 == 0 and i > 0:
            print(f"  Processed {i}/{len(sections)} sections...")
        chunks = chunk_section(section, max_tokens=1500, overlap_tokens=200)
        all_chunks.extend(chunks)
    print(f"✓ Created {len(all_chunks)} chunks")

    # Create corpus version directory
    version = f"corpus-{datetime.now().strftime('%Y-%m-%d')}"
    version_dir = args.output / version
    version_dir.mkdir(parents=True, exist_ok=True)

    # Save chunks to JSONL
    chunks_path = version_dir / "chunks.jsonl"
    print(f"Saving chunks to {chunks_path}...")
    with open(chunks_path, "w") as f:
        for chunk in all_chunks:
            f.write(
                json.dumps(
                    {
                        "chunk_id": chunk.chunk_id,
                        "text": chunk.text,
                        "metadata": chunk.metadata,
                        "token_count": chunk.token_count,
                    }
                )
                + "\n"
            )
    print(f"✓ Saved chunks")

    # Initialize vector store
    print("Generating embeddings and indexing...")
    print(f"  Using model: {args.model}")
    print(f"  Using API: {args.use_api}")

    embedder_config = EmbedderConfig(
        model_name=args.model,
        use_api=args.use_api,
    )
    store = VectorStore(
        persist_directory=version_dir / "chroma",
        embedder_config=embedder_config,
    )

    # Add chunks in batches to show progress
    batch_size = 100
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i : i + batch_size]
        store.add_chunks(batch)
        print(f"  Indexed {min(i + batch_size, len(all_chunks))}/{len(all_chunks)} chunks")

    print(f"✓ Indexed {store.count()} chunks")

    # Create manifest
    print("Creating manifest...")
    manifest = create_manifest(xml_path, all_chunks, args.model)
    manifest_path = version_dir / "corpus_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"✓ Created manifest at {manifest_path}")

    # Update symlink
    current_link = args.output / "current"
    if current_link.is_symlink():
        current_link.unlink()
    elif current_link.exists():
        if current_link.is_dir():
            import shutil

            shutil.rmtree(current_link)
        else:
            current_link.unlink()
    current_link.symlink_to(version)
    print(f"✓ Updated 'current' symlink to {version}")

    print("\n" + "=" * 60)
    print("Ingestion complete!")
    print(f"Corpus version: {version}")
    print(f"Total chunks: {len(all_chunks)}")
    print(f"Location: {version_dir}")
    print("=" * 60)

    return 0


def download_ita(output_dir: Path) -> Path:
    """Download ITA XML from Justice Laws"""
    import httpx

    url = "https://laws-lois.justice.gc.ca/eng/XML/I-3.3.xml"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "I-3.3.xml"

    print(f"Downloading ITA from {url}...")
    response = httpx.get(url, timeout=60.0, follow_redirects=True)
    response.raise_for_status()

    output_path.write_bytes(response.content)
    size_mb = len(response.content) / (1024 * 1024)
    print(f"✓ Downloaded {size_mb:.2f} MB to {output_path}")

    return output_path


def create_manifest(xml_path: Path, chunks: list, model: str) -> dict:
    """Create corpus manifest with checksums"""
    xml_content = xml_path.read_bytes()
    xml_hash = hashlib.sha256(xml_content).hexdigest()

    return {
        "version": f"corpus-{datetime.now().strftime('%Y-%m-%d')}",
        "created_at": datetime.now().isoformat(),
        "sources": {"ITA": {"file": xml_path.name, "sha256": xml_hash}},
        "processing": {
            "chunk_count": len(chunks),
            "embedding_model": model,
            "chunking_config": {"max_tokens": 1500, "overlap_tokens": 200},
        },
    }


if __name__ == "__main__":
    sys.exit(main())
