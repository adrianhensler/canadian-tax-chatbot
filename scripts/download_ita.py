#!/usr/bin/env python3
"""
Download Income Tax Act XML from Justice Laws.

Usage:
    python scripts/download_ita.py
"""

import httpx
from pathlib import Path


def main():
    # ITA URL
    url = "https://laws-lois.justice.gc.ca/eng/XML/I-3.3.xml"

    # Output directory
    output_dir = Path("data/corpus/sources")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "I-3.3.xml"

    print(f"Downloading Income Tax Act from {url}...")

    try:
        response = httpx.get(url, timeout=60.0, follow_redirects=True)
        response.raise_for_status()

        output_path.write_bytes(response.content)

        size_mb = len(response.content) / (1024 * 1024)
        print(f"✓ Downloaded {size_mb:.2f} MB to {output_path}")

    except httpx.HTTPError as e:
        print(f"✗ HTTP error: {e}")
        return 1
    except Exception as e:
        print(f"✗ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
