"""
Document Section Detection & Extraction System
Menangani multi-section documents dengan selective extraction
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SectionType(Enum):
    DISPOSISI = "disposisi"
    NOTA_DINAS = "nota_dinas"
    LAMPIRAN_TEXT = "lampiran_text"
    LAMPIRAN_TABEL = "lampiran_tabel"
    SURAT_PENDUKUNG = "surat_pendukung"
    COVER_LETTER = "cover_letter"
    ATTACHMENT = "attachment"
    REFERENCE = "reference"


@dataclass
class DocumentSection:
    """Representasi section dalam dokumen"""

    section_type: SectionType
    page_start: int
    page_end: int
    title: str
    content: str
    confidence: float
    keywords: List[str]
    patterns: List[str]


class DocumentSectionDetector:
    """
    Detector untuk multi-section documents
    """

    def __init__(self):
        self.section_patterns = self._build_section_patterns()
        self.page_break_indicators = [
            "halaman",
            "page",
            "lembar",
            "---",
            "===",
            "lampiran",
            "attachment",
            "surat",
            "nota",
        ]

    def _build_section_patterns(self) -> Dict[SectionType, Dict]:
        """Build patterns untuk setiap section type"""
        return {
            SectionType.DISPOSISI: {
                "keywords": [
                    "disposisi",
                    "diteruskan",
                    "kepada",
                    "untuk",
                    "tindak lanjut",
                ],
                "title_patterns": [
                    r"lembar\s+disposisi",
                    r"disposisi",
                    r"tindak\s+lanjut",
                ],
                "structure_indicators": ["kepada:", "dari:", "perihal:", "tanggal:"],
                "position": "early",  # Usually at beginning
            },
            SectionType.NOTA_DINAS: {
                "keywords": ["nota dinas", "memorandum", "kepada", "dari", "perihal"],
                "title_patterns": [r"nota\s+dinas", r"memorandum"],
                "structure_indicators": ["kepada:", "dari:", "perihal:", "nomor:"],
                "position": "early",
            },
            SectionType.LAMPIRAN_TEXT: {
                "keywords": ["lampiran", "attachment", "terlampir", "sebagai berikut"],
                "title_patterns": [r"lampiran\s*\d*", r"attachment"],
                "structure_indicators": ["lampiran:", "terlampir:", "sebagai berikut:"],
                "position": "middle",
            },
            SectionType.LAMPIRAN_TABEL: {
                "keywords": ["tabel", "daftar", "data", "statistik", "laporan"],
                "title_patterns": [r"tabel\s*\d*", r"daftar", r"data"],
                "structure_indicators": [
                    "no.",
                    "nama",
                    "jumlah",
                    "total",
                    "|",
                    "kolom",
                ],
                "position": "middle",
            },
            SectionType.SURAT_PENDUKUNG: {
                "keywords": ["surat", "referensi", "pendukung", "dengan hormat"],
                "title_patterns": [r"surat\s+(pendukung|referensi)", r"referensi"],
                "structure_indicators": ["dengan hormat", "demikian", "hormat kami"],
                "position": "late",
            },
        }

    def detect_sections(self, pages_content: List[str]) -> List[DocumentSection]:
        """Detect sections dalam multi-page document"""
        sections = []

        for page_idx, content in enumerate(pages_content):
            detected_sections = self._analyze_page_content(content, page_idx)
            sections.extend(detected_sections)

        # Merge adjacent pages dengan same section type
        merged_sections = self._merge_adjacent_sections(sections)

        return merged_sections

    def _analyze_page_content(
        self, content: str, page_idx: int
    ) -> List[DocumentSection]:
        """Analyze single page content"""
        sections = []
        content_lower = content.lower()

        for section_type, patterns in self.section_patterns.items():
            confidence = self._calculate_section_confidence(content_lower, patterns)

            if confidence > 0.3:  # Threshold untuk detection
                title = self._extract_section_title(content, patterns["title_patterns"])
                keywords = self._extract_matching_keywords(
                    content_lower, patterns["keywords"]
                )

                section = DocumentSection(
                    section_type=section_type,
                    page_start=page_idx,
                    page_end=page_idx,
                    title=title,
                    content=content,
                    confidence=confidence,
                    keywords=keywords,
                    patterns=patterns["title_patterns"],
                )
                sections.append(section)

        return sections

    def _calculate_section_confidence(self, content: str, patterns: Dict) -> float:
        """Calculate confidence untuk section detection"""
        score = 0.0

        # Keyword matching
        keyword_matches = sum(1 for kw in patterns["keywords"] if kw in content)
        if patterns["keywords"]:
            score += (keyword_matches / len(patterns["keywords"])) * 0.4

        # Title pattern matching
        title_matches = sum(
            1
            for pattern in patterns["title_patterns"]
            if re.search(pattern, content, re.IGNORECASE)
        )
        if patterns["title_patterns"]:
            score += (title_matches / len(patterns["title_patterns"])) * 0.3

        # Structure indicators
        structure_matches = sum(
            1 for indicator in patterns["structure_indicators"] if indicator in content
        )
        if patterns["structure_indicators"]:
            score += (structure_matches / len(patterns["structure_indicators"])) * 0.3

        return min(score, 1.0)

    def _extract_section_title(self, content: str, title_patterns: List[str]) -> str:
        """Extract title dari section"""
        for pattern in title_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                # Get surrounding context
                start = max(0, match.start() - 20)
                end = min(len(content), match.end() + 50)
                context = content[start:end].strip()

                # Extract clean title
                lines = context.split("\n")
                for line in lines:
                    if re.search(pattern, line, re.IGNORECASE):
                        return line.strip()

        return "Unknown Section"

    def _extract_matching_keywords(
        self, content: str, keywords: List[str]
    ) -> List[str]:
        """Extract keywords yang match dari content"""
        return [kw for kw in keywords if kw in content]

    def _merge_adjacent_sections(
        self, sections: List[DocumentSection]
    ) -> List[DocumentSection]:
        """Merge adjacent pages dengan same section type"""
        if not sections:
            return sections

        merged = []
        current_section = sections[0]

        for next_section in sections[1:]:
            if (
                current_section.section_type == next_section.section_type
                and next_section.page_start == current_section.page_end + 1
            ):
                # Merge sections
                current_section.page_end = next_section.page_end
                current_section.content += "\n\n" + next_section.content
                current_section.confidence = max(
                    current_section.confidence, next_section.confidence
                )
            else:
                merged.append(current_section)
                current_section = next_section

        merged.append(current_section)
        return merged

    def extract_section(
        self, sections: List[DocumentSection], section_type: SectionType
    ) -> Optional[DocumentSection]:
        """Extract specific section dari document"""
        matching_sections = [s for s in sections if s.section_type == section_type]

        if matching_sections:
            # Return section dengan confidence tertinggi
            return max(matching_sections, key=lambda x: x.confidence)

        return None

    def extract_multiple_sections(
        self, sections: List[DocumentSection], section_types: List[SectionType]
    ) -> List[DocumentSection]:
        """Extract multiple sections sekaligus"""
        result = []
        for section_type in section_types:
            section = self.extract_section(sections, section_type)
            if section:
                result.append(section)
        return result


class DocumentSectionAPI:
    """
    API wrapper untuk section detection dan extraction
    """

    def __init__(self):
        self.detector = DocumentSectionDetector()

    def process_multi_section_document(self, pages_content: List[str]) -> Dict:
        """Process multi-section document dan return structured result"""
        sections = self.detector.detect_sections(pages_content)

        result = {
            "total_pages": len(pages_content),
            "sections_detected": len(sections),
            "sections": [],
            "section_map": {},
        }

        for section in sections:
            section_data = {
                "type": section.section_type.value,
                "title": section.title,
                "pages": f"{section.page_start + 1}-{section.page_end + 1}",
                "confidence": section.confidence,
                "keywords": section.keywords,
                "content_length": len(section.content),
            }
            result["sections"].append(section_data)
            result["section_map"][section.section_type.value] = section_data

        return result

    def get_section_content(
        self, pages_content: List[str], section_type: str
    ) -> Optional[Dict]:
        """Get specific section content"""
        sections = self.detector.detect_sections(pages_content)

        try:
            target_type = SectionType(section_type)
            section = self.detector.extract_section(sections, target_type)

            if section:
                return {
                    "type": section.section_type.value,
                    "title": section.title,
                    "content": section.content,
                    "pages": f"{section.page_start + 1}-{section.page_end + 1}",
                    "confidence": section.confidence,
                    "keywords": section.keywords,
                }
        except ValueError:
            logger.error(f"Invalid section type: {section_type}")

        return None


def create_section_detector() -> DocumentSectionDetector:
    """Factory function"""
    return DocumentSectionDetector()


def create_section_api() -> DocumentSectionAPI:
    """Factory function untuk API"""
    return DocumentSectionAPI()
