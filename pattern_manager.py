"""
Pattern Manager - Excel-based OCR Pattern Management System
Mengelola pattern corrections, spatial patterns, dan context rules
"""

import pandas as pd
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)


class PatternType(Enum):
    OCR_CORRECTION = "ocr_correction"
    SPATIAL_PATTERN = "spatial_pattern"
    CONTEXT_RULE = "context_rule"
    DOCUMENT_TYPE = "document_type"


@dataclass
class OCRPattern:
    """OCR Correction Pattern"""

    pattern_id: int
    wrong_text: str
    correct_text: str
    context_type: str
    priority: int
    confidence_boost: float
    enabled: bool
    language: str
    notes: str


@dataclass
class SpatialPattern:
    """Spatial Position Pattern"""

    pattern_id: int
    region_name: str
    position_type: str
    x_range: Tuple[float, float]
    y_range: Tuple[float, float]
    content_type: str
    confidence_boost: float
    ocr_config: str
    priority: int
    enabled: bool
    document_type: str


@dataclass
class ContextRule:
    """Context Validation Rule"""

    rule_id: int
    rule_name: str
    trigger_pattern: str
    context_window: str
    validation_logic: str
    action_type: str
    action_value: str
    priority: int
    enabled: bool
    language: str


class PatternManager:
    """
    Manages OCR patterns from Excel/CSV files
    Provides pattern matching and correction capabilities
    """

    def __init__(self, pattern_dir: str = None):
        self.pattern_dir = Path(pattern_dir) if pattern_dir else Path(".")
        self.ocr_patterns: List[OCRPattern] = []
        self.spatial_patterns: List[SpatialPattern] = []
        self.context_rules: List[ContextRule] = []
        self.document_types: Dict[str, Dict] = {}
        self.performance_metrics: Dict[int, Dict] = {}

        self._load_all_patterns()

    def _load_all_patterns(self):
        """Load all pattern files"""
        try:
            self._load_ocr_patterns()
            self._load_spatial_patterns()
            self._load_context_rules()
            self._load_document_types()
            self._load_performance_metrics()
            logger.info(
                f"Loaded {len(self.ocr_patterns)} OCR patterns, "
                f"{len(self.spatial_patterns)} spatial patterns, "
                f"{len(self.context_rules)} context rules"
            )
        except Exception as e:
            logger.error(f"Error loading patterns: {e}")
            # Continue with empty patterns if files don't exist

    def _load_ocr_patterns(self):
        """Load OCR correction patterns"""
        file_path = self.pattern_dir / "OCR_Patterns_Template.csv"
        if not file_path.exists():
            logger.warning(f"OCR patterns file not found: {file_path}")
            return

        try:
            df = pd.read_csv(file_path, on_bad_lines="skip")
            for _, row in df.iterrows():
                if row.get("Enabled", True):
                    pattern = OCRPattern(
                        pattern_id=int(row["Pattern_ID"]),
                        wrong_text=str(row["Wrong_Text"]),
                        correct_text=str(row["Correct_Text"]),
                        context_type=str(row.get("Context_Type", "any")),
                        priority=int(row.get("Priority", 3)),
                        confidence_boost=float(row.get("Confidence_Boost", 0.1)),
                        enabled=bool(row.get("Enabled", True)),
                        language=str(row.get("Language", "ANY")),
                        notes=str(row.get("Notes", "")),
                    )
                    self.ocr_patterns.append(pattern)

            # Sort by priority
            self.ocr_patterns.sort(key=lambda x: x.priority)
            logger.info(f"Loaded {len(self.ocr_patterns)} OCR correction patterns")

        except Exception as e:
            logger.error(f"Error loading OCR patterns: {e}")

    def _load_spatial_patterns(self):
        """Load spatial position patterns"""
        file_path = self.pattern_dir / "Spatial_Patterns_Template.csv"
        if not file_path.exists():
            logger.warning(f"Spatial patterns file not found: {file_path}")
            return

        try:
            df = pd.read_csv(file_path, on_bad_lines="skip")
            for _, row in df.iterrows():
                if row.get("Enabled", True):
                    # Parse range strings like "0.7-1.0"
                    x_range = self._parse_range(str(row.get("X_Range", "0.0-1.0")))
                    y_range = self._parse_range(str(row.get("Y_Range", "0.0-1.0")))

                    pattern = SpatialPattern(
                        pattern_id=int(row["Pattern_ID"]),
                        region_name=str(row["Region_Name"]),
                        position_type=str(row["Position_Type"]),
                        x_range=x_range,
                        y_range=y_range,
                        content_type=str(row.get("Content_Type", "text")),
                        confidence_boost=float(row.get("Confidence_Boost", 0.1)),
                        ocr_config=str(row.get("OCR_Config", "mixed")),
                        priority=int(row.get("Priority", 3)),
                        enabled=bool(row.get("Enabled", True)),
                        document_type=str(row.get("Document_Type", "General")),
                    )
                    self.spatial_patterns.append(pattern)

            # Sort by priority
            self.spatial_patterns.sort(key=lambda x: x.priority)
            logger.info(f"Loaded {len(self.spatial_patterns)} spatial patterns")

        except Exception as e:
            logger.error(f"Error loading spatial patterns: {e}")

    def _load_context_rules(self):
        """Load context validation rules"""
        file_path = self.pattern_dir / "Context_Rules_Template.csv"
        if not file_path.exists():
            logger.warning(f"Context rules file not found: {file_path}")
            return

        try:
            df = pd.read_csv(file_path, on_bad_lines="skip")
            for _, row in df.iterrows():
                if row.get("Enabled", True):
                    rule = ContextRule(
                        rule_id=int(row["Rule_ID"]),
                        rule_name=str(row["Rule_Name"]),
                        trigger_pattern=str(row["Trigger_Pattern"]),
                        context_window=str(row.get("Context_Window", "any")),
                        validation_logic=str(row.get("Validation_Logic", "")),
                        action_type=str(row.get("Action_Type", "boost_confidence")),
                        action_value=str(row.get("Action_Value", "0.1")),
                        priority=int(row.get("Priority", 3)),
                        enabled=bool(row.get("Enabled", True)),
                        language=str(row.get("Language", "ANY")),
                    )
                    self.context_rules.append(rule)

            # Sort by priority
            self.context_rules.sort(key=lambda x: x.priority)
            logger.info(f"Loaded {len(self.context_rules)} context rules")

        except Exception as e:
            logger.error(f"Error loading context rules: {e}")

    def _load_document_types(self):
        """Load document type patterns"""
        file_path = self.pattern_dir / "Document_Types_Template.csv"
        if not file_path.exists():
            logger.warning(f"Document types file not found: {file_path}")
            return

        try:
            df = pd.read_csv(file_path, on_bad_lines="skip")
            for _, row in df.iterrows():
                if row.get("Enabled", True):
                    doc_type = str(row["Document_Type"])
                    self.document_types[doc_type] = {
                        "keywords": str(row.get("Keywords", "")).split(","),
                        "layout_indicators": str(row.get("Layout_Indicators", "")),
                        "ocr_engine_priority": str(
                            row.get("OCR_Engine_Priority", "easyocr_tesseract")
                        ),
                        "preprocessing_profile": str(
                            row.get("Preprocessing_Profile", "default")
                        ),
                        "confidence_threshold": float(
                            row.get("Confidence_Threshold", 0.3)
                        ),
                        "priority": int(row.get("Priority", 3)),
                    }

            logger.info(f"Loaded {len(self.document_types)} document types")

        except Exception as e:
            logger.error(f"Error loading document types: {e}")

    def _load_performance_metrics(self):
        """Load performance metrics if available"""
        file_path = self.pattern_dir / "Performance_Metrics_Template.csv"
        if not file_path.exists():
            return

        try:
            df = pd.read_csv(file_path)
            for _, row in df.iterrows():
                pattern_id = int(row["Pattern_ID"])
                self.performance_metrics[pattern_id] = {
                    "usage_count": int(row.get("Usage_Count", 0)),
                    "success_rate": float(row.get("Success_Rate", 0.0)),
                    "effectiveness_score": float(row.get("Effectiveness_Score", 0.0)),
                    "status": str(row.get("Status", "ACTIVE")),
                }

            logger.info(f"Loaded metrics for {len(self.performance_metrics)} patterns")

        except Exception as e:
            logger.error(f"Error loading performance metrics: {e}")

    def _parse_range(self, range_str: str) -> Tuple[float, float]:
        """Parse range string like '0.7-1.0' to tuple"""
        try:
            parts = range_str.split("-")
            return (float(parts[0]), float(parts[1]))
        except:
            return (0.0, 1.0)

    def apply_ocr_corrections(
        self, text: str, context: str = "any"
    ) -> Tuple[str, float]:
        """Apply OCR correction patterns to text"""
        if not text:
            return text, 0.0

        corrected_text = text
        total_boost = 0.0
        corrections_applied = 0

        for pattern in self.ocr_patterns:
            if not pattern.enabled:
                continue

            # Check context match
            if pattern.context_type != "any" and context != "any":
                if pattern.context_type != context:
                    continue

            # Apply correction
            if pattern.wrong_text in corrected_text:
                if pattern.correct_text == "EMPTY":
                    corrected_text = corrected_text.replace(pattern.wrong_text, "")
                else:
                    corrected_text = corrected_text.replace(
                        pattern.wrong_text, pattern.correct_text
                    )

                total_boost += pattern.confidence_boost
                corrections_applied += 1

                logger.debug(
                    f"Applied pattern {pattern.pattern_id}: '{pattern.wrong_text}' -> '{pattern.correct_text}'"
                )

        # Average boost if multiple corrections
        avg_boost = (
            total_boost / corrections_applied if corrections_applied > 0 else 0.0
        )

        return corrected_text, min(avg_boost, 0.5)  # Cap boost at 0.5

    def get_spatial_patterns_for_region(
        self,
        bbox: Tuple[int, int, int, int],
        image_shape: Tuple[int, int],
        document_type: str = "General",
    ) -> List[SpatialPattern]:
        """Get spatial patterns that match a region"""
        if not bbox or not image_shape:
            return []

        x1, y1, x2, y2 = bbox
        img_height, img_width = image_shape[:2]

        # Normalize coordinates to 0-1 range
        norm_x1 = x1 / img_width
        norm_y1 = y1 / img_height
        norm_x2 = x2 / img_width
        norm_y2 = y2 / img_height

        matching_patterns = []

        for pattern in self.spatial_patterns:
            if not pattern.enabled:
                continue

            # Check document type match
            if (
                pattern.document_type != "General"
                and pattern.document_type != document_type
            ):
                continue

            # Check if region overlaps with pattern area
            px1, px2 = pattern.x_range
            py1, py2 = pattern.y_range

            # Simple overlap check
            if norm_x1 <= px2 and norm_x2 >= px1 and norm_y1 <= py2 and norm_y2 >= py1:
                matching_patterns.append(pattern)

        return sorted(matching_patterns, key=lambda x: x.priority)

    def detect_document_type(self, text_content: str) -> Optional[str]:
        """Detect document type based on content"""
        if not text_content:
            return None

        text_lower = text_content.lower()
        best_match = None
        best_score = 0

        for doc_type, config in self.document_types.items():
            score = 0
            keywords = [kw.strip().lower() for kw in config["keywords"] if kw.strip()]

            for keyword in keywords:
                if keyword in text_lower:
                    score += 1

            # Normalize score by number of keywords
            if keywords:
                normalized_score = score / len(keywords)
                if normalized_score > best_score:
                    best_score = normalized_score
                    best_match = doc_type

        # Require at least 30% keyword match
        if best_score >= 0.3:
            logger.info(
                f"Detected document type: {best_match} (score: {best_score:.2f})"
            )
            return best_match

        return "General"

    def apply_context_rules(
        self, text: str, context: Dict[str, Any]
    ) -> Tuple[str, float]:
        """Apply context validation rules"""
        if not text:
            return text, 0.0

        processed_text = text
        total_boost = 0.0
        rules_applied = 0

        for rule in self.context_rules:
            if not rule.enabled:
                continue

            try:
                # Check if trigger pattern matches
                if re.search(rule.trigger_pattern, processed_text, re.IGNORECASE):
                    if rule.action_type == "boost_confidence":
                        boost_value = float(rule.action_value)
                        total_boost += boost_value
                        rules_applied += 1
                        logger.debug(
                            f"Applied context rule {rule.rule_id}: {rule.rule_name}"
                        )

                    elif rule.action_type == "replace":
                        # Apply replacement logic here
                        pass

                    elif rule.action_type == "validate_format":
                        # Apply format validation here
                        pass

            except re.error as e:
                logger.warning(f"Invalid regex in rule {rule.rule_id}: {e}")
                continue

        avg_boost = total_boost / rules_applied if rules_applied > 0 else 0.0
        return processed_text, min(avg_boost, 0.3)  # Cap boost at 0.3

    def get_pattern_stats(self) -> Dict[str, int]:
        """Get pattern statistics"""
        return {
            "ocr_patterns": len(self.ocr_patterns),
            "spatial_patterns": len(self.spatial_patterns),
            "context_rules": len(self.context_rules),
            "document_types": len(self.document_types),
            "enabled_ocr_patterns": len([p for p in self.ocr_patterns if p.enabled]),
            "enabled_spatial_patterns": len(
                [p for p in self.spatial_patterns if p.enabled]
            ),
            "enabled_context_rules": len([r for r in self.context_rules if r.enabled]),
        }

    def reload_patterns(self):
        """Reload all patterns from files"""
        logger.info("Reloading patterns...")
        self.ocr_patterns.clear()
        self.spatial_patterns.clear()
        self.context_rules.clear()
        self.document_types.clear()
        self.performance_metrics.clear()

        self._load_all_patterns()
        logger.info("Patterns reloaded successfully")

    def add_pattern_from_verification(
        self,
        wrong_text: str,
        correct_text: str,
        category: str = "Text",
        context_type: str = "any",
    ) -> bool:
        """Add new pattern from user verification"""
        try:
            # Create new pattern
            new_pattern = OCRPattern(
                pattern_id=len(self.ocr_patterns) + 1,
                wrong_text=wrong_text,
                correct_text=correct_text,
                context_type=context_type,
                priority=1,
                confidence_boost=0.2,
                enabled=True,
                language="ANY",
                notes=f"Auto-generated from user verification",
            )

            # Check for duplicates
            for existing in self.ocr_patterns:
                if (
                    existing.wrong_text == wrong_text
                    and existing.correct_text == correct_text
                ):
                    logger.info(
                        f"Pattern already exists: {wrong_text} -> {correct_text}"
                    )
                    return False

            # Add to memory
            self.ocr_patterns.append(new_pattern)
            self.ocr_patterns.sort(key=lambda x: x.priority)

            logger.info(f"Added new pattern: {wrong_text} -> {correct_text}")
            return True

        except Exception as e:
            logger.error(f"Error adding pattern from verification: {e}")
            return False


# Factory function
def create_pattern_manager(pattern_dir: str = None) -> PatternManager:
    """Create PatternManager instance"""
    return PatternManager(pattern_dir)


if __name__ == "__main__":
    # Test pattern manager
    pm = create_pattern_manager()
    stats = pm.get_pattern_stats()
    print("Pattern Manager Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Test OCR correction
    test_text = "5 Fcbruar` 9025"
    corrected, boost = pm.apply_ocr_corrections(test_text, "date")
    print(f"\nOCR Correction Test:")
    print(f"  Original: {test_text}")
    print(f"  Corrected: {corrected}")
    print(f"  Confidence Boost: {boost:.3f}")
