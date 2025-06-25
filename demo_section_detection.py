"""
Demo Document Section Detection
Demonstrasi multi-section document processing
"""

from document_section_detector import (
    create_section_detector,
    SectionType,
    create_section_api,
)


def demo_multi_section_document():
    """Demo complete multi-section document processing"""
    print("🚀 Demo Multi-Section Document Processing")
    print("=" * 60)

    # Initialize detector
    detector = create_section_detector()
    section_api = create_section_api()

    # Mock multi-section document
    mock_pages = [
        # Page 1: Lembar Disposisi
        """
        LEMBAR DISPOSISI

        Kepada: Kepala Dinas Pendidikan
        Dari: Sekretaris Daerah
        Perihal: Tindak Lanjut Surat Edaran Menteri
        Tanggal: 15 Desember 2024

        Mohon untuk ditindaklanjuti sesuai dengan ketentuan yang berlaku.

        Disposisi:
        - Koordinasi dengan unit terkait
        - Laporkan hasil pelaksanaan
        """,
        # Page 2-3: Nota Dinas
        """
        NOTA DINAS

        Kepada: Bapak Gubernur Aceh
        Dari: Kepala Dinas Pendidikan
        Nomor: 123/ND/2024
        Perihal: Laporan Pelaksanaan Program

        Dengan hormat,

        Bersama ini kami sampaikan laporan pelaksanaan program pendidikan
        di wilayah Aceh untuk periode 2024.

        Program yang telah dilaksanakan meliputi:
        1. Peningkatan kualitas guru
        2. Pembangunan infrastruktur sekolah
        3. Bantuan operasional sekolah
        """,
        # Page 4: Lampiran Tabel
        """
        LAMPIRAN 1
        TABEL DATA SEKOLAH

        No. | Nama Sekolah        | Jumlah Siswa | Status
        ----|--------------------|--------------|---------
        1   | SDN 1 Banda Aceh   | 450         | Negeri
        2   | SDN 2 Banda Aceh   | 380         | Negeri
        3   | SMP 1 Banda Aceh   | 520         | Negeri
        4   | SMA 1 Banda Aceh   | 680         | Negeri

        Total Siswa: 2,030 orang
        Total Sekolah: 4 unit
        """,
        # Page 5: Surat Pendukung
        """
        SURAT PENDUKUNG

        Nomor: 456/SP/2024
        Lampiran: 1 berkas
        Perihal: Referensi Program Pendidikan

        Kepada Yth.
        Bapak Menteri Pendidikan dan Kebudayaan
        di Jakarta

        Dengan hormat,

        Sebagai referensi dan pendukung laporan yang telah disampaikan,
        bersama ini kami lampirkan dokumen-dokumen terkait pelaksanaan
        program pendidikan di Aceh.

        Demikian surat ini kami sampaikan untuk menjadi perhatian.

        Hormat kami,
        Kepala Dinas Pendidikan Aceh
        """,
    ]

    print(f"📄 Processing document dengan {len(mock_pages)} halaman...")

    # Detect sections
    sections = detector.detect_sections(mock_pages)

    print(f"\n🔍 Section Detection Results:")
    print(f"   Total sections detected: {len(sections)}")

    for i, section in enumerate(sections):
        print(f"\n   {i+1}. {section.section_type.value.upper()}")
        print(f"      Title: {section.title}")
        print(f"      Pages: {section.page_start+1}-{section.page_end+1}")
        print(f"      Confidence: {section.confidence:.2f}")
        print(f"      Keywords: {', '.join(section.keywords[:5])}")
        print(f"      Content length: {len(section.content)} chars")

    # Demo selective extraction
    print(f"\n🎯 Selective Section Extraction Demo:")

    # Extract only Disposisi
    disposisi = detector.extract_section(sections, SectionType.DISPOSISI)
    if disposisi:
        print(f"\n📋 DISPOSISI SECTION:")
        print(f"   Title: {disposisi.title}")
        print(f"   Content preview: {disposisi.content[:200]}...")

    # Extract only Lampiran Tabel
    tabel = detector.extract_section(sections, SectionType.LAMPIRAN_TABEL)
    if tabel:
        print(f"\n📊 TABEL SECTION:")
        print(f"   Title: {tabel.title}")
        print(f"   Content preview: {tabel.content[:200]}...")

    # API Demo
    print(f"\n🌐 API Processing Demo:")
    api_result = section_api.process_multi_section_document(mock_pages)

    print(f"   API Result:")
    print(f"   • Total pages: {api_result['total_pages']}")
    print(f"   • Sections detected: {api_result['sections_detected']}")
    print(f"   • Section types: {list(api_result['section_map'].keys())}")

    # Specific section extraction via API
    disposisi_content = section_api.get_section_content(mock_pages, "disposisi")
    if disposisi_content:
        print(f"\n   📋 API Section Extraction (Disposisi):")
        print(f"      Type: {disposisi_content['type']}")
        print(f"      Pages: {disposisi_content['pages']}")
        print(f"      Confidence: {disposisi_content['confidence']:.2f}")

    print(f"\n🎉 Multi-Section Processing Demo Completed!")


def demo_use_cases():
    """Demo real-world use cases"""
    print(f"\n" + "=" * 60)
    print(f"💼 Real-World Use Cases")

    use_cases = [
        {
            "scenario": "Government Document Processing",
            "need": "Extract only 'Disposisi' untuk workflow routing",
            "solution": "GET /sections/{task_id}/disposisi",
            "benefit": "Automated document routing tanpa manual review",
        },
        {
            "scenario": "Report Generation",
            "need": "Extract only 'Lampiran Tabel' untuk data analysis",
            "solution": "GET /sections/{task_id}/lampiran_tabel",
            "benefit": "Direct data extraction untuk dashboard/analytics",
        },
        {
            "scenario": "Reference Management",
            "need": "Extract 'Surat Pendukung' untuk document linking",
            "solution": "GET /sections/{task_id}/surat_pendukung",
            "benefit": "Automated reference tracking dan linking",
        },
        {
            "scenario": "Multi-System Integration",
            "need": "Route different sections ke different systems",
            "solution": "Section-based API calls dengan selective processing",
            "benefit": "Efficient system integration tanpa data noise",
        },
    ]

    for i, case in enumerate(use_cases, 1):
        print(f"\n   {i}. {case['scenario']}")
        print(f"      Need: {case['need']}")
        print(f"      Solution: {case['solution']}")
        print(f"      Benefit: {case['benefit']}")


if __name__ == "__main__":
    demo_multi_section_document()
    demo_use_cases()

    print(f"\n" + "=" * 60)
    print(f"🎯 SOLUTION SUMMARY:")
    print(f"✅ Multi-section document detection")
    print(f"✅ Selective section extraction")
    print(f"✅ API-based section access")
    print(f"✅ Integration dengan existing system")
    print(f"✅ Real-world use case support")
    print(f"\n🚀 READY FOR PRODUCTION!")
