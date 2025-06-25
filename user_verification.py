"""
User Verification System - Auto-Pattern Learning dari User Corrections
Mengimplementasikan visual verification dan auto-pattern generation
"""

import cv2
import numpy as np
import base64
import pandas as pd
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
from pattern_manager import PatternManager
from document_type_discovery import DocumentTypeCandidate

logger = logging.getLogger(__name__)


@dataclass
class VerificationRegion:
    """Region yang perlu diverifikasi user"""

    region_id: int
    text: str
    bbox: Tuple[int, int, int, int]
    confidence: float
    region_type: str
    cropped_image_b64: str
    priority_score: float
    document_id: str


@dataclass
class UserCorrection:
    """User correction untuk region"""

    region_id: int
    original_text: str
    corrected_text: str
    user_id: str
    document_id: str
    confidence: float
    region_type: str


@dataclass
class DocumentTypeValidation:
    """User validation untuk document type suggestion"""

    document_id: str
    suggested_type: str
    user_action: str  # 'accept', 'reject', 'modify'
    final_type: str
    user_id: str
    confidence: float
    keywords: List[str]


class UserVerificationSystem:
    """
    Sistem verifikasi user untuk auto-pattern learning
    """

    def __init__(self, pattern_manager: PatternManager, pattern_dir: str = None):
        self.pattern_manager = pattern_manager
        self.pattern_dir = Path(pattern_dir) if pattern_dir else Path(".")
        self.verification_threshold = 0.5  # Confidence threshold untuk flagging

    def get_regions_for_verification(
        self, regions: List[Dict], image: np.ndarray, document_id: str
    ) -> List[VerificationRegion]:
        """Dapatkan regions yang perlu diverifikasi berdasarkan priority"""
        verification_regions = []

        for i, region in enumerate(regions):
            priority_score = self._calculate_priority_score(region)

            if priority_score > 0.3:  # Threshold untuk verification
                cropped_b64 = self._crop_region_image(image, region["bbox"])

                verification_regions.append(
                    VerificationRegion(
                        region_id=i,
                        text=region["text"],
                        bbox=region["bbox"],
                        confidence=region["confidence"],
                        region_type=region["region_type"],
                        cropped_image_b64=cropped_b64,
                        priority_score=priority_score,
                        document_id=document_id,
                    )
                )

        # Sort by priority score (highest first)
        verification_regions.sort(key=lambda x: x.priority_score, reverse=True)
        return verification_regions[:10]  # Limit to top 10

    def _calculate_priority_score(self, region: Dict) -> float:
        """Hitung priority score untuk region"""
        score = 0.0

        # Low confidence regions
        if region["confidence"] < self.verification_threshold:
            score += 0.4

        # Handwritten regions
        if region["region_type"] == "handwritten":
            score += 0.3

        # Suspicious patterns
        text = region["text"]
        suspicious_chars = ["`", "~", "|", "io8", "9025", "Fcbruar"]
        if any(char in text for char in suspicious_chars):
            score += 0.3

        # Short text (likely errors)
        if len(text.strip()) < 5:
            score += 0.2

        return min(score, 1.0)

    def _crop_region_image(
        self, image: np.ndarray, bbox: Tuple[int, int, int, int], padding: int = 10
    ) -> str:
        """Crop region dari image dengan padding dan convert ke base64"""
        try:
            x1, y1, x2, y2 = bbox
            h, w = image.shape[:2]

            # Add padding
            x1 = max(0, x1 - padding)
            y1 = max(0, y1 - padding)
            x2 = min(w, x2 + padding)
            y2 = min(h, y2 + padding)

            # Crop image
            cropped = image[y1:y2, x1:x2]

            # Resize if too small
            if cropped.shape[0] < 50 or cropped.shape[1] < 50:
                scale = max(50 / cropped.shape[0], 50 / cropped.shape[1])
                new_h, new_w = int(cropped.shape[0] * scale), int(
                    cropped.shape[1] * scale
                )
                cropped = cv2.resize(cropped, (new_w, new_h))

            # Convert to base64
            _, buffer = cv2.imencode(".png", cropped)
            img_b64 = base64.b64encode(buffer).decode("utf-8")

            return img_b64

        except Exception as e:
            logger.error(f"Error cropping region: {e}")
            return ""

    def process_user_correction(self, correction: UserCorrection) -> List[Dict]:
        """Process user correction dan generate patterns"""
        patterns = self._generate_patterns_from_correction(correction)

        if patterns:
            self._update_pattern_csv(patterns)
            self.pattern_manager.reload_patterns()
            logger.info(f"Generated {len(patterns)} patterns from user correction")

        return patterns

    def _generate_patterns_from_correction(
        self, correction: UserCorrection
    ) -> List[Dict]:
        """Generate patterns dari user correction"""
        patterns = []
        original = correction.original_text.strip()
        corrected = correction.corrected_text.strip()

        if not original or not corrected or original == corrected:
            return patterns

        # Direct replacement pattern
        pattern = {
            "Wrong_Text": original,
            "Correct_Text": corrected,
            "Category": self._detect_pattern_category(original, corrected),
            "Context_Type": self._detect_context_type(correction),
            "Priority": 1,
            "Confidence_Boost": 0.2,
            "Enabled": True,
            "Language": "ANY",
            "Notes": f"Auto-generated from user correction",
            "Created_Date": datetime.now().strftime("%Y-%m-%d"),
            "Last_Modified": datetime.now().strftime("%Y-%m-%d"),
        }
        patterns.append(pattern)

        # Word-level patterns
        original_words = original.split()
        corrected_words = corrected.split()

        if len(original_words) == len(corrected_words):
            for orig_word, corr_word in zip(original_words, corrected_words):
                if orig_word != corr_word and len(orig_word) > 1:
                    patterns.append(
                        {
                            "Wrong_Text": orig_word,
                            "Correct_Text": corr_word,
                            "Category": self._detect_pattern_category(
                                orig_word, corr_word
                            ),
                            "Context_Type": "any",
                            "Priority": 2,
                            "Confidence_Boost": 0.15,
                            "Enabled": True,
                            "Language": "ANY",
                            "Notes": f"Word-level auto-pattern",
                            "Created_Date": datetime.now().strftime("%Y-%m-%d"),
                            "Last_Modified": datetime.now().strftime("%Y-%m-%d"),
                        }
                    )

        return patterns

    def _detect_pattern_category(self, original: str, corrected: str) -> str:
        """Detect category dari pattern"""
        # Month patterns
        months = [
            "januari",
            "februari",
            "maret",
            "april",
            "mei",
            "juni",
            "juli",
            "agustus",
            "september",
            "oktober",
            "november",
            "desember",
        ]
        if any(month in corrected.lower() for month in months):
            return "Month"

        # Number patterns
        if corrected.isdigit() or original.isdigit():
            return "Number"

        # Punctuation patterns (single non-alphanumeric character)
        if len(original) == 1 and not original.isalnum():
            return "Punctuation"

        # Character patterns (short replacements, not punctuation)
        if len(original) <= 2 and len(corrected) <= 2 and original.isalnum():
            return "Character"

        return "Text"

    def _detect_context_type(self, correction: UserCorrection) -> str:
        """Detect context type dari correction"""
        text = correction.corrected_text.lower()

        # Date context
        months = ["januari", "februari", "maret", "april", "mei", "juni"]
        if any(month in text for month in months):
            return "date"

        # Number context
        if correction.corrected_text.replace(".", "").replace("/", "").isdigit():
            return "number"

        # Document number context
        if any(char.isdigit() for char in text) and any(
            char.isalpha() for char in text
        ):
            return "document_number"

        return "any"

    def _update_pattern_csv(self, patterns: List[Dict]):
        """Update OCR_Patterns_Template.csv dengan patterns baru"""
        try:
            csv_path = self.pattern_dir / "OCR_Patterns_Template.csv"

            # Load existing patterns
            if csv_path.exists():
                df = pd.read_csv(csv_path)
                next_id = df["Pattern_ID"].max() + 1
            else:
                df = pd.DataFrame()
                next_id = 1

            # Add new patterns
            for pattern in patterns:
                pattern["Pattern_ID"] = next_id
                next_id += 1

                # Check for duplicates
                if not df.empty:
                    duplicate = df[
                        (df["Wrong_Text"] == pattern["Wrong_Text"])
                        & (df["Correct_Text"] == pattern["Correct_Text"])
                    ]
                    if not duplicate.empty:
                        continue  # Skip duplicate

                df = pd.concat([df, pd.DataFrame([pattern])], ignore_index=True)

            # Save updated CSV
            df.to_csv(csv_path, index=False)
            logger.info(f"Updated {csv_path} with {len(patterns)} new patterns")

        except Exception as e:
            logger.error(f"Error updating pattern CSV: {e}")

    def process_document_type_validation(
        self, validation: DocumentTypeValidation
    ) -> bool:
        """Process user validation untuk document type suggestion"""
        try:
            if validation.user_action == "accept":
                return self._add_new_document_type(
                    validation.final_type, validation.keywords, validation.confidence
                )
            elif validation.user_action == "modify":
                return self._add_new_document_type(
                    validation.final_type, validation.keywords, validation.confidence
                )
            # 'reject' - do nothing
            return True

        except Exception as e:
            logger.error(f"Error processing document type validation: {e}")
            return False

    def _add_new_document_type(
        self, doc_type: str, keywords: List[str], confidence: float
    ) -> bool:
        """Add new document type to CSV"""
        try:
            csv_path = self.pattern_dir / "Document_Types_Template.csv"

            # Load existing types
            if csv_path.exists():
                df = pd.read_csv(csv_path)
            else:
                df = pd.DataFrame()

            # Check for duplicates
            if not df.empty and doc_type in df["Document_Type"].values:
                logger.info(f"Document type already exists: {doc_type}")
                return False

            # Create new entry
            new_entry = {
                "Document_Type": doc_type,
                "Keywords": ",".join(keywords[:10]),
                "Layout_Indicators": "standard_layout",
                "OCR_Engine_Priority": "tesseract_easyocr",
                "Preprocessing_Profile": "default",
                "Confidence_Threshold": max(0.25, confidence - 0.1),
                "Language_Mix": "ID_EN",
                "Priority": 3,
                "Enabled": True,
                "Description": f"Auto-discovered document type",
                "Sample_Patterns": "Auto-generated",
            }

            # Add to dataframe
            df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)

            # Save CSV
            df.to_csv(csv_path, index=False)
            logger.info(f"Added new document type: {doc_type}")

            # Reload pattern manager
            self.pattern_manager.reload_patterns()
            return True

        except Exception as e:
            logger.error(f"Error adding document type: {e}")
            return False

    def get_verification_stats(self) -> Dict[str, Any]:
        """Get verification statistics"""
        return {
            "verification_threshold": self.verification_threshold,
            "pattern_stats": self.pattern_manager.get_pattern_stats(),
            "last_updated": datetime.now().isoformat(),
        }


def create_verification_system(
    pattern_manager: PatternManager, pattern_dir: str = None
) -> UserVerificationSystem:
    """Factory function untuk UserVerificationSystem"""
    return UserVerificationSystem(pattern_manager, pattern_dir)
