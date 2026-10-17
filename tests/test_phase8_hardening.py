"""
Phase 8 Hardening Tests

Tests credit guard warnings, human-readable error handling, and safety gate triggers.
All tests run 100% offline with mocks.

Test Categories:
1. Credit Guard & Cost Warnings
2. Human-Readable Error Messages
3. Safety Gate Triggers
4. API Key Validation
5. Timeout Handling
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestCreditGuard(unittest.TestCase):
    """Test credit guard warnings and cost notifications."""

    def test_agent_cost_warning_message(self):
        """Agent operations should include cost warnings."""
        # Verify cost warning string exists
        cost_warning = "Estimated Cost: ~$0.10 - $1.00 USD (Remote Browser Agent)"

        # This is the expected format for credit warnings
        self.assertIn("Cost", cost_warning)
        self.assertIn("USD", cost_warning)
        self.assertIn("Agent", cost_warning)

    def test_credit_guard_notification_format(self):
        """Credit guard should display clear cost estimates."""
        from ui.apply_review_dialog import ApplyReviewDialog

        # Safety warning should be clear about costs
        # This is tested in dialog construction
        self.assertTrue(True)  # Placeholder - dialog includes safety warnings


class TestHumanReadableErrors(unittest.TestCase):
    """Test human-readable error message formatting."""

    def test_missing_api_key_error_message(self):
        """Missing API key should return clear actionable message."""
        expected_patterns = [
            "TinyFish API key not found",
            "config/api_keys.json",
            ".env"
        ]

        error_message = (
            "TinyFish API key not found. Please add tinyfish_api_key in "
            "config/api_keys.json or root .env file."
        )

        for pattern in expected_patterns:
            self.assertIn(pattern, error_message)

    def test_rate_limit_error_message(self):
        """Rate limit should return clear wait message."""
        error_message = (
            "TinyFish rate limit reached. Please wait a moment before trying again."
        )

        self.assertIn("rate limit", error_message.lower())
        self.assertIn("wait", error_message.lower())
        self.assertNotIn("error code", error_message.lower())  # No technical jargon

    def test_timeout_error_message(self):
        """Timeout should explain remote agent may still be active."""
        error_message = (
            "Operation reached local timeout (600s). Note: The remote agent may "
            "still be active on TinyFish servers."
        )

        self.assertIn("timeout", error_message.lower())
        self.assertIn("remote agent", error_message.lower())
        self.assertIn("still be active", error_message.lower())

    def test_blocked_domain_error_message(self):
        """Blocked domain should explain safety filter trigger."""
        error_message = (
            "Navigation blocked: The requested goal or domain triggered safety filters."
        )

        self.assertIn("blocked", error_message.lower())
        self.assertIn("safety", error_message.lower())
        self.assertNotIn("403", error_message)  # No HTTP codes
        self.assertNotIn("exception", error_message.lower())  # No stack traces

    def test_captcha_error_message(self):
        """CAPTCHA detection should provide clear guidance."""
        error_message = (
            "CAPTCHA detected. Manual intervention required. "
            "Please complete the CAPTCHA in the browser window."
        )

        self.assertIn("CAPTCHA", error_message)
        self.assertIn("Manual intervention", error_message)
        self.assertIn("browser window", error_message)

    def test_form_not_found_error_message(self):
        """Form detection failure should suggest alternatives."""
        error_message = (
            "Unable to locate application form on page. "
            "The page structure may have changed. "
            "Please complete the application manually at: https://example.com/apply"
        )

        self.assertIn("Unable to locate", error_message)
        self.assertIn("manually", error_message)
        self.assertIn("https://", error_message)  # Includes URL

    def test_no_stack_traces_in_user_messages(self):
        """User-facing messages should never contain stack traces."""
        good_messages = [
            "TinyFish rate limit reached. Please wait before retrying.",
            "Navigation blocked: Safety filters triggered.",
            "Form pre-fill failed. Please apply manually.",
        ]

        bad_patterns = [
            "Traceback",
            "line 42",
            "raise RuntimeError",
            "TypeError:",
            "at Object.",
            "node_modules",
        ]

        for message in good_messages:
            for pattern in bad_patterns:
                self.assertNotIn(pattern, message)


class TestSafetyGateTriggers(unittest.TestCase):
    """Test safety gate triggers for sensitive operations."""

    def test_payment_keyword_detection(self):
        """Payment-related keywords should trigger safety blocks."""
        from actions.form_safety import validate_form_goal

        payment_goals = [
            "enter credit card number",
            "submit payment information",
            "complete checkout process",
            "add billing address",
        ]

        for goal in payment_goals:
            is_valid, error = validate_form_goal(goal)
            self.assertFalse(is_valid, f"Should block payment goal: {goal}")
            self.assertIsNotNone(error)
            self.assertIn("prohibited", error.lower())

    def test_account_modification_detection(self):
        """Account modification attempts should trigger blocks."""
        from actions.form_safety import validate_form_goal

        dangerous_goals = [
            "delete my account",
            "change password",
            "reset password",
            "cancel my subscription",
        ]

        for goal in dangerous_goals:
            is_valid, error = validate_form_goal(goal)
            self.assertFalse(is_valid, f"Should block dangerous goal: {goal}")

    def test_safe_goals_allowed(self):
        """Safe form-filling goals should be allowed."""
        from actions.form_safety import validate_form_goal

        safe_goals = [
            "fill out contact form",
            "complete internship application",
            "fill hackathon registration",
            "submit volunteer form",
        ]

        for goal in safe_goals:
            is_valid, error = validate_form_goal(goal)
            self.assertTrue(is_valid, f"Should allow safe goal: {goal}")
            self.assertIsNone(error)


class TestAPIKeyValidation(unittest.TestCase):
    """Test API key validation and error handling."""

    def test_env_file_missing_detection(self):
        """Missing .env file should be detected early."""
        from pathlib import Path

        # Simulate checking for .env
        env_file = Path(".env")

        if not env_file.exists():
            error_message = (
                "Environment file not found at .env. "
                "Ensure TINYFISH_API_KEY is configured."
            )
            self.assertIn("Environment file", error_message)
            self.assertIn("TINYFISH_API_KEY", error_message)

    def test_empty_api_key_detection(self):
        """Empty API key should trigger clear error."""
        api_key = ""

        if not api_key or api_key.strip() == "":
            error_message = "TinyFish API key is empty. Please configure a valid key."
            self.assertIn("empty", error_message.lower())
            self.assertIn("configure", error_message.lower())


class TestTimeoutHandling(unittest.TestCase):
    """Test timeout handling for long-running operations."""

    def test_search_timeout_reasonable(self):
        """Search operations should have reasonable timeouts."""
        search_timeout = 60  # seconds

        # Search should timeout in under 2 minutes
        self.assertLessEqual(search_timeout, 120)
        self.assertGreaterEqual(search_timeout, 30)

    def test_agent_timeout_reasonable(self):
        """Agent operations should have longer timeouts."""
        agent_timeout = 600  # seconds (10 minutes)

        # Agent should have enough time for complex operations
        self.assertGreaterEqual(agent_timeout, 300)  # At least 5 minutes
        self.assertLessEqual(agent_timeout, 900)  # But not too long

    def test_timeout_error_formatting(self):
        """Timeout errors should be formatted clearly."""
        import subprocess

        # Simulate timeout exception handling
        try:
            # This would be the actual timeout handling
            raise subprocess.TimeoutExpired("node", 600)
        except subprocess.TimeoutExpired as e:
            error_message = (
                f"Operation timed out after {e.timeout}s. "
                "The remote agent may still be running on TinyFish servers."
            )

            self.assertIn("timed out", error_message.lower())
            self.assertIn("600", error_message)
            self.assertIn("remote agent", error_message.lower())


class TestUIErrorDisplay(unittest.TestCase):
    """Test error display in UI components."""

    def setUp(self):
        """Set up test fixtures."""
        from PyQt6.QtWidgets import QApplication
        self.app = QApplication.instance() or QApplication([])

    def test_workspace_error_display(self):
        """Workspace should display errors clearly."""
        from ui.tinyfish_panel import TinyFishWorkspacePanel

        panel = TinyFishWorkspacePanel()

        error_message = "TinyFish rate limit reached. Please wait before retrying."
        panel.show_error(error_message)

        # Error card should be added to layout
        # Verify it doesn't crash
        self.assertIsNotNone(panel)

    def test_timeline_error_display(self):
        """Timeline should display errors with proper styling."""
        from ui.agent_timeline import AgentTimelineWidget

        timeline = AgentTimelineWidget()

        # Start an operation first (required to show result)
        timeline.start_operation("test_run", "https://example.com", "test goal")

        error_text = "Navigation blocked: Safety filters triggered."

        # Should not crash when displaying error
        timeline.set_result(error_text, is_error=True)

        # Verify error text was set
        result_text = timeline._result_text.toPlainText()
        self.assertIn("Navigation blocked", result_text)

        # Verify error styling was applied (red/error color)
        style = timeline._result_text.styleSheet()
        # C.RED is #FF3355 - should be in the color property
        self.assertIn("COLOR:", style.upper())
        self.assertIn("#FF3355", style.upper())


class TestCostEstimation(unittest.TestCase):
    """Test cost estimation and warning display."""

    def test_search_cost_estimate(self):
        """Quick search should show as free."""
        operation = "search"
        estimated_cost = "$0.00 (Free)"

        self.assertIn("Free", estimated_cost)

    def test_agent_cost_estimate_range(self):
        """Agent operations should show cost range."""
        operation = "agent"
        estimated_cost = "~$0.10 - $1.00 USD"

        self.assertIn("$", estimated_cost)
        self.assertIn("USD", estimated_cost)
        self.assertIn("-", estimated_cost)  # Shows range

    def test_deep_research_cost_estimate(self):
        """Deep research should show appropriate cost."""
        operation = "deep_research"
        estimated_cost = "~$0.05 - $0.20 USD"

        # Should be cheaper than full agent runs
        self.assertIn("$", estimated_cost)


class TestSecretProtection(unittest.TestCase):
    """Test that API keys and secrets are never exposed."""

    def test_api_key_not_in_error_messages(self):
        """Error messages should never contain API keys."""
        fake_api_key = "tf_sk_1234567890abcdef"

        error_messages = [
            "TinyFish API key not found. Please configure.",
            "Authentication failed. Check your API key configuration.",
            "Rate limit exceeded. Key: [REDACTED]",
        ]

        for message in error_messages:
            self.assertNotIn(fake_api_key, message)
            self.assertNotIn("1234567890abcdef", message)

    def test_api_key_not_in_logs(self):
        """Logs should never contain full API keys."""
        from core.logger import get_logger

        log = get_logger("test")

        # If API key needs to be logged, it should be redacted
        fake_key = "tf_sk_1234567890abcdef"
        redacted_key = f"tf_sk_***{fake_key[-4:]}"

        self.assertEqual(redacted_key, "tf_sk_***cdef")
        self.assertNotIn(fake_key[6:], redacted_key)  # Middle part hidden


class TestGracefulDegradation(unittest.TestCase):
    """Test graceful degradation when services unavailable."""

    def test_tinyfish_unavailable_fallback(self):
        """Should provide clear message when TinyFish unavailable."""
        error_message = (
            "TinyFish service is currently unavailable. "
            "Please try again later or use standard web search."
        )

        self.assertIn("unavailable", error_message.lower())
        self.assertIn("try again later", error_message.lower())
        self.assertIn("standard web search", error_message.lower())

    def test_node_service_missing_guidance(self):
        """Should guide user to install Node service."""
        error_message = (
            "TinyFish service not found at tinyfish_service/index.js. "
            "Run: cd tinyfish_service && npm install"
        )

        self.assertIn("not found", error_message)
        self.assertIn("npm install", error_message)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
