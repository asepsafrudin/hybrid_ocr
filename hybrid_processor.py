"""
Hybrid Document Processor - Core OCR Pipeline
Mengimplementasikan alur kerja 3-layer untuk ekstraksi teks hybrid
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import yaml

# Image processing
import cv2
import numpy as np
from PIL import Image
from pdf2image import convert_from_path

# OCR engines
import easyocr
import pytesseract
from paddleocr import PaddleOCR

# Pattern management
from pattern_manager import PatternManager, create_pattern_manager
from document_type_discovery import DocumentTypeDiscovery, create_document_discovery
from document_section_detector import DocumentSectionDetector, create_section_detector

# Layout detection (placeholder for future implementation)
# from transformers import pipeline

logger = logging.getLogger(__name__)


class FileType(Enum):
    PDF = "pdf"
    IMAGE = "image"
    UNSUPPORTED = "unsupported"


@dataclass
class ProcessingResult:
    """Struktur hasil pemrosesan dokumen"""

    success: bool
    text_content: str
    regions: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    confidence_scores: Dict[str, float]
    error_message: Optional[str] = None


@dataclass
class TextRegion:
    """Representasi region teks dalam dokumen"""

    text: str
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    confidence: float
    region_type: str  # 'printed', 'handwritten', 'table', 'other'


class HybridProcessor:
    """
    Core processor untuk ekstraksi teks hybrid dari dokumen
    Mengimplementasikan alur kerja 3-layer: Layout Detection -> Region Processing -> Smart Merging
    """

    def __init__(
        self, config: Optional[Dict] = None, pattern_dir: Optional[str] = None
    ):
        self.config = config or self._default_config()
        self.pattern_manager = create_pattern_manager(pattern_dir)
        self.document_discovery = create_document_discovery()
        self.section_detector = create_section_detector()
        self.detected_document_type = "General"
        self.document_type_candidate = None
        self.detected_sections = []
        self._initialize_engines()

    def _default_config(self) -> Dict:
        """Konfigurasi default untuk processor"""
        return {
            "processing": {
                "layout_confidence_threshold": 0.7,
                "ocr_confidence_threshold": 0.3,
                "overlap_threshold": 0.5,
            },
            "features": {
                "enable_layout_detection": True,
                "enable_handwriting": True,
                "enable_table_detection": False,
            },
            "performance": {"max_workers": 4, "batch_size": 8, "pdf_dpi": 300},
            "ocr_engines": {
                "tesseract": {
                    "config": "--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz ",
                    "config_handwriting": "--oem 3 --psm 8",
                    "config_indonesian": "--oem 3 --psm 6 -l ind+eng",
                    "languages": ["eng", "ind"],
                },
                "easyocr": {
                    "languages": ["en", "id"],
                    "gpu": False,
                    "paragraph": False,  # Better for mixed content
                },
                "paddle": {"use_angle_cls": True, "lang": "en", "show_log": False},
            },
            "preprocessing": {
                "enhance_handwriting": True,
                "denoise": True,
                "contrast_enhancement": True,
                "morphology_operations": True,
                "gaussian_blur": False,
            },
            "post_processing": {
                "enable_corrections": True,
                "language_specific": True,
                "confidence_boost": 0.1,
            },
        }

    def _initialize_engines(self):
        """Inisialisasi semua OCR engines"""
        try:
            # Get config values
            easyocr_config = self.config.get("ocr_engines", {}).get("easyocr", {})
            paddle_config = self.config.get("ocr_engines", {}).get("paddle", {})

            # EasyOCR
            self.easyocr_reader = easyocr.Reader(
                easyocr_config.get("languages", ["en", "id"]),
                gpu=easyocr_config.get("gpu", False),
            )
            logger.info("EasyOCR initialized")

            # PaddleOCR
            self.paddle_ocr = PaddleOCR(
                use_angle_cls=paddle_config.get("use_angle_cls", True),
                lang=paddle_config.get("lang", "en"),
            )
            logger.info("PaddleOCR initialized")

            # Tesseract (sudah tersedia via pytesseract)
            logger.info("Tesseract ready")

        except Exception as e:
            logger.error(f"Error initializing OCR engines: {e}")
            raise

    def process_document(self, file_path: str) -> ProcessingResult:
        """
        Main entry point untuk memproses dokumen
        Mengikuti alur kerja: File Type Detection -> Processing -> Output
        """
        try:
            print(f"🔄 Starting document processing: {file_path}")
            logger.info(f"Starting document processing: {file_path}")

            # Step 1: Deteksi tipe file dan validasi
            file_type = self._detect_file_type(file_path)
            if file_type == FileType.UNSUPPORTED:
                return ProcessingResult(
                    success=False,
                    text_content="",
                    regions=[],
                    metadata={},
                    confidence_scores={},
                    error_message="Unsupported file type",
                )

            # Step 2: Konversi ke gambar jika diperlukan
            print(f"📄 Converting to images...")
            images = self._prepare_images(file_path, file_type)
            print(f"✅ Converted to {len(images)} images")

            # Step 3: Proses setiap halaman/gambar
            all_regions = []
            all_text = []
            pages_content = []

            for i, image in enumerate(images):
                print(f"🔍 Processing page/image {i+1}/{len(images)}")
                logger.info(f"Processing page/image {i+1}/{len(images)}")

                # Layout detection dan region-based processing
                print(f"🧠 Running OCR engines...")
                if self.config.get("features", {}).get("enable_layout_detection", True):
                    regions = self._process_with_layout_detection(image)
                else:
                    regions = self._process_dual_layer(image)
                print(f"✅ Found {len(regions)} text regions")

                all_regions.extend(regions)
                page_text = self._extract_text_from_regions(regions)
                all_text.append(page_text)
                pages_content.append(page_text)

            # Step 4: Document type detection with ML discovery
            print(f"🔍 Detecting document type...")
            combined_text = self._merge_text_results(all_text)
            self.detected_document_type = self.pattern_manager.detect_document_type(
                combined_text
            )

            # ML Auto-discovery for new document types
            if self.detected_document_type == "General":
                print(f"🤖 Running ML auto-discovery...")
                metadata = self._generate_metadata(file_path, len(images), all_regions)
                self.document_type_candidate = self.document_discovery.analyze_document(
                    combined_text, metadata
                )
                if self.document_type_candidate:
                    print(
                        f"💡 Suggested new type: {self.document_type_candidate.suggested_type} (confidence: {self.document_type_candidate.confidence:.2f})"
                    )

            print(f"📋 Document type: {self.detected_document_type}")

            # Step 4.5: Multi-section detection
            if len(pages_content) > 1:
                print(f"📑 Detecting document sections...")
                self.detected_sections = self.section_detector.detect_sections(
                    pages_content
                )
                if self.detected_sections:
                    print(f"✅ Found {len(self.detected_sections)} sections:")
                    for section in self.detected_sections:
                        print(
                            f"   • {section.section_type.value}: pages {section.page_start+1}-{section.page_end+1} (confidence: {section.confidence:.2f})"
                        )

            # Step 5: Smart merging dan post-processing with patterns
            print(f"🔧 Post-processing with patterns...")
            final_text = self._post_process_text_with_patterns(combined_text)
            print(f"✅ Processing completed! Text length: {len(final_text)} chars")

            # Step 5: Generate metadata
            metadata = self._generate_metadata(file_path, len(images), all_regions)
            if self.document_type_candidate:
                metadata["suggested_document_type"] = {
                    "type": self.document_type_candidate.suggested_type,
                    "confidence": self.document_type_candidate.confidence,
                    "keywords": self.document_type_candidate.keywords,
                    "patterns": self.document_type_candidate.sample_patterns,
                }
            if self.detected_sections:
                metadata["document_sections"] = [
                    {
                        "type": section.section_type.value,
                        "title": section.title,
                        "pages": f"{section.page_start+1}-{section.page_end+1}",
                        "confidence": section.confidence,
                        "keywords": section.keywords,
                    }
                    for section in self.detected_sections
                ]
            confidence_scores = self._calculate_confidence_scores(all_regions)

            return ProcessingResult(
                success=True,
                text_content=final_text,
                regions=[region.__dict__ for region in all_regions],
                metadata=metadata,
                confidence_scores=confidence_scores,
            )

        except Exception as e:
            logger.error(f"Error processing document {file_path}: {e}")
            return ProcessingResult(
                success=False,
                text_content="",
                regions=[],
                metadata={},
                confidence_scores={},
                error_message=str(e),
            )

    def _detect_file_type(self, file_path: str) -> FileType:
        """Deteksi tipe file berdasarkan ekstensi"""
        ext = Path(file_path).suffix.lower()
        if ext == ".pdf":
            return FileType.PDF
        elif ext in [".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp"]:
            return FileType.IMAGE
        else:
            return FileType.UNSUPPORTED

    def _prepare_images(self, file_path: str, file_type: FileType) -> List[np.ndarray]:
        """Konversi file ke format gambar untuk pemrosesan"""
        images = []

        if file_type == FileType.PDF:
            # Konversi PDF ke gambar
            pil_images = convert_from_path(file_path, dpi=300)
            for pil_img in pil_images:
                # Konversi PIL ke OpenCV format
                cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                images.append(cv_img)

        elif file_type == FileType.IMAGE:
            # Load gambar langsung
            img = cv2.imread(file_path)
            if img is not None:
                images.append(img)

        return images

    def _process_with_layout_detection(self, image: np.ndarray) -> List[TextRegion]:
        """
        Proses gambar dengan layout detection
        TODO: Implementasi layout detection model (LayoutLMv3/YOLO)
        Sementara fallback ke dual-layer processing
        """
        logger.info("Layout detection not yet implemented, using dual-layer processing")
        return self._process_dual_layer(image)

    def _process_dual_layer(self, image: np.ndarray) -> List[TextRegion]:
        """
        Dual-layer processing: Parallel OCR dari multiple engines
        """
        regions = []

        # Preprocessing untuk meningkatkan kualitas OCR
        processed_image = self._preprocess_image(image)

        # Jalankan OCR engines (disable PaddleOCR karena terlalu lambat)
        ocr_results = {
            "easyocr": self._run_easyocr(processed_image),
            # 'paddle': self._run_paddle_ocr(processed_image),  # Disabled - too slow
            "tesseract": self._run_tesseract(processed_image),
        }

        # Smart merging hasil OCR
        merged_regions = self._smart_merge_ocr_results(ocr_results, image.shape)

        return merged_regions

    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocessing gambar untuk meningkatkan kualitas OCR"""
        if not self.config.get("preprocessing", {}).get("enhance_handwriting", True):
            return image

        processed = image.copy()

        # Convert to grayscale
        if len(processed.shape) == 3:
            processed = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)

        # Aggressive denoising for handwriting
        if self.config.get("preprocessing", {}).get("denoise", True):
            processed = cv2.fastNlMeansDenoising(processed, h=10)
            processed = cv2.bilateralFilter(processed, 9, 75, 75)

        # Enhanced contrast for handwriting
        if self.config.get("preprocessing", {}).get("contrast_enhancement", True):
            processed = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(
                processed
            )
            # Additional contrast enhancement
            processed = cv2.convertScaleAbs(processed, alpha=1.2, beta=10)

        # Morphological operations for text enhancement
        if self.config.get("preprocessing", {}).get("morphology_operations", True):
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel)
            processed = cv2.morphologyEx(processed, cv2.MORPH_OPEN, kernel)

        # Convert back to BGR for consistency
        if len(image.shape) == 3:
            processed = cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)

        return processed

    def _run_easyocr(self, image: np.ndarray) -> List[Dict]:
        """Jalankan EasyOCR pada gambar"""
        try:
            print("🔍 Running EasyOCR...")
            results = self.easyocr_reader.readtext(image)
            print(f"✅ EasyOCR completed: {len(results)} detections")
            formatted_results = []

            for bbox, text, confidence in results:
                if confidence >= self.config.get("processing", {}).get(
                    "ocr_confidence_threshold", 0.3
                ):
                    # Convert bbox format
                    x_coords = [point[0] for point in bbox]
                    y_coords = [point[1] for point in bbox]
                    bbox_rect = (
                        min(x_coords),
                        min(y_coords),
                        max(x_coords),
                        max(y_coords),
                    )

                    formatted_results.append(
                        {
                            "text": text.strip(),
                            "bbox": bbox_rect,
                            "confidence": confidence,
                            "engine": "easyocr",
                        }
                    )

            return formatted_results
        except Exception as e:
            logger.error(f"EasyOCR error: {e}")
            return []

    def _run_paddle_ocr(self, image: np.ndarray) -> List[Dict]:
        """Jalankan PaddleOCR pada gambar"""
        try:
            print("🔍 Running PaddleOCR...")
            results = self.paddle_ocr.ocr(image)
            print(f"✅ PaddleOCR completed")
            formatted_results = []

            if results and results[0]:
                for line in results[0]:
                    if line:
                        bbox_points, (text, confidence) = line
                        if confidence >= self.config.get("processing", {}).get(
                            "ocr_confidence_threshold", 0.3
                        ):
                            # Convert bbox format
                            x_coords = [point[0] for point in bbox_points]
                            y_coords = [point[1] for point in bbox_points]
                            bbox_rect = (
                                min(x_coords),
                                min(y_coords),
                                max(x_coords),
                                max(y_coords),
                            )

                            formatted_results.append(
                                {
                                    "text": text.strip(),
                                    "bbox": bbox_rect,
                                    "confidence": confidence,
                                    "engine": "paddle",
                                }
                            )

            return formatted_results
        except Exception as e:
            logger.error(f"PaddleOCR error: {e}")
            return []

    def _run_tesseract(self, image: np.ndarray) -> List[Dict]:
        """Jalankan Tesseract pada gambar"""
        try:
            print("🔍 Running Tesseract...")
            # Get detailed data from Tesseract
            tesseract_config = (
                self.config.get("ocr_engines", {})
                .get("tesseract", {})
                .get("config", "--oem 3 --psm 6")
            )
            data = pytesseract.image_to_data(
                image, config=tesseract_config, output_type=pytesseract.Output.DICT
            )

            formatted_results = []
            n_boxes = len(data["text"])

            for i in range(n_boxes):
                confidence = float(data["conf"][i])
                text = data["text"][i].strip()

                if (
                    confidence
                    >= self.config.get("processing", {}).get(
                        "ocr_confidence_threshold", 0.3
                    )
                    * 100
                    and text
                ):
                    x, y, w, h = (
                        data["left"][i],
                        data["top"][i],
                        data["width"][i],
                        data["height"][i],
                    )
                    bbox_rect = (x, y, x + w, y + h)

                    formatted_results.append(
                        {
                            "text": text,
                            "bbox": bbox_rect,
                            "confidence": confidence / 100.0,  # Normalize to 0-1
                            "engine": "tesseract",
                        }
                    )

            return formatted_results
        except Exception as e:
            logger.error(f"Tesseract error: {e}")
            return []

    def _smart_merge_ocr_results(
        self, ocr_results: Dict, image_shape: Tuple
    ) -> List[TextRegion]:
        """
        Smart merging hasil dari multiple OCR engines
        Menggunakan voting dan confidence scoring
        """
        all_detections = []

        # Gabungkan semua deteksi
        for engine, results in ocr_results.items():
            for result in results:
                all_detections.append(result)

        # Group overlapping detections
        merged_regions = []
        used_indices = set()

        for i, detection in enumerate(all_detections):
            if i in used_indices:
                continue

            # Find overlapping detections
            overlapping = [detection]
            used_indices.add(i)

            for j, other_detection in enumerate(all_detections[i + 1 :], i + 1):
                if j in used_indices:
                    continue

                if self._boxes_overlap(detection["bbox"], other_detection["bbox"]):
                    overlapping.append(other_detection)
                    used_indices.add(j)

            # Merge overlapping detections
            merged_region = self._merge_overlapping_detections(overlapping)
            if merged_region:
                merged_regions.append(merged_region)

        return merged_regions

    def _boxes_overlap(self, box1: Tuple, box2: Tuple, threshold: float = 0.3) -> bool:
        """Check if two bounding boxes overlap significantly"""
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2

        # Check if boxes are too far apart horizontally (likely separate text)
        horizontal_gap = abs(x1_2 - x2_1) if x1_2 > x2_1 else abs(x1_1 - x2_2)
        if horizontal_gap > 50:  # 50 pixels gap = separate regions
            return False

        # Calculate intersection
        x_left = max(x1_1, x1_2)
        y_top = max(y1_1, y1_2)
        x_right = min(x2_1, x2_2)
        y_bottom = min(y2_1, y2_2)

        if x_right < x_left or y_bottom < y_top:
            return False

        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
        box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)

        union_area = box1_area + box2_area - intersection_area
        iou = intersection_area / union_area if union_area > 0 else 0

        return iou >= threshold

    def _merge_overlapping_detections(
        self, detections: List[Dict]
    ) -> Optional[TextRegion]:
        """Merge multiple overlapping detections into single region"""
        if not detections:
            return None

        # Choose best text based on confidence and length
        best_detection = max(detections, key=lambda x: x["confidence"] * len(x["text"]))

        # Calculate average confidence
        avg_confidence = sum(d["confidence"] for d in detections) / len(detections)

        # Merge bounding boxes
        all_x1 = [d["bbox"][0] for d in detections]
        all_y1 = [d["bbox"][1] for d in detections]
        all_x2 = [d["bbox"][2] for d in detections]
        all_y2 = [d["bbox"][3] for d in detections]

        merged_bbox = (min(all_x1), min(all_y1), max(all_x2), max(all_y2))

        # Detect if handwritten based on confidence and characteristics
        region_type = self._detect_region_type(best_detection, avg_confidence)

        return TextRegion(
            text=best_detection["text"],
            bbox=merged_bbox,
            confidence=avg_confidence,
            region_type=region_type,
        )

    def _detect_region_type(self, detection: Dict, confidence: float) -> str:
        """Detect if region contains handwritten or printed text"""
        text = detection["text"]

        # Low confidence often indicates handwriting
        if confidence < 0.5:
            return "handwritten"

        # Check for handwriting patterns
        handwriting_indicators = [
            len(text) < 15,  # Short text segments
            any(char in text for char in "`~|"),  # OCR artifacts common in handwriting
            confidence < 0.6
            and len(text) > 5,  # Medium confidence with reasonable length
        ]

        if sum(handwriting_indicators) >= 2:
            return "handwritten"

        return "printed"

    def _extract_text_from_regions(self, regions: List[TextRegion]) -> str:
        """Extract dan susun teks dari regions"""
        if not regions:
            return ""

        # Sort regions by position (top to bottom, left to right)
        sorted_regions = sorted(regions, key=lambda r: (r.bbox[1], r.bbox[0]))

        # Extract text
        texts = [region.text for region in sorted_regions if region.text.strip()]
        return "\n".join(texts)

    def _merge_text_results(self, text_pages: List[str]) -> str:
        """Merge teks dari multiple halaman"""
        return "\n\n".join(page for page in text_pages if page.strip())

    def _post_process_text_with_patterns(self, text: str) -> str:
        """Post-processing dengan pattern-based corrections"""
        if not text:
            return text

        # Apply global OCR corrections
        corrected_text, _ = self.pattern_manager.apply_ocr_corrections(text, "global")

        # Apply context rules
        context = {
            "document_type": self.detected_document_type,
            "text_length": len(corrected_text),
        }
        final_text, _ = self.pattern_manager.apply_context_rules(
            corrected_text, context
        )

        # Basic cleaning
        lines = final_text.split("\n")
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if line:
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    def _post_process_text(self, text: str) -> str:
        """Legacy post-processing method - kept for compatibility"""
        return self._post_process_text_with_patterns(text)

    def _apply_ocr_corrections(self, text: str) -> str:
        """Apply common OCR error corrections"""
        corrections = {
            # Month corrections (handwriting specific)
            "Fcbruar": "Februari",
            "Fcbruari": "Februari",
            "Fcbruan": "Februari",
            "Fcbruar`": "Februari",
            "Januan": "Januari",
            "Maret": "Maret",
            "Apnl": "April",
            "Mei": "Mei",
            "Juni": "Juni",
            "Juli": "Juli",
            "Agustus": "Agustus",
            "Septcmber": "September",
            "Oktober": "Oktober",
            "Novembcr": "November",
            "Desember": "Desember",
            # Common punctuation and character errors
            "`": "",
            "~": "",
            "|": "l",
            "rn": "m",
            "cl": "d",
            "ii": "ll",
            # Number corrections for handwriting
            "9025": "2025",  # Specific correction based on your case
        }

        corrected = text
        for wrong, right in corrections.items():
            corrected = corrected.replace(wrong, right)

        # Pattern-based corrections for dates
        import re

        # Fix date patterns like "5 Fcbruar` 9025" -> "5 Februari 2025"
        date_pattern = r"(\d+)\s+(\w+)\s+(\d{4})"
        if re.search(date_pattern, corrected):
            corrected = re.sub(r"9025", "2025", corrected)

        return corrected

    def _get_context_from_region(self, region: TextRegion) -> str:
        """Determine context type from region characteristics"""
        text = region.text.lower()

        # Date context
        if any(
            month in text
            for month in [
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
        ):
            return "date"

        # Number context
        if region.text.replace(".", "").replace("/", "").replace("-", "").isdigit():
            return "number"

        # Mixed alphanumeric (document numbers)
        if any(char.isdigit() for char in region.text) and any(
            char.isalpha() for char in region.text
        ):
            return "document_number"

        return "text"

    def _generate_metadata(
        self, file_path: str, num_pages: int, regions: List[TextRegion]
    ) -> Dict:
        """Generate metadata untuk hasil pemrosesan"""
        pattern_stats = self.pattern_manager.get_pattern_stats()

        return {
            "source_file": Path(file_path).name,
            "file_size": os.path.getsize(file_path),
            "num_pages": num_pages,
            "num_text_regions": len(regions),
            "document_type": self.detected_document_type,
            "processing_timestamp": None,  # Will be set by caller
            "engines_used": ["easyocr", "tesseract"],
            "pattern_stats": pattern_stats,
            "handwritten_regions": len(
                [r for r in regions if r.region_type == "handwritten"]
            ),
            "printed_regions": len([r for r in regions if r.region_type == "printed"]),
        }

    def _calculate_confidence_scores(
        self, regions: List[TextRegion]
    ) -> Dict[str, float]:
        """Calculate overall confidence scores"""
        if not regions:
            return {"overall": 0.0}

        confidences = [region.confidence for region in regions]
        return {
            "overall": sum(confidences) / len(confidences),
            "min": min(confidences),
            "max": max(confidences),
            "regions_count": len(regions),
        }


# Utility functions
def create_processor(
    config_path: Optional[str] = None, pattern_dir: Optional[str] = None
) -> HybridProcessor:
    """Factory function untuk membuat HybridProcessor instance"""
    config = None
    if config_path and Path(config_path).exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                if config_path.endswith(".yaml") or config_path.endswith(".yml"):
                    config = yaml.safe_load(f)
                else:
                    config = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load config from {config_path}: {e}")
            logger.info("Using default configuration")

    return HybridProcessor(config, pattern_dir)


if __name__ == "__main__":
    # Test basic functionality with patterns
    processor = create_processor(pattern_dir=".")
    print("Hybrid Processor with Pattern Manager initialized successfully!")

    # Print pattern stats
    stats = processor.pattern_manager.get_pattern_stats()
    print("\nPattern Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
