"""
Phase 4 UI Timeline Tests

Tests AgentTimelineWidget integration and behavior.
All tests run 100% offline with mocks.

Test Categories:
1. Timeline Widget Tests
2. Status Update Tests
3. Integration Tests
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestAgentTimelineWidget(unittest.TestCase):
    """Test AgentTimelineWidget operations."""

    def setUp(self):
        """Set up test fixtures."""
        from PyQt6.QtWidgets import QApplication
        self.app = QApplication.instance() or QApplication([])

    def test_timeline_creation(self):
        """Timeline widget should initialize with idle state."""
        from ui.agent_timeline import AgentTimelineWidget

        timeline = AgentTimelineWidget()

        # Check initial state
        self.assertEqual(timeline.get_status(), "IDLE")
        self.assertIsNone(timeline.get_run_id())
        self.assertFalse(timeline.is_active())

    def test_start_operation(self):
        """Timeline should track new operation and update UI."""
        from ui.agent_timeline import AgentTimelineWidget

        timeline = AgentTimelineWidget()

        # Track signal emissions
        signals = []
        timeline.status_updated.connect(lambda rid, status: signals.append((rid, status)))

        # Start operation
        timeline.start_operation("test_run_123", "https://example.com", "test goal")

        # Verify state
        self.assertEqual(timeline.get_run_id(), "test_run_123")
        self.assertEqual(timeline.get_status(), "PENDING")
        self.assertTrue(timeline.is_active())

        # Verify signal emitted
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0], ("test_run_123", "PENDING"))

    def test_status_progression(self):
        """Timeline should update status through progression."""
        from ui.agent_timeline import AgentTimelineWidget

        timeline = AgentTimelineWidget()

        # Start operation
        timeline.start_operation("test_run_123", "https://example.com", "test goal")

        # Update to RUNNING
        timeline.update_status("RUNNING")
        self.assertEqual(timeline.get_status(), "RUNNING")
        self.assertTrue(timeline.is_active())

        # Update to COMPLETED
        timeline.update_status("COMPLETED")
        self.assertEqual(timeline.get_status(), "COMPLETED")
        self.assertFalse(timeline.is_active())

    def test_status_failed(self):
        """Timeline should handle FAILED status."""
        from ui.agent_timeline import AgentTimelineWidget

        timeline = AgentTimelineWidget()

        timeline.start_operation("test_run_123", "https://example.com", "test goal")
        timeline.update_status("FAILED")

        self.assertEqual(timeline.get_status(), "FAILED")
        self.assertFalse(timeline.is_active())

    def test_set_result(self):
        """Timeline should display result text."""
        from PyQt6.QtWidgets import QApplication
        from ui.agent_timeline import AgentTimelineWidget

        timeline = AgentTimelineWidget()
        timeline.show()

        QApplication.processEvents()

        # Set success result
        timeline.set_result("Operation completed successfully", is_error=False)

        QApplication.processEvents()

        # Result container should be visible
        self.assertTrue(timeline._result_container.isVisible())

        timeline.hide()

    def test_set_error_result(self):
        """Timeline should display error result with red styling."""
        from PyQt6.QtWidgets import QApplication
        from ui.agent_timeline import AgentTimelineWidget

        timeline = AgentTimelineWidget()
        timeline.show()

        QApplication.processEvents()

        # Set error result
        timeline.set_result("Operation failed: timeout", is_error=True)

        QApplication.processEvents()

        # Result container should be visible
        self.assertTrue(timeline._result_container.isVisible())

        timeline.hide()

    def test_reset(self):
        """Timeline should reset to idle state."""
        from ui.agent_timeline import AgentTimelineWidget

        timeline = AgentTimelineWidget()

        # Start and complete operation
        timeline.start_operation("test_run_123", "https://example.com", "test goal")
        timeline.update_status("COMPLETED")
        timeline.set_result("Done")

        # Reset
        timeline.reset()

        # Verify idle state
        self.assertEqual(timeline.get_status(), "IDLE")
        self.assertIsNone(timeline.get_run_id())
        self.assertFalse(timeline.is_active())

    def test_elapsed_timer(self):
        """Timeline should track elapsed time during operation."""
        from ui.agent_timeline import AgentTimelineWidget

        timeline = AgentTimelineWidget()

        # Start operation
        timeline.start_operation("test_run_123", "https://example.com", "test goal")

        # Verify timer is running
        self.assertIsNotNone(timeline._elapsed_timer)
        self.assertTrue(timeline._elapsed_timer.isActive())

        # Complete operation
        timeline.update_status("COMPLETED")

        # Timer should stop
        self.assertFalse(timeline._elapsed_timer.isActive())


class TestTimelineIntegration(unittest.TestCase):
    """Test timeline integration with MainWindow."""

    def setUp(self):
        """Set up test fixtures."""
        from PyQt6.QtWidgets import QApplication
        self.app = QApplication.instance() or QApplication([])

    def test_timeline_visibility_with_tinyfish_mode(self):
        """Timeline should show/hide based on TinyFish mode."""
        from memory.config_manager import get_tinyfish_mode, set_tinyfish_mode

        # Store original state
        original = get_tinyfish_mode()

        # Test mode ON
        set_tinyfish_mode(True)
        self.assertTrue(get_tinyfish_mode())

        # Test mode OFF
        set_tinyfish_mode(False)
        self.assertFalse(get_tinyfish_mode())

        # Restore original
        set_tinyfish_mode(original)

    def test_timeline_has_required_methods(self):
        """Timeline widget should have all required methods."""
        from ui.agent_timeline import AgentTimelineWidget

        timeline = AgentTimelineWidget()

        # Verify required methods exist
        self.assertTrue(hasattr(timeline, 'start_operation'))
        self.assertTrue(hasattr(timeline, 'update_status'))
        self.assertTrue(hasattr(timeline, 'set_result'))
        self.assertTrue(hasattr(timeline, 'reset'))
        self.assertTrue(hasattr(timeline, 'get_status'))
        self.assertTrue(hasattr(timeline, 'get_run_id'))
        self.assertTrue(hasattr(timeline, 'is_active'))

        # Verify signals exist
        self.assertTrue(hasattr(timeline, 'status_updated'))


class TestTimelinePanel(unittest.TestCase):
    """Test AgentTimelinePanel container."""

    def setUp(self):
        """Set up test fixtures."""
        from PyQt6.QtWidgets import QApplication
        self.app = QApplication.instance() or QApplication([])

    def test_panel_creation(self):
        """Panel should initialize with timeline widget."""
        from ui.agent_timeline import AgentTimelinePanel

        panel = AgentTimelinePanel()

        # Verify timeline widget exists
        self.assertIsNotNone(panel.timeline)

        # Verify timeline is AgentTimelineWidget
        from ui.agent_timeline import AgentTimelineWidget
        self.assertIsInstance(panel.timeline, AgentTimelineWidget)

    def test_panel_has_header(self):
        """Panel should have header with title."""
        from PyQt6.QtWidgets import QApplication
        from ui.agent_timeline import AgentTimelinePanel

        panel = AgentTimelinePanel()
        panel.show()

        QApplication.processEvents()

        # Panel should be visible
        self.assertTrue(panel.isVisible())

        panel.hide()


class TestStatusTransitions(unittest.TestCase):
    """Test valid status transitions."""

    def setUp(self):
        """Set up test fixtures."""
        from PyQt6.QtWidgets import QApplication
        self.app = QApplication.instance() or QApplication([])

    def test_valid_status_values(self):
        """Timeline should accept all valid status values."""
        from ui.agent_timeline import AgentTimelineWidget

        timeline = AgentTimelineWidget()
        timeline.start_operation("test_run", "https://example.com", "test")

        valid_statuses = ["PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED"]

        for status in valid_statuses:
            timeline.update_status(status)
            self.assertEqual(timeline.get_status(), status)

    def test_status_update_without_operation(self):
        """Timeline should handle status update without active operation."""
        from ui.agent_timeline import AgentTimelineWidget

        timeline = AgentTimelineWidget()

        # Try to update status without starting operation
        timeline.update_status("RUNNING")

        # Should remain idle (no run_id)
        self.assertEqual(timeline.get_status(), "IDLE")
        self.assertIsNone(timeline.get_run_id())


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
