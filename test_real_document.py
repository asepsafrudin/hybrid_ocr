"""
Test Real Document - Testing Pattern System dengan Dokumen Real
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from hybrid_processor import create_processor
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_document_with_patterns(document_path: str):
    """Test dokumen real dengan pattern system"""

    if not os.path.exists(document_path):
        print(f"❌ File tidak ditemukan: {document_path}")
        return False

    print(f"🔄 Processing document: {document_path}")
    print("=" * 60)

    try:
        # Create processor with pattern support
        print("🚀 Initializing Hybrid Processor with Pattern Manager...")
        processor = create_processor(pattern_dir=".")

        # Show pattern stats
        stats = processor.pattern_manager.get_pattern_stats()
        print(f"📊 Pattern Statistics:")
        print(
            f"   OCR Patterns: {stats['enabled_ocr_patterns']}/{stats['ocr_patterns']}"
        )
        print(
            f"   Spatial Patterns: {stats['enabled_spatial_patterns']}/{stats['spatial_patterns']}"
        )
        print(
            f"   Context Rules: {stats['enabled_context_rules']}/{stats['context_rules']}"
        )
        print(f"   Document Types: {stats['document_types']}")
        print()

        # Process document
        print("🔍 Processing document...")
        result = processor.process_document(document_path)

        if not result.success:
            print(f"❌ Processing failed: {result.error_message}")
            return False

        # Display results
        print("✅ Processing completed successfully!")
        print("=" * 60)

        # Document metadata
        print("📋 DOCUMENT METADATA:")
        print(f"   File: {result.metadata['source_file']}")
        print(f"   Size: {result.metadata['file_size']:,} bytes")
        print(f"   Pages: {result.metadata['num_pages']}")
        print(f"   Document Type: {result.metadata['document_type']}")
        print(f"   Text Regions: {result.metadata['num_text_regions']}")
        print(f"   Handwritten Regions: {result.metadata['handwritten_regions']}")
        print(f"   Printed Regions: {result.metadata['printed_regions']}")
        print()

        # Confidence scores
        print("📊 CONFIDENCE SCORES:")
        for key, value in result.confidence_scores.items():
            if isinstance(value, float):
                print(f"   {key.title()}: {value:.3f}")
            else:
                print(f"   {key.title()}: {value}")
        print()

        # Sample text regions (first 5)
        print("📝 SAMPLE TEXT REGIONS:")
        for i, region in enumerate(result.regions[:5]):
            print(f"   Region {i+1}:")
            print(f"     Text: '{region['text']}'")
            print(f"     Type: {region['region_type']}")
            print(f"     Confidence: {region['confidence']:.3f}")
            print(f"     BBox: {region['bbox']}")
            print()

        if len(result.regions) > 5:
            print(f"   ... and {len(result.regions) - 5} more regions")
            print()

        # Full extracted text (first 500 chars)
        print("📄 EXTRACTED TEXT (Preview):")
        preview_text = result.text_content[:500]
        print(f"   {preview_text}")
        if len(result.text_content) > 500:
            print(f"   ... (total {len(result.text_content)} characters)")
        print()

        # Save detailed results
        output_file = f"ocr_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        # Convert numpy types to native Python types for JSON serialization
        def convert_numpy_types(obj):
            import numpy as np

            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif hasattr(obj, "tolist"):
                return obj.tolist()
            elif hasattr(obj, "item"):
                return obj.item()
            elif isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            elif isinstance(obj, tuple):
                return tuple(convert_numpy_types(item) for item in obj)
            return obj

        serializable_data = convert_numpy_types(
            {
                "metadata": result.metadata,
                "confidence_scores": result.confidence_scores,
                "regions": result.regions,
                "full_text": result.text_content,
                "processing_timestamp": datetime.now().isoformat(),
            }
        )

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(serializable_data, f, indent=2, ensure_ascii=False)

        print(f"💾 Detailed results saved to: {output_file}")

        return True

    except Exception as e:
        print(f"❌ Error processing document: {e}")
        logger.exception("Document processing error")
        return False


def compare_with_previous_results(current_regions):
    """Compare dengan hasil sebelumnya untuk melihat improvement"""
    print("\n🔍 IMPROVEMENT ANALYSIS:")

    # Analisis berdasarkan hasil sebelumnya yang Anda berikan
    previous_results = [
        {"text": "5 Fcbruar`", "confidence": 0.44, "type": "printed"},
        {"text": "9025", "confidence": 0.61, "type": "printed"},
        {"text": "io8 . 4.3/3 1/ Puu", "confidence": 0.30, "type": "handwritten"},
    ]

    improvements = []

    for region in current_regions:
        text = region["text"]
        confidence = region["confidence"]
        region_type = region["region_type"]

        # Check for specific improvements
        if "februari" in text.lower() and "fcbruar" not in text.lower():
            improvements.append(
                f"✅ Month correction: Found 'Februari' (was 'Fcbruar`')"
            )

        if "2025" in text and region_type == "handwritten":
            improvements.append(f"✅ Year correction: Found '2025' in handwritten text")

        if "100" in text and region_type == "handwritten":
            improvements.append(f"✅ Number correction: Found '100' (was 'io8')")

        if region_type == "handwritten" and confidence > 0.3:
            improvements.append(
                f"✅ Handwriting detection: Properly classified as handwritten"
            )

    if improvements:
        print("   Detected Improvements:")
        for improvement in improvements:
            print(f"     {improvement}")
    else:
        print("   No specific improvements detected in this sample")

    print()


def main():
    """Main function untuk testing"""
    print("🚀 Real Document Testing with Pattern System")
    print("=" * 60)

    # Contoh penggunaan - ganti dengan path dokumen Anda
    document_paths = [
        "sample_document.pdf",  # Ganti dengan path dokumen Anda
        "test_document.pdf",
        # Tambahkan path dokumen lain yang ingin ditest
    ]

    # Jika tidak ada argumen, gunakan default paths
    if len(sys.argv) > 1:
        document_paths = sys.argv[1:]

    success_count = 0
    total_count = len(document_paths)

    for doc_path in document_paths:
        print(f"\n{'='*60}")
        print(f"Testing: {doc_path}")
        print("=" * 60)

        if test_document_with_patterns(doc_path):
            success_count += 1

        print("\n" + "=" * 60)

    # Summary
    print(f"\n📊 TESTING SUMMARY")
    print("=" * 60)
    print(f"Successfully processed: {success_count}/{total_count} documents")
    print(f"Success rate: {(success_count/total_count)*100:.1f}%")

    if success_count == total_count:
        print("🎉 All documents processed successfully!")
    else:
        print("⚠️  Some documents failed to process.")


if __name__ == "__main__":
    main()
