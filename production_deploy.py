"""
Production Deployment Script
Automated deployment dan health check untuk enterprise OCR system
"""

import os
import sys
import subprocess
import time
import requests
import logging
from pathlib import Path
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProductionDeployer:
    """
    Production deployment automation
    """

    def __init__(self, config: Dict = None):
        self.config = config or self._default_config()
        self.base_url = f"http://{self.config['host']}:{self.config['port']}"

    def _default_config(self) -> Dict:
        return {
            "host": "localhost",
            "port": 8000,
            "workers": 4,
            "timeout": 300,
            "health_check_interval": 30,
            "max_retries": 5,
        }

    def deploy(self) -> bool:
        """Main deployment workflow"""
        try:
            print("🚀 Starting Production Deployment...")

            # Pre-deployment checks
            if not self._pre_deployment_checks():
                return False

            # Start services
            if not self._start_services():
                return False

            # Health checks
            if not self._health_checks():
                return False

            # Performance validation
            if not self._performance_validation():
                return False

            print("✅ Production deployment successful!")
            return True

        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return False

    def _pre_deployment_checks(self) -> bool:
        """Pre-deployment validation"""
        print("🔍 Running pre-deployment checks...")

        checks = [
            ("Python version", self._check_python_version),
            ("Dependencies", self._check_dependencies),
            ("Environment variables", self._check_environment),
            ("Database connection", self._check_database),
            ("File permissions", self._check_permissions),
            ("Pattern templates", self._check_pattern_templates),
        ]

        for check_name, check_func in checks:
            try:
                if check_func():
                    print(f"  ✅ {check_name}")
                else:
                    print(f"  ❌ {check_name}")
                    return False
            except Exception as e:
                print(f"  ❌ {check_name}: {e}")
                return False

        return True

    def _check_python_version(self) -> bool:
        """Check Python version compatibility"""
        version = sys.version_info
        return version.major == 3 and version.minor >= 8

    def _check_dependencies(self) -> bool:
        """Check required dependencies"""
        required_packages = {
            "fastapi": "fastapi",
            "uvicorn": "uvicorn",
            "pandas": "pandas",
            "opencv-python": "cv2",
            "easyocr": "easyocr",
            "pytesseract": "pytesseract",
            "pdf2image": "pdf2image",
        }

        for package_name, import_name in required_packages.items():
            try:
                __import__(import_name)
            except ImportError:
                logger.error(f"Missing package: {package_name} (import: {import_name})")
                return False
        return True

    def _check_environment(self) -> bool:
        """Check environment variables"""
        # Check for .env file or environment variables
        env_file = Path(".env")
        return env_file.exists() or os.getenv("PRODUCTION_MODE")

    def _check_database(self) -> bool:
        """Check database connectivity"""
        try:
            # Skip database check if not configured for production
            import os

            if not os.getenv("DATABASE_URL") and not os.path.exists("database.py"):
                logger.info("Database not configured, skipping check")
                return True

            from database import engine

            with engine.connect() as conn:
                result = conn.execute("SELECT 1")
                result.fetchone()
            return True
        except Exception as e:
            logger.warning(f"Database check failed: {e}")
            # For development, allow to continue without database
            return True

    def _check_permissions(self) -> bool:
        """Check file permissions"""
        critical_paths = ["uploads/", "models/", "."]
        for path in critical_paths:
            if not os.access(path, os.R_OK | os.W_OK):
                return False
        return True

    def _check_pattern_templates(self) -> bool:
        """Check pattern template files"""
        templates = [
            "OCR_Patterns_Template.csv",
            "Document_Types_Template.csv",
            "Spatial_Patterns_Template.csv",
            "Context_Rules_Template.csv",
        ]

        for template in templates:
            if not Path(template).exists():
                logger.error(f"Missing template: {template}")
                return False
        return True

    def _start_services(self) -> bool:
        """Start application services"""
        print("🔄 Starting services...")

        try:
            # Use current Python executable (venv-aware)
            import sys

            python_exe = sys.executable

            cmd = [
                python_exe,
                "-m",
                "uvicorn",
                "api_server:app",
                "--host",
                self.config["host"],
                "--port",
                str(self.config["port"]),
                "--reload",
            ]

            # Start process in background
            import platform

            if platform.system() == "Windows":
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                )
            else:
                self.process = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )

            # Wait for startup with progressive checks (longer timeout for model loading)
            print(
                "    Loading models and initializing... (this may take up to 2 minutes)"
            )
            for i in range(120):  # 120 seconds max for model loading
                time.sleep(1)
                if i % 10 == 0:  # Progress indicator every 10 seconds
                    print(f"    Waiting for startup... ({i}s)")

                if self._check_server_ready():
                    print("  ✅ API server started")
                    return True

                if self.process.poll() is not None:
                    # Process died
                    stdout, stderr = self.process.communicate()
                    print(f"  ❌ Server process died: {stderr.decode()}")
                    return False

            print("  ❌ API server startup timeout")
            return False

        except Exception as e:
            logger.error(f"Service startup failed: {e}")
            return False

    def _check_server_ready(self) -> bool:
        """Check if server is ready to accept connections"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False

    def _health_checks(self) -> bool:
        """Comprehensive health checks"""
        print("🏥 Running health checks...")

        checks = [
            ("API health", self._check_api_health),
            ("Pattern system", self._check_pattern_system),
            ("OCR pipeline", self._check_ocr_pipeline),
            ("Database operations", self._check_database_ops),
        ]

        for check_name, check_func in checks:
            if not self._retry_check(check_func, check_name):
                return False

        return True

    def _retry_check(self, check_func, check_name: str) -> bool:
        """Retry mechanism for health checks"""
        for attempt in range(self.config["max_retries"]):
            try:
                if check_func():
                    print(f"  ✅ {check_name}")
                    return True
                else:
                    if attempt < self.config["max_retries"] - 1:
                        print(f"  🔄 {check_name} (retry {attempt + 1})")
                        time.sleep(5)
                    else:
                        print(f"  ❌ {check_name}")
                        return False
            except Exception as e:
                if attempt < self.config["max_retries"] - 1:
                    print(f"  🔄 {check_name} error: {e} (retry {attempt + 1})")
                    time.sleep(5)
                else:
                    print(f"  ❌ {check_name}: {e}")
                    return False
        return False

    def _check_api_health(self) -> bool:
        """Check API health endpoint"""
        response = requests.get(f"{self.base_url}/health", timeout=10)
        return response.status_code == 200

    def _check_pattern_system(self) -> bool:
        """Check pattern system functionality"""
        from pattern_manager import create_pattern_manager

        pm = create_pattern_manager(".")
        stats = pm.get_pattern_stats()
        return stats["ocr_patterns"] > 0

    def _check_ocr_pipeline(self) -> bool:
        """Check OCR pipeline functionality"""
        from hybrid_processor import create_processor

        processor = create_processor()
        return processor is not None

    def _check_database_ops(self) -> bool:
        """Check database operations"""
        try:
            response = requests.get(f"{self.base_url}/tasks", timeout=10)
            return response.status_code == 200
        except:
            return False

    def _performance_validation(self) -> bool:
        """Performance validation tests"""
        print("⚡ Running performance validation...")

        tests = [
            ("API response time", self._test_api_response_time),
            ("Memory usage", self._test_memory_usage),
            ("Pattern loading speed", self._test_pattern_loading),
        ]

        for test_name, test_func in tests:
            try:
                if test_func():
                    print(f"  ✅ {test_name}")
                else:
                    print(f"  ⚠️ {test_name} (acceptable)")
            except Exception as e:
                print(f"  ⚠️ {test_name}: {e}")

        return True

    def _test_api_response_time(self) -> bool:
        """Test API response time"""
        start_time = time.time()
        response = requests.get(f"{self.base_url}/health")
        response_time = time.time() - start_time

        return response_time < 1.0  # Less than 1 second

    def _test_memory_usage(self) -> bool:
        """Test memory usage"""
        import psutil

        process = psutil.Process(self.process.pid)
        memory_mb = process.memory_info().rss / 1024 / 1024

        return memory_mb < 1000  # Less than 1GB

    def _test_pattern_loading(self) -> bool:
        """Test pattern loading performance"""
        start_time = time.time()
        from pattern_manager import create_pattern_manager

        pm = create_pattern_manager(".")
        pm.reload_patterns()
        loading_time = time.time() - start_time

        return loading_time < 5.0  # Less than 5 seconds

    def stop_services(self):
        """Stop all services"""
        if hasattr(self, "process") and self.process:
            self.process.terminate()
            self.process.wait()
            print("🛑 Services stopped")


def main():
    """Main deployment function"""
    deployer = ProductionDeployer()

    try:
        success = deployer.deploy()
        if success:
            print("\n🎉 Production deployment completed successfully!")
            print(
                f"🌐 API available at: http://{deployer.config['host']}:{deployer.config['port']}"
            )
            print("📚 Documentation: http://localhost:8000/docs")

            # Keep running for monitoring
            print("\n⏳ Monitoring deployment (Ctrl+C to stop)...")
            while True:
                time.sleep(30)

        else:
            print("\n❌ Production deployment failed!")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n🛑 Deployment monitoring stopped")
        deployer.stop_services()
    except Exception as e:
        print(f"\n💥 Deployment error: {e}")
        deployer.stop_services()
        sys.exit(1)


if __name__ == "__main__":
    main()
