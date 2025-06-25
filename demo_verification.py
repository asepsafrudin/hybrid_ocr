"""
Demo User Verification System
Demonstrasi workflow verification dan auto-pattern generation
"""

import cv2
import numpy as np
from user_verification import create_verification_system, UserCorrection
from pattern_manager import create_pattern_manager


def demo_verification_workflow():
    """Demo complete verification workflow"""
    print("🚀 Demo User Verification System")
    print("=" * 50)

    # Initialize systems
    pattern_manager = create_pattern_manager(".")
    verification_system = create_verification_system(pattern_manager, ".")

    print(f"✅ Pattern Manager loaded: {pattern_manager.get_pattern_stats()}")

    # Mock document processing result
    mock_regions = [
        {
            "text": "io8",
            "bbox": (10, 10, 50, 30),
            "confidence": 0.3,
            "region_type": "handwritten",
        },
        {
            "text": "Fcbruar`",
            "bbox": (60, 10, 120, 30),
            "confidence": 0.4,
            "region_type": "handwritten",
        },
        {
            "text": "9025",
            "bbox": (130, 10, 170, 30),
            "confidence": 0.45,
            "region_type": "handwritten",
        },
        {
            "text": "Normal printed text",
            "bbox": (10, 40, 200, 60),
            "confidence": 0.9,
            "region_type": "printed",
        },
    ]

    # Create mock image
    image = np.ones((200, 300, 3), dtype=np.uint8) * 255
    cv2.putText(image, "io8", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(
        image, "Fcbruar`", (60, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2
    )
    cv2.putText(image, "9025", (130, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(
        image, "Normal text", (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2
    )

    # Get regions for verification
    print("\n🔍 Getting regions for verification...")
    verification_regions = verification_system.get_regions_for_verification(
        mock_regions, image, "demo_doc"
    )

    print(f"📋 Found {len(verification_regions)} regions needing verification:")
    for i, region in enumerate(verification_regions):
        print(
            f"  {i+1}. '{region.text}' (confidence: {region.confidence:.2f}, priority: {region.priority_score:.2f})"
        )

    # Simulate user corrections
    print("\n✏️ Simulating user corrections...")
    corrections = [
        UserCorrection(
            region_id=0,
            original_text="io8",
            corrected_text="100",
            user_id="demo_user",
            document_id="demo_doc",
            confidence=0.3,
            region_type="handwritten",
        ),
        UserCorrection(
            region_id=1,
            original_text="Fcbruar`",
            corrected_text="Februari",
            user_id="demo_user",
            document_id="demo_doc",
            confidence=0.4,
            region_type="handwritten",
        ),
        UserCorrection(
            region_id=2,
            original_text="9025",
            corrected_text="2025",
            user_id="demo_user",
            document_id="demo_doc",
            confidence=0.45,
            region_type="handwritten",
        ),
    ]

    # Process corrections and generate patterns
    total_patterns = 0
    for correction in corrections:
        print(
            f"\n🔧 Processing correction: '{correction.original_text}' → '{correction.corrected_text}'"
        )
        patterns = verification_system.process_user_correction(correction)
        total_patterns += len(patterns)

        for pattern in patterns:
            print(
                f"  ✨ Generated pattern: {pattern['Wrong_Text']} → {pattern['Correct_Text']} ({pattern['Category']})"
            )

    print(f"\n📊 Summary:")
    print(f"  • Total corrections processed: {len(corrections)}")
    print(f"  • Total patterns generated: {total_patterns}")

    # Show updated pattern stats
    updated_stats = verification_system.get_verification_stats()
    print(f"  • Updated pattern stats: {updated_stats['pattern_stats']}")

    print("\n🎉 Demo completed successfully!")
    print("💡 User Verification System is ready for production use!")


def demo_pattern_application():
    """Demo pattern application setelah user corrections"""
    print("\n" + "=" * 50)
    print("🧪 Testing Pattern Application After User Corrections")

    pattern_manager = create_pattern_manager(".")

    # Test texts with common errors
    test_texts = ["5 Fcbruar` 9025", "Nomor: io8/PUU/2024", "Tanggal: 15 Fcbruar 9025"]

    print("\n📝 Testing OCR corrections:")
    for text in test_texts:
        corrected, boost = pattern_manager.apply_ocr_corrections(text, "any")
        print(f"  Original: '{text}'")
        print(f"  Corrected: '{corrected}' (boost: +{boost:.2f})")
        print()


if __name__ == "__main__":
    demo_verification_workflow()
    demo_pattern_application()
