#!/usr/bin/env python3
"""
Script untuk mengunduh model AI yang diperlukan untuk Hybrid Document Processor
"""

import os
import sys
from pathlib import Path
import requests
from tqdm import tqdm


def download_file(url, filename):
    """Download file dengan progress bar"""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get("content-length", 0))

    with (
        open(filename, "wb") as file,
        tqdm(
            desc=filename,
            total=total_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
        ) as bar,
    ):
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                file.write(chunk)
                bar.update(len(chunk))


def main():
    """Main function untuk mengunduh semua model yang diperlukan"""
    print("🚀 Mengunduh model AI untuk Hybrid Document Processor...")

    # Buat direktori models jika belum ada
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)

    try:
        # Import library untuk memastikan model akan diunduh otomatis
        print("📦 Mengunduh model EasyOCR...")
        import easyocr

        reader = easyocr.Reader(["en", "id"])  # English dan Indonesian
        print("✅ Model EasyOCR berhasil diunduh")

        print("📦 Mengunduh model Transformers...")
        from transformers import pipeline

        # Download model untuk embedding
        embedding_model = pipeline(
            "feature-extraction", model="sentence-transformers/all-MiniLM-L6-v2"
        )
        print("✅ Model Transformers berhasil diunduh")

        print("📦 Inisialisasi PaddleOCR...")
        from paddleocr import PaddleOCR

        ocr = PaddleOCR(use_angle_cls=True, lang="en")
        print("✅ Model PaddleOCR berhasil diunduh")

        print("🎉 Semua model berhasil diunduh!")

    except ImportError as e:
        print(f"❌ Error: Library tidak ditemukan - {e}")
        print(
            "💡 Pastikan semua dependensi sudah diinstal dengan: pip install -r requirements.txt"
        )
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error saat mengunduh model: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
