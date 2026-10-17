"""TinyFish search worker threads — executes searches in background."""
from __future__ import annotations

import json
from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal

from core.logger import get_logger

log = get_logger(__name__)


class TinyFishSearchWorker(QThread):
    """
    Background worker for TinyFish search operations.

    Signals:
        result_ready(dict) - Emitted when a search result is ready
        error_occurred(str) - Emitted when an error occurs
        finished() - Emitted when work is complete
    """

    result_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, query: str, mode: str):
        super().__init__()
        self._query = query
        self._mode = mode  # "quick" or "deep"
        self._cancelled = False

    def cancel(self):
        """Request cancellation of the search."""
        self._cancelled = True

    def run(self):
        """Execute the search operation in background thread."""
        try:
            if self._mode == "quick":
                self._run_quick_search()
            else:
                self._run_deep_research()
        except Exception as e:
            log.error(f"[TinyFishWorker] Error: {e}")
            self.error_occurred.emit(str(e))
        finally:
            self.finished.emit()

    def _run_quick_search(self):
        """Execute quick search and emit results."""
        if self._cancelled:
            return

        try:
            from actions.tinyfish_action import tinyfish_search

            # Call TinyFish search operation
            result = tinyfish_search({
                "operation": "search",
                "query": self._query,
            })

            if self._cancelled:
                return

            # Parse result string (TinyFish returns formatted text)
            # Expected format: multiple result blocks with title, url, snippet
            if isinstance(result, str):
                self._parse_and_emit_quick_results(result)
            else:
                self.error_occurred.emit("Unexpected result format from TinyFish")

        except Exception as e:
            if not self._cancelled:
                self.error_occurred.emit(f"Search failed: {e}")

    def _parse_and_emit_quick_results(self, result_text: str):
        """Parse TinyFish search result text and emit individual cards."""
        # TinyFish search returns formatted text with results
        # Parse and emit each result as a separate card
        lines = result_text.split('\n')

        current_result = {}
        in_result = False

        for line in lines:
            if self._cancelled:
                return

            line = line.strip()

            # Detect result boundaries (heuristic parsing)
            if line.startswith('[') and ']' in line:
                # Result number: [1], [2], etc.
                if current_result:
                    self.result_ready.emit(current_result)
                current_result = {}
                in_result = True
                continue

            if in_result and line:
                # First non-empty line after number is likely the title
                if 'title' not in current_result:
                    current_result['title'] = line
                # URL detection (contains http)
                elif 'url' not in current_result and ('http://' in line or 'https://' in line):
                    current_result['url'] = line
                # Everything else is snippet
                elif 'snippet' not in current_result:
                    current_result['snippet'] = line
                else:
                    current_result['snippet'] += ' ' + line

        # Emit last result if exists
        if current_result and not self._cancelled:
            self.result_ready.emit(current_result)

    def _run_deep_research(self):
        """Execute deep research and emit synthesized content."""
        if self._cancelled:
            return

        try:
            from actions.tinyfish_action import tinyfish_search

            # Step 1: Search for sources
            search_result = tinyfish_search({
                "operation": "search",
                "query": self._query,
            })

            if self._cancelled:
                return

            # Step 2: Synthesize deep research content
            # For Phase 3, we create a formatted markdown summary
            content = self._synthesize_deep_research(search_result)

            if not self._cancelled:
                self.result_ready.emit({
                    'type': 'deep_research',
                    'content': content
                })

        except Exception as e:
            if not self._cancelled:
                self.error_occurred.emit(f"Research failed: {e}")

    def _synthesize_deep_research(self, search_result: str) -> str:
        """Synthesize deep research content with citations."""
        # Create formatted markdown with numbered citations
        lines = [
            f"# Deep Research: {self._query}",
            "",
            "## Summary",
            "",
            "Based on available sources, here are the key findings:",
            "",
        ]

        # Parse search results and create citations
        result_lines = search_result.split('\n')
        citation_num = 1
        sources = []

        for line in result_lines:
            if self._cancelled:
                break

            line = line.strip()
            if line:
                # Add content with citation markers
                if 'http://' in line or 'https://' in line:
                    sources.append(line)
                elif len(line) > 20:  # Substantial content line
                    lines.append(f"{line} [[{citation_num}]]")
                    citation_num += 1

        # Add sources section
        if sources:
            lines.extend([
                "",
                "## Sources",
                "",
            ])
            for i, source in enumerate(sources, 1):
                lines.append(f"[{i}] {source}")

        return '\n'.join(lines)
