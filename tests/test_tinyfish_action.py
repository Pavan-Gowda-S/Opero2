"""
Unit tests for TinyFish action integration (Phase 4)

Tests the agent confirmation gate, history tracking, and error handling.
Does NOT make live API calls - uses mocking for subprocess calls.
"""

import json
import subprocess
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from actions.tinyfish_action import (
    tinyfish_search,
    _agent,
    _format_agent_response,
    _save_to_history,
    _call_tinyfish_service,
)


class TestTinyFishAgentConfirmation(unittest.TestCase):
    """Test agent confirmation gate (Phase 4)"""

    @patch('actions.tinyfish_action.confirm.request')
    @patch('actions.tinyfish_action.confirm.pending_title')
    def test_agent_requests_confirmation(self, mock_pending, mock_request):
        """Agent operation should request user confirmation"""
        mock_pending.return_value = ""  # No pending confirmation
        mock_request.return_value = "[CONFIRMATION_PENDING] Waiting for user..."

        result = _agent(
            url="https://example.com",
            goal="Extract page title",
            max_steps=50,
            max_duration_seconds=300,
            browser_profile="lite"
        )

        # Should have called confirm.request
        mock_request.assert_called_once()
        call_args = mock_request.call_args

        # Verify confirmation parameters
        self.assertEqual(call_args.kwargs['key'], 'tinyfish_agent')
        self.assertEqual(call_args.kwargs['title'], 'TinyFish Browser Agent')
        self.assertIn('example.com', call_args.kwargs['detail'])
        self.assertIn('Extract page title', call_args.kwargs['detail'])
        self.assertIn('billable', call_args.kwargs['detail'])
        self.assertTrue(callable(call_args.kwargs['run']))

        # Should return confirmation pending message
        self.assertIn("CONFIRMATION_PENDING", result)

    @patch('actions.tinyfish_action.confirm.pending_title')
    def test_agent_blocks_when_confirmation_pending(self, mock_pending):
        """Agent should refuse if another confirmation is pending"""
        mock_pending.return_value = "Some Other Action"

        result = _agent(
            url="https://example.com",
            goal="Test",
        )

        # Should refuse and explain
        self.assertIn("Another confirmation is pending", result)

    def test_agent_validates_inputs(self):
        """Agent should reject invalid inputs before confirmation"""
        # Missing URL
        result = _agent(url="", goal="Test goal")
        self.assertIn("provide a target URL", result)

        # Missing goal
        result = _agent(url="https://example.com", goal="")
        self.assertIn("provide a goal", result)


class TestAgentResponseFormatting(unittest.TestCase):
    """Test agent response formatting (Phase 4 improvements)"""

    def test_format_success_response(self):
        """Should format successful agent response clearly"""
        response = {
            "success": True,
            "status": "COMPLETED",
            "result": "Page title: Example Domain",
            "run_id": "run_abc123"
        }

        formatted = _format_agent_response(
            response,
            url="https://example.com",
            goal="Extract title"
        )

        self.assertIn("✅", formatted)
        self.assertIn("COMPLETED", formatted)
        self.assertIn("run_abc123", formatted)
        self.assertIn("Page title: Example Domain", formatted)

    def test_format_timeout_with_explanation(self):
        """Timeout errors should include clear explanation"""
        response = {
            "success": False,
            "error": "Operation timed out after 600 seconds",
            "code": "TIMEOUT"
        }

        formatted = _format_agent_response(
            response,
            url="https://example.com",
            goal="Long running task"
        )

        # Should explain remote execution continues
        self.assertIn("agent may still be running", formatted)
        self.assertIn("TinyFish servers", formatted)
        self.assertIn("Do NOT retry", formatted)
        self.assertIn("example.com", formatted)

    def test_format_generic_error(self):
        """Generic errors should be formatted clearly"""
        response = {
            "success": False,
            "error": "Authentication failed",
            "code": "AUTH_ERROR",
            "message": "Invalid API key"
        }

        formatted = _format_agent_response(
            response,
            url="https://example.com",
            goal="Test"
        )

        self.assertIn("failed", formatted)
        self.assertIn("Authentication failed", formatted)


class TestAgentHistory(unittest.TestCase):
    """Test agent operation history tracking (Phase 4)"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = Path(__file__).parent.parent / "actions"
        self.test_history_file = self.test_dir / "tinyfish_history_test.json"
        if self.test_history_file.exists():
            self.test_history_file.unlink()

    def tearDown(self):
        """Clean up test files"""
        if self.test_history_file.exists():
            self.test_history_file.unlink()
        # Also clean up production history file if created during test
        prod_file = self.test_dir / "tinyfish_history.json"
        if prod_file.exists() and prod_file.stat().st_size < 1000:  # Only delete if small (test data)
            try:
                prod_file.unlink()
            except:
                pass

    def test_save_successful_operation(self):
        """Should save successful operations to history"""
        response = {
            "success": True,
            "status": "COMPLETED",
            "run_id": "run_test123",
            "result": "Success"
        }

        _save_to_history(
            url="https://example.com",
            goal="Test goal",
            response=response
        )

        # History file should exist
        history_file = self.test_dir / "tinyfish_history.json"
        self.assertTrue(history_file.exists())

        # Verify content
        with open(history_file, "r") as f:
            history = json.load(f)

        self.assertGreater(len(history), 0)
        # Find our test entry
        test_entries = [e for e in history if e.get('run_id') == 'run_test123']
        self.assertEqual(len(test_entries), 1)

        entry = test_entries[0]
        self.assertEqual(entry['url'], 'https://example.com')
        self.assertEqual(entry['goal'], 'Test goal')
        self.assertEqual(entry['status'], 'COMPLETED')
        self.assertTrue(entry['success'])

    def test_history_truncates_long_goals(self):
        """History should truncate very long goals"""
        long_goal = "A" * 500

        response = {"success": True, "status": "COMPLETED", "run_id": "run_test_long"}

        _save_to_history(
            url="https://example.com",
            goal=long_goal,
            response=response
        )

        history_file = self.test_dir / "tinyfish_history.json"
        with open(history_file, "r") as f:
            history = json.load(f)

        # Find our test entry
        test_entries = [e for e in history if e.get('run_id') == 'run_test_long']
        self.assertEqual(len(test_entries), 1)

        # Goal should be truncated to 200 chars
        self.assertLessEqual(len(test_entries[0]['goal']), 200)


class TestActionHandlerIntegration(unittest.TestCase):
    """Test main action handler integration"""

    @patch('actions.tinyfish_action._agent')
    def test_handler_routes_agent_operation(self, mock_agent):
        """Handler should route agent operations to _agent"""
        mock_agent.return_value = "Agent result"

        result = tinyfish_search({
            "operation": "agent",
            "url": "https://example.com",
            "goal": "Test goal",
            "max_steps": 50,
            "max_duration_seconds": 300,
            "browser_profile": "lite"
        })

        mock_agent.assert_called_once_with(
            url="https://example.com",
            goal="Test goal",
            max_steps=50,
            max_duration_seconds=300,
            browser_profile="lite"
        )

    @patch('actions.tinyfish_action._search')
    def test_search_operation_unaffected(self, mock_search):
        """Search operation should work unchanged (regression test)"""
        mock_search.return_value = "Search results"

        result = tinyfish_search({
            "operation": "search",
            "query": "test query"
        })

        mock_search.assert_called_once()
        self.assertEqual(result, "Search results")

    @patch('actions.tinyfish_action._fetch')
    def test_fetch_operation_unaffected(self, mock_fetch):
        """Fetch operation should work unchanged (regression test)"""
        mock_fetch.return_value = "Fetch results"

        result = tinyfish_search({
            "operation": "fetch",
            "urls": ["https://example.com"]
        })

        mock_fetch.assert_called_once()
        self.assertEqual(result, "Fetch results")


class TestSubprocessCalls(unittest.TestCase):
    """Test subprocess execution (mocked)"""

    @patch('actions.tinyfish_action.subprocess.run')
    @patch('actions.tinyfish_action.SERVICE_ENTRY')
    @patch('actions.tinyfish_action.ENV_FILE')
    def test_subprocess_timeout_handling(self, mock_env, mock_service, mock_run):
        """Subprocess timeouts should be handled gracefully"""
        mock_env.exists.return_value = True
        mock_service.exists.return_value = True

        # Simulate subprocess timeout
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=['node'], timeout=600)

        result = _call_tinyfish_service("agent", ["--url", "test"], timeout=600)

        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("code"), "TIMEOUT")


if __name__ == '__main__':
    unittest.main()
