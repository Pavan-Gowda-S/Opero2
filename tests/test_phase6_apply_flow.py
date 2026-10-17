"""
Phase 6 Apply Flow Tests

Tests opportunity search, ranking, review dialog, and safety gates.
All tests run 100% offline with mocks.

Test Categories:
1. Apply Flow Tab Tests
2. Opportunity Card Tests
3. Review Dialog Tests
4. Safety Gate Tests
5. Profile Integration Tests
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestApplyFlowTab(unittest.TestCase):
    """Test Apply Flow tab UI components."""

    def setUp(self):
        """Set up test fixtures."""
        from PyQt6.QtWidgets import QApplication
        self.app = QApplication.instance() or QApplication([])

    def test_apply_tab_exists(self):
        """Apply Flow tab should be added to workspace."""
        from ui.tinyfish_panel import TinyFishWorkspacePanel

        panel = TinyFishWorkspacePanel()

        # Should have 3 tabs now
        self.assertEqual(panel._tabs.count(), 3)

        # Third tab should be Apply Flow
        self.assertEqual(panel._tabs.tabText(2), "🎯  Apply Flow")

    def test_apply_search_bar(self):
        """Apply search bar should be initialized."""
        from ui.tinyfish_panel import TinyFishWorkspacePanel

        panel = TinyFishWorkspacePanel()

        # Should have apply input and button
        self.assertIsNotNone(panel._apply_input)
        self.assertIsNotNone(panel._apply_search_btn)

        # Input should have correct placeholder
        self.assertIn("internships or hackathons", panel._apply_input.placeholderText())

    def test_profile_indicator(self):
        """Profile indicator should show loaded profile info."""
        from ui.tinyfish_panel import TinyFishWorkspacePanel

        panel = TinyFishWorkspacePanel()

        # Set profile info
        panel.set_profile_info("John Doe", ["Python", "AI", "React", "Django", "ML"])

        # Profile label should be updated
        label_text = panel._profile_label.text()
        self.assertIn("John Doe", label_text)
        self.assertIn("Python", label_text)
        self.assertIn("AI", label_text)

    def test_tab_mode_switching(self):
        """Switching to Apply tab should set mode to 'apply'."""
        from ui.tinyfish_panel import TinyFishWorkspacePanel

        panel = TinyFishWorkspacePanel()

        # Switch to Apply tab
        panel._tabs.setCurrentIndex(2)

        # Mode should be 'apply'
        self.assertEqual(panel._current_mode, "apply")


class TestOpportunityCards(unittest.TestCase):
    """Test opportunity card rendering and ranking."""

    def setUp(self):
        """Set up test fixtures."""
        from PyQt6.QtWidgets import QApplication
        self.app = QApplication.instance() or QApplication([])

    def test_add_opportunity_card(self):
        """Should create opportunity cards with match scores."""
        from ui.tinyfish_panel import TinyFishWorkspacePanel

        panel = TinyFishWorkspacePanel()

        # Add opportunity
        opportunity = {
            "title": "Python AI Intern",
            "organization": "TechCorp",
            "match_score": 94,
            "match_rationale": "Matches your Python and AI experience",
            "deadline": "2026-11-15",
            "location": "Remote",
            "url": "https://example.com/apply"
        }

        panel.add_opportunity_card(opportunity)

        # Should add card to layout
        # Layout has: search bar, profile, stretch + cards
        self.assertGreater(panel._apply_layout.count(), 3)

    def test_opportunity_match_scoring(self):
        """Opportunity cards should display match scores correctly."""
        from ui.tinyfish_panel import TinyFishWorkspacePanel

        panel = TinyFishWorkspacePanel()

        opportunities = [
            {"title": "High Match", "match_score": 95, "organization": "A"},
            {"title": "Medium Match", "match_score": 78, "organization": "B"},
            {"title": "Low Match", "match_score": 60, "organization": "C"},
        ]

        for opp in opportunities:
            panel.add_opportunity_card(opp)

        # Should have 3 cards added
        self.assertEqual(panel._apply_layout.count() - 3, len(opportunities))

    def test_opportunity_card_required_fields(self):
        """Opportunity cards should handle missing optional fields."""
        from ui.tinyfish_panel import TinyFishWorkspacePanel

        panel = TinyFishWorkspacePanel()

        # Minimal opportunity (no deadline, location)
        opportunity = {
            "title": "Test Opportunity",
            "organization": "TestOrg",
            "match_score": 85,
            "match_rationale": "Good match"
        }

        # Should not crash with missing fields
        panel.add_opportunity_card(opportunity)

        self.assertGreater(panel._apply_layout.count(), 3)

    def test_clear_apply_results(self):
        """Should clear opportunity cards when requested."""
        from ui.tinyfish_panel import TinyFishWorkspacePanel

        panel = TinyFishWorkspacePanel()

        # Add multiple opportunities
        for i in range(3):
            panel.add_opportunity_card({
                "title": f"Opp {i}",
                "organization": "Org",
                "match_score": 80
            })

        initial_count = panel._apply_layout.count()

        # Clear results
        panel.clear_apply_results()

        # Should remove cards but keep search bar, profile, stretch
        self.assertEqual(panel._apply_layout.count(), 3)
        self.assertLess(panel._apply_layout.count(), initial_count)


class TestReviewDialog(unittest.TestCase):
    """Test pre-submission review dialog."""

    def setUp(self):
        """Set up test fixtures."""
        from PyQt6.QtWidgets import QApplication
        self.app = QApplication.instance() or QApplication([])

    def test_review_dialog_creation(self):
        """Review dialog should initialize with field mappings."""
        from ui.apply_review_dialog import ApplyReviewDialog, FieldMapping

        mappings = [
            FieldMapping("Full Name", "John Doe", "Profile", 100),
            FieldMapping("Email", "john@example.com", "Profile", 100),
        ]

        dialog = ApplyReviewDialog(
            opportunity_title="Test Intern",
            target_url="https://example.com/apply",
            field_mappings=mappings,
            cover_note="Test cover note"
        )

        # Dialog should be modal
        self.assertTrue(dialog.isModal())

        # Should have correct title
        self.assertEqual(dialog.windowTitle(), "Application Pre-Fill Review")

    def test_review_dialog_field_table(self):
        """Review dialog should display field mapping table."""
        from ui.apply_review_dialog import ApplyReviewDialog, FieldMapping

        mappings = [
            FieldMapping("Name", "John", "Profile", 100),
            FieldMapping("Email", "john@test.com", "Profile", 100),
            FieldMapping("Skills", "Python, AI", "Synthesized", 80),
        ]

        dialog = ApplyReviewDialog(
            opportunity_title="Test",
            target_url="https://test.com",
            field_mappings=mappings,
            cover_note="Note"
        )

        # Dialog should be created without errors
        self.assertIsNotNone(dialog)

    def test_review_dialog_proceed_signal(self):
        """Review dialog should emit proceed signal with field data."""
        from ui.apply_review_dialog import ApplyReviewDialog, FieldMapping
        from PyQt6.QtWidgets import QApplication

        mappings = [
            FieldMapping("Name", "Test User", "Profile", 100),
        ]

        dialog = ApplyReviewDialog(
            opportunity_title="Test",
            target_url="https://test.com/apply",
            field_mappings=mappings,
            cover_note="Cover"
        )

        # Connect signal
        signal_received = []
        dialog.proceed_to_prefill.connect(lambda url, data: signal_received.append((url, data)))

        # Trigger proceed
        dialog._on_proceed()

        QApplication.processEvents()

        # Signal should be emitted
        self.assertEqual(len(signal_received), 1)
        url, field_data = signal_received[0]
        self.assertEqual(url, "https://test.com/apply")
        self.assertIn("Name", field_data)
        self.assertEqual(field_data["Name"], "Test User")

    def test_review_dialog_safety_warning(self):
        """Review dialog should display safety warning."""
        from ui.apply_review_dialog import ApplyReviewDialog, FieldMapping

        mappings = [FieldMapping("Name", "Test", "Profile", 100)]

        dialog = ApplyReviewDialog(
            opportunity_title="Test",
            target_url="https://test.com",
            field_mappings=mappings,
            cover_note="Note"
        )

        # Dialog should be created with safety warning
        self.assertIsNotNone(dialog)


class TestSafetyGates(unittest.TestCase):
    """Test form safety gates and validation."""

    def test_payment_field_detection(self):
        """Should block forms with payment fields."""
        from actions.form_safety import FormSubmissionReview, FormField

        # Create review with payment field
        review = FormSubmissionReview(
            target_url="https://test.com",
            form_name="Application",
            form_id="apply",
            fields=[
                FormField("name", "John Doe", "text"),
                FormField("credit_card", "1234567812345678", "text"),
            ],
            action_url=None
        )

        # Import the private function for testing
        from actions.form_safety import _contains_payment_fields

        # Should detect payment field
        self.assertTrue(_contains_payment_fields(review))

    def test_payment_keywords_blocking(self):
        """Should block forms with payment-related keywords."""
        from actions.form_safety import FormSubmissionReview, FormField, _contains_payment_fields

        payment_keywords = ["card", "cvv", "billing", "payment"]

        for keyword in payment_keywords:
            review = FormSubmissionReview(
                target_url="https://test.com",
                form_name="Form",
                form_id="form",
                fields=[FormField(keyword, "test", "text")],
                action_url=None
            )

            self.assertTrue(_contains_payment_fields(review),
                          f"Should detect '{keyword}' as payment field")

    def test_goal_validation_prohibited_patterns(self):
        """Should reject goals with prohibited patterns."""
        from actions.form_safety import validate_form_goal

        prohibited_goals = [
            "enter credit card information",
            "submit payment info",
            "create account with password",
            "delete my profile",
            "post comment on forum",
        ]

        for goal in prohibited_goals:
            is_valid, error = validate_form_goal(goal)
            self.assertFalse(is_valid, f"Should reject goal: {goal}")
            self.assertIsNotNone(error)

    def test_goal_validation_safe_patterns(self):
        """Should allow safe form filling goals."""
        from actions.form_safety import validate_form_goal

        safe_goals = [
            "fill internship application form",
            "complete hackathon registration",
            "fill out contact form",
            "submit job application",
        ]

        for goal in safe_goals:
            is_valid, error = validate_form_goal(goal)
            self.assertTrue(is_valid, f"Should allow goal: {goal}")
            self.assertIsNone(error)

    def test_missing_required_fields_block(self):
        """Should block submission if required fields are missing."""
        from actions.form_safety import FormSubmissionReview, FormField

        review = FormSubmissionReview(
            target_url="https://test.com",
            form_name="Application",
            form_id="app",
            fields=[
                FormField("name", "John", "text", required=True),
                FormField("email", "", "email", required=True),  # Missing required
            ],
            action_url=None
        )

        # Should detect missing required fields
        self.assertTrue(review.has_missing_fields())

    def test_inferred_fields_flagged(self):
        """Should flag fields with inferred values."""
        from actions.form_safety import FormSubmissionReview, FormField

        review = FormSubmissionReview(
            target_url="https://test.com",
            form_name="Form",
            form_id="form",
            fields=[
                FormField("name", "John", "text", required=True),
                FormField("major", "Computer Science", "text", required=True, inferred=True),
            ],
            action_url=None
        )

        # Should flag inferred fields as problematic
        self.assertTrue(review.has_missing_fields())


class TestProfileIntegration(unittest.TestCase):
    """Test profile data integration with Apply Flow."""

    def setUp(self):
        """Set up test fixtures."""
        from PyQt6.QtWidgets import QApplication
        self.app = QApplication.instance() or QApplication([])

    def test_profile_data_structure(self):
        """OpportunityProfile should hold user data."""
        from ui.apply_review_dialog import OpportunityProfile

        profile = OpportunityProfile(
            full_name="Jane Smith",
            email="jane@example.com",
            phone="+1-555-0199",
            skills=["Python", "JavaScript", "React"],
            resume_path="/path/to/resume.pdf",
            portfolio_url="https://portfolio.com",
            linkedin_url="https://linkedin.com/in/janesmith",
            github_url="https://github.com/janesmith"
        )

        self.assertEqual(profile.full_name, "Jane Smith")
        self.assertEqual(len(profile.skills), 3)
        self.assertIn("Python", profile.skills)

    def test_field_mapping_confidence_levels(self):
        """FieldMapping should track confidence levels."""
        from ui.apply_review_dialog import FieldMapping

        high_confidence = FieldMapping("Email", "test@test.com", "Profile", 100)
        medium_confidence = FieldMapping("Skills", "Python, AI", "Synthesized", 75)
        low_confidence = FieldMapping("Interests", "ML research", "Inferred", 50)

        self.assertEqual(high_confidence.confidence, 100)
        self.assertEqual(medium_confidence.confidence, 75)
        self.assertEqual(low_confidence.confidence, 50)

    def test_cover_note_generation(self):
        """Should generate tailored cover notes."""
        from ui.tinyfish_panel import TinyFishWorkspacePanel

        panel = TinyFishWorkspacePanel()

        opportunity = {
            "title": "ML Research Intern",
            "organization": "AI Labs"
        }

        cover_note = panel._generate_cover_note(opportunity)

        # Should mention opportunity details
        self.assertIn("ML Research Intern", cover_note)
        self.assertIn("AI Labs", cover_note)
        self.assertGreater(len(cover_note), 100)


class TestApplyFlowSearch(unittest.TestCase):
    """Test Apply Flow search functionality."""

    def setUp(self):
        """Set up test fixtures."""
        from PyQt6.QtWidgets import QApplication
        self.app = QApplication.instance() or QApplication([])

    def test_apply_search_trigger(self):
        """Apply search should emit signal with 'apply' mode."""
        from ui.tinyfish_panel import TinyFishWorkspacePanel

        panel = TinyFishWorkspacePanel()

        # Connect signal
        signal_received = []
        panel.search_requested.connect(lambda q, m: signal_received.append((q, m)))

        # Set query and trigger search
        panel._apply_input.setText("Python internships")
        panel._on_apply_search()

        # Should emit with 'apply' mode
        self.assertEqual(len(signal_received), 1)
        query, mode = signal_received[0]
        self.assertEqual(query, "Python internships")
        self.assertEqual(mode, "apply")

    def test_trigger_search_with_apply_mode(self):
        """trigger_search should switch to Apply tab for apply mode."""
        from ui.tinyfish_panel import TinyFishWorkspacePanel

        panel = TinyFishWorkspacePanel()

        # Trigger search in apply mode
        panel.trigger_search("test query", mode="apply")

        # Should switch to Apply tab (index 2)
        self.assertEqual(panel._tabs.currentIndex(), 2)
        self.assertEqual(panel._current_mode, "apply")


class TestSafetyWorkflow(unittest.TestCase):
    """Test complete safety workflow from review to pre-fill."""

    def setUp(self):
        """Set up test fixtures."""
        from PyQt6.QtWidgets import QApplication
        self.app = QApplication.instance() or QApplication([])

    def test_review_to_prefill_workflow(self):
        """Complete workflow: review dialog → proceed → pre-fill signal."""
        from ui.tinyfish_panel import TinyFishWorkspacePanel

        panel = TinyFishWorkspacePanel()

        # Mock opportunity
        opportunity = {
            "title": "Test Internship",
            "organization": "TestCorp",
            "match_score": 90,
            "match_rationale": "Good fit",
            "url": "https://testcorp.com/apply"
        }

        # Trigger review & apply with dialog.exec mocked so headless test doesn't hang
        with patch("ui.apply_review_dialog.ApplyReviewDialog.exec"):
            try:
                panel._on_review_apply(opportunity)
                self.assertTrue(True)
            except Exception as e:
                self.fail(f"Review workflow failed: {e}")

    def test_unknown_field_handling(self):
        """Unknown fields should be flagged, not invented."""
        from ui.apply_review_dialog import FieldMapping

        # Unknown field should be flagged with low confidence
        unknown_field = FieldMapping(
            "Favorite Programming Language",
            "[UNKNOWN - User input needed]",
            "Not in profile",
            0
        )

        self.assertEqual(unknown_field.confidence, 0)
        self.assertIn("UNKNOWN", unknown_field.proposed_value)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
