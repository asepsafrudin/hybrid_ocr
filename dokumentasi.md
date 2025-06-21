# Hybrid Document Processor

Selamat datang di dokumentasi resmi Hybrid Document Processor, sebuah platform cerdas untuk mengubah dokumen statis (PDF, gambar) menjadi data terstruktur yang siap dianalisis dan dapat dicari secara semantik.

## 1. 🎯 Overview

Proyek ini lebih dari sekadar OCR. Ini adalah pipeline lengkap yang dirancang untuk menangani tantangan dokumen dunia nyata, termasuk campuran teks cetak dan tulisan tangan. Tujuannya adalah untuk menciptakan fondasi data yang kuat untuk aplikasi tingkat lanjut seperti analitik, otomatisasi alur kerja, dan *Retrieval-Augmented Generation* (RAG) dengan LLM.

### ✨ Fitur Utama

*   **Ekstraksi Teks Hybrid**: Menggabungkan beberapa mesin OCR (EasyOCR, PaddleOCR, Tesseract) dengan model pengenalan tulisan tangan (TrOCR) untuk akurasi maksimal.
*   **Pemahaman Layout**: Mengidentifikasi secara otomatis struktur dokumen seperti judul, paragraf, dan tabel.
*   **Pencarian Semantik**: Mengubah teks yang diekstraksi menjadi *vector embeddings* untuk memungkinkan pencarian berdasarkan makna, bukan hanya kata kunci.
*   **Arsitektur Skalabel**: Dibangun dengan FastAPI, PostgreSQL, dan arsitektur berbasis antrian untuk menangani volume pekerjaan yang tinggi.
*   **API-First Design**: Semua fungsionalitas diekspos melalui REST API yang modern dan WebSocket untuk pemantauan *real-time*.

## 2. 🏗️ Arsitektur Sistem

Sistem ini dirancang dengan pendekatan modular untuk memastikan skalabilitas, persistensi, dan kemudahan pemeliharaan.

### Arsitektur Data dan Layanan

Diagram berikut menunjukkan alur data dari saat pengguna mengunggah file hingga data siap dikonsumsi oleh aplikasi lain.

```mermaid
graph TD
    subgraph User Interaction
        A[Client/User] -- Upload File --> B(FastAPI Server)
    end

    subgraph Data Storage & Processing
        B -- 1. Simpan File Mentah --> C[Object Storage <br> (MinIO/S3)]
        B -- 2. Buat Task Record --> D{PostgreSQL DB}
        B -- 3. Mulai Background Task --> E(Hybrid OCR Processor)
        
        E -- 4. Proses Dokumen --> E
        E -- 5. Simpan Hasil OCR (JSON) --> D
        
        subgraph Semantic Indexing
            E -- 6. Ekstrak Teks --> F(Embedding Model)
            F -- 7. Hasilkan Vektor --> G[Vector Database <br> (ChromaDB)]
        end
    end

    subgraph Data Consumption
        H(Aplikasi LLM / RAG) -- Kueri Semantik --> G
        G -- Kirim ID Dokumen Relevan --> H
        H -- Ambil Konten Lengkap --> D
    end

    D -- Menyimpan Metadata & Hasil OCR --> D
    C -- Menyimpan File PDF/Gambar --> C
    G -- Menyimpan Indeks Semantik --> G
```

*   **PostgreSQL (SQL DB):** Menjadi "source of truth" untuk semua metadata pemrosesan dan hasil ekstraksi OCR terstruktur.
*   **ChromaDB (Vector DB):** Menyimpan *vector embeddings* dari teks, memungkinkan pencarian semantik.
*   **Object Storage (MinIO/S3):** Bertindak sebagai gudang untuk file input mentah.

### Alur Kerja Pemrosesan OCR

Di dalam `Hybrid OCR Processor`, proses ekstraksi teks itu sendiri mengikuti alur kerja 3-layer yang canggih.

```mermaid
graph TD
    A[Input Document] --> B{File Type?}
    B -->|PDF| C[PDF to Images]
    B -->|Image| D[Direct Processing]
    C --> D
    D --> E{Layout Detection}
    E -->|Success| F[Region-Based Processing]
    E -->|Failed| G[Dual-Layer Processing]
    F --> H[Printed Text OCR]
    F --> I[Handwriting OCR]
    G --> J[Parallel OCR Processing]
    H --> K[Smart Merging]
    I --> K
    J --> K
    K --> L[Final Results]
```

## 3. 🚀 Instalasi dan Setup

Ikuti langkah-langkah ini untuk menyiapkan lingkungan pengembangan Anda.

### Langkah 1: Persiapan Environment

Disarankan untuk menggunakan *virtual environment* Python.

```bash
# Buat virtual environment
python -m venv venv

# Aktifkan
source venv/bin/activate  # Linux/Mac
# atau
venv\Scripts\activate     # Windows
```

### Langkah 2: Instal Dependensi Sistem

Dependensi ini diperlukan untuk pemrosesan PDF dan fungsionalitas Tesseract.

*   **Windows:**
    *   **Poppler:** Unduh dari Poppler for Windows dan tambahkan folder `bin`-nya ke `PATH`.
    *   **Tesseract:** Unduh installer dari UB-Mannheim dan tambahkan path instalasinya ke `PATH`.
*   **Linux (Debian/Ubuntu):**
    ```bash
    sudo apt-get update && sudo apt-get install -y poppler-utils tesseract-ocr
    ```
*   **macOS (via Homebrew):**
    ```bash
    brew install poppler tesseract
    ```

### Langkah 3: Instal Dependensi Python

Instal semua pustaka Python yang diperlukan dari file `requirements.txt`.

```bash
pip install -r requirements.txt
```

### Langkah 4: Unduh Model AI

Jalankan skrip berikut untuk mengunduh model deteksi layout dan pengenalan tulisan tangan.

```bash
python download_models.py
```

### Langkah 5: Siapkan Database

Proyek ini memerlukan PostgreSQL. Pastikan Anda memiliki server PostgreSQL yang berjalan dan perbarui string koneksi di `database.py`.

```python
# c:\Users\aseps\OneDrive\Project-onedrive\hybrid_ocr\database.py

# Ganti dengan URL koneksi PostgreSQL Anda
SQLALCHEMY_DATABASE_URL = "postgresql://user:password@host:port/dbname"
```

## 4. 🛠️ Panduan Penggunaan (Via API)

Cara utama untuk berinteraksi dengan sistem ini adalah melalui API web.

### Menjalankan Server

1.  **Jalankan Backend (FastAPI Server)**:
    Dari direktori root proyek, jalankan:
    ```bash
    uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
    ```
    Server API sekarang akan berjalan di `http://localhost:8000`. Anda dapat mengakses dokumentasi API interaktif di `http://localhost:8000/docs`.

2.  **Jalankan Frontend (Jika Ada)**:
    Jika Anda memiliki aplikasi frontend (React/Vue), jalankan server pengembangannya.

### Alur Kerja API

1.  **Unggah Dokumen**: Kirim permintaan `POST` dengan file dokumen ke endpoint `/process-document/`.
2.  **Terima Task ID**: Server akan merespons dengan `task_id` yang unik.
3.  **Pantau Status**: Buka koneksi WebSocket ke `/ws/status/{task_id}` untuk menerima pembaruan status pemrosesan secara *real-time*.
4.  **Ambil Hasil**: Setelah status `completed`, Anda dapat mengambil hasil terstruktur dari database menggunakan `task_id`.

### Detail Endpoint

#### `POST /process-document/`

*   **Deskripsi**: Memulai tugas pemrosesan dokumen.
*   **Request**: `multipart/form-data` dengan field `file`.
*   **Response**: JSON berisi `task_id`, `filename`, dan `message`.

    ```json
    {
      "task_id": "f8e4a2e0-2c1c-4a4d-8a0e-9f8b1b5a3c7d",
      "filename": "dokumen.pdf",
      "message": "Document processing started."
    }
    ```

#### `WebSocket /ws/status/{task_id}`

*   **Deskripsi**: Mengirimkan pembaruan status secara *real-time*.
*   **Pesan**: JSON berisi `step`, `total_steps`, `message`, `progress`, dan `status`.

    ```json
    {
      "step": 6,
      "total_steps": 6,
      "message": "Processing complete!",
      "progress": 100.0,
      "status": "completed"
    }
    ```

## 5. 🔬 Untuk Pengembang (Project Internals)

Bagian ini merinci komponen internal proyek bagi mereka yang ingin berkontribusi atau memahami lebih dalam.

### Struktur Direktori

Struktur proyek dirancang untuk modularitas dan kejelasan.

```
C:\Project\LayoutLMv3\modul_hybrid\
├── 📄 README.md
├── 📄 requirements.txt
├── 📄 config.yaml
├── 📄 download_models.py
├── 📄 api_server.py               # Titik masuk utama (FastAPI)
├── 📄 hybrid_processor.py         # Logika inti OCR
├── 📄 vector_store.py             # Abstraksi untuk Vector DB
├── 📄 database.py                 # Konfigurasi koneksi DB
├── 📄 models.py                   # Model tabel SQLAlchemy
├── 📁 examples/
├── 📁 tests/
└── 📁 docs/
```

### Konfigurasi (`config.yaml`)

Hampir semua aspek dari pipeline pemrosesan dapat dikonfigurasi melalui file `config.yaml`. Ini memungkinkan penyesuaian tanpa mengubah kode.

```yaml
# Processing Settings
processing:
  layout_confidence_threshold: 0.7
  ocr_confidence_threshold: 0.3
  
# Feature Toggles
features:
  enable_layout_detection: true
  enable_handwriting: true

# Performance
performance:
  max_workers: 4
  batch_size: 8
```

### API Reference

Dokumentasi API yang lengkap dan interaktif (dihasilkan oleh Swagger UI) tersedia secara otomatis saat server berjalan. Silakan kunjungi:

**`http://localhost:8000/docs`**

---

*Dokumentasi ini terakhir diperbarui pada [tanggal hari ini].*
