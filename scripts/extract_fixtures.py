#!/usr/bin/env python3
"""
Extract test fixture sections from ITA XML.

Usage:
    python scripts/extract_fixtures.py
"""

from pathlib import Path
from lxml import etree

def main():
    ita_path = Path("data/corpus/sources/I-3.3.xml")
    fixtures_dir = Path("tests/fixtures")
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    # Sections to extract
    sections_to_extract = {
        "118": "ita_section_118.xml",  # Personal credits (basic personal amount)
        "146": "ita_section_146.xml",  # RRSP
        "248": "ita_section_248.xml",  # Definitions
    }

    print(f"Parsing {ita_path}...")
    tree = etree.parse(str(ita_path))
    root = tree.getroot()

    # Define namespace (Justice Laws XML uses default namespace)
    nsmap = {'ns': root.nsmap[None]} if None in root.nsmap else {}

    for section_num, filename in sections_to_extract.items():
        print(f"Extracting section {section_num}...")

        # Find the section
        if nsmap:
            sections = root.xpath(f".//ns:Section[ns:Label/text()='{section_num}']", namespaces=nsmap)
        else:
            sections = root.xpath(f".//Section[Label/text()='{section_num}']")

        if not sections:
            print(f"  ✗ Section {section_num} not found")
            continue

        section_elem = sections[0]

        # Create a new document with just this section
        fixture_root = etree.Element("Statute")
        fixture_root.append(section_elem)

        # Write to file
        output_path = fixtures_dir / filename
        with open(output_path, 'wb') as f:
            f.write(etree.tostring(fixture_root, pretty_print=True, xml_declaration=True, encoding='UTF-8'))

        print(f"  ✓ Saved to {output_path}")

    print("Fixture extraction complete!")
    return 0

if __name__ == "__main__":
    exit(main())
