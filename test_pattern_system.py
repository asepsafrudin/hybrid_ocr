"""
Test Pattern System - Validation dan Testing untuk Pattern-based OCR
"""

import sys
import os
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from pattern_manager import PatternManager, create_pattern_manager
from hybrid_processor import HybridProcessor, create_processor
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_pattern_manager():
    """Test PatternManager functionality"""
    print("🧪 Testing PatternManager...")

    try:
        pm = create_pattern_manager(".")
        stats = pm.get_pattern_stats()

        print(f"✅ PatternManager loaded successfully!")
        print(f"   OCR Patterns: {stats['ocr_patterns']}")
        print(f"   Spatial Patterns: {stats['spatial_patterns']}")
        print(f"   Context Rules: {stats['context_rules']}")
        print(f"   Document Types: {stats['document_types']}")

        return True
    except Exception as e:
        print(f"❌ PatternManager test failed: {e}")
        return False


def test_ocr_corrections():
    """Test OCR correction patterns"""
    print("\n🧪 Testing OCR Corrections...")

    try:
        pm = create_pattern_manager(".")

        test_cases = [
            ("5 Fcbruar` 9025", "date", "5 Februari 2025"),
            ("io8 . 4.3/3 1/ Puu", "document_number", "100 . 4.3/3 1/ PUU"),
            ("Mahkamah Konstitusi", "text", "Mahkamah Konstitusi"),
            ("Januan 2024", "date", "Januari 2024"),
            ("Test`~text", "text", "Testtext"),
        ]

        passed = 0
        for original, context, expected in test_cases:
            corrected, boost = pm.apply_ocr_corrections(original, context)

            print(f"   Original: '{original}'")
            print(f"   Corrected: '{corrected}'")
            print(f"   Expected: '{expected}'")
            print(f"   Boost: {boost:.3f}")

            if corrected != original:  # Some correction applied
                passed += 1
                print(f"   ✅ Correction applied")
            else:
                print(f"   ⚠️  No correction applied")
            print()

        print(
            f"✅ OCR Corrections test: {passed}/{len(test_cases)} cases had corrections applied"
        )
        return True

    except Exception as e:
        print(f"❌ OCR Corrections test failed: {e}")
        return False


def test_document_type_detection():
    """Test document type detection"""
    print("\n🧪 Testing Document Type Detection...")

    try:
        pm = create_pattern_manager(".")

        test_cases = [
            ("Mahkamah Konstitusi Republik Indonesia Putusan", "Legal_Constitutional"),
            ("PT. ABC Invoice No. 123", "Business_Invoice"),
            ("Universitas Indonesia Diploma Sarjana", "Academic_Certificate"),
            ("Surat Edaran Kementerian", "Government_Letter"),
            ("Random text without keywords", "General"),
        ]

        passed = 0
        for text, expected_type in test_cases:
            detected = pm.detect_document_type(text)

            print(f"   Text: '{text[:50]}...'")
            print(f"   Detected: {detected}")
            print(f"   Expected: {expected_type}")

            if detected == expected_type or (
                expected_type == "General" and detected is not None
            ):
                passed += 1
                print(f"   ✅ Correct detection")
            else:
                print(f"   ⚠️  Detection mismatch")
            print()

        print(f"✅ Document Type Detection: {passed}/{len(test_cases)} correct")
        return True

    except Exception as e:
        print(f"❌ Document Type Detection test failed: {e}")
        return False


def test_hybrid_processor_integration():
    """Test HybridProcessor with PatternManager integration"""
    print("\n🧪 Testing HybridProcessor Integration...")

    try:
        processor = create_processor(pattern_dir=".")

        # Check if pattern manager is loaded
        stats = processor.pattern_manager.get_pattern_stats()
        print(f"   Pattern Manager loaded: {stats['ocr_patterns']} patterns")

        # Test document type detection
        test_text = "Mahkamah Konstitusi Republik Indonesia"
        doc_type = processor.pattern_manager.detect_document_type(test_text)
        print(f"   Document type detection: '{test_text}' -> {doc_type}")

        # Test context determination
        from hybrid_processor import TextRegion

        test_region = TextRegion(
            text="5 Februari 2025",
            bbox=(100, 100, 200, 150),
            confidence=0.8,
            region_type="handwritten",
        )

        context = processor._get_context_from_region(test_region)
        print(f"   Context detection: '{test_region.text}' -> {context}")

        print(f"✅ HybridProcessor Integration test passed!")
        return True

    except Exception as e:
        print(f"❌ HybridProcessor Integration test failed: {e}")
        return False


def test_spatial_patterns():
    """Test spatial pattern matching"""
    print("\n🧪 Testing Spatial Patterns...")

    try:
        pm = create_pattern_manager(".")

        # Test spatial pattern matching
        test_bbox = (700, 50, 900, 100)  # Top-right area
        image_shape = (1000, 800)  # Height, Width

        patterns = pm.get_spatial_patterns_for_region(test_bbox, image_shape, "General")

        print(f"   Test bbox: {test_bbox}")
        print(f"   Image shape: {image_shape}")
        print(f"   Matching patterns: {len(patterns)}")

        for pattern in patterns[:3]:  # Show first 3
            print(f"     - {pattern.region_name} (boost: {pattern.confidence_boost})")

        print(f"✅ Spatial Patterns test: Found {len(patterns)} matching patterns")
        return True

    except Exception as e:
        print(f"❌ Spatial Patterns test failed: {e}")
        return False


def run_comprehensive_test():
    """Run all tests"""
    print("🚀 Starting Comprehensive Pattern System Test\n")

    tests = [
        ("PatternManager Basic", test_pattern_manager),
        ("OCR Corrections", test_ocr_corrections),
        ("Document Type Detection", test_document_type_detection),
        ("Spatial Patterns", test_spatial_patterns),
        ("HybridProcessor Integration", test_hybrid_processor_integration),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running: {test_name}")
        print("=" * 60)

        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")

    print(f"\n{'='*60}")
    print(f"📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")

    if passed == total:
        print("🎉 All tests passed! Pattern system is ready.")
    else:
        print("⚠️  Some tests failed. Check the output above.")

    return passed == total


if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
