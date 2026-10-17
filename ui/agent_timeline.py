"""Live Agent Timeline Widget — displays TinyFish agent operation status."""
from __future__ import annotations

import time
from typing import Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget,
    QScrollArea, QSizePolicy, QTextEdit,
)

from core.logger import get_logger
from ui.theme import C

log = get_logger(__name__)


class AgentTimelineWidget(QFrame):
    """
    Live agent operation timeline display.

    Shows agent status progression: PENDING → RUNNING → COMPLETED/FAILED
    Displays elapsed time, run_id, and final result.

    Signals:
        status_updated(str, str) - Emitted when status changes (run_id, status)
    """

    status_updated = pyqtSignal(str, str)  # (run_id, status)
    stop_requested = pyqtSignal()  # Emitted when stop button clicked

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AgentTimeline")
        self.setStyleSheet(f"""
            QFrame#AgentTimeline {{
                background: {C.PANEL2};
                border: 1px solid {C.BORDER};
                border-radius: 6px;
            }}
        """)

        # State tracking
        self._run_id: Optional[str] = None
        self._status: str = "IDLE"
        self._start_time: Optional[float] = None
        self._elapsed_timer: Optional[QTimer] = None

        # Build UI
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # Header with status badge
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        self._status_badge = QLabel("●")
        self._status_badge.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
        self._status_badge.setStyleSheet(f"color: {C.TEXT_DIM}; background: transparent;")
        header_layout.addWidget(self._status_badge)

        self._status_label = QLabel("Agent Ready")
        self._status_label.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        self._status_label.setStyleSheet(f"color: {C.TEXT}; background: transparent;")
        header_layout.addWidget(self._status_label)

        header_layout.addStretch()

        self._elapsed_label = QLabel("")
        self._elapsed_label.setFont(QFont("Courier New", 8))
        self._elapsed_label.setStyleSheet(f"color: {C.TEXT_DIM}; background: transparent;")
        header_layout.addWidget(self._elapsed_label)

        # Stop button (hidden by default, shown when PENDING/RUNNING)
        self._stop_btn = QPushButton("⏹ STOP RUN")
        self._stop_btn.setFont(QFont("Courier New", 7, QFont.Weight.Bold))
        self._stop_btn.setFixedHeight(20)
        self._stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._stop_btn.setStyleSheet(f"""
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
            QPushButton:disabled {{
                background: transparent;
                color: {C.TEXT_DIM};
                border: 1px solid {C.TEXT_DIM};
            }}
        """)
        self._stop_btn.clicked.connect(self._on_stop_clicked)
        self._stop_btn.hide()
        header_layout.addWidget(self._stop_btn)

        layout.addLayout(header_layout)

        # Timeline content area for history and warning messages
        self._timeline_content = QWidget()
        self._timeline_content.setStyleSheet("background: transparent;")
        self._timeline_layout = QVBoxLayout(self._timeline_content)
        self._timeline_layout.setContentsMargins(0, 0, 0, 0)
        self._timeline_layout.setSpacing(4)
        layout.addWidget(self._timeline_content)

        # Run ID display (hidden when idle)
        self._run_id_container = QWidget()
        self._run_id_container.setStyleSheet("background: transparent;")
        run_id_layout = QHBoxLayout(self._run_id_container)
        run_id_layout.setContentsMargins(0, 0, 0, 0)
        run_id_layout.setSpacing(6)

        run_id_label_prefix = QLabel("Run ID:")
        run_id_label_prefix.setFont(QFont("Courier New", 7))
        run_id_label_prefix.setStyleSheet(f"color: {C.TEXT_DIM}; background: transparent;")
        run_id_layout.addWidget(run_id_label_prefix)

        self._run_id_label = QLabel("")
        self._run_id_label.setFont(QFont("Courier New", 7, QFont.Weight.Bold))
        self._run_id_label.setStyleSheet(f"color: {C.PRI}; background: transparent;")
        self._run_id_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        run_id_layout.addWidget(self._run_id_label)

        run_id_layout.addStretch()

        self._run_id_container.hide()
        layout.addWidget(self._run_id_container)

        # Result display (hidden until complete)
        self._result_container = QScrollArea()
        self._result_container.setWidgetResizable(True)
        self._result_container.setFixedHeight(150)
        self._result_container.setStyleSheet(f"""
            QScrollArea {{
                background: {C.PANEL};
                border: 1px solid {C.BORDER};
                border-radius: 4px;
            }}
        """)

        self._result_text = QTextEdit()
        self._result_text.setReadOnly(True)
        self._result_text.setFont(QFont("Segoe UI", 8))
        self._result_text.setStyleSheet(f"""
            QTextEdit {{
                background: {C.PANEL};
                color: {C.TEXT};
                border: none;
                padding: 6px;
            }}
        """)
        self._result_container.setWidget(self._result_text)
        self._result_container.hide()
        layout.addWidget(self._result_container)

        # Initialize timer
        self._elapsed_timer = QTimer()
        self._elapsed_timer.timeout.connect(self._update_elapsed_time)

    def start_operation(self, run_id: str, url: str, goal: str):
        """Start tracking a new agent operation."""
        self._run_id = run_id
        self._status = "PENDING"
        self._start_time = time.time()

        # Update UI
        self._status_badge.setText("◐")
        self._status_badge.setStyleSheet(f"color: {C.ACC2}; background: transparent;")
        self._status_label.setText("Agent Starting...")

        self._run_id_label.setText(run_id)
        self._run_id_container.show()

        self._result_container.hide()
        self._result_text.clear()

        # Show stop button
        self._stop_btn.setEnabled(True)
        self._stop_btn.show()

        # Start elapsed timer (update every second)
        self._elapsed_timer.start(1000)

        # Emit signal
        self.status_updated.emit(run_id, "PENDING")

        log.info(f"[AgentTimeline] Started tracking: {run_id}")

    def update_status(self, status: str):
        """Update agent operation status."""
        if not self._run_id:
            return

        self._status = status

        # Update status badge and label
        if status == "RUNNING":
            self._status_badge.setText("◉")
            self._status_badge.setStyleSheet(f"color: {C.PRI}; background: transparent;")
            self._status_label.setText("Agent Running...")
            self._stop_btn.show()
        elif status == "COMPLETED":
            self._status_badge.setText("●")
            self._status_badge.setStyleSheet(f"color: {C.GREEN}; background: transparent;")
            self._status_label.setText("✅ Completed")
            self._elapsed_timer.stop()
            self._stop_btn.hide()
        elif status == "FAILED":
            self._status_badge.setText("●")
            self._status_badge.setStyleSheet(f"color: {C.RED}; background: transparent;")
            self._status_label.setText("❌ Failed")
            self._elapsed_timer.stop()
            self._stop_btn.hide()
        elif status == "CANCELLED":
            self._status_badge.setText("●")
            self._status_badge.setStyleSheet(f"color: {C.TEXT_DIM}; background: transparent;")
            self._status_label.setText("⊗ Cancelled")
            self._elapsed_timer.stop()
            self._stop_btn.hide()

        # Emit signal
        self.status_updated.emit(self._run_id, status)

        log.info(f"[AgentTimeline] Status updated: {self._run_id} → {status}")

    def set_result(self, result_text: str, is_error: bool = False):
        """Display operation result."""
        self._result_text.setPlainText(result_text)

        # Style based on success/error
        if is_error:
            self._result_text.setStyleSheet(f"""
                QTextEdit {{
                    background: {C.PANEL};
                    color: {C.RED};
                    border: none;
                    padding: 6px;
                }}
            """)
        else:
            self._result_text.setStyleSheet(f"""
                QTextEdit {{
                    background: {C.PANEL};
                    color: {C.TEXT};
                    border: none;
                    padding: 6px;
                }}
            """)

        self._result_container.show()

    def reset(self):
        """Reset timeline to idle state."""
        self._run_id = None
        self._status = "IDLE"
        self._start_time = None

        if self._elapsed_timer:
            self._elapsed_timer.stop()

        # Reset UI
        self._status_badge.setText("●")
        self._status_badge.setStyleSheet(f"color: {C.TEXT_DIM}; background: transparent;")
        self._status_label.setText("Agent Ready")
        self._elapsed_label.setText("")

        self._run_id_container.hide()
        self._result_container.hide()
        self._stop_btn.hide()

        # Clear timeline content (warnings, history)
        self._clear_timeline_content()

        log.info("[AgentTimeline] Reset to idle state")

    def _update_elapsed_time(self):
        """Update elapsed time display."""
        if not self._start_time:
            return

        elapsed = int(time.time() - self._start_time)
        minutes = elapsed // 60
        seconds = elapsed % 60

        self._elapsed_label.setText(f"{minutes:02d}:{seconds:02d}")

    def get_status(self) -> str:
        """Get current operation status."""
        return self._status

    def get_run_id(self) -> Optional[str]:
        """Get current run ID."""
        return self._run_id

    def is_active(self) -> bool:
        """Check if timeline is tracking an active operation."""
        return self._status in ("PENDING", "RUNNING")

    def _on_stop_clicked(self):
        """Handle stop button click."""
        # Emit signal
        self.stop_requested.emit()

        # Disable button to prevent double-clicks
        self._stop_btn.setEnabled(False)

        # Add warning message to timeline content
        warning = QLabel("⚠️ Stop requested — remote agent may still be running")
        warning.setFont(QFont("Segoe UI", 8))
        warning.setStyleSheet(f"color: {C.ACC}; background: transparent;")
        warning.setWordWrap(True)
        self._timeline_layout.addWidget(warning)

        log.info("[AgentTimeline] Stop requested by user")

    def load_history_preview(self):
        """Load last 3 runs from history as dimmed preview entries."""
        from pathlib import Path
        import json
        from urllib.parse import urlparse

        history_file = Path(__file__).parent.parent / "actions" / "tinyfish_history.json"

        if not history_file.exists():
            log.debug("[AgentTimeline] No history file found, skipping preview")
            return

        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)

            if not history or len(history) == 0:
                log.debug("[AgentTimeline] History file empty, skipping preview")
                return

            # Take last 3 entries
            recent = history[-3:]

            # Add separator
            sep1 = QLabel("── Previous Runs ──")
            sep1.setFont(QFont("Courier New", 7))
            sep1.setStyleSheet(f"color: {C.BORDER}; background: transparent;")
            sep1.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._timeline_layout.addWidget(sep1)

            # Add history entries
            for entry in recent:
                timestamp = entry.get("timestamp", "")[:10]  # Date only
                status = entry.get("status", "UNKNOWN")
                url = entry.get("url", "")
                goal = entry.get("goal", "")

                # Extract domain from URL
                try:
                    domain = urlparse(url).netloc if url else "N/A"
                except:
                    domain = "N/A"

                # Truncate goal
                goal_short = goal[:60] + "..." if len(goal) > 60 else goal

                # Format entry
                entry_text = f"[{timestamp}]  {status}  →  {domain}  —  {goal_short}"

                entry_label = QLabel(entry_text)
                entry_label.setFont(QFont("Courier New", 7))
                entry_label.setStyleSheet(f"color: {C.TEXT_DIM}; background: transparent;")
                entry_label.setWordWrap(True)
                self._timeline_layout.addWidget(entry_label)

            # Add live separator
            sep2 = QLabel("── Live ──")
            sep2.setFont(QFont("Courier New", 7))
            sep2.setStyleSheet(f"color: {C.BORDER}; background: transparent;")
            sep2.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._timeline_layout.addWidget(sep2)

            log.info(f"[AgentTimeline] Loaded {len(recent)} history preview entries")

        except Exception as e:
            log.error(f"[AgentTimeline] Failed to load history preview: {e}")

    def _clear_timeline_content(self):
        """Clear all timeline content entries (history, warnings)."""
        while self._timeline_layout.count() > 0:
            item = self._timeline_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


class AgentTimelinePanel(QFrame):
    """
    Container panel for agent timeline with header.

    Used in MainWindow activity log area when TinyFish mode is ON.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AgentTimelinePanel")
        self.setStyleSheet(f"""
            QFrame#AgentTimelinePanel {{
                background: {C.PANEL};
                border: none;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header
        header = QWidget()
        header.setStyleSheet(f"background: {C.DARK}; border-bottom: 1px solid {C.BORDER};")
        header.setFixedHeight(28)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 4, 10, 4)

        title = QLabel("◈  AGENT TIMELINE")
        title.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {C.PRI}; background: transparent;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        layout.addWidget(header)

        # Timeline widget
        self.timeline = AgentTimelineWidget()
        layout.addWidget(self.timeline)

        layout.addStretch()
