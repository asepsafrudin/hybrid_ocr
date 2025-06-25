"""
Test User Verification System
Testing auto-pattern generation dan verification workflow
"""

import numpy as np
import cv2
from pathlib import Path
from user_verification import (
    UserVerificationSystem,
    UserCorrection,
    create_verification_system,
)
from pattern_manager import create_pattern_manager


def test_verification_system_initialization():
    """Test initialization verification system"""
    pattern_manager = create_pattern_manager(".")
    verification_system = create_verification_system(pattern_manager, ".")

    assert verification_system is not None
    assert verification_system.pattern_manager is not None
    assert verification_system.verification_threshold == 0.5


def test_priority_score_calculation():
    """Test priority score calculation untuk regions"""
    pattern_manager = create_pattern_manager(".")
    verification_system = create_verification_system(pattern_manager, ".")

    # Low confidence region
    low_conf_region = {"text": "io8", "confidence": 0.3, "region_type": "handwritten"}
    score = verification_system._calculate_priority_score(low_conf_region)
    assert score > 0.5  # Should be high priority

    # High confidence region
    high_conf_region = {
        "text": "Normal text",
        "confidence": 0.9,
        "region_type": "printed",
    }
    score = verification_system._calculate_priority_score(high_conf_region)
    assert score < 0.3  # Should be low priority


def test_pattern_generation_from_correction():
    """Test auto-pattern generation dari user correction"""
    pattern_manager = create_pattern_manager(".")
    verification_system = create_verification_system(pattern_manager, ".")

    correction = UserCorrection(
        region_id=1,
        original_text="io8",
        corrected_text="100",
        user_id="test_user",
        document_id="test_doc",
        confidence=0.3,
        region_type="handwritten",
    )

    patterns = verification_system._generate_patterns_from_correction(correction)

    assert len(patterns) > 0
    assert patterns[0]["Wrong_Text"] == "io8"
    assert patterns[0]["Correct_Text"] == "100"
    assert patterns[0]["Category"] == "Number"


def test_pattern_category_detection():
    """Test detection kategori pattern"""
    pattern_manager = create_pattern_manager(".")
    verification_system = create_verification_system(pattern_manager, ".")

    # Month pattern
    category = verification_system._detect_pattern_category("Fcbruar", "Februari")
    assert category == "Month"

    # Number pattern
    category = verification_system._detect_pattern_category("io8", "100")
    assert category == "Number"

    # Punctuation pattern
    category = verification_system._detect_pattern_category("|", "l")
    assert category == "Punctuation"

    # Character pattern
    category = verification_system._detect_pattern_category("rn", "m")
    assert category == "Character"


def test_image_cropping():
    """Test image cropping functionality"""
    pattern_manager = create_pattern_manager(".")
    verification_system = create_verification_system(pattern_manager, ".")

    # Create dummy image
    image = np.ones((200, 300, 3), dtype=np.uint8) * 255
    bbox = (50, 50, 150, 100)

    cropped_b64 = verification_system._crop_region_image(image, bbox)

    assert cropped_b64 != ""
    assert len(cropped_b64) > 100  # Should be valid base64


def test_context_type_detection():
    """Test detection context type"""
    pattern_manager = create_pattern_manager(".")
    verification_system = create_verification_system(pattern_manager, ".")

    # Date context
    correction = UserCorrection(
        region_id=1,
        original_text="Fcbruar",
        corrected_text="Februari",
        user_id="test",
        document_id="test",
        confidence=0.5,
        region_type="handwritten",
    )
    context = verification_system._detect_context_type(correction)
    assert context == "date"

    # Number context
    correction.corrected_text = "12345"
    context = verification_system._detect_context_type(correction)
    assert context == "number"


def test_verification_stats():
    """Test verification statistics"""
    pattern_manager = create_pattern_manager(".")
    verification_system = create_verification_system(pattern_manager, ".")

    stats = verification_system.get_verification_stats()

    assert "verification_threshold" in stats
    assert "pattern_stats" in stats
    assert "last_updated" in stats


def test_get_regions_for_verification():
    """Test getting regions untuk verification"""
    pattern_manager = create_pattern_manager(".")
    verification_system = create_verification_system(pattern_manager, ".")

    # Mock regions data
    regions = [
        {
            "text": "io8",
            "bbox": (10, 10, 50, 30),
            "confidence": 0.3,
            "region_type": "handwritten",
        },
        {
            "text": "Normal text",
            "bbox": (60, 10, 150, 30),
            "confidence": 0.9,
            "region_type": "printed",
        },
    ]

    # Create dummy image
    image = np.ones((200, 300, 3), dtype=np.uint8) * 255

    verification_regions = verification_system.get_regions_for_verification(
        regions, image, "test_doc"
    )

    # Should prioritize low confidence region
    assert len(verification_regions) >= 1
    assert verification_regions[0].text == "io8"
    assert verification_regions[0].priority_score > 0.5


if __name__ == "__main__":
    print("🧪 Running User Verification System Tests...")

    # Run basic tests
    test_verification_system_initialization()
    print("✅ Initialization test passed")

    test_priority_score_calculation()
    print("✅ Priority score calculation test passed")

    test_pattern_generation_from_correction()
    print("✅ Pattern generation test passed")

    test_pattern_category_detection()
    print("✅ Pattern category detection test passed")

    test_image_cropping()
    print("✅ Image cropping test passed")

    test_context_type_detection()
    print("✅ Context type detection test passed")

    test_verification_stats()
    print("✅ Verification stats test passed")

    test_get_regions_for_verification()
    print("✅ Get verification regions test passed")

    print("\n🎉 All User Verification System tests passed!")
    print("📊 System ready for user verification workflow")
