# OCR Pattern Templates - User Guide

## Overview
Template Excel ini dirancang untuk mengelola pattern-based corrections dalam sistem Hybrid OCR. Setiap sheet memiliki fungsi spesifik untuk meningkatkan akurasi OCR.

## File Structure

### 1. OCR_Corrections_Template.csv
**Fungsi**: Pattern koreksi teks OCR
**Kolom Utama**:
- `Wrong_Text`: Teks hasil OCR yang salah
- `Correct_Text`: Teks yang benar (gunakan "EMPTY" untuk menghapus)
- `Context_Type`: Konteks dimana koreksi berlaku (date, number, text, etc.)
- `Priority`: 1=Highest, 5=Lowest
- `Confidence_Boost`: Peningkatan confidence score (0.0-1.0)

**Contoh Penggunaan**:
- Koreksi bulan: "Fcbruar`" → "Februari"
- Koreksi angka: "io8" → "100"
- Hapus noise: "`" → "" (EMPTY)

### 2. Document_Types_Template.csv
**Fungsi**: Identifikasi jenis dokumen
**Kolom Utama**:
- `Keywords`: Kata kunci untuk deteksi (pisahkan dengan koma)
- `Layout_Indicators`: Petunjuk layout dokumen
- `OCR_Engine_Priority`: Urutan engine OCR yang digunakan
- `Preprocessing_Profile`: Profil preprocessing yang sesuai

**Contoh Penggunaan**:
- Legal: Keywords="Mahkamah,Konstitusi" → OCR khusus dokumen hukum
- Business: Keywords="Invoice,PT" → OCR untuk dokumen bisnis

### 3. Spatial_Patterns_Template.csv
**Fungsi**: Pattern berdasarkan posisi dalam dokumen
**Kolom Utama**:
- `Position_Type`: Lokasi dalam dokumen (top_right, bottom_left, etc.)
- `X_Range`, `Y_Range`: Koordinat relatif (0.0-1.0)
- `Content_Type`: Jenis konten yang diharapkan
- `OCR_Config`: Konfigurasi OCR khusus untuk area ini

**Contoh Penggunaan**:
- Tanggal di kanan atas: Position="top_right", Content="date"
- Tanda tangan di kiri bawah: Position="bottom_left", Content="name"

### 4. Context_Rules_Template.csv
**Fungsi**: Aturan validasi berdasarkan konteks
**Kolom Utama**:
- `Trigger_Pattern`: Pattern regex yang memicu aturan
- `Validation_Logic`: Logika validasi
- `Action_Type`: Jenis aksi (replace, boost_confidence, validate_format)
- `Action_Value`: Nilai aksi yang dilakukan

**Contoh Penggunaan**:
- Validasi tahun: Pattern="\d{4}" → Pastikan tahun masuk akal
- Format NIK: Pattern="\d{16}" → Validasi 16 digit

### 5. Performance_Metrics_Template.csv
**Fungsi**: Monitoring performa pattern
**Kolom Utama**:
- `Usage_Count`: Berapa kali pattern digunakan
- `Success_Rate`: Tingkat keberhasilan (0.0-1.0)
- `Effectiveness_Score`: Skor efektivitas keseluruhan
- `Status`: ACTIVE, REVIEW, DISABLED

## Cara Penggunaan

### Step 1: Import ke Excel
1. Buka Excel
2. Import setiap file CSV sebagai sheet terpisah
3. Format sebagai Table untuk kemudahan filtering

### Step 2: Customization
1. Tambah pattern sesuai kebutuhan dokumen Anda
2. Sesuaikan priority dan confidence boost
3. Enable/disable pattern sesuai kebutuhan

### Step 3: Testing
1. Test dengan sample dokumen
2. Monitor performance metrics
3. Adjust pattern berdasarkan hasil

### Step 4: Maintenance
1. Review performance metrics secara berkala
2. Disable pattern dengan success rate rendah
3. Tambah pattern baru berdasarkan error yang ditemukan

## Best Practices

### Pattern Design
- **Spesifik**: Buat pattern yang spesifik untuk menghindari false positive
- **Prioritas**: Set priority berdasarkan kepentingan dan akurasi
- **Testing**: Selalu test pattern baru dengan sample data

### Performance Optimization
- **Monitor**: Pantau success rate dan processing time
- **Cleanup**: Hapus pattern yang tidak efektif
- **Balance**: Seimbangkan antara akurasi dan kecepatan

### Documentation
- **Notes**: Selalu isi kolom notes untuk dokumentasi
- **Examples**: Berikan contoh penggunaan yang jelas
- **Version Control**: Track perubahan dengan tanggal

## Advanced Features

### Conditional Patterns
- Gunakan context_type untuk pattern yang conditional
- Combine multiple patterns untuk akurasi maksimal

### Performance Tuning
- Monitor effectiveness_score untuk optimasi
- Adjust confidence_boost berdasarkan hasil testing

### Integration
- Pattern akan di-load otomatis oleh sistem OCR
- Hot-reload support untuk update tanpa restart

## Troubleshooting

### Pattern Tidak Bekerja
1. Check enabled status
2. Verify priority setting
3. Test trigger pattern dengan regex tester

### Performance Issues
1. Review processing time metrics
2. Disable pattern dengan time > 5ms
3. Optimize regex patterns

### False Positives
1. Make patterns more specific
2. Add context validation
3. Lower confidence boost

## Support
Untuk pertanyaan dan support, dokumentasikan issue di kolom Notes dengan format:
- Date: [YYYY-MM-DD]
- Issue: [Deskripsi masalah]
- Status: [OPEN/RESOLVED]
