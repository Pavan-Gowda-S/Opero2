"""
Phase 3 UI Workspace Tests

Tests TinyFish workspace panel, search worker, and integration.
All tests run 100% offline with mocks.

Test Categories:
1. Worker Thread Tests
2. Panel UI Tests
3. Integration Tests
4. Cancellation Tests
5. Configuration Tests
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestTinyFishWorker(unittest.TestCase):
    """Test TinyFishSearchWorker thread operations."""

    @patch('actions.tinyfish_action.tinyfish_search')
    def test_quick_search_worker_executes(self, mock_search):
        """Quick search worker should call tinyfish_search with correct params."""
        from ui.tinyfish_worker import TinyFishSearchWorker

        mock_search.return_value = "[1] Test Result\nhttps://example.com\nTest snippet"

        worker = TinyFishSearchWorker("test query", "quick")

        # Track signal emissions
        results = []
        worker.result_ready.connect(lambda r: results.append(r))

        errors = []
        worker.error_occurred.connect(lambda e: errors.append(e))

        finished = []
        worker.finished.connect(lambda: finished.append(True))

        # Run worker (synchronous for testing)
        worker.run()

        # Verify search was called
        mock_search.assert_called_once()
        call_args = mock_search.call_args[0][0]
        self.assertEqual(call_args['operation'], 'search')
        self.assertEqual(call_args['query'], 'test query')

        # Verify finished signal
        self.assertEqual(len(finished), 1)

        # Verify no errors
        self.assertEqual(len(errors), 0)

    @patch('actions.tinyfish_action.tinyfish_search')
    def test_deep_research_worker_executes(self, mock_search):
        """Deep research worker should synthesize content."""
        from ui.tinyfish_worker import TinyFishSearchWorker

        mock_search.return_value = "Source 1\nhttps://example.com\nContent line"

        worker = TinyFishSearchWorker("research question", "deep")

        results = []
        worker.result_ready.connect(lambda r: results.append(r))

        worker.run()

        # Verify at least one result
        self.assertGreater(len(results), 0)

        # Verify deep research format
        result = results[0]
        self.assertEqual(result.get('type'), 'deep_research')
        self.assertIn('content', result)
        self.assertIsInstance(result['content'], str)

    def test_worker_cancellation(self):
        """Worker should respect cancellation request."""
        from ui.tinyfish_worker import TinyFishSearchWorker

        worker = TinyFishSearchWorker("test", "quick")

        # Cancel before running
        worker.cancel()

        # Run should exit early
        worker.run()

        # Worker should be marked as cancelled
        self.assertTrue(worker._cancelled)

    @patch('actions.tinyfish_action.tinyfish_search')
    def test_worker_handles_search_error(self, mock_search):
        """Worker should emit error signal on search failure."""
        from ui.tinyfish_worker import TinyFishSearchWorker

        mock_search.side_effect = RuntimeError("Search failed")

        worker = TinyFishSearchWorker("test", "quick")

        errors = []
        worker.error_occurred.connect(lambda e: errors.append(e))

        finished = []
        worker.finished.connect(lambda: finished.append(True))

        worker.run()

        # Verify error was emitted
        self.assertEqual(len(errors), 1)
        self.assertIn("Search failed", errors[0])

        # Verify finished was still emitted
        self.assertEqual(len(finished), 1)


class TestTinyFishPanel(unittest.TestCase):
    """Test TinyFishWorkspacePanel UI behavior."""

    def setUp(self):
        """Set up test fixtures."""
        from PyQt6.QtWidgets import QApplication
        self.app = QApplication.instance() or QApplication([])

    def test_panel_creation(self):
        """Panel should initialize with correct default state."""
        from ui.tinyfish_panel import TinyFishWorkspacePanel

        panel = TinyFishWorkspacePanel()

        # Check initial state
        self.assertFalse(panel._is_searching)
        self.assertEqual(panel._current_mode, "quick")
        self.assertIsNotNone(panel._tabs)
        self.assertIsNotNone(panel._input)

    def test_search_requested_signal(self):
        """Panel should emit search_requested when user searches."""
        from ui.tinyfish_panel import TinyFishWorkspacePanel

        panel = TinyFishWorkspacePanel()

        # Track signal
        searches = []
        panel.search_requested.connect(lambda q, m: searches.append((q, m)))

        # Simulate user input
        panel._input.setText("test query")
        panel._on_search()

        # Verify signal was emitted
        self.assertEqual(len(searches), 1)
        self.assertEqual(searches[0], ("test query", "quick"))

    def test_panel_ignores_empty_search(self):
        """Panel should not emit signal for empty query."""
        from ui.tinyfish_panel import TinyFishWorkspacePanel

        panel = TinyFishWorkspacePanel()

        searches = []
        panel.search_requested.connect(lambda q, m: searches.append((q, m)))

        # Try to search with empty input
        panel._input.setText("")
        panel._on_search()

        # Verify no signal
        self.assertEqual(len(searches), 0)

    def test_panel_searching_state(self):
        """Panel should update UI when searching state changes."""
        from PyQt6.QtWidgets import QApplication
        from ui.tinyfish_panel import TinyFishWorkspacePanel

        panel = TinyFishWorkspacePanel()
        panel.show()  # Panel must be shown for visibility checks

        # Process events to ensure UI updates
        QApplication.processEvents()

        # Set searching
        panel.set_searching(True)
        QApplication.processEvents()

        self.assertTrue(panel._is_searching)
        self.assertFalse(panel._search_btn.isEnabled())
        self.assertTrue(panel._progress.isVisible())

        # Clear searching
        panel.set_searching(False)
        QApplication.processEvents()

        self.assertFalse(panel._is_searching)
        self.assertTrue(panel._search_btn.isEnabled())
        self.assertFalse(panel._progress.isVisible())

        panel.hide()

    def test_add_result_card(self):
        """Panel should add result cards to layout."""
        from ui.tinyfish_panel import TinyFishWorkspacePanel

        panel = TinyFishWorkspacePanel()

        initial_count = panel._quick_layout.count()

        # Add a result
        panel.add_result_card("Test Title", "https://example.com", "Test snippet")

        # Verify card was added
        self.assertGreater(panel._quick_layout.count(), initial_count)

    def test_clear_results(self):
        """Panel should clear all results from current tab."""
        from ui.tinyfish_panel import TinyFishWorkspacePanel

        panel = TinyFishWorkspacePanel()

        # Add some results
        panel.add_result_card("Title 1", "url1", "snippet1")
        panel.add_result_card("Title 2", "url2", "snippet2")

        # Clear results
        panel.clear_results()

        # Layout should have only stretch item left
        self.assertEqual(panel._quick_layout.count(), 1)

    def test_show_error(self):
        """Panel should display error messages."""
        from ui.tinyfish_panel import TinyFishWorkspacePanel

        panel = TinyFishWorkspacePanel()

        initial_count = panel._quick_layout.count()

        # Show error
        panel.show_error("Test error message")

        # Verify error card was added
        self.assertGreater(panel._quick_layout.count(), initial_count)

    def test_tab_change_updates_mode(self):
        """Changing tabs should update current mode."""
        from ui.tinyfish_panel import TinyFishWorkspacePanel

        panel = TinyFishWorkspacePanel()

        # Start on quick search tab
        self.assertEqual(panel._current_mode, "quick")

        # Switch to deep research tab
        panel._tabs.setCurrentIndex(1)
        panel._on_tab_changed(1)

        self.assertEqual(panel._current_mode, "deep")


class TestWorkspaceIntegration(unittest.TestCase):
    """Test integration between panel, worker, and main window."""

    def setUp(self):
        """Set up test fixtures."""
        from PyQt6.QtWidgets import QApplication
        self.app = QApplication.instance() or QApplication([])

    def test_config_integration(self):
        """TinyFish mode config should control panel visibility."""
        from memory.config_manager import get_tinyfish_mode, set_tinyfish_mode

        # Verify config functions exist and work
        original = get_tinyfish_mode()

        set_tinyfish_mode(True)
        self.assertTrue(get_tinyfish_mode())

        set_tinyfish_mode(False)
        self.assertFalse(get_tinyfish_mode())

        # Restore original
        set_tinyfish_mode(original)

    def test_has_tinyfish_key_check(self):
        """has_tinyfish_key should return boolean without exposing key."""
        from memory.config_manager import has_tinyfish_key

        # Should return boolean
        result = has_tinyfish_key()
        self.assertIsInstance(result, bool)

        # Should never return the actual key
        self.assertNotIsInstance(result, str)


class TestCancellation(unittest.TestCase):
    """Test search cancellation behavior."""

    def test_worker_cancel_flag(self):
        """Worker cancel() should set internal flag."""
        from ui.tinyfish_worker import TinyFishSearchWorker

        worker = TinyFishSearchWorker("test", "quick")

        self.assertFalse(worker._cancelled)

        worker.cancel()

        self.assertTrue(worker._cancelled)

    def test_panel_cancel_signal(self):
        """Panel should emit cancelled signal when cancel button clicked."""
        from PyQt6.QtWidgets import QApplication
        self.app = QApplication.instance() or QApplication([])

        from ui.tinyfish_panel import TinyFishWorkspacePanel

        panel = TinyFishWorkspacePanel()

        cancellations = []
        panel.search_cancelled.connect(lambda: cancellations.append(True))

        # Simulate cancel button click
        panel._on_cancel()

        # Verify signal
        self.assertEqual(len(cancellations), 1)


class TestResultParsing(unittest.TestCase):
    """Test result parsing logic in worker."""

    def test_parse_quick_results(self):
        """Worker should parse TinyFish search results correctly."""
        from ui.tinyfish_worker import TinyFishSearchWorker

        worker = TinyFishSearchWorker("test", "quick")

        # Mock result text with structured format
        result_text = """[1] First Result
https://example.com/1
This is the first snippet

[2] Second Result
https://example.com/2
This is the second snippet"""

        results = []
        worker.result_ready.connect(lambda r: results.append(r))

        # Parse results
        worker._parse_and_emit_quick_results(result_text)

        # Verify results were parsed
        self.assertGreater(len(results), 0)

    def test_synthesize_deep_research(self):
        """Worker should create formatted deep research content."""
        from ui.tinyfish_worker import TinyFishSearchWorker

        worker = TinyFishSearchWorker("test question", "deep")

        search_result = """Source information here
https://example.com
Content with details"""

        content = worker._synthesize_deep_research(search_result)

        # Verify markdown structure
        self.assertIsInstance(content, str)
        self.assertIn("# Deep Research:", content)
        self.assertIn("## Summary", content)
        self.assertIn("## Sources", content)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
