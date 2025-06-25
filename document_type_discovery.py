"""
Document Type Auto-Discovery System
ML-based automatic document type detection dan template enrichment
"""

import re
import pandas as pd
from collections import Counter
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class DocumentTypeCandidate:
    """Kandidat document type baru"""

    suggested_type: str
    confidence: float
    keywords: List[str]
    layout_indicators: str
    sample_patterns: List[str]
    frequency: int


class DocumentTypeDiscovery:
    """
    Auto-discovery system untuk document types baru
    """

    def __init__(self, existing_types_csv: str = "Document_Types_Template.csv"):
        self.existing_types = self._load_existing_types(existing_types_csv)
        self.keyword_patterns = self._build_keyword_patterns()
        self.min_confidence = 0.7
        self.min_frequency = 3  # Minimal 3 dokumen untuk suggest new type

    def _load_existing_types(self, csv_path: str) -> Dict:
        """Load existing document types"""
        try:
            df = pd.read_csv(csv_path, on_bad_lines="skip")
            types = {}
            for _, row in df.iterrows():
                doc_type = row["Document_Type"]
                keywords = [
                    k.strip() for k in str(row["Keywords"]).split(",") if k.strip()
                ]
                types[doc_type] = {
                    "keywords": keywords,
                    "layout_indicators": row.get("Layout_Indicators", ""),
                    "patterns": row.get("Sample_Patterns", ""),
                }
            return types
        except Exception as e:
            logger.error(f"Error loading document types: {e}")
            return {}

    def _build_keyword_patterns(self) -> Dict:
        """Build keyword patterns untuk detection"""
        patterns = {
            "legal": [
                "pengadilan",
                "hakim",
                "putusan",
                "mahkamah",
                "konstitusi",
                "puu",
                "terdakwa",
            ],
            "business": [
                "pt",
                "cv",
                "invoice",
                "faktur",
                "kontrak",
                "perjanjian",
                "npwp",
            ],
            "government": [
                "kementerian",
                "dinas",
                "menteri",
                "surat edaran",
                "peraturan",
            ],
            "academic": ["universitas", "diploma", "sarjana", "ipk", "ijazah"],
            "medical": ["rumah sakit", "dokter", "diagnosa", "resep", "pasien"],
            "financial": ["laporan", "keuangan", "neraca", "rugi", "laba"],
            "personal": ["ktp", "nik", "tempat lahir", "alamat"],
            "form": ["permohonan", "formulir", "aplikasi"],
        }
        return patterns

    def analyze_document(
        self, text_content: str, metadata: Dict
    ) -> Optional[DocumentTypeCandidate]:
        """Analyze dokumen untuk auto-discovery"""
        if not text_content:
            return None

        text_lower = text_content.lower()

        # Extract keywords
        keywords = self._extract_keywords(text_lower)

        # Detect category
        category = self._detect_category(keywords, text_lower)

        # Extract patterns
        patterns = self._extract_patterns(text_content)

        # Check if existing type
        existing_match = self._match_existing_type(keywords, text_lower)
        if existing_match and existing_match[1] > 0.8:
            return None  # Already covered by existing type

        # Generate suggestion
        if category and len(keywords) >= 3:
            suggested_type = self._generate_type_name(category, keywords)
            confidence = self._calculate_confidence(keywords, patterns, text_lower)

            if confidence >= self.min_confidence:
                return DocumentTypeCandidate(
                    suggested_type=suggested_type,
                    confidence=confidence,
                    keywords=keywords[:10],  # Top 10 keywords
                    layout_indicators=self._detect_layout_indicators(text_content),
                    sample_patterns=patterns[:3],  # Top 3 patterns
                    frequency=1,
                )

        return None

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords dari text"""
        # Remove common words
        stop_words = {
            "dan",
            "atau",
            "yang",
            "dengan",
            "untuk",
            "pada",
            "dalam",
            "dari",
            "ke",
            "di",
            "republik",
            "indonesia",
            "nomor",
            "tahun",
        }

        # Extract words (2+ chars, alphanumeric)
        words = re.findall(r"\b[a-zA-Z]{2,}\b", text)
        words = [w.lower() for w in words if w.lower() not in stop_words and len(w) > 2]

        # Count frequency
        word_freq = Counter(words)

        # Return top keywords (lower threshold for better detection)
        return [word for word, freq in word_freq.most_common(30) if freq >= 1]

    def _detect_category(self, keywords: List[str], text: str) -> Optional[str]:
        """Detect category berdasarkan keywords"""
        category_scores = {}

        for category, patterns in self.keyword_patterns.items():
            score = 0
            for pattern in patterns:
                if pattern in text:
                    score += 2
                for keyword in keywords:
                    if pattern in keyword or keyword in pattern:
                        score += 1
            category_scores[category] = score

        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            if category_scores[best_category] >= 3:
                return best_category

        return None

    def _extract_patterns(self, text: str) -> List[str]:
        """Extract common patterns dari text"""
        patterns = []

        # Number patterns
        number_patterns = re.findall(r"\b\d+[/\-\.]\w+[/\-\.]\d+\b", text)
        patterns.extend(number_patterns[:3])

        # Code patterns
        code_patterns = re.findall(r"\b[A-Z]{2,}[/\-\.]\d+\b", text)
        patterns.extend(code_patterns[:3])

        # Date patterns
        date_patterns = re.findall(r"\b\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}\b", text)
        patterns.extend(date_patterns[:2])

        return list(set(patterns))

    def _match_existing_type(
        self, keywords: List[str], text: str
    ) -> Optional[Tuple[str, float]]:
        """Check match dengan existing types"""
        best_match = None
        best_score = 0

        for doc_type, config in self.existing_types.items():
            score = 0
            type_keywords = config["keywords"]

            for keyword in type_keywords:
                if keyword.lower() in text:
                    score += 2
                for extracted_keyword in keywords:
                    if (
                        keyword.lower() in extracted_keyword
                        or extracted_keyword in keyword.lower()
                    ):
                        score += 1

            # Normalize score
            if type_keywords:
                normalized_score = score / (len(type_keywords) * 2)
                if normalized_score > best_score:
                    best_score = normalized_score
                    best_match = doc_type

        return (best_match, best_score) if best_match else None

    def _generate_type_name(self, category: str, keywords: List[str]) -> str:
        """Generate nama untuk document type baru"""
        # Capitalize category
        category_name = category.title()

        # Find distinctive keyword
        distinctive_keywords = []
        for keyword in keywords[:5]:
            if len(keyword) > 3 and keyword not in ["surat", "nomor", "tanggal"]:
                distinctive_keywords.append(keyword.title())

        if distinctive_keywords:
            return f"{category_name}_{distinctive_keywords[0]}"
        else:
            return f"{category_name}_Document"

    def _detect_layout_indicators(self, text: str) -> str:
        """Detect layout indicators"""
        indicators = []

        if re.search(r"logo|kop|header", text.lower()):
            indicators.append("official_header")
        if re.search(r"tabel|daftar", text.lower()):
            indicators.append("table_layout")
        if re.search(r"nomor|no\.|ref", text.lower()):
            indicators.append("numbered_document")
        if re.search(r"lampiran|attachment", text.lower()):
            indicators.append("attachment_format")

        return ",".join(indicators) if indicators else "standard_layout"

    def _calculate_confidence(
        self, keywords: List[str], patterns: List[str], text: str
    ) -> float:
        """Calculate confidence score"""
        score = 0.0

        # Keyword diversity
        if len(keywords) >= 5:
            score += 0.3
        elif len(keywords) >= 3:
            score += 0.2

        # Pattern presence
        if len(patterns) >= 2:
            score += 0.2
        elif len(patterns) >= 1:
            score += 0.1

        # Text length (longer = more reliable)
        if len(text) > 1000:
            score += 0.2
        elif len(text) > 500:
            score += 0.1

        # Structure indicators
        if re.search(r"nomor|tanggal|perihal", text.lower()):
            score += 0.2

        # Formal language indicators
        formal_indicators = [
            "dengan hormat",
            "demikian",
            "atas perhatian",
            "terima kasih",
        ]
        if any(indicator in text.lower() for indicator in formal_indicators):
            score += 0.1

        return min(score, 1.0)


def create_document_discovery(
    existing_types_csv: str = "Document_Types_Template.csv",
) -> DocumentTypeDiscovery:
    """Factory function"""
    return DocumentTypeDiscovery(existing_types_csv)
