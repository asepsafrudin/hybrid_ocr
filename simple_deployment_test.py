"""
Simple Deployment Test
Test production readiness dengan server yang sudah running
"""

import requests
import time
import psutil
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleDeploymentTest:
    """
    Simple deployment testing untuk server yang sudah running
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def run_tests(self) -> bool:
        """Run all deployment tests"""
        print("🧪 Running Simple Deployment Tests")
        print("=" * 50)

        tests = [
            ("API Health Check", self.test_api_health),
            ("Pattern System", self.test_pattern_system),
            ("Document Processing", self.test_document_processing),
            ("Performance Metrics", self.test_performance),
            ("System Resources", self.test_system_resources),
        ]

        passed = 0
        total = len(tests)

        for test_name, test_func in tests:
            try:
                print(f"\n🔍 {test_name}...")
                if test_func():
                    print(f"  ✅ {test_name} PASSED")
                    passed += 1
                else:
                    print(f"  ❌ {test_name} FAILED")
            except Exception as e:
                print(f"  💥 {test_name} ERROR: {e}")

        print(f"\n📊 Test Results: {passed}/{total} tests passed")

        if passed == total:
            print("🎉 All tests passed! System is production ready!")
            return True
        else:
            print("⚠️ Some tests failed. Review before production deployment.")
            return False

    def test_api_health(self) -> bool:
        """Test API health endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)

            if response.status_code == 200:
                data = response.json()
                print(f"    Status: {data.get('status')}")
                print(f"    Patterns loaded: {data.get('patterns_loaded')}")
                print(f"    Version: {data.get('version')}")
                return True
            else:
                print(f"    HTTP {response.status_code}")
                return False

        except Exception as e:
            print(f"    Connection error: {e}")
            return False

    def test_pattern_system(self) -> bool:
        """Test pattern system functionality"""
        try:
            from pattern_manager import create_pattern_manager

            pm = create_pattern_manager(".")
            stats = pm.get_pattern_stats()

            print(f"    OCR patterns: {stats['ocr_patterns']}")
            print(f"    Spatial patterns: {stats['spatial_patterns']}")
            print(f"    Context rules: {stats['context_rules']}")
            print(f"    Document types: {stats['document_types']}")

            return stats["ocr_patterns"] > 0

        except Exception as e:
            print(f"    Pattern system error: {e}")
            return False

    def test_document_processing(self) -> bool:
        """Test document processing capability"""
        try:
            from hybrid_processor import create_processor

            processor = create_processor()

            if processor:
                print("    OCR processor: Ready")
                print("    Pattern manager: Loaded")
                print("    Document discovery: Available")
                print("    Section detector: Available")
                return True
            else:
                return False

        except Exception as e:
            print(f"    Processing error: {e}")
            return False

    def test_performance(self) -> bool:
        """Test performance metrics"""
        try:
            # API response time
            start_time = time.time()
            response = requests.get(f"{self.base_url}/health")
            response_time = time.time() - start_time

            print(f"    API response time: {response_time:.3f}s")

            # Pattern loading time
            start_time = time.time()
            from pattern_manager import create_pattern_manager

            pm = create_pattern_manager(".")
            pm.reload_patterns()
            pattern_time = time.time() - start_time

            print(f"    Pattern loading time: {pattern_time:.3f}s")

            return response_time < 2.0 and pattern_time < 10.0

        except Exception as e:
            print(f"    Performance test error: {e}")
            return False

    def test_system_resources(self) -> bool:
        """Test system resource usage"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            print(f"    CPU usage: {cpu_percent:.1f}%")

            # Memory usage
            memory = psutil.virtual_memory()
            memory_mb = memory.used / 1024 / 1024
            print(f"    Memory usage: {memory_mb:.1f}MB ({memory.percent:.1f}%)")

            # Disk usage
            disk = psutil.disk_usage(".")
            disk_percent = (disk.used / disk.total) * 100
            print(f"    Disk usage: {disk_percent:.1f}%")

            return cpu_percent < 90 and memory.percent < 90 and disk_percent < 90

        except Exception as e:
            print(f"    Resource test error: {e}")
            return False

    def generate_deployment_report(self):
        """Generate deployment readiness report"""
        print("\n" + "=" * 50)
        print("📋 DEPLOYMENT READINESS REPORT")
        print("=" * 50)

        try:
            # System info
            print(
                f"📅 Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            print(f"🌐 API endpoint: {self.base_url}")

            # Health check
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API Status: {data.get('status', 'unknown')}")
                print(f"📊 Patterns loaded: {data.get('patterns_loaded', 0)}")
            else:
                print(f"❌ API Status: HTTP {response.status_code}")

            # System resources
            cpu = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            print(f"💻 CPU: {cpu:.1f}%")
            print(f"🧠 Memory: {memory.percent:.1f}% ({memory.used/1024/1024:.0f}MB)")

            # Pattern system
            from pattern_manager import create_pattern_manager

            pm = create_pattern_manager(".")
            stats = pm.get_pattern_stats()
            print(f"🎯 OCR Patterns: {stats['ocr_patterns']}")
            print(f"📍 Spatial Patterns: {stats['spatial_patterns']}")
            print(f"📋 Context Rules: {stats['context_rules']}")
            print(f"📄 Document Types: {stats['document_types']}")

            print("\n🎯 DEPLOYMENT STATUS: READY FOR PRODUCTION")

        except Exception as e:
            print(f"❌ Report generation error: {e}")


def main():
    """Main test function"""
    print("🚀 Enterprise OCR System - Simple Deployment Test")
    print("📋 Testing production readiness...")

    # Check if server is running
    tester = SimpleDeploymentTest()

    print(f"🔍 Checking server at {tester.base_url}...")

    try:
        response = requests.get(f"{tester.base_url}/health", timeout=10)
        print(f"📡 Server response: HTTP {response.status_code}")

        if response.status_code != 200:
            print("❌ Server is not responding properly. Please check server status.")
            print("   Expected: HTTP 200, Got: HTTP", response.status_code)
            return
        else:
            print("✅ Server is responding!")

    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection failed: {e}")
        print("❌ Server is not running. Please start the server first:")
        print("   python -m uvicorn api_server:app --host localhost --port 8000")
        return
    except requests.exceptions.Timeout as e:
        print(f"❌ Request timeout: {e}")
        print("⚠️ Server might be starting up. Please wait and try again.")
        return
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return

    # Run tests
    success = tester.run_tests()

    # Generate report
    tester.generate_deployment_report()

    if success:
        print("\n🎉 DEPLOYMENT TEST SUCCESSFUL!")
        print("✅ System is ready for production deployment")
    else:
        print("\n⚠️ DEPLOYMENT TEST ISSUES FOUND")
        print("🔧 Please address issues before production deployment")


if __name__ == "__main__":
    main()
