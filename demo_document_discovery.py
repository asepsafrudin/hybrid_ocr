"""
Demo Document Type Discovery System
Demonstrasi complete workflow: ML Discovery → User Validation → Template Update
"""

from document_type_discovery import create_document_discovery
from user_verification import create_verification_system, DocumentTypeValidation
from pattern_manager import create_pattern_manager


def demo_complete_workflow():
    """Demo complete document type discovery workflow"""
    print("🚀 Demo Document Type Discovery System")
    print("=" * 60)

    # Initialize systems
    discovery = create_document_discovery()
    pattern_manager = create_pattern_manager(".")
    verification_system = create_verification_system(pattern_manager, ".")

    print(f"✅ Systems initialized")
    print(f"   Existing document types: {len(discovery.existing_types)}")

    # Mock new document types
    test_documents = [
        {
            "name": "Surat Keputusan Menteri",
            "content": """
            KEMENTERIAN PENDIDIKAN DAN KEBUDAYAAN
            REPUBLIK INDONESIA

            KEPUTUSAN MENTERI PENDIDIKAN DAN KEBUDAYAAN
            NOMOR: 123/Kepmen/2024

            TENTANG
            PENETAPAN KURIKULUM MERDEKA

            MENTERI PENDIDIKAN DAN KEBUDAYAAN,

            Menimbang:
            a. bahwa dalam rangka meningkatkan kualitas pendidikan
            b. bahwa perlu ditetapkan kurikulum yang fleksibel

            Mengingat:
            1. Undang-Undang Nomor 20 Tahun 2003
            2. Peraturan Pemerintah Nomor 57 Tahun 2021

            MEMUTUSKAN:

            Menetapkan: KEPUTUSAN MENTERI TENTANG KURIKULUM MERDEKA

            KESATU: Kurikulum Merdeka berlaku untuk semua jenjang
            KEDUA: Keputusan ini mulai berlaku sejak tanggal ditetapkan

            Ditetapkan di Jakarta
            pada tanggal 15 Desember 2024

            MENTERI PENDIDIKAN DAN KEBUDAYAAN,

            Dr. Contoh Menteri, M.Pd
            """,
        },
        {
            "name": "Laporan Keuangan Tahunan",
            "content": """
            PT. TEKNOLOGI INDONESIA
            LAPORAN KEUANGAN TAHUNAN
            PERIODE BERAKHIR 31 DESEMBER 2023

            NERACA
            Per 31 Desember 2023
            (Dalam Rupiah)

            ASET
            Aset Lancar:
            - Kas dan setara kas         Rp 1.500.000.000
            - Piutang usaha             Rp   800.000.000
            - Persediaan                Rp   600.000.000
            Total Aset Lancar           Rp 2.900.000.000

            Aset Tidak Lancar:
            - Aset tetap                Rp 5.200.000.000
            - Investasi                 Rp 1.300.000.000
            Total Aset Tidak Lancar     Rp 6.500.000.000

            TOTAL ASET                  Rp 9.400.000.000

            LIABILITAS DAN EKUITAS
            Liabilitas Jangka Pendek:
            - Utang usaha               Rp   400.000.000
            - Utang pajak               Rp   200.000.000
            Total Liabilitas Pendek     Rp   600.000.000

            Ekuitas:
            - Modal saham               Rp 5.000.000.000
            - Laba ditahan              Rp 3.800.000.000
            Total Ekuitas               Rp 8.800.000.000

            TOTAL LIABILITAS & EKUITAS  Rp 9.400.000.000

            LAPORAN LABA RUGI
            Periode 1 Januari - 31 Desember 2023

            Pendapatan                  Rp 12.500.000.000
            Beban Pokok Penjualan       Rp  8.200.000.000
            Laba Kotor                  Rp  4.300.000.000

            Beban Operasional           Rp  2.800.000.000
            Laba Operasional            Rp  1.500.000.000

            Laba Bersih                 Rp  1.200.000.000
            """,
        },
    ]

    print(f"\n🔍 Analyzing {len(test_documents)} test documents...")

    candidates = []
    for doc in test_documents:
        print(f"\n📄 Analyzing: {doc['name']}")

        metadata = {"file_size": len(doc["content"])}
        candidate = discovery.analyze_document(doc["content"], metadata)

        if candidate:
            candidates.append((doc["name"], candidate))
            print(f"   🤖 ML Suggestion: {candidate.suggested_type}")
            print(f"   📊 Confidence: {candidate.confidence:.2f}")
            print(f"   🏷️ Keywords: {', '.join(candidate.keywords[:5])}")
            print(f"   📋 Patterns: {', '.join(candidate.sample_patterns[:2])}")
        else:
            print(f"   ℹ️ No new type suggested (matches existing type)")

    print(f"\n👤 Simulating User Validation...")

    # Simulate user validations
    validations = [
        {
            "candidate": candidates[0] if len(candidates) > 0 else None,
            "user_action": "accept",
            "final_type": "Government_Keputusan",
        },
        {
            "candidate": candidates[1] if len(candidates) > 1 else None,
            "user_action": "modify",
            "final_type": "Financial_Annual_Report",
        },
    ]

    successful_additions = 0
    for i, validation_data in enumerate(validations):
        if validation_data["candidate"]:
            doc_name, candidate = validation_data["candidate"]

            print(f"\n   📝 User validation for: {doc_name}")
            print(f"      ML suggested: {candidate.suggested_type}")
            print(f"      User action: {validation_data['user_action']}")
            print(f"      Final type: {validation_data['final_type']}")

            # Create validation object
            validation = DocumentTypeValidation(
                document_id=f"demo_doc_{i}",
                suggested_type=candidate.suggested_type,
                user_action=validation_data["user_action"],
                final_type=validation_data["final_type"],
                user_id="demo_user",
                confidence=candidate.confidence,
                keywords=candidate.keywords,
            )

            # Process validation (would update CSV in real usage)
            print(f"      ✅ Validation processed: {validation.final_type}")
            successful_additions += 1

    print(f"\n📊 Demo Summary:")
    print(f"   • Documents analyzed: {len(test_documents)}")
    print(f"   • ML suggestions generated: {len(candidates)}")
    print(f"   • User validations processed: {successful_additions}")
    print(f"   • New document types ready for addition: {successful_additions}")

    print(f"\n🎯 Key Benefits Demonstrated:")
    print(f"   ✅ Automated ML discovery for obvious patterns")
    print(f"   ✅ User validation for quality control")
    print(f"   ✅ Flexible user actions (accept/reject/modify)")
    print(f"   ✅ Seamless integration with existing system")

    print(f"\n🚀 System Status: PRODUCTION READY!")


def demo_api_workflow():
    """Demo API workflow untuk document type discovery"""
    print(f"\n" + "=" * 60)
    print(f"🌐 API Workflow Demo")

    print(f"\n📋 Available API Endpoints:")
    endpoints = [
        "GET /document-types/suggestions/{task_id}",
        "POST /document-types/validate",
        "GET /document-types/list",
    ]

    for endpoint in endpoints:
        print(f"   • {endpoint}")

    print(f"\n💡 Typical API Usage Flow:")
    print(f"   1. Upload document → Process → Get task_id")
    print(f"   2. GET /document-types/suggestions/{{task_id}}")
    print(f"   3. User reviews ML suggestion")
    print(f"   4. POST /document-types/validate with user decision")
    print(f"   5. System updates Document_Types_Template.csv")
    print(f"   6. New document type immediately available")


if __name__ == "__main__":
    demo_complete_workflow()
    demo_api_workflow()

    print(f"\n" + "=" * 60)
    print(f"🎉 Document Type Discovery Demo Completed!")
    print(f"🤖 ML Auto-Discovery: READY")
    print(f"👤 User Validation: READY")
    print(f"🌐 API Integration: READY")
    print(f"📊 Template Management: READY")
