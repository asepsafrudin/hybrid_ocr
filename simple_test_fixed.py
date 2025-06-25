"""
Simple Test - Test tanpa dependencies yang belum terinstall
"""

import sys
import os
from pathlib import Path


def simple_pattern_test():
    """Test pattern manager tanpa hybrid processor"""

    try:
        # Test pattern manager saja
        sys.path.append(str(Path(__file__).parent))
        from pattern_manager import create_pattern_manager

        print("Testing Pattern Manager...")
        pm = create_pattern_manager(".")

        # Test OCR corrections
        test_cases = [
            ("5 Fcbruar` 9025", "date"),
            ("io8 . 4.3/3 1/ Puu", "document_number"),
            ("Mahkamah Konstitusi", "text"),
        ]

        print("\nOCR Correction Tests:")
        for original, context in test_cases:
            corrected, boost = pm.apply_ocr_corrections(original, context)
            print(f"   '{original}' -> '{corrected}' (boost: {boost:.3f})")

        # Test document type detection
        print("\nDocument Type Detection:")
        test_text = "Mahkamah Konstitusi Republik Indonesia Putusan"
        doc_type = pm.detect_document_type(test_text)
        print(f"   '{test_text}' -> {doc_type}")

        # Pattern stats
        stats = pm.get_pattern_stats()
        print(f"\nPattern Statistics:")
        for key, value in stats.items():
            print(f"   {key}: {value}")

        print("\nPattern system working correctly!")
        return True

    except Exception as e:
        print(f"Error: {e}")
        return False


def test_image_processing():
    """Test basic image processing tanpa OCR engines"""

    try:
        import cv2
        import numpy as np

        image_path = "pengantar puu sk sekretariat_001.png"

        if not os.path.exists(image_path):
            print(f"Image not found: {image_path}")
            return False

        print(f"Testing image processing: {image_path}")

        # Load image
        img = cv2.imread(image_path)
        if img is None:
            print("Failed to load image")
            return False

        print(f"   Image shape: {img.shape}")
        print(f"   Image size: {img.shape[0] * img.shape[1]} pixels")

        # Basic preprocessing
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        print(f"   Converted to grayscale: {gray.shape}")

        # Test spatial pattern matching
        sys.path.append(str(Path(__file__).parent))
        from pattern_manager import create_pattern_manager

        pm = create_pattern_manager(".")

        # Test bbox in top-right area
        test_bbox = (700, 50, 900, 100)
        patterns = pm.get_spatial_patterns_for_region(test_bbox, img.shape, "General")

        print(f"   Spatial patterns found: {len(patterns)}")
        for pattern in patterns[:3]:
            print(f"     - {pattern.region_name} (boost: {pattern.confidence_boost})")

        print("Image processing test passed!")
        return True

    except ImportError as e:
        print(f"Missing dependency: {e}")
        return False
    except Exception as e:
        print(f"Error in image processing: {e}")
        return False


def main():
    """Main test function"""
    print("Simple Pattern System Test")
    print("=" * 50)

    tests = [
        ("Pattern Manager", simple_pattern_test),
        ("Image Processing", test_image_processing),
    ]

    passed = 0
    for test_name, test_func in tests:
        print(f"\n{'-'*30}")
        print(f"Running: {test_name}")
        print("-" * 30)

        if test_func():
            passed += 1

    print(f"\n{'='*50}")
    print(f"Results: {passed}/{len(tests)} tests passed")

    if passed == len(tests):
        print("All tests passed! Pattern system is working.")
    else:
        print("Some tests failed. Check dependencies.")


if __name__ == "__main__":
    main()
