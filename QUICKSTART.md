# Quick Start Guide - Hybrid Document Processor

## 🚀 Menjalankan Sistem

### 1. Persiapan Environment
```bash
# Aktifkan virtual environment
venv\Scripts\activate  # Windows

# Install dependencies (jika belum)
pip install -r requirements.txt

# Download model AI
python download_models.py
```

### 2. Jalankan API Server
```bash
# Jalankan server FastAPI
python api_server.py

# Atau menggunakan uvicorn
uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
```

Server akan berjalan di: `http://localhost:8000`

### 3. Test Processor
```bash
# Test basic functionality
python test_processor.py
```

## 📡 Menggunakan API

### Upload dan Proses Dokumen
```bash
curl -X POST "http://localhost:8000/process-document/" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@your_document.pdf"
```

Response:
```json
{
  "message": "Document processing started",
  "task_id": "f8e4a2e0-2c1c-4a4d-8a0e-9f8b1b5a3c7d",
  "filename": "your_document.pdf",
  "status": "queued"
}
```

### Cek Status Processing
```bash
curl "http://localhost:8000/tasks/{task_id}"
```

### Ambil Hasil Processing
```bash
curl "http://localhost:8000/results/{task_id}"
```

## 🔧 Konfigurasi

Edit file `config.yaml` untuk menyesuaikan:
- Threshold confidence OCR
- Enable/disable fitur tertentu
- Pengaturan performa

## 📊 API Documentation

Akses dokumentasi interaktif di: `http://localhost:8000/docs`

## ✅ Status Implementasi

### ✅ Yang Sudah Selesai:
- [x] Core OCR Pipeline (`hybrid_processor.py`)
- [x] Multi-engine OCR (EasyOCR, PaddleOCR, Tesseract)
- [x] Smart merging hasil OCR
- [x] API endpoints dasar
- [x] File processing (PDF, Images)
- [x] Configuration system

### 🔄 Sedang Dikembangkan:
- [ ] Layout detection dengan AI model
- [ ] Handwriting recognition (TrOCR)
- [ ] Database integration
- [ ] WebSocket real-time monitoring
- [ ] Celery async processing

### 📋 Next Steps:
1. Implementasi layout detection
2. Integrasi database PostgreSQL
3. Setup Celery untuk async processing
4. Implementasi semantic search
