#!/usr/bin/env python3
"""
Test script untuk Hybrid Document Processor
"""

import sys
import json
from pathlib import Path
from hybrid_processor import create_processor


def test_processor():
    """Test basic functionality of hybrid processor"""
    print("🧪 Testing Hybrid Document Processor...")

    try:
        # Initialize processor
        print("📦 Initializing processor...")
        processor = create_processor("config.yaml")
        print("✅ Processor initialized successfully")

        # Test dengan file contoh (jika ada)
        test_files = ["test_document.pdf", "test_image.jpg", "test_image.png"]

        uploads_dir = Path("uploads")
        found_files = []

        for test_file in test_files:
            file_path = uploads_dir / test_file
            if file_path.exists():
                found_files.append(str(file_path))

        if not found_files:
            print("⚠️  No test files found in uploads/ directory")
            print("💡 Place some PDF or image files in uploads/ directory to test")
            return

        # Process found files
        for file_path in found_files:
            print(f"\n📄 Processing: {Path(file_path).name}")

            result = processor.process_document(file_path)

            if result.success:
                print("✅ Processing successful!")
                print(f"📊 Text length: {len(result.text_content)} characters")
                print(f"🔍 Regions found: {len(result.regions)}")
                print(
                    f"📈 Overall confidence: {result.confidence_scores.get('overall', 0):.2f}"
                )

                # Show first 200 characters of extracted text
                preview = result.text_content[:200]
                if len(result.text_content) > 200:
                    preview += "..."
                print(f"📝 Text preview: {preview}")

            else:
                print(f"❌ Processing failed: {result.error_message}")

        print("\n🎉 Test completed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

    return True


if __name__ == "__main__":
    success = test_processor()
    sys.exit(0 if success else 1)
