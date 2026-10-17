"""
Phase 5 UI Export Tests

Tests PDF export and WhatsApp sharing functionality in TinyFish workspace.
All tests run 100% offline with mocks.

Test Categories:
1. Export Toolbar Tests
2. PDF Export Tests
3. WhatsApp Share Tests
4. Integration Tests
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestExportToolbar(unittest.TestCase):
    """Test export toolbar UI components."""

    def setUp(self):
        """Set up test fixtures."""
        from PyQt6.QtWidgets import QApplication
        self.app = QApplication.instance() or QApplication([])

    def test_toolbar_creation(self):
        """Export toolbar should initialize with buttons."""
        from ui.tinyfish_panel import TinyFishWorkspacePanel

        panel = TinyFishWorkspacePanel()

        # Verify toolbar exists
        self.assertIsNotNone(panel._export_toolbar)

        # Verify buttons exist
        self.assertIsNotNone(panel._pdf_btn)
        self.assertIsNotNone(panel._whatsapp_btn)

    def test_toolbar_hidden_by_default(self):
        """Export toolbar should be hidden initially."""
        from PyQt6.QtWidgets import QApplication
        from ui.tinyfish_panel import TinyFishWorkspacePanel

        panel = TinyFishWorkspacePanel()
        panel.show()

        QApplication.processEvents()

        # Toolbar should be hidden initially
        self.assertFalse(panel._export_toolbar.isVisible())

        panel.hide()

    def test_show_export_toolbar(self):
        """Export toolbar should show when called."""
        from PyQt6.QtWidgets import QApplication
        from ui.tinyfish_panel import TinyFishWorkspacePanel

        panel = TinyFishWorkspacePanel()
        panel.show()

        QApplication.processEvents()

        # Show toolbar
        panel.show_export_toolbar(True)
        QApplication.processEvents()

        # Toolbar should be visible
        self.assertTrue(panel._export_toolbar.isVisible())

        # Hide toolbar
        panel.show_export_toolbar(False)
        QApplication.processEvents()

        # Toolbar should be hidden
        self.assertFalse(panel._export_toolbar.isVisible())

        panel.hide()


class TestPDFExport(unittest.TestCase):
    """Test PDF export functionality."""

    def setUp(self):
        """Set up test fixtures."""
        from PyQt6.QtWidgets import QApplication
        self.app = QApplication.instance() or QApplication([])

    @patch('actions.report_generator.generate_pdf_report')
    def test_pdf_export_quick_search(self, mock_generate_pdf):
        """PDF export should work for quick search results."""
        from ui.tinyfish_panel import TinyFishWorkspacePanel
        from pathlib import Path

        panel = TinyFishWorkspacePanel()

        # Mock PDF generation
        mock_pdf_path = Path('/tmp/report.pdf')
        mock_generate_pdf.return_value = mock_pdf_path

        # Set input text
        panel._input.setText("test query")

        # Mock _open_pdf to avoid opening actual file
        panel._open_pdf = Mock()

        # Trigger PDF export
        panel._on_export_pdf()

        # Verify generate_pdf_report was called
        self.assertTrue(mock_generate_pdf.called)

        # Verify _open_pdf was called with path
        panel._open_pdf.assert_called_once_with(mock_pdf_path)

    @patch('actions.report_generator.generate_pdf_report')
    def test_pdf_export_deep_research(self, mock_generate_pdf):
        """PDF export should work for deep research results."""
        from ui.tinyfish_panel import TinyFishWorkspacePanel
        from pathlib import Path

        panel = TinyFishWorkspacePanel()

        # Switch to deep research tab
        panel._tabs.setCurrentIndex(1)
        panel._current_mode = "deep"

        # Mock PDF generation
        mock_pdf_path = Path('/tmp/report.pdf')
        mock_generate_pdf.return_value = mock_pdf_path

        # Set input text
        panel._input.setText("test research query")

        # Mock _open_pdf
        panel._open_pdf = Mock()

        # Trigger PDF export
        panel._on_export_pdf()

        # Verify generate_pdf_report was called
        self.assertTrue(mock_generate_pdf.called)

        # Verify _open_pdf was called
        panel._open_pdf.assert_called_once()

    @patch('actions.report_generator.generate_pdf_report')
    def test_pdf_export_handles_errors(self, mock_generate_pdf):
        """PDF export should handle errors gracefully."""
        from ui.tinyfish_panel import TinyFishWorkspacePanel

        panel = TinyFishWorkspacePanel()

        # Mock PDF generation to raise error
        mock_generate_pdf.side_effect = RuntimeError("PDF generation failed")

        # Set input text
        panel._input.setText("test query")

        # Trigger PDF export (should not crash)
        panel._on_export_pdf()

        # Panel should still be functional
        self.assertIsNotNone(panel._input)


class TestWhatsAppShare(unittest.TestCase):
    """Test WhatsApp share functionality."""

    def setUp(self):
        """Set up test fixtures."""
        from PyQt6.QtWidgets import QApplication
        self.app = QApplication.instance() or QApplication([])

    @patch('time.sleep')
    @patch('subprocess.run')
    @patch('platform.system')
    @patch('actions.report_generator.generate_pdf_report')
    def test_whatsapp_share_generates_pdf(self, mock_generate_pdf, mock_system, mock_subprocess, mock_sleep):
        """WhatsApp share should generate PDF first."""
        from ui.tinyfish_panel import TinyFishWorkspacePanel
        from pathlib import Path

        panel = TinyFishWorkspacePanel()

        # Mock PDF generation
        mock_pdf_path = Path('/tmp/report.pdf')
        mock_generate_pdf.return_value = mock_pdf_path
        mock_system.return_value = "Windows"

        # Set input text
        panel._input.setText("test query")

        # Trigger WhatsApp share
        panel._on_export_whatsapp()

        # Verify generate_pdf_report was called
        self.assertTrue(mock_generate_pdf.called)

        # Verify subprocess was called (for opening WhatsApp)
        self.assertTrue(mock_subprocess.called)

    @patch('actions.report_generator.generate_pdf_report')
    def test_whatsapp_share_handles_errors(self, mock_generate_pdf):
        """WhatsApp share should handle errors gracefully."""
        from ui.tinyfish_panel import TinyFishWorkspacePanel

        panel = TinyFishWorkspacePanel()

        # Mock PDF generation to raise error
        mock_generate_pdf.side_effect = RuntimeError("PDF generation failed")

        # Set input text
        panel._input.setText("test query")

        # Trigger WhatsApp share (should not crash)
        panel._on_export_whatsapp()

        # Panel should still be functional
        self.assertIsNotNone(panel._input)


class TestExportIntegration(unittest.TestCase):
    """Test export integration with search results."""

    def setUp(self):
        """Set up test fixtures."""
        from PyQt6.QtWidgets import QApplication
        self.app = QApplication.instance() or QApplication([])

    def test_toolbar_shows_after_results(self):
        """Export toolbar should show after search results arrive."""
        from ui.tinyfish_panel import TinyFishWorkspacePanel

        panel = TinyFishWorkspacePanel()
        panel.show()

        # Initially hidden
        self.assertFalse(panel._export_toolbar.isVisible())

        # Add a result
        panel.add_result_card("Test Title", "https://example.com", "Test snippet")

        # Show toolbar manually (normally done by window handler)
        panel.show_export_toolbar(True)

        # Should now be visible
        self.assertTrue(panel._export_toolbar.isVisible())

        panel.hide()

    def test_gather_quick_results_text(self):
        """Should gather text from quick search result cards."""
        from ui.tinyfish_panel import TinyFishWorkspacePanel

        panel = TinyFishWorkspacePanel()

        # Add some results
        panel.add_result_card("Title 1", "https://example.com/1", "Snippet 1")
        panel.add_result_card("Title 2", "https://example.com/2", "Snippet 2")

        # Gather text
        text = panel._gather_quick_results_text()

        # Should contain result content
        self.assertIsInstance(text, str)
        self.assertGreater(len(text), 0)


class TestHelperMethods(unittest.TestCase):
    """Test helper methods for PDF and WhatsApp."""

    def setUp(self):
        """Set up test fixtures."""
        from PyQt6.QtWidgets import QApplication
        self.app = QApplication.instance() or QApplication([])

    @patch('os.startfile')
    @patch('platform.system')
    def test_open_pdf_windows(self, mock_system, mock_startfile):
        """Should open PDF on Windows."""
        from ui.tinyfish_panel import TinyFishWorkspacePanel
        from pathlib import Path

        mock_system.return_value = "Windows"

        panel = TinyFishWorkspacePanel()
        pdf_path = Path('/tmp/report.pdf')

        panel._open_pdf(pdf_path)

        # Should call os.startfile on Windows
        mock_startfile.assert_called_once()

    @patch('subprocess.run')
    @patch('platform.system')
    def test_open_pdf_macos(self, mock_system, mock_run):
        """Should open PDF on macOS."""
        from ui.tinyfish_panel import TinyFishWorkspacePanel
        from pathlib import Path

        mock_system.return_value = "Darwin"

        panel = TinyFishWorkspacePanel()
        pdf_path = Path('/tmp/report.pdf')

        panel._open_pdf(pdf_path)

        # Should call subprocess.run with 'open' on macOS
        self.assertTrue(mock_run.called)

    @patch('subprocess.run')
    @patch('platform.system')
    @patch('time.sleep')
    def test_open_whatsapp_windows(self, mock_sleep, mock_system, mock_run):
        """Should open WhatsApp on Windows."""
        from ui.tinyfish_panel import TinyFishWorkspacePanel

        mock_system.return_value = "Windows"

        panel = TinyFishWorkspacePanel()

        panel._open_whatsapp()

        # Should call subprocess.run
        self.assertTrue(mock_run.called)


class TestButtonStates(unittest.TestCase):
    """Test export button enable/disable states."""

    def setUp(self):
        """Set up test fixtures."""
        from PyQt6.QtWidgets import QApplication
        self.app = QApplication.instance() or QApplication([])

    def test_buttons_initially_enabled(self):
        """Export buttons should be enabled initially."""
        from ui.tinyfish_panel import TinyFishWorkspacePanel

        panel = TinyFishWorkspacePanel()

        # Buttons should be enabled
        self.assertTrue(panel._pdf_btn.isEnabled())
        self.assertTrue(panel._whatsapp_btn.isEnabled())


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
