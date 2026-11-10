"""
TinyFish Demo Pre-Flight Test Script

Run this script before your presentation to verify all TinyFish functionality works.
Tests are ordered from fastest to slowest for quick verification.

Usage:
    python scripts/test_tinyfish_demo.py

Requirements:
    - TINYFISH_API_KEY configured in .env or config/api_keys.json
    - Node.js service dependencies installed (cd tinyfish_service && npm install)
    - Internet connection for API calls
"""

import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.logger import get_logger
from memory.config_manager import has_tinyfish_key, get_tinyfish_mode

log = get_logger(__name__)

# ANSI color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"

class TestResult:
    """Track test results for summary."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.warnings = 0
        self.start_time = time.time()
        self.tests = []

    def add_pass(self, name, duration):
        self.passed += 1
        self.tests.append((name, "PASS", duration, None))
        print(f"{GREEN}✓{RESET} {name} ({duration:.2f}s)")

    def add_fail(self, name, duration, error):
        self.failed += 1
        self.tests.append((name, "FAIL", duration, error))
        print(f"{RED}✗{RESET} {name} ({duration:.2f}s)")
        print(f"  {RED}Error: {error}{RESET}")

    def add_skip(self, name, reason):
        self.skipped += 1
        self.tests.append((name, "SKIP", 0, reason))
        print(f"{YELLOW}⊘{RESET} {name} - {reason}")

    def add_warning(self, name, duration, warning):
        self.warnings += 1
        self.tests.append((name, "WARN", duration, warning))
        print(f"{YELLOW}⚠{RESET} {name} ({duration:.2f}s)")
        print(f"  {YELLOW}Warning: {warning}{RESET}")

    def print_summary(self):
        total_time = time.time() - self.start_time
        total = self.passed + self.failed + self.skipped + self.warnings

        print("\n" + "=" * 70)
        print(f"{BOLD}TEST SUMMARY{RESET}")
        print("=" * 70)
        print(f"Total Tests:  {total}")
        print(f"{GREEN}Passed:       {self.passed}{RESET}")
        print(f"{RED}Failed:       {self.failed}{RESET}")
        print(f"{YELLOW}Warnings:     {self.warnings}{RESET}")
        print(f"{YELLOW}Skipped:      {self.skipped}{RESET}")
        print(f"Total Time:   {total_time:.2f}s")
        print("=" * 70)

        if self.failed > 0:
            print(f"\n{RED}⚠️  SOME TESTS FAILED - Review errors above{RESET}")
            return False
        elif self.warnings > 0:
            print(f"\n{YELLOW}⚠️  All tests passed with warnings{RESET}")
            return True
        else:
            print(f"\n{GREEN}✅ ALL TESTS PASSED - Ready for demo!{RESET}")
            return True


def print_header(title):
    """Print test section header."""
    print(f"\n{BLUE}{BOLD}{'─' * 70}{RESET}")
    print(f"{BLUE}{BOLD}{title}{RESET}")
    print(f"{BLUE}{BOLD}{'─' * 70}{RESET}\n")


def test_environment(results: TestResult):
    """Test 1: Environment Setup"""
    print_header("TEST 1: Environment Setup")

    # Check Python version
    start = time.time()
    try:
        version = sys.version_info
        if version.major == 3 and version.minor >= 11:
            results.add_pass(f"Python version ({version.major}.{version.minor})", time.time() - start)
        else:
            results.add_warning(
                f"Python version ({version.major}.{version.minor})",
                time.time() - start,
                "Python 3.11+ recommended"
            )
    except Exception as e:
        results.add_fail("Python version check", time.time() - start, str(e))

    # Check API key configuration
    start = time.time()
    try:
        if has_tinyfish_key():
            results.add_pass("TinyFish API key configured", time.time() - start)
        else:
            results.add_fail(
                "TinyFish API key configured",
                time.time() - start,
                "API key not found in .env or config/api_keys.json"
            )
    except Exception as e:
        results.add_fail("TinyFish API key check", time.time() - start, str(e))

    # Check Node.js installation
    start = time.time()
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            results.add_pass(f"Node.js installed ({version})", time.time() - start)
        else:
            results.add_fail("Node.js installed", time.time() - start, "Node.js not found")
    except FileNotFoundError:
        results.add_fail("Node.js installed", time.time() - start, "Node.js not found in PATH")
    except Exception as e:
        results.add_fail("Node.js installation check", time.time() - start, str(e))

    # Check service files exist
    start = time.time()
    try:
        base_dir = Path(__file__).parent.parent
        service_dir = base_dir / "tinyfish_service"
        index_js = service_dir / "index.js"

        if index_js.exists():
            results.add_pass("TinyFish service files present", time.time() - start)
        else:
            results.add_fail(
                "TinyFish service files present",
                time.time() - start,
                f"Service not found at {index_js}"
            )
    except Exception as e:
        results.add_fail("Service files check", time.time() - start, str(e))

    # Check dependencies installed
    start = time.time()
    try:
        node_modules = service_dir / "node_modules"
        if node_modules.exists() and (node_modules / "@tinyfish-ai").exists():
            results.add_pass("Node.js dependencies installed", time.time() - start)
        else:
            results.add_fail(
                "Node.js dependencies installed",
                time.time() - start,
                "Run: cd tinyfish_service && npm install"
            )
    except Exception as e:
        results.add_fail("Dependencies check", time.time() - start, str(e))


def test_service_connectivity(results: TestResult):
    """Test 2: Service Connectivity (Quick Ping)"""
    print_header("TEST 2: Service Connectivity")

    start = time.time()
    try:
        base_dir = Path(__file__).parent.parent
        service_entry = base_dir / "tinyfish_service" / "index.js"
        env_file = base_dir / ".env"

        # Quick test: run service with --version or minimal search
        cmd = [
            "node",
            f"--env-file={env_file}",
            str(service_entry),
            "search",
            "--query", "test",
            "--max-results", "1"
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=15,  # Fast timeout for connectivity test
            cwd=str(base_dir),
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )

        duration = time.time() - start

        if result.returncode == 0:
            # Try to parse response
            try:
                response = json.loads(result.stdout)
                if response.get("success"):
                    results.add_pass(f"Service responds to search ({duration:.1f}s)", duration)
                else:
                    error = response.get("error", "Unknown error")
                    if "API key" in error:
                        results.add_fail("Service responds to search", duration, "Invalid API key")
                    elif "rate limit" in error.lower():
                        results.add_warning("Service responds to search", duration, "Rate limited - wait before demo")
                    else:
                        results.add_fail("Service responds to search", duration, error)
            except json.JSONDecodeError:
                results.add_fail("Service responds to search", duration, "Invalid JSON response")
        else:
            error = result.stderr or result.stdout or "Unknown error"
            results.add_fail("Service responds to search", duration, error[:200])

    except subprocess.TimeoutExpired:
        results.add_fail("Service responds to search", time.time() - start, "Timeout (15s)")
    except Exception as e:
        results.add_fail("Service connectivity test", time.time() - start, str(e))


def test_quick_search(results: TestResult):
    """Test 3: Quick Search Operation"""
    print_header("TEST 3: Quick Search Operation")

    start = time.time()
    try:
        from actions.tinyfish_action import _search

        result = _search(query="Python AI", max_results=3)
        duration = time.time() - start

        if result and not result.startswith("No results"):
            if "Search results for:" in result:
                results.add_pass(f"Quick search returns results ({duration:.1f}s)", duration)
            else:
                results.add_warning(
                    f"Quick search returns data ({duration:.1f}s)",
                    duration,
                    "Unexpected format - check output"
                )
        else:
            results.add_fail("Quick search returns results", duration, "No results returned")

    except Exception as e:
        results.add_fail("Quick search operation", time.time() - start, str(e))


def test_fetch_content(results: TestResult):
    """Test 4: Content Fetch Operation"""
    print_header("TEST 4: Content Fetch Operation")

    start = time.time()
    try:
        from actions.tinyfish_action import _fetch

        # Use a reliable, fast-loading site
        test_url = "https://example.com"
        result = _fetch(urls=[test_url], format="markdown")
        duration = time.time() - start

        if result and "Fetch failed" not in result:
            if "Result 1:" in result or "example" in result.lower():
                results.add_pass(f"Fetch extracts content ({duration:.1f}s)", duration)
            else:
                results.add_warning(
                    f"Fetch returns data ({duration:.1f}s)",
                    duration,
                    "Content format unexpected"
                )
        else:
            results.add_fail("Fetch extracts content", duration, result[:200])

    except Exception as e:
        results.add_fail("Fetch content operation", time.time() - start, str(e))


def test_ui_integration(results: TestResult):
    """Test 5: UI Integration (PyQt6 imports)"""
    print_header("TEST 5: UI Integration")

    # Check PyQt6 imports
    start = time.time()
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt, QThread
        results.add_pass("PyQt6 imports", time.time() - start)
    except ImportError as e:
        results.add_fail("PyQt6 imports", time.time() - start, str(e))
        return

    # Check TinyFish UI components
    start = time.time()
    try:
        from ui.tinyfish_panel import TinyFishWorkspacePanel
        from ui.agent_timeline import AgentTimelineWidget
        from ui.tinyfish_worker import TinyFishSearchWorker
        results.add_pass("TinyFish UI components import", time.time() - start)
    except ImportError as e:
        results.add_fail("TinyFish UI components import", time.time() - start, str(e))

    # Check dialog components
    start = time.time()
    try:
        from ui.apply_review_dialog import ApplyReviewDialog, FieldMapping
        results.add_pass("Apply Flow components import", time.time() - start)
    except ImportError as e:
        results.add_fail("Apply Flow components import", time.time() - start, str(e))


def test_pdf_generation(results: TestResult):
    """Test 6: PDF Report Generation"""
    print_header("TEST 6: PDF Report Generation")

    start = time.time()
    try:
        from actions.report_generator import generate_test_report

        # Generate a test PDF
        test_data = {
            "title": "Test Report",
            "content": "This is a test report generated during pre-flight checks.",
            "timestamp": datetime.now().isoformat(),
        }

        pdf_path = generate_test_report(test_data)
        duration = time.time() - start

        if pdf_path and pdf_path.exists():
            size_kb = pdf_path.stat().st_size / 1024
            results.add_pass(f"PDF generation works ({size_kb:.1f} KB, {duration:.1f}s)", duration)

            # Clean up test file
            try:
                pdf_path.unlink()
            except:
                pass
        else:
            results.add_fail("PDF generation works", duration, "PDF not created")

    except Exception as e:
        results.add_fail("PDF generation test", time.time() - start, str(e))


def test_safety_gates(results: TestResult):
    """Test 7: Form Safety Validation"""
    print_header("TEST 7: Form Safety Validation")

    start = time.time()
    try:
        from actions.form_safety import validate_form_goal

        # Test safe goals
        safe_goals = [
            "fill out contact form",
            "complete internship application",
        ]

        for goal in safe_goals:
            is_valid, error = validate_form_goal(goal)
            if is_valid:
                results.add_pass(f"Safety: Allows safe goal '{goal[:30]}...'", 0.01)
            else:
                results.add_fail(f"Safety: Allows safe goal '{goal[:30]}...'", 0.01, f"Blocked: {error}")

        # Test dangerous goals
        dangerous_goals = [
            "enter credit card number",
            "submit payment information",
        ]

        for goal in dangerous_goals:
            is_valid, error = validate_form_goal(goal)
            if not is_valid:
                results.add_pass(f"Safety: Blocks dangerous goal '{goal[:30]}...'", 0.01)
            else:
                results.add_fail(f"Safety: Blocks dangerous goal '{goal[:30]}...'", 0.01, "Should have been blocked")

    except Exception as e:
        results.add_fail("Form safety validation test", time.time() - start, str(e))


def test_workspace_mode(results: TestResult):
    """Test 8: TinyFish Mode Configuration"""
    print_header("TEST 8: TinyFish Mode Configuration")

    start = time.time()
    try:
        mode_enabled = get_tinyfish_mode()
        results.add_pass(f"TinyFish mode: {mode_enabled}", time.time() - start)
    except Exception as e:
        results.add_fail("TinyFish mode check", time.time() - start, str(e))


def main():
    """Run all pre-flight tests."""
    print(f"\n{BOLD}╔═════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}║         TinyFish Demo Pre-Flight Test Suite                        ║{RESET}")
    print(f"{BOLD}║         Testing Opero2 × TinyFish Integration                      ║{RESET}")
    print(f"{BOLD}╚═════════════════════════════════════════════════════════════════════╝{RESET}")
    print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    results = TestResult()

    # Run tests in order (fastest to slowest)
    test_environment(results)
    test_ui_integration(results)
    test_safety_gates(results)
    test_workspace_mode(results)
    test_service_connectivity(results)
    test_quick_search(results)
    test_fetch_content(results)
    test_pdf_generation(results)

    # Print summary
    results.print_summary()

    # Exit with appropriate code
    sys.exit(0 if results.failed == 0 else 1)


if __name__ == "__main__":
    main()
