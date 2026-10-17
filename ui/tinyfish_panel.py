"""TinyFish Search Workspace Panel — Quick Search and Deep Research tabs."""
from __future__ import annotations

import threading
from typing import Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTabWidget, QScrollArea, QWidget, QProgressBar, QTextEdit, QSizePolicy,
)

from core.logger import get_logger
from ui.theme import C

log = get_logger(__name__)


class TinyFishWorkspacePanel(QFrame):
    """
    TinyFish workspace with Quick Search and Deep Research tabs.

    Signals:
        search_requested(str, str) - Emitted when search is initiated (query, mode)
        search_cancelled() - Emitted when user cancels ongoing search
    """

    search_requested = pyqtSignal(str, str)  # (query, mode)
    search_cancelled = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TinyFishPanel")
        self.setStyleSheet(f"""
            QFrame#TinyFishPanel {{
                background: {C.PANEL};
                border-top: 1px solid {C.BORDER_B};
            }}
        """)

        self._is_searching = False
        self._current_mode = "quick"

        # Build UI
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        layout.addWidget(self._build_header())

        # Tabs
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: {C.PANEL};
            }}
            QTabBar::tab {{
                background: {C.PANEL2};
                color: {C.TEXT_DIM};
                border: 1px solid {C.BORDER};
                border-bottom: none;
                padding: 6px 16px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background: {C.PANEL};
                color: {C.PRI};
                border-bottom: 2px solid {C.PRI};
            }}
            QTabBar::tab:hover {{
                color: {C.TEXT};
            }}
        """)

        # Quick Search tab
        self._quick_scroll = QScrollArea()
        self._quick_scroll.setWidgetResizable(True)
        self._quick_scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: {C.PANEL};
            }}
        """)
        self._quick_content = QWidget()
        self._quick_layout = QVBoxLayout(self._quick_content)
        self._quick_layout.setContentsMargins(12, 12, 12, 12)
        self._quick_layout.setSpacing(8)
        self._quick_layout.addStretch()
        self._quick_scroll.setWidget(self._quick_content)

        # Deep Research tab
        self._deep_scroll = QScrollArea()
        self._deep_scroll.setWidgetResizable(True)
        self._deep_scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: {C.PANEL};
            }}
        """)
        self._deep_content = QWidget()
        self._deep_layout = QVBoxLayout(self._deep_content)
        self._deep_layout.setContentsMargins(12, 12, 12, 12)
        self._deep_layout.setSpacing(8)
        self._deep_layout.addStretch()
        self._deep_scroll.setWidget(self._deep_content)

        # Apply Flow tab (Phase 6)
        self._apply_scroll = QScrollArea()
        self._apply_scroll.setWidgetResizable(True)
        self._apply_scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: {C.PANEL};
            }}
        """)
        self._apply_content = QWidget()
        self._apply_layout = QVBoxLayout(self._apply_content)
        self._apply_layout.setContentsMargins(12, 12, 12, 12)
        self._apply_layout.setSpacing(8)

        # Apply Flow search bar
        self._apply_layout.addWidget(self._build_apply_search_bar())

        # Profile indicator
        self._apply_layout.addWidget(self._build_profile_indicator())

        # Opportunity cards container
        self._apply_layout.addStretch()
        self._apply_scroll.setWidget(self._apply_content)

        self._tabs.addTab(self._quick_scroll, "◈  Quick Search")
        self._tabs.addTab(self._deep_scroll, "◈  Deep Research")
        self._tabs.addTab(self._apply_scroll, "🎯  Apply Flow")
        self._tabs.currentChanged.connect(self._on_tab_changed)

        layout.addWidget(self._tabs, stretch=1)

        # Progress bar (hidden by default)
        self._progress = QProgressBar()
        self._progress.setFixedHeight(3)
        self._progress.setTextVisible(False)
        self._progress.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background: {C.PANEL2};
            }}
            QProgressBar::chunk {{
                background: {C.PRI};
            }}
        """)
        self._progress.setRange(0, 0)  # Indeterminate
        self._progress.hide()
        layout.addWidget(self._progress)

        # Input area
        layout.addWidget(self._build_input_area())

        # Export toolbar (Phase 5) - shown after results available
        self._export_toolbar = self._build_export_toolbar()
        self._export_toolbar.hide()  # Hidden until results available
        layout.addWidget(self._export_toolbar)

    def _build_header(self) -> QWidget:
        """Build panel header with title and close button."""
        header = QWidget()
        header.setStyleSheet(f"background: {C.DARK}; border-bottom: 1px solid {C.BORDER};")
        header.setFixedHeight(32)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(8)

        # Title
        title = QLabel("◈  TINYFISH WORKSPACE")
        title.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {C.PRI}; background: transparent;")
        layout.addWidget(title)

        layout.addStretch()

        # Status indicator
        self._status_label = QLabel("READY")
        self._status_label.setFont(QFont("Courier New", 7))
        self._status_label.setStyleSheet(f"color: {C.TEXT_DIM}; background: transparent;")
        layout.addWidget(self._status_label)

        # Cancel button (hidden by default)
        self._cancel_btn = QPushButton("✕  CANCEL")
        self._cancel_btn.setFont(QFont("Courier New", 7, QFont.Weight.Bold))
        self._cancel_btn.setFixedHeight(20)
        self._cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {C.RED};
                border: 1px solid {C.RED};
                border-radius: 3px;
                padding: 0 6px;
            }}
            QPushButton:hover {{
                background: {C.RED};
                color: {C.DARK};
            }}
        """)
        self._cancel_btn.clicked.connect(self._on_cancel)
        self._cancel_btn.hide()
        layout.addWidget(self._cancel_btn)

        return header

    def _build_input_area(self) -> QWidget:
        """Build input field with search button."""
        container = QWidget()
        container.setStyleSheet(f"""
            background: {C.PANEL2};
            border-top: 1px solid {C.BORDER};
        """)
        container.setFixedHeight(52)

        layout = QHBoxLayout(container)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        # Input field
        self._input = QLineEdit()
        self._input.setPlaceholderText("Enter search query or research question…")
        self._input.setFont(QFont("Segoe UI", 9))
        self._input.setFixedHeight(36)
        self._input.setStyleSheet(f"""
            QLineEdit {{
                background: {C.PANEL};
                color: {C.WHITE};
                border: 1px solid {C.BORDER};
                border-radius: 4px;
                padding: 4px 10px;
            }}
            QLineEdit:focus {{
                border: 1px solid {C.PRI};
            }}
        """)
        self._input.returnPressed.connect(self._on_search)
        layout.addWidget(self._input)

        # Search button
        self._search_btn = QPushButton("▸  SEARCH")
        self._search_btn.setFixedSize(100, 36)
        self._search_btn.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        self._search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._search_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C.PRI_GHO};
                color: {C.PRI};
                border: 1px solid {C.PRI_DIM};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background: {C.PRI_DIM};
                color: {C.WHITE};
            }}
            QPushButton:disabled {{
                background: {C.PANEL2};
                color: {C.TEXT_DIM};
                border: 1px solid {C.BORDER};
            }}
        """)
        self._search_btn.clicked.connect(self._on_search)
        layout.addWidget(self._search_btn)

        return container

    def _on_tab_changed(self, index: int):
        """Handle tab change."""
        if index == 0:
            self._current_mode = "quick"
        elif index == 1:
            self._current_mode = "deep"
        elif index == 2:
            self._current_mode = "apply"

    def _on_search(self):
        """Handle search button click."""
        query = self._input.text().strip()
        if not query:
            return

        if self._is_searching:
            return

        # Emit signal (main.py will handle actual search)
        self.search_requested.emit(query, self._current_mode)

        # Update UI state
        self.set_searching(True)

    def _on_cancel(self):
        """Handle cancel button click."""
        self.search_cancelled.emit()
        self.set_searching(False)

    def set_searching(self, searching: bool):
        """Update UI to reflect search state."""
        self._is_searching = searching

        if searching:
            self._status_label.setText("SEARCHING…")
            self._status_label.setStyleSheet(f"color: {C.PRI}; background: transparent;")
            self._progress.show()
            self._cancel_btn.show()
            self._search_btn.setEnabled(False)
            self._input.setEnabled(False)
        else:
            self._status_label.setText("READY")
            self._status_label.setStyleSheet(f"color: {C.TEXT_DIM}; background: transparent;")
            self._progress.hide()
            self._cancel_btn.hide()
            self._search_btn.setEnabled(True)
            self._input.setEnabled(True)

    def clear_results(self):
        """Clear all results from current tab."""
        if self._current_mode == "quick":
            self._clear_layout(self._quick_layout)
        else:
            self._clear_layout(self._deep_layout)

    def _clear_layout(self, layout: QVBoxLayout):
        """Remove all widgets from layout except stretch."""
        while layout.count() > 1:  # Keep stretch at end
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def add_result_card(self, title: str, url: str, snippet: str):
        """Add a result card to the current tab (Quick Search)."""
        card = self._create_result_card(title, url, snippet)

        if self._current_mode == "quick":
            self._quick_layout.insertWidget(self._quick_layout.count() - 1, card)
        else:
            self._deep_layout.insertWidget(self._deep_layout.count() - 1, card)

    def _create_result_card(self, title: str, url: str, snippet: str) -> QFrame:
        """Create a single result card widget."""
        card = QFrame()
        card.setObjectName("ResultCard")
        card.setStyleSheet(f"""
            QFrame#ResultCard {{
                background: {C.PANEL2};
                border: 1px solid {C.BORDER};
                border-radius: 6px;
                padding: 0;
            }}
            QFrame#ResultCard:hover {{
                border: 1px solid {C.BORDER_B};
                background: {C.DARK};
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        title_label.setStyleSheet(f"color: {C.PRI}; background: transparent;")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        # URL
        url_label = QLabel(url)
        url_label.setFont(QFont("Segoe UI", 7))
        url_label.setStyleSheet(f"color: {C.TEXT_DIM}; background: transparent;")
        url_label.setWordWrap(True)
        layout.addWidget(url_label)

        # Snippet
        snippet_label = QLabel(snippet)
        snippet_label.setFont(QFont("Segoe UI", 8))
        snippet_label.setStyleSheet(f"color: {C.TEXT}; background: transparent;")
        snippet_label.setWordWrap(True)
        layout.addWidget(snippet_label)

        return card

    def set_deep_research_content(self, content: str):
        """Set formatted content for Deep Research tab."""
        self._clear_layout(self._deep_layout)

        # Create text display
        text_widget = QTextEdit()
        text_widget.setReadOnly(True)
        text_widget.setMarkdown(content)
        text_widget.setFont(QFont("Segoe UI", 9))
        text_widget.setStyleSheet(f"""
            QTextEdit {{
                background: {C.PANEL2};
                color: {C.TEXT};
                border: 1px solid {C.BORDER};
                border-radius: 6px;
                padding: 12px;
            }}
        """)
        text_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._deep_layout.insertWidget(0, text_widget)

    def show_error(self, message: str):
        """Display error message in current tab."""
        error_card = QFrame()
        error_card.setStyleSheet(f"""
            QFrame {{
                background: {C.PANEL2};
                border: 1px solid {C.RED};
                border-radius: 6px;
            }}
        """)

        layout = QVBoxLayout(error_card)
        layout.setContentsMargins(12, 10, 12, 10)

        error_label = QLabel(f"⚠️  {message}")
        error_label.setFont(QFont("Segoe UI", 9))
        error_label.setStyleSheet(f"color: {C.RED}; background: transparent;")
        error_label.setWordWrap(True)
        layout.addWidget(error_label)

        if self._current_mode == "quick":
            self._quick_layout.insertWidget(0, error_card)
        else:
            self._deep_layout.insertWidget(0, error_card)

    def trigger_search(self, query: str, mode: str = "quick") -> None:
        """Programmatically trigger a search — called from voice routing."""
        # Switch to appropriate tab
        if mode == "apply":
            self._tabs.setCurrentIndex(2)
        elif mode == "deep":
            self._tabs.setCurrentIndex(1)
        else:
            self._tabs.setCurrentIndex(0)
        self._current_mode = mode

        # Set query text
        self._input.setText(query)

        # Trigger search
        self._on_search()

    def _build_apply_search_bar(self) -> QWidget:
        """Build Apply Flow search bar (Phase 6)."""
        container = QWidget()
        container.setStyleSheet(f"""
            background: {C.PANEL2};
            border: 1px solid {C.BORDER};
            border-radius: 6px;
        """)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # Title
        title = QLabel("🎯  Find Opportunities")
        title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {C.PRI}; background: transparent;")
        layout.addWidget(title)

        # Search input
        self._apply_input = QLineEdit()
        self._apply_input.setPlaceholderText("Search internships or hackathons (e.g., Python AI Intern, HackMIT)...")
        self._apply_input.setFont(QFont("Segoe UI", 9))
        self._apply_input.setFixedHeight(36)
        self._apply_input.setStyleSheet(f"""
            QLineEdit {{
                background: {C.PANEL};
                color: {C.WHITE};
                border: 1px solid {C.BORDER};
                border-radius: 4px;
                padding: 4px 10px;
            }}
            QLineEdit:focus {{
                border: 1px solid {C.PRI};
            }}
        """)
        self._apply_input.returnPressed.connect(self._on_apply_search)
        layout.addWidget(self._apply_input)

        # Button row
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        btn_layout.addStretch()

        # Find Matches button
        self._apply_search_btn = QPushButton("🔍  Find Matches")
        self._apply_search_btn.setFixedSize(140, 34)
        self._apply_search_btn.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self._apply_search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_search_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C.PRI};
                color: {C.DARK};
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background: {C.PRI_DIM};
                color: {C.WHITE};
            }}
            QPushButton:disabled {{
                background: {C.PANEL2};
                color: {C.TEXT_DIM};
            }}
        """)
        self._apply_search_btn.clicked.connect(self._on_apply_search)
        btn_layout.addWidget(self._apply_search_btn)

        layout.addLayout(btn_layout)

        return container

    def _build_profile_indicator(self) -> QWidget:
        """Build profile indicator chip (Phase 6)."""
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background: {C.DARK};
                border: 1px solid {C.GREEN};
                border-radius: 4px;
            }}
        """)

        layout = QHBoxLayout(container)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(6)

        icon = QLabel("✓")
        icon.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        icon.setStyleSheet(f"color: {C.GREEN}; background: transparent;")
        layout.addWidget(icon)

        # Profile info label
        self._profile_label = QLabel("Profile: Loading...")
        self._profile_label.setFont(QFont("Segoe UI", 8))
        self._profile_label.setStyleSheet(f"color: {C.TEXT}; background: transparent;")
        layout.addWidget(self._profile_label)

        layout.addStretch()

        return container

    def set_profile_info(self, name: str, skills: list):
        """Update profile indicator with loaded profile info."""
        skills_text = ", ".join(skills[:5])  # Show first 5 skills
        if len(skills) > 5:
            skills_text += f" +{len(skills) - 5} more"
        self._profile_label.setText(f"Profile: {name} (skills: {skills_text})")

    def _on_apply_search(self):
        """Handle Apply Flow search (Phase 6)."""
        query = self._apply_input.text().strip()
        if not query:
            return

        if self._is_searching:
            return

        # Emit signal (main.py will handle actual search)
        self.search_requested.emit(query, "apply")

        # Update UI state
        self.set_searching(True)

    def add_opportunity_card(self, opportunity: dict):
        """Add ranked opportunity card to Apply Flow tab (Phase 6)."""
        card = self._create_opportunity_card(opportunity)
        # Insert before stretch
        self._apply_layout.insertWidget(self._apply_layout.count() - 1, card)

    def _create_opportunity_card(self, opportunity: dict) -> QFrame:
        """Create opportunity card widget (Phase 6)."""
        card = QFrame()
        card.setObjectName("OpportunityCard")
        card.setStyleSheet(f"""
            QFrame#OpportunityCard {{
                background: {C.PANEL2};
                border: 1px solid {C.BORDER};
                border-radius: 8px;
                padding: 0;
            }}
            QFrame#OpportunityCard:hover {{
                border: 1px solid {C.PRI};
                background: {C.DARK};
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        # Header row: Title + Match Badge
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        # Title
        title = QLabel(opportunity.get("title", "Untitled"))
        title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {C.PRI}; background: transparent;")
        title.setWordWrap(True)
        header_layout.addWidget(title, stretch=1)

        # Match score badge
        match_score = opportunity.get("match_score", 0)
        badge = QLabel(f"{match_score}% Match")
        badge.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
        badge.setFixedSize(85, 24)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Color code by match score
        if match_score >= 90:
            badge_color = C.GREEN
        elif match_score >= 75:
            badge_color = C.PRI
        else:
            badge_color = C.ACC

        badge.setStyleSheet(f"""
            QLabel {{
                background: {badge_color};
                color: {C.DARK};
                border-radius: 4px;
            }}
        """)
        header_layout.addWidget(badge)

        layout.addLayout(header_layout)

        # Organization
        org = QLabel(opportunity.get("organization", "Unknown Organization"))
        org.setFont(QFont("Segoe UI", 8))
        org.setStyleSheet(f"color: {C.TEXT_DIM}; background: transparent;")
        layout.addWidget(org)

        # Match rationale
        rationale = QLabel(f"💡 {opportunity.get('match_rationale', 'No rationale available')}")
        rationale.setFont(QFont("Segoe UI", 8))
        rationale.setStyleSheet(f"color: {C.TEXT}; background: transparent;")
        rationale.setWordWrap(True)
        layout.addWidget(rationale)

        # Details row: Deadline + Location
        details_layout = QHBoxLayout()
        details_layout.setSpacing(12)

        if opportunity.get("deadline"):
            deadline = QLabel(f"📅 {opportunity['deadline']}")
            deadline.setFont(QFont("Segoe UI", 7))
            deadline.setStyleSheet(f"color: {C.TEXT_DIM}; background: transparent;")
            details_layout.addWidget(deadline)

        if opportunity.get("location"):
            location = QLabel(f"📍 {opportunity['location']}")
            location.setFont(QFont("Segoe UI", 7))
            location.setStyleSheet(f"color: {C.TEXT_DIM}; background: transparent;")
            details_layout.addWidget(location)

        details_layout.addStretch()
        layout.addLayout(details_layout)

        # Apply button
        apply_btn = QPushButton("📝  Review & Apply")
        apply_btn.setFixedSize(140, 32)
        apply_btn.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C.PRI_GHO};
                color: {C.PRI};
                border: 1px solid {C.PRI_DIM};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background: {C.PRI};
                color: {C.DARK};
            }}
        """)
        apply_btn.clicked.connect(lambda: self._on_review_apply(opportunity))

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(apply_btn)
        layout.addLayout(btn_layout)

        return card

    def _on_review_apply(self, opportunity: dict):
        """Handle Review & Apply button click (Phase 6)."""
        from ui.apply_review_dialog import ApplyReviewDialog, FieldMapping

        # Build field mappings (mock data for now - real implementation would fetch from profile)
        field_mappings = [
            FieldMapping("Full Name", "John Doe", "Profile", 100),
            FieldMapping("Email", "john@example.com", "Profile", 100),
            FieldMapping("Phone", "+1-555-0123", "Profile", 100),
            FieldMapping("Resume", "resume_2024.pdf", "file_processor", 100),
            FieldMapping("LinkedIn", "linkedin.com/in/johndoe", "Profile", 100),
            FieldMapping("Why are you interested?",
                        f"I am excited about this {opportunity.get('title', 'opportunity')} because...",
                        "Generated", 85),
        ]

        # Generate tailored cover note
        cover_note = self._generate_cover_note(opportunity)

        # Show review dialog
        dialog = ApplyReviewDialog(
            opportunity_title=opportunity.get("title", "Untitled"),
            target_url=opportunity.get("url", "https://example.com/apply"),
            field_mappings=field_mappings,
            cover_note=cover_note,
            parent=self
        )

        # Connect proceed signal
        dialog.proceed_to_prefill.connect(self._on_proceed_to_prefill)

        dialog.exec()

    def _generate_cover_note(self, opportunity: dict) -> str:
        """Generate tailored cover note for opportunity (Phase 6)."""
        title = opportunity.get("title", "this opportunity")
        org = opportunity.get("organization", "your organization")

        return (
            f"I am writing to express my strong interest in the {title} position at {org}. "
            f"With my background in software development and passion for innovation, "
            f"I believe I would be a great fit for this role. My experience with Python, "
            f"AI/ML technologies, and collaborative projects aligns well with the requirements. "
            f"I am excited about the opportunity to contribute to your team and learn from "
            f"experienced professionals in the field."
        )

    def _on_proceed_to_prefill(self, url: str, field_data: dict):
        """Handle proceed to pre-fill from review dialog (Phase 6)."""
        log.info(f"[ApplyFlow] Starting pre-fill for: {url}")

        # Emit signal to trigger agent execution
        # This will be handled by main.py window
        from PyQt6.QtCore import pyqtSignal
        if not hasattr(self, 'apply_prefill_requested'):
            self.apply_prefill_requested = pyqtSignal(str, dict)

        # For now, just log (window.py will connect this signal)
        log.info(f"[ApplyFlow] Pre-fill requested with {len(field_data)} fields")

    def clear_apply_results(self):
        """Clear opportunity cards from Apply Flow tab (Phase 6)."""
        # Remove all widgets except search bar, profile indicator, and stretch
        while self._apply_layout.count() > 3:  # Keep first 3 items
            item = self._apply_layout.takeAt(2)  # Always remove 3rd item
            if item.widget():
                item.widget().deleteLater()

    def _build_export_toolbar(self) -> QWidget:
        """Build export toolbar with PDF and WhatsApp buttons (Phase 5)."""
        toolbar = QWidget()
        toolbar.setStyleSheet(f"""
            background: {C.PANEL2};
            border-top: 1px solid {C.BORDER};
        """)
        toolbar.setFixedHeight(48)

        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(8)

        # Export label
        label = QLabel("📄  Export:")
        label.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold))
        label.setStyleSheet(f"color: {C.TEXT_DIM}; background: transparent;")
        layout.addWidget(label)

        # PDF button
        self._pdf_btn = QPushButton("📋 PDF")
        self._pdf_btn.setFixedSize(80, 34)
        self._pdf_btn.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        self._pdf_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._pdf_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C.PRI_GHO};
                color: {C.PRI};
                border: 1px solid {C.PRI_DIM};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background: {C.PRI_DIM};
                color: {C.WHITE};
            }}
            QPushButton:disabled {{
                background: {C.PANEL2};
                color: {C.TEXT_DIM};
                border: 1px solid {C.BORDER};
            }}
        """)
        self._pdf_btn.clicked.connect(self._on_export_pdf)
        layout.addWidget(self._pdf_btn)

        # WhatsApp button
        self._whatsapp_btn = QPushButton("💬 WhatsApp")
        self._whatsapp_btn.setFixedSize(110, 34)
        self._whatsapp_btn.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        self._whatsapp_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._whatsapp_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C.GREEN_D};
                color: {C.WHITE};
                border: 1px solid {C.GREEN};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background: {C.GREEN};
                color: {C.DARK};
            }}
            QPushButton:disabled {{
                background: {C.PANEL2};
                color: {C.TEXT_DIM};
                border: 1px solid {C.BORDER};
            }}
        """)
        self._whatsapp_btn.clicked.connect(self._on_export_whatsapp)
        layout.addWidget(self._whatsapp_btn)

        layout.addStretch()

        return toolbar

    def _on_export_pdf(self):
        """Handle PDF export button click (Phase 5)."""
        try:
            from actions.report_generator import ReportData, generate_pdf_report
            from datetime import datetime

            # Gather content from current tab
            if self._current_mode == "deep":
                # Deep research: extract markdown content from text widget inside scroll area
                content = ""
                for i in range(self._deep_layout.count()):
                    item = self._deep_layout.itemAt(i)
                    if item and item.widget() and isinstance(item.widget(), QTextEdit):
                        content = item.widget().toPlainText()
                        break
                if not content:
                    content = "No deep research content available."
                title = f"Deep Research: {self._input.text()[:60]}"
            else:
                # Quick search: gather result cards
                content = self._gather_quick_results_text()
                title = f"Quick Search: {self._input.text()[:60]}"

            # Build report data
            report_data = ReportData(
                title=title,
                target_url="TinyFish Search Results",
                status="COMPLETED",
                timestamp=datetime.now().isoformat(),
                executive_summary=content[:1000] if content else "Search results exported from TinyFish workspace.",
                raw_result=content,
                goal=self._input.text(),
            )

            # Generate PDF
            pdf_path = generate_pdf_report(report_data)

            # Open PDF in system viewer
            self._open_pdf(pdf_path)

            # Show success message
            self.show_error(f"✅ PDF exported: {pdf_path.name}")

            log.info(f"[TinyFish] PDF exported: {pdf_path}")

        except Exception as e:
            log.error(f"[TinyFish] PDF export failed: {e}")
            self.show_error(f"PDF export failed: {e}")

    def _on_export_whatsapp(self):
        """Handle WhatsApp export button click (Phase 5)."""
        try:
            from actions.report_generator import ReportData, generate_pdf_report
            from datetime import datetime
            import subprocess
            import time
            import platform

            # Gather content
            if self._current_mode == "deep":
                # Deep research: extract markdown content from text widget inside scroll area
                content = ""
                for i in range(self._deep_layout.count()):
                    item = self._deep_layout.itemAt(i)
                    if item and item.widget() and isinstance(item.widget(), QTextEdit):
                        content = item.widget().toPlainText()
                        break
                if not content:
                    content = "No deep research content available."
                title = f"Deep Research: {self._input.text()[:60]}"
            else:
                content = self._gather_quick_results_text()
                title = f"Quick Search: {self._input.text()[:60]}"

            # Build report data
            report_data = ReportData(
                title=title,
                target_url="TinyFish Search Results",
                status="COMPLETED",
                timestamp=datetime.now().isoformat(),
                executive_summary=content[:1000] if content else "Search results from TinyFish.",
                raw_result=content,
                goal=self._input.text(),
            )

            # Generate PDF
            pdf_path = generate_pdf_report(report_data)

            # Open WhatsApp
            system = platform.system()
            if system == "Windows":
                subprocess.run(["start", "", str(pdf_path)], shell=True, check=False)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", str(pdf_path)], check=False)
            else:  # Linux
                subprocess.run(["xdg-open", str(pdf_path)], check=False)

            time.sleep(1.5)

            # Open WhatsApp
            self._open_whatsapp()

            # Show instructions
            self.show_error(f"✅ PDF created. Attach {pdf_path.name} in WhatsApp chat.")

            log.info(f"[TinyFish] WhatsApp share initiated: {pdf_path}")

        except Exception as e:
            log.error(f"[TinyFish] WhatsApp share failed: {e}")
            self.show_error(f"WhatsApp share failed: {e}")

    def _gather_quick_results_text(self) -> str:
        """Gather text from quick search result cards."""
        results = []
        for i in range(self._quick_layout.count() - 1):  # -1 to skip stretch
            item = self._quick_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                # Extract text from labels in card
                for child in widget.findChildren(QLabel):
                    text = child.text()
                    if text:
                        results.append(text)
        return "\n\n".join(results) if results else "No results available."

    def _open_pdf(self, pdf_path):
        """Open PDF in system viewer."""
        import platform
        import subprocess
        import os

        system = platform.system()
        try:
            if system == "Windows":
                os.startfile(str(pdf_path))
            elif system == "Darwin":  # macOS
                subprocess.run(["open", str(pdf_path)], check=False)
            else:  # Linux
                subprocess.run(["xdg-open", str(pdf_path)], check=False)
        except Exception as e:
            log.error(f"[TinyFish] Failed to open PDF: {e}")

    def _open_whatsapp(self):
        """Open WhatsApp Desktop application."""
        import platform
        import subprocess
        import time

        system = platform.system()
        try:
            if system == "Windows":
                subprocess.run(["start", "", "whatsapp:"], shell=True, check=False)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", "-a", "WhatsApp"], check=False)
            else:  # Linux
                subprocess.run(["whatsapp"], check=False)

            time.sleep(2.0)
        except Exception as e:
            log.warning(f"[TinyFish] Could not open WhatsApp: {e}")

    def show_export_toolbar(self, show: bool = True):
        """Show or hide export toolbar (Phase 5)."""
        if show:
            self._export_toolbar.show()
        else:
            self._export_toolbar.hide()
