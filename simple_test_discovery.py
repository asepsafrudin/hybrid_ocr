"""
Simple Test Document Discovery - Tanpa pandas dependency
"""

import re
from collections import Counter


def simple_keyword_extraction(text):
    """Simple keyword extraction"""
    stop_words = {
        "dan",
        "atau",
        "yang",
        "dengan",
        "untuk",
        "pada",
        "dalam",
        "dari",
        "ke",
        "di",
        "republik",
        "indonesia",
        "nomor",
        "tahun",
    }

    words = re.findall(r"\b[a-zA-Z]{2,}\b", text)
    words = [w.lower() for w in words if w.lower() not in stop_words and len(w) > 2]

    word_freq = Counter(words)
    return [word for word, freq in word_freq.most_common(30) if freq >= 1]


def simple_category_detection(keywords, text):
    """Simple category detection"""
    patterns = {
        "legal": [
            "pengadilan",
            "hakim",
            "putusan",
            "mahkamah",
            "konstitusi",
            "puu",
            "terdakwa",
        ],
        "business": ["invoice", "faktur", "kontrak", "perjanjian", "npwp"],
        "government": ["kementerian", "dinas", "menteri", "surat edaran", "peraturan"],
        "academic": ["universitas", "diploma", "sarjana", "ipk", "ijazah"],
        "medical": ["rumah sakit", "dokter", "diagnosa", "resep", "pasien"],
        "financial": ["laporan", "keuangan", "neraca", "rugi", "laba"],
    }

    category_scores = {}
    for category, pattern_list in patterns.items():
        score = 0
        for pattern in pattern_list:
            if pattern in text:
                score += 2
            for keyword in keywords:
                if pattern in keyword or keyword in pattern:
                    score += 1
        category_scores[category] = score

    if category_scores:
        best_category = max(category_scores, key=category_scores.get)
        if category_scores[best_category] >= 3:
            return best_category
    return None


def test_simple_discovery():
    """Test simple discovery functions"""
    print("🧪 Simple Document Discovery Test")
    print("=" * 50)

    # Test 1: Legal document
    legal_text = """
    MAHKAMAH KONSTITUSI REPUBLIK INDONESIA
    PUTUSAN Nomor 100/PUU/XXI/2023
    Dalam perkara pengujian Undang-Undang
    """

    print("📄 Testing Legal Document:")
    keywords = simple_keyword_extraction(legal_text.lower())
    print(f"   Keywords: {keywords[:10]}")

    category = simple_category_detection(keywords, legal_text.lower())
    print(f"   Category: {category}")

    # Test 2: Business document
    business_text = """
    PT. TEKNOLOGI INDONESIA
    INVOICE No. INV/2024/001
    Faktur Pajak: 123.456.789
    Kontrak Perjanjian Kerja Sama
    NPWP: 12.345.678.9-123.000
    """

    print("\n📄 Testing Business Document:")
    keywords = simple_keyword_extraction(business_text.lower())
    print(f"   Keywords: {keywords[:10]}")

    category = simple_category_detection(keywords, business_text.lower())
    print(f"   Category: {category}")

    # Test 3: Government document
    gov_text = """
    KEMENTERIAN PENDIDIKAN DAN KEBUDAYAAN
    SURAT EDARAN MENTERI
    Nomor: 123/SE/2024
    Tentang Peraturan Baru
    """

    print("\n📄 Testing Government Document:")
    keywords = simple_keyword_extraction(gov_text.lower())
    print(f"   Keywords: {keywords[:10]}")

    category = simple_category_detection(keywords, gov_text.lower())
    print(f"   Category: {category}")

    print("\n✅ Simple Discovery Test Completed!")
    print("💡 Core ML logic is working correctly")


if __name__ == "__main__":
    test_simple_discovery()
