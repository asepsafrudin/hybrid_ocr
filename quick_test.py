"""
Quick Test - Simple implementation untuk test cepat
"""

from hybrid_processor import create_processor


def quick_test(document_path):
    """Quick test implementation"""

    # Create processor with pattern support
    processor = create_processor(pattern_dir=".")

    # Process your document
    result = processor.process_document(document_path)

    if result.success:
        # Check improvements
        print(f"Document Type: {result.metadata['document_type']}")
        print(f"Handwritten Regions: {result.metadata['handwritten_regions']}")
        print(f"Printed Regions: {result.metadata['printed_regions']}")
        print(f"Pattern Stats: {result.metadata['pattern_stats']}")

        print(f"\nConfidence Scores:")
        print(f"  Overall: {result.confidence_scores['overall']:.3f}")
        print(f"  Min: {result.confidence_scores['min']:.3f}")
        print(f"  Max: {result.confidence_scores['max']:.3f}")

        print(f"\nSample Text Regions:")
        for i, region in enumerate(result.regions[:3]):
            print(
                f"  Region {i+1}: '{region['text']}' ({region['region_type']}, conf: {region['confidence']:.3f})"
            )

        print(f"\nExtracted Text Preview:")
        print(
            result.text_content[:200] + "..."
            if len(result.text_content) > 200
            else result.text_content
        )

        return result
    else:
        print(f"Error: {result.error_message}")
        return None


if __name__ == "__main__":
    # Ganti dengan path dokumen Anda
    document_path = "your_document.pdf"

    print("🚀 Quick Test with Pattern System")
    print("=" * 50)

    result = quick_test(document_path)

    if result:
        print("\n✅ Test completed successfully!")
    else:
        print("\n❌ Test failed!")
