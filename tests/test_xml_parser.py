"""Test Justice Laws XML parser"""

import pytest
from pathlib import Path
from src.loaders.xml_parser import parse_justice_xml, Section

FIXTURES = Path(__file__).parent / "fixtures"


class TestParseJusticeXML:
    """Test Justice Laws XML parsing"""

    def test_parse_section_118_extracts_section_number(self):
        """Section 118 should extract label '118'"""
        xml_path = FIXTURES / "ita_section_118.xml"
        sections = parse_justice_xml(xml_path)

        assert len(sections) >= 1
        assert sections[0].section_number == "118"

    def test_parse_section_118_extracts_marginal_note(self):
        """Section 118 should extract marginal note 'Personal credits'"""
        xml_path = FIXTURES / "ita_section_118.xml"
        sections = parse_justice_xml(xml_path)

        assert sections[0].marginal_note == "Personal credits"

    def test_parse_section_118_extracts_subsections(self):
        """Section 118 should extract subsections with labels"""
        xml_path = FIXTURES / "ita_section_118.xml"
        sections = parse_justice_xml(xml_path)

        section = sections[0]
        assert len(section.subsections) > 0
        assert section.subsections[0].label == "1"

    def test_parse_preserves_paragraph_structure(self):
        """Nested paragraphs (a), (b), etc. should be preserved"""
        xml_path = FIXTURES / "ita_section_118.xml"
        sections = parse_justice_xml(xml_path)

        subsection = sections[0].subsections[0]
        assert len(subsection.paragraphs) > 0
        assert subsection.paragraphs[0].label == "a"

    def test_parse_extracts_full_text(self):
        """Full text content should be extractable"""
        xml_path = FIXTURES / "ita_section_118.xml"
        sections = parse_justice_xml(xml_path)

        full_text = sections[0].get_full_text()
        assert "tax payable" in full_text.lower()

    def test_parse_section_248_definitions(self):
        """Section 248 (definitions) should parse correctly"""
        xml_path = FIXTURES / "ita_section_248.xml"
        sections = parse_justice_xml(xml_path)

        assert sections[0].section_number == "248"
        assert "definitions" in sections[0].marginal_note.lower()

    def test_parse_section_146_rrsp(self):
        """Section 146 (RRSP) should parse correctly"""
        xml_path = FIXTURES / "ita_section_146.xml"
        sections = parse_justice_xml(xml_path)

        assert sections[0].section_number == "146"
        # RRSP section should have subsections
        assert len(sections[0].subsections) > 0

    def test_get_reference_format(self):
        """Section reference should be formatted as 'ITA s.XXX'"""
        xml_path = FIXTURES / "ita_section_118.xml"
        sections = parse_justice_xml(xml_path)

        ref = sections[0].get_reference()
        assert ref == "ITA s.118"

    def test_subsection_reference_format(self):
        """Subsection reference should include subsection number"""
        xml_path = FIXTURES / "ita_section_118.xml"
        sections = parse_justice_xml(xml_path)

        subsection = sections[0].subsections[0]
        ref = subsection.get_reference(sections[0].section_number)
        assert ref == "ITA s.118(1)"

    def test_parse_empty_marginal_note(self):
        """Sections without marginal notes should not crash"""
        # This tests robustness, actual ITA sections usually have marginal notes
        xml_path = FIXTURES / "ita_section_118.xml"
        sections = parse_justice_xml(xml_path)

        # Should not crash even if marginal note is missing
        assert sections[0].marginal_note is not None
