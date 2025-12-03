#!/usr/bin/env python3
# ========================================
# Automated Test Runner Script
# ========================================

import os
import sys
import subprocess
import argparse
import json
import time
from pathlib import Path
from datetime import datetime
import webbrowser

# เพิ่ม project path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestRunner:
    """คลาสสำหรับรันการทดสอบแบบอัตโนมัติ"""
    
    def __init__(self):
        self.project_root = project_root
        self.test_dir = self.project_root / "09_Testing"
        self.reports_dir = self.test_dir / "reports"
        self.reports_dir.mkdir(exist_ok=True)
        
        # สร้าง timestamp สำหรับ report
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def run_unit_tests(self, verbose=False, coverage=False):
        """รัน Unit Tests"""
        print("🧪 Running Unit Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir),
            "-m", "unit",
            "--tb=short"
        ]
        
        if verbose:
            cmd.append("-v")
        
        if coverage:
            cmd.extend([
                "--cov=.",
                "--cov-report=html:reports/coverage_unit",
                "--cov-report=term-missing"
            ])
        
        # เพิ่ม JUnit XML report
        cmd.extend([
            "--junit-xml", f"reports/unit_tests_{self.timestamp}.xml"
        ])
        
        return self._run_command(cmd, "Unit Tests")
    
    def run_integration_tests(self, verbose=False):
        """รัน Integration Tests"""
        print("🔗 Running Integration Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir),
            "-m", "integration",
            "--tb=short"
        ]
        
        if verbose:
            cmd.append("-v")
        
        # เพิ่ม JUnit XML report
        cmd.extend([
            "--junit-xml", f"reports/integration_tests_{self.timestamp}.xml"
        ])
        
        return self._run_command(cmd, "Integration Tests")
    
    def run_performance_tests(self, verbose=False):
        """รัน Performance Tests"""
        print("⚡ Running Performance Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir),
            "-m", "performance",
            "--tb=short",
            "--benchmark-only",
            "--benchmark-json", f"reports/benchmark_{self.timestamp}.json"
        ]
        
        if verbose:
            cmd.append("-v")
        
        return self._run_command(cmd, "Performance Tests")
    
    def run_hardware_tests(self, verbose=False):
        """รัน Hardware Tests (ต้องมี hardware)"""
        print("🔧 Running Hardware Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir),
            "-m", "hardware",
            "--tb=short"
        ]
        
        if verbose:
            cmd.append("-v")
        
        # เพิ่ม JUnit XML report
        cmd.extend([
            "--junit-xml", f"reports/hardware_tests_{self.timestamp}.xml"
        ])
        
        return self._run_command(cmd, "Hardware Tests")
    
    def run_network_tests(self, verbose=False):
        """รัน Network Tests (ต้องมี internet)"""
        print("🌐 Running Network Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir),
            "-m", "network",
            "--tb=short"
        ]
        
        if verbose:
            cmd.append("-v")
        
        # เพิ่ม JUnit XML report
        cmd.extend([
            "--junit-xml", f"reports/network_tests_{self.timestamp}.xml"
        ])
        
        return self._run_command(cmd, "Network Tests")
    
    def run_all_tests(self, verbose=False, coverage=False, skip_slow=False):
        """รันการทดสอบทั้งหมด"""
        print("🚀 Running All Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir),
            "--tb=short"
        ]
        
        if verbose:
            cmd.append("-v")
        
        if skip_slow:
            cmd.extend(["-m", "not slow"])
        
        if coverage:
            cmd.extend([
                "--cov=.",
                "--cov-report=html:reports/coverage_all",
                "--cov-report=term-missing",
                "--cov-report=json:reports/coverage.json"
            ])
        
        # เพิ่ม JUnit XML report
        cmd.extend([
            "--junit-xml", f"reports/all_tests_{self.timestamp}.xml"
        ])
        
        return self._run_command(cmd, "All Tests")
    
    def run_specific_test(self, test_path, verbose=False):
        """รันการทดสอบเฉพาะ"""
        print(f"🎯 Running Specific Test: {test_path}")
        
        cmd = [
            "python", "-m", "pytest",
            str(test_path),
            "--tb=short"
        ]
        
        if verbose:
            cmd.append("-v")
        
        return self._run_command(cmd, f"Test: {test_path}")
    
    def run_failed_tests(self, verbose=False):
        """รันการทดสอบที่ fail ในครั้งก่อน"""
        print("🔄 Running Failed Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            "--lf",  # last failed
            "--tb=short"
        ]
        
        if verbose:
            cmd.append("-v")
        
        return self._run_command(cmd, "Failed Tests")
    
    def _run_command(self, cmd, test_type):
        """รันคำสั่งและจัดการผลลัพธ์"""
        start_time = time.time()
        
        try:
            # เปลี่ยน working directory
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # บันทึกผลลัพธ์
            self._save_test_result(test_type, result, duration)
            
            if result.returncode == 0:
                print(f"✅ {test_type} passed in {duration:.2f}s")
                return True
            else:
                print(f"❌ {test_type} failed in {duration:.2f}s")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {test_type} timed out after 5 minutes")
            return False
        except Exception as e:
            print(f"💥 Error running {test_type}: {e}")
            return False
    
    def _save_test_result(self, test_type, result, duration):
        """บันทึกผลลัพธ์การทดสอบ"""
        result_data = {
            "test_type": test_type,
            "timestamp": self.timestamp,
            "duration": duration,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
        
        result_file = self.reports_dir / f"{test_type.lower().replace(' ', '_')}_{self.timestamp}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False)
    
    def generate_html_report(self):
        """สร้าง HTML report รวม"""
        print("📊 Generating HTML Report...")
        
        html_content = self._create_html_report()
        report_file = self.reports_dir / f"test_report_{self.timestamp}.html"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"📄 Report saved: {report_file}")
        return report_file
    
    def _create_html_report(self):
        """สร้างเนื้อหา HTML report"""
        # อ่านผลลัพธ์จากไฟล์ JSON
        results = []
        for json_file in self.reports_dir.glob(f"*_{self.timestamp}.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    results.append(json.load(f))
            except Exception:
                continue
        
        html = f"""
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Report - {self.timestamp}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; text-align: center; margin-bottom: 30px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .summary-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; }}
        .summary-card h3 {{ margin: 0 0 10px 0; }}
        .summary-card .number {{ font-size: 2em; font-weight: bold; }}
        .test-result {{ margin-bottom: 20px; padding: 15px; border-radius: 8px; border-left: 5px solid; }}
        .test-result.success {{ background-color: #d4edda; border-color: #28a745; }}
        .test-result.failure {{ background-color: #f8d7da; border-color: #dc3545; }}
        .test-result h3 {{ margin: 0 0 10px 0; }}
        .test-details {{ font-size: 0.9em; color: #666; }}
        .duration {{ font-weight: bold; color: #007bff; }}
        .timestamp {{ color: #6c757d; font-size: 0.8em; }}
        pre {{ background: #f8f9fa; padding: 10px; border-radius: 5px; overflow-x: auto; font-size: 0.8em; }}
        .footer {{ text-align: center; margin-top: 30px; color: #6c757d; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 Test Report</h1>
        <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="summary">
            <div class="summary-card">
                <h3>Total Tests</h3>
                <div class="number">{len(results)}</div>
            </div>
            <div class="summary-card">
                <h3>Passed</h3>
                <div class="number">{sum(1 for r in results if r.get('success', False))}</div>
            </div>
            <div class="summary-card">
                <h3>Failed</h3>
                <div class="number">{sum(1 for r in results if not r.get('success', False))}</div>
            </div>
            <div class="summary-card">
                <h3>Total Duration</h3>
                <div class="number">{sum(r.get('duration', 0) for r in results):.1f}s</div>
            </div>
        </div>
        
        <div class="test-results">
"""
        
        for result in results:
            success_class = "success" if result.get('success', False) else "failure"
            status_icon = "✅" if result.get('success', False) else "❌"
            
            html += f"""
            <div class="test-result {success_class}">
                <h3>{status_icon} {result.get('test_type', 'Unknown Test')}</h3>
                <div class="test-details">
                    <span class="duration">Duration: {result.get('duration', 0):.2f}s</span> | 
                    <span>Return Code: {result.get('return_code', 'N/A')}</span>
                </div>
"""
            
            if result.get('stdout'):
                html += f"<details><summary>Output</summary><pre>{result['stdout']}</pre></details>"
            
            if result.get('stderr'):
                html += f"<details><summary>Errors</summary><pre>{result['stderr']}</pre></details>"
            
            html += "</div>"
        
        html += """
        </div>
        
        <div class="footer">
            <p>Generated by Automated Test Runner</p>
        </div>
    </div>
</body>
</html>
"""
        return html
    
    def open_coverage_report(self):
        """เปิด coverage report ในเบราว์เซอร์"""
        coverage_file = self.reports_dir / "coverage_all" / "index.html"
        if coverage_file.exists():
            webbrowser.open(f"file://{coverage_file.absolute()}")
            print(f"🌐 Coverage report opened: {coverage_file}")
        else:
            print("❌ Coverage report not found. Run tests with --coverage first.")
    
    def clean_reports(self):
        """ลบ reports เก่า"""
        print("🧹 Cleaning old reports...")
        
        for file in self.reports_dir.glob("*"):
            if file.is_file():
                file.unlink()
            elif file.is_dir():
                import shutil
                shutil.rmtree(file)
        
        print("✅ Reports cleaned")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Automated Test Runner")
    
    # Test types
    parser.add_argument("--unit", action="store_true", help="Run unit tests")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--hardware", action="store_true", help="Run hardware tests")
    parser.add_argument("--network", action="store_true", help="Run network tests")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--failed", action="store_true", help="Run only failed tests")
    
    # Options
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--skip-slow", action="store_true", help="Skip slow tests")
    parser.add_argument("--test", type=str, help="Run specific test file")
    
    # Reports
    parser.add_argument("--report", action="store_true", help="Generate HTML report")
    parser.add_argument("--open-coverage", action="store_true", help="Open coverage report")
    parser.add_argument("--clean", action="store_true", help="Clean old reports")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    # Clean reports if requested
    if args.clean:
        runner.clean_reports()
        return
    
    # Open coverage report if requested
    if args.open_coverage:
        runner.open_coverage_report()
        return
    
    # Run tests
    results = []
    
    if args.unit:
        results.append(runner.run_unit_tests(args.verbose, args.coverage))
    
    if args.integration:
        results.append(runner.run_integration_tests(args.verbose))
    
    if args.performance:
        results.append(runner.run_performance_tests(args.verbose))
    
    if args.hardware:
        results.append(runner.run_hardware_tests(args.verbose))
    
    if args.network:
        results.append(runner.run_network_tests(args.verbose))
    
    if args.all:
        results.append(runner.run_all_tests(args.verbose, args.coverage, args.skip_slow))
    
    if args.failed:
        results.append(runner.run_failed_tests(args.verbose))
    
    if args.test:
        results.append(runner.run_specific_test(args.test, args.verbose))
    
    # ถ้าไม่ได้เลือกอะไร ให้รัน unit tests
    if not any([args.unit, args.integration, args.performance, 
                args.hardware, args.network, args.all, args.failed, args.test]):
        print("No test type specified. Running unit tests...")
        results.append(runner.run_unit_tests(args.verbose, args.coverage))
    
    # Generate HTML report if requested
    if args.report or len(results) > 1:
        report_file = runner.generate_html_report()
        webbrowser.open(f"file://{report_file.absolute()}")
    
    # Summary
    if results:
        passed = sum(results)
        total = len(results)
        print(f"\n📊 Summary: {passed}/{total} test suites passed")
        
        if passed == total:
            print("🎉 All tests passed!")
            sys.exit(0)
        else:
            print("💥 Some tests failed!")
            sys.exit(1)

if __name__ == "__main__":
    main()