# Gunakan base image Python yang ramping
FROM python:3.11-slim

# Set variabel environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set direktori kerja di dalam container
WORKDIR /app

# Instal dependensi sistem yang dibutuhkan oleh OCR
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    poppler-utils \
    tesseract-ocr \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Instal dependensi Python
# Pertama, salin hanya requirements.txt untuk memanfaatkan cache Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

# Salin seluruh kode aplikasi ke dalam container
COPY . .

# Ekspos port yang digunakan oleh FastAPI
EXPOSE 8000

# Perintah untuk menjalankan aplikasi saat container dimulai
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
