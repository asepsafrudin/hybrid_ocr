# Hybrid Document Processor

[![CI/CD Pipeline](https://github.com/asepsafrudin/hybrid_ocr/actions/workflows/ci.yml/badge.svg)](https://github.com/asepsafrudin/hybrid_ocr/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://github.com/asepsafrudin/hybrid_ocr/blob/main/LICENSE)

Selamat datang di Hybrid Document Processor, sebuah platform cerdas untuk mengubah dokumen statis (PDF, gambar) menjadi data terstruktur yang siap dianalisis dan dapat dicari secara semantik.

## 🎯 Overview

Proyek ini lebih dari sekadar OCR. Ini adalah pipeline lengkap yang dirancang untuk menangani tantangan dokumen dunia nyata, termasuk campuran teks cetak dan tulisan tangan. Tujuannya adalah untuk menciptakan fondasi data yang kuat untuk aplikasi tingkat lanjut seperti analitik, otomatisasi alur kerja, dan *Retrieval-Augmented Generation* (RAG) dengan LLM.

### ✨ Fitur Utama

*   **Ekstraksi Teks Hybrid**: Menggabungkan beberapa mesin OCR dengan model pengenalan tulisan tangan untuk akurasi maksimal.
*   **Pemahaman Layout**: Mengidentifikasi secara otomatis struktur dokumen seperti judul, paragraf, dan tabel.
*   **Pencarian Semantik**: Mengubah teks yang diekstraksi menjadi *vector embeddings* untuk memungkinkan pencarian berdasarkan makna.
*   **Arsitektur Skalabel**: Dibangun dengan FastAPI, PostgreSQL, Celery, dan Redis untuk menangani volume pekerjaan yang tinggi.
*   **API-First Design**: Semua fungsionalitas diekspos melalui REST API modern dan WebSocket untuk pemantauan *real-time*.

---

## 🏗️ Arsitektur Sistem

Sistem ini dirancang dengan pendekatan modular untuk memastikan skalabilitas, persistensi, dan kemudahan pemeliharaan.

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
```

---

## 🚀 Getting Started

Ikuti langkah-langkah ini untuk menjalankan sistem di lingkungan pengembangan lokal Anda.

### 1. Prasyarat

*   **Dependensi Sistem**: Pastikan Anda telah menginstal **Poppler** dan **Tesseract OCR**. Lihat [dokumentasi lengkap](dokumentasi.md) untuk instruksi spesifik per OS.
*   **Database**: Proyek ini memerlukan **PostgreSQL** dan **Redis**. Cara termudah untuk menjalankannya secara lokal adalah menggunakan Docker.
*   **Python**: Python 3.9+

### 2. Instalasi

```bash
# 1. Clone repositori
git clone https://github.com/asepsafrudin/hybrid_ocr.git
cd hybrid_ocr

# 2. Buat dan aktifkan virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate    # Windows

# 3. Instal dependensi Python
pip install -r requirements.txt

# 4. Unduh model AI
python download_models.py
```

### 3. Konfigurasi

Proyek ini menggunakan file `.env` untuk mengelola konfigurasi sensitif.

```bash
# Salin file contoh
cp .env.example .env
```

Buka file `.env` yang baru dibuat dan sesuaikan nilai-nilainya, terutama `DATABASE_URL` dan `REDIS_URL`, agar sesuai dengan pengaturan lokal Anda.

### 4. Menjalankan Server

```bash
# Jalankan server API dengan Uvicorn
uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
```

Server sekarang berjalan! Anda dapat mengakses dokumentasi API interaktif (Swagger UI) di **http://localhost:8000/docs**.

---

## 🛠️ Penggunaan API

Interaksi utama dengan sistem dilakukan melalui REST API.

1.  **Mulai Pemrosesan**: Kirim permintaan `POST` ke `/process-document/` dengan file dokumen Anda.
    ```bash
    curl -X POST -F "file=@/path/to/your/document.pdf" http://localhost:8000/process-document/
    ```
2.  **Dapatkan Task ID**: Server akan merespons dengan `task_id` unik.
3.  **Pantau Status**: Hubungkan ke endpoint WebSocket di `/ws/status/{task_id}` untuk menerima pembaruan status secara *real-time*.

---

## 💻 Tumpukan Teknologi (Tech Stack)

| Kategori                | Teknologi                                                                                             |
| ----------------------- | ----------------------------------------------------------------------------------------------------- |
| **Backend Framework**   | FastAPI                                                              |
| **Database Relasional** | PostgreSQL dengan SQLAlchemy & Alembic |
| **Database Vektor**     | ChromaDB                                                                |
| **Antrian Tugas**       | Celery dengan Redis                                   |
| **OCR & AI**            | PyTorch, Transformers, EasyOCR, PaddleOCR |
| **Deployment**          | Docker, GitHub Actions               |
| **Linting & Formatting**| Black, Flake8                   |

---

## 🤝 Berkontribusi

Kontribusi sangat kami harapkan! Baik itu melaporkan bug, menyarankan fitur baru, atau mengirimkan *pull request*, semua bantuan Anda sangat berharga.

Silakan lihat `CONTRIBUTING.md` (akan datang) untuk panduan lebih lanjut dan gunakan template isu yang tersedia untuk membuat laporan yang jelas dan terstruktur.

1.  **Fork** repositori ini.
2.  Buat **branch** fitur baru (`git checkout -b feature/AmazingFeature`).
3.  **Commit** perubahan Anda (`git commit -m 'Add some AmazingFeature'`).
4.  **Push** ke branch (`git push origin feature/AmazingFeature`).
5.  Buka **Pull Request**.

---

## 📄 Lisensi

Proyek ini dilisensikan di bawah Lisensi Apache 2.0, yang memberikan kebebasan untuk menggunakan, memodifikasi, dan mendistribusikan perangkat lunak dengan persyaratan tertentu. Untuk informasi rinci tentang hak dan batasan penggunaan, silakan merujuk pada file LICENSE yang disertakan dalam repositori.
