"""Parser for Justice Laws XML format (ITA, Regulations)"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from lxml import etree


@dataclass
class Paragraph:
    """ITA paragraph (e.g., 118(1)(a))"""

    label: str
    text: str
    subparagraphs: list["Paragraph"] = field(default_factory=list)

    def get_reference(self, section: str, subsection: str) -> str:
        """Return ITA reference for this paragraph"""
        return f"ITA s.{section}({subsection})({self.label})"


@dataclass
class Subsection:
    """ITA subsection (e.g., 118(1))"""

    label: str
    text: str
    paragraphs: list[Paragraph] = field(default_factory=list)

    def get_reference(self, section: str) -> str:
        """Return ITA reference for this subsection"""
        return f"ITA s.{section}({self.label})"


@dataclass
class Section:
    """ITA section with hierarchical structure"""

    section_number: str
    marginal_note: str
    subsections: list[Subsection] = field(default_factory=list)

    def get_full_text(self) -> str:
        """Return reconstructed text with labels"""
        parts = [f"Section {self.section_number} - {self.marginal_note}\n"]
        for ss in self.subsections:
            parts.append(f"({ss.label}) {ss.text}")
            for p in ss.paragraphs:
                parts.append(f"  ({p.label}) {p.text}")
                for sp in p.subparagraphs:
                    parts.append(f"    ({sp.label}) {sp.text}")
        return "\n".join(parts)

    def get_reference(self) -> str:
        """Return ITA reference string"""
        return f"ITA s.{self.section_number}"


def parse_justice_xml(xml_path: Path) -> list[Section]:
    """
    Parse Justice Laws XML and extract sections.

    Args:
        xml_path: Path to XML file (full ITA or section fragment)

    Returns:
        List of Section objects with hierarchical structure
    """
    tree = etree.parse(str(xml_path))
    root = tree.getroot()

    # Handle namespace (Justice Laws uses default namespace)
    nsmap = {}
    if None in root.nsmap:
        nsmap = {"ns": root.nsmap[None]}

    sections = []

    # Find all Section elements (with or without namespace)
    if nsmap:
        section_elems = root.xpath(".//ns:Section", namespaces=nsmap)
    else:
        section_elems = root.findall(".//Section")

    for section_elem in section_elems:
        sections.append(_parse_section(section_elem, nsmap))

    return sections


def _parse_section(section_elem, nsmap: dict) -> Section:
    """Parse a single Section element"""
    label = _get_text(section_elem, "Label", nsmap) or ""
    label = label.strip("()")  # Remove parentheses from labels
    marginal = _get_text(section_elem, "MarginalNote", nsmap) or ""

    subsections = []

    # Find subsections
    if nsmap:
        ss_elems = section_elem.xpath("./ns:Subsection", namespaces=nsmap)
    else:
        ss_elems = section_elem.findall("./Subsection")

    for ss_elem in ss_elems:
        subsections.append(_parse_subsection(ss_elem, nsmap))

    return Section(
        section_number=label,
        marginal_note=marginal,
        subsections=subsections,
    )


def _parse_subsection(ss_elem, nsmap: dict) -> Subsection:
    """Parse a Subsection element"""
    label = _get_text(ss_elem, "Label", nsmap) or ""
    label = label.strip("()")  # Remove parentheses from labels
    text = _get_text(ss_elem, "Text", nsmap) or ""

    paragraphs = []

    # Find paragraphs
    if nsmap:
        p_elems = ss_elem.xpath("./ns:Paragraph", namespaces=nsmap)
    else:
        p_elems = ss_elem.findall("./Paragraph")

    for p_elem in p_elems:
        paragraphs.append(_parse_paragraph(p_elem, nsmap))

    return Subsection(label=label, text=text, paragraphs=paragraphs)


def _parse_paragraph(p_elem, nsmap: dict) -> Paragraph:
    """Parse a Paragraph element (recursive for subparagraphs)"""
    label = _get_text(p_elem, "Label", nsmap) or ""
    label = label.strip("()")  # Remove parentheses from labels
    text = _get_text(p_elem, "Text", nsmap) or ""

    subparas = []

    # Find subparagraphs (recursive)
    if nsmap:
        sp_elems = p_elem.xpath("./ns:Subparagraph", namespaces=nsmap)
    else:
        sp_elems = p_elem.findall("./Subparagraph")

    for sp_elem in sp_elems:
        # Treat subparagraphs as paragraphs structurally
        sp_label = _get_text(sp_elem, "Label", nsmap) or ""
        sp_label = sp_label.strip("()")  # Remove parentheses from labels
        sp_text = _get_text(sp_elem, "Text", nsmap) or ""
        subparas.append(Paragraph(label=sp_label, text=sp_text))

    return Paragraph(label=label, text=text, subparagraphs=subparas)


def _get_text(elem, tag: str, nsmap: dict) -> Optional[str]:
    """Get text content of child element"""
    if nsmap:
        children = elem.xpath(f"./ns:{tag}", namespaces=nsmap)
        if children:
            return children[0].text
    else:
        child = elem.find(tag)
        if child is not None:
            return child.text
    return None
