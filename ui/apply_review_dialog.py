"""Apply Flow Review Dialog - Pre-submission safety gate for opportunity applications."""
from __future__ import annotations

from typing import Optional, Dict, List
from dataclasses import dataclass

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QTextEdit, QFrame, QScrollArea,
    QWidget, QHeaderView,
)

from core.logger import get_logger
from ui.theme import C

log = get_logger(__name__)


@dataclass
class OpportunityProfile:
    """User profile data for opportunity applications."""
    full_name: str = ""
    email: str = ""
    phone: str = ""
    skills: List[str] = None
    resume_path: str = ""
    portfolio_url: str = ""
    linkedin_url: str = ""
    github_url: str = ""

    def __post_init__(self):
        if self.skills is None:
            self.skills = []


@dataclass
class FieldMapping:
    """Single form field mapping with value and metadata."""
    field_name: str
    proposed_value: str
    source: str
    confidence: int  # 0-100
    editable: bool = False


class ApplyReviewDialog(QDialog):
    """
    Pre-submission review dialog for opportunity applications.

    Shows exact field-value pairs to be filled, with mandatory user confirmation
    before agent execution. Enforces safety barrier: agent fills form but NEVER
    clicks final submit button.

    Signals:
        proceed_to_prefill(str, Dict) - Emitted when user confirms (url, field_data)
    """

    proceed_to_prefill = pyqtSignal(str, dict)  # (url, field_mappings)

    def __init__(
        self,
        opportunity_title: str,
        target_url: str,
        field_mappings: List[FieldMapping],
        cover_note: str,
        parent=None
    ):
        super().__init__(parent)

        self._opportunity_title = opportunity_title
        self._target_url = target_url
        self._field_mappings = field_mappings
        self._cover_note = cover_note

        self._init_ui()

    def _init_ui(self):
        """Initialize dialog UI."""
        self.setWindowTitle("Application Pre-Fill Review")
        self.setModal(True)
        self.resize(800, 700)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        layout.addWidget(self._build_header())

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: {C.PANEL};
            }}
        """)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(16)

        # URL preview
        content_layout.addWidget(self._build_url_section())

        # Field mapping table
        content_layout.addWidget(self._build_field_table())

        # Cover note
        content_layout.addWidget(self._build_cover_note_section())

        # Safety warning
        content_layout.addWidget(self._build_safety_warning())

        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)

        # Action buttons
        layout.addWidget(self._build_action_buttons())

    def _build_header(self) -> QWidget:
        """Build dialog header."""
        header = QWidget()
        header.setStyleSheet(f"""
            background: {C.DARK};
            border-bottom: 2px solid {C.PRI};
        """)
        header.setFixedHeight(60)

        layout = QVBoxLayout(header)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(4)

        title = QLabel(f"Application Pre-Fill Review")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {C.PRI}; background: transparent;")
        layout.addWidget(title)

        subtitle = QLabel(self._opportunity_title)
        subtitle.setFont(QFont("Segoe UI", 9))
        subtitle.setStyleSheet(f"color: {C.TEXT}; background: transparent;")
        layout.addWidget(subtitle)

        return header

    def _build_url_section(self) -> QWidget:
        """Build target URL preview section."""
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background: {C.PANEL2};
                border: 1px solid {C.BORDER};
                border-radius: 6px;
            }}
        """)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        label = QLabel("Target URL:")
        label.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold))
        label.setStyleSheet(f"color: {C.TEXT_DIM}; background: transparent;")
        layout.addWidget(label)

        url_label = QLabel(self._target_url)
        url_label.setFont(QFont("Courier New", 8))
        url_label.setStyleSheet(f"color: {C.PRI}; background: transparent;")
        url_label.setWordWrap(True)
        url_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(url_label)

        return container

    def _build_field_table(self) -> QWidget:
        """Build field mapping table."""
        container = QWidget()
        container.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Section header
        header = QLabel("Field Mapping:")
        header.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        header.setStyleSheet(f"color: {C.TEXT}; background: transparent;")
        layout.addWidget(header)

        # Table
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Field Name", "Proposed Value", "Source / Confidence"])
        table.setRowCount(len(self._field_mappings))

        table.setStyleSheet(f"""
            QTableWidget {{
                background: {C.PANEL2};
                border: 1px solid {C.BORDER};
                border-radius: 6px;
                gridline-color: {C.BORDER};
            }}
            QTableWidget::item {{
                padding: 6px;
                color: {C.TEXT};
            }}
            QHeaderView::section {{
                background: {C.DARK};
                color: {C.TEXT};
                padding: 8px;
                border: none;
                border-bottom: 1px solid {C.BORDER};
                font-weight: bold;
            }}
        """)

        # Populate table
        for row, mapping in enumerate(self._field_mappings):
            # Field name
            field_item = QTableWidgetItem(mapping.field_name)
            field_item.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold))
            table.setItem(row, 0, field_item)

            # Proposed value
            value = mapping.proposed_value
            if len(value) > 100:
                value = value[:100] + "..."
            value_item = QTableWidgetItem(value)
            value_item.setFont(QFont("Segoe UI", 8))
            table.setItem(row, 1, value_item)

            # Source / Confidence
            source_text = f"{mapping.source} ({mapping.confidence}%)"
            source_item = QTableWidgetItem(source_text)
            source_item.setFont(QFont("Courier New", 7))

            # Color code by confidence
            from PyQt6.QtGui import QColor
            if mapping.confidence >= 100:
                source_item.setForeground(QColor(C.GREEN))
            elif mapping.confidence >= 70:
                source_item.setForeground(QColor(C.PRI))
            else:
                source_item.setForeground(QColor(C.ACC))

            table.setItem(row, 2, source_item)

        # Set column widths
        header_view = table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        table.setFixedHeight(min(300, (len(self._field_mappings) + 1) * 35 + 10))

        layout.addWidget(table)

        return container

    def _build_cover_note_section(self) -> QWidget:
        """Build tailored cover note section."""
        container = QWidget()
        container.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Section header
        header = QLabel("Generated Tailored Cover Note:")
        header.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        header.setStyleSheet(f"color: {C.TEXT}; background: transparent;")
        layout.addWidget(header)

        # Cover note display
        note_display = QTextEdit()
        note_display.setReadOnly(True)
        note_display.setPlainText(self._cover_note)
        note_display.setFont(QFont("Segoe UI", 8))
        note_display.setFixedHeight(120)
        note_display.setStyleSheet(f"""
            QTextEdit {{
                background: {C.PANEL2};
                color: {C.TEXT};
                border: 1px solid {C.BORDER};
                border-radius: 6px;
                padding: 10px;
            }}
        """)
        layout.addWidget(note_display)

        return container

    def _build_safety_warning(self) -> QWidget:
        """Build safety warning notice."""
        warning = QFrame()
        warning.setStyleSheet(f"""
            QFrame {{
                background: {C.PANEL2};
                border: 2px solid {C.ACC};
                border-radius: 6px;
            }}
        """)

        layout = QVBoxLayout(warning)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        icon_label = QLabel("⚠️")
        icon_label.setFont(QFont("Segoe UI", 16))
        icon_label.setStyleSheet(f"color: {C.ACC}; background: transparent;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        title = QLabel("Safety Rule: Pre-Fill Only, Manual Submit Required")
        title.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {C.ACC}; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setWordWrap(True)
        layout.addWidget(title)

        detail = QLabel(
            "The agent will navigate to the form, fill in all fields with the values shown above, "
            "and STOP immediately before the final submit button. You must review the pre-filled "
            "form in the browser window and click Submit yourself to complete the application."
        )
        detail.setFont(QFont("Segoe UI", 8))
        detail.setStyleSheet(f"color: {C.TEXT}; background: transparent;")
        detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        detail.setWordWrap(True)
        layout.addWidget(detail)

        return warning

    def _build_action_buttons(self) -> QWidget:
        """Build action button bar."""
        container = QWidget()
        container.setStyleSheet(f"""
            background: {C.PANEL2};
            border-top: 1px solid {C.BORDER};
        """)
        container.setFixedHeight(70)

        layout = QHBoxLayout(container)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(12)

        layout.addStretch()

        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedSize(100, 40)
        cancel_btn.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C.PANEL};
                color: {C.TEXT};
                border: 1px solid {C.BORDER};
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background: {C.DARK};
                border: 1px solid {C.BORDER_B};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)

        # Proceed button
        proceed_btn = QPushButton("Proceed to Pre-Fill")
        proceed_btn.setFixedSize(160, 40)
        proceed_btn.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        proceed_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        proceed_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C.PRI};
                color: {C.DARK};
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background: {C.PRI_DIM};
                color: {C.WHITE};
            }}
        """)
        proceed_btn.clicked.connect(self._on_proceed)
        layout.addWidget(proceed_btn)

        return container

    def _on_proceed(self):
        """Handle proceed button click."""
        # Build field data dictionary
        field_data = {
            mapping.field_name: mapping.proposed_value
            for mapping in self._field_mappings
        }

        # Add cover note if present
        if self._cover_note:
            field_data["__cover_note__"] = self._cover_note

        log.info(f"[ApplyReview] User confirmed pre-fill for: {self._opportunity_title}")

        # Emit signal
        self.proceed_to_prefill.emit(self._target_url, field_data)

        # Close dialog
        self.accept()
