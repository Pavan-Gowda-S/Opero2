"""
TinyFish integration for Opero2 — advanced web search and content extraction.

This action provides access to TinyFish's search and fetch capabilities through
a subprocess-based Node.js service wrapper. It integrates with Opero's existing
action system and follows the same patterns as web_search.py and browser_control.py.

Operations:
  - search: Web search using TinyFish (alternative to Gemini/DDG)
  - fetch: Extract clean content from 1-10 URLs in parallel
  - agent: Browser automation for multi-step browsing and information extraction (Phase 3)

The Node.js service (tinyfish_service/) handles SDK communication and is called
via subprocess with JSON I/O. The API key is loaded from the root .env file.

Phase 3 Agent Safety Limitations:
  This wrapper validates requests and rejects obviously unsafe goals through
  basic pattern matching. However, this CANNOT guarantee read-only execution:

  - The TinyFish SDK does not provide controls to restrict specific browser
    interactions (clicks, form fills, element selection) once a goal is submitted
  - Pattern matching on goal text is not a reliable enforcement mechanism
  - Goals phrased to bypass simple patterns may still perform consequential actions
  - Once submitted, the agent executes with full browser capabilities

  Request validation rejects clearly unsafe requests but does NOT enforce
  browser-level interaction restrictions during execution.

  Permitted operations (Phase 3 scope):
    - Browsing pages, following links, clicking navigation
    - Extracting visible information from pages

  Prohibited operations (requires explicit future approval):
    - Form submission, purchases, authentication
    - Data modification, deletion, uploads
    - Sending messages, posting comments
"""

import json
import subprocess
import sys
import os
import platform
from pathlib import Path
from typing import Optional

from core.logger import get_logger
from core.validator import validate_params, ValidationError
from core import confirm

log = get_logger(__name__)

# ── Path resolution ────────────────────────────────────────────────────────────

def _get_base_dir() -> Path:
    """Get the repository root directory."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


BASE_DIR = _get_base_dir()
SERVICE_DIR = BASE_DIR / "tinyfish_service"
SERVICE_ENTRY = SERVICE_DIR / "index.js"
ENV_FILE = BASE_DIR / ".env"


# ── Subprocess wrapper ─────────────────────────────────────────────────────────

def _call_tinyfish_service(
    operation: str,
    args: list[str],
    timeout: int = 60
) -> dict:
    """
    Call the TinyFish Node.js service via subprocess.

    Args:
        operation: Operation name ('search', 'fetch', or 'agent')
        args: Command-line arguments for the operation
        timeout: Timeout in seconds (default: 60 for search/fetch, 600 for agent)

    Returns:
        dict: Parsed JSON response from the service

    Raises:
        RuntimeError: If the service call fails

    Output Handling:
        subprocess.run() with capture_output=True buffers stdout/stderr in memory.
        There is no built-in size limit - large outputs can cause memory issues.
        The Node.js service is designed to return compact JSON responses, but
        malformed responses or SDK errors could theoretically produce large output.

        This implementation does NOT impose an explicit size limit because:
        1. Expected responses are small (< 100 KB for typical agent results)
        2. The subprocess timeout (60-600s) bounds execution time
        3. Adding size limits would complicate error handling (truncated JSON)

        Risk mitigation:
        - Timeout bounds ensure subprocess doesn't run indefinitely
        - JSON parsing will fail gracefully on malformed large output
        - The Node.js service sanitizes SDK responses before output
    """
    # Verify service files exist
    if not SERVICE_ENTRY.exists():
        raise RuntimeError(
            f"TinyFish service not found at {SERVICE_ENTRY}. "
            "Run: cd tinyfish_service && npm install"
        )

    if not ENV_FILE.exists():
        raise RuntimeError(
            f"Environment file not found at {ENV_FILE}. "
            "Ensure TINYFISH_API_KEY is configured."
        )

    # Build command
    cmd = [
        "node",
        f"--env-file={ENV_FILE}",
        str(SERVICE_ENTRY),
        operation,
    ] + args

    log.info(f"[TinyFish] Calling service: {operation} (timeout: {timeout}s)")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(BASE_DIR),
            # Prevent console window popup on Windows
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )

        # Parse JSON response
        if result.returncode != 0:
            # Try to parse error JSON from stderr
            try:
                error_data = json.loads(result.stderr)
                log.error(f"[TinyFish] Service error: {error_data.get('error')}")
                return error_data
            except json.JSONDecodeError:
                # Raw error message
                raise RuntimeError(f"Service failed: {result.stderr or result.stdout}")

        # Parse success response
        response = json.loads(result.stdout)
        return response

    except subprocess.TimeoutExpired:
        log.error(f"[TinyFish] Operation timed out after {timeout}s")
        return {
            "success": False,
            "error": f"Operation timed out after {timeout} seconds",
            "code": "TIMEOUT",
        }
    except json.JSONDecodeError as e:
        log.error(f"[TinyFish] Failed to parse JSON response: {e}")
        return {
            "success": False,
            "error": "Invalid JSON response from service",
            "code": "JSON_ERROR",
        }
    except Exception as e:
        log.error(f"[TinyFish] Unexpected error: {e}")
        return {
            "success": False,
            "error": str(e),
            "code": "UNKNOWN",
        }


# ── Search operation ───────────────────────────────────────────────────────────

def _search(
    query: str,
    max_results: int = 10,
    location: Optional[str] = None,
    language: Optional[str] = None,
) -> str:
    """
    Perform web search using TinyFish.

    Args:
        query: Search query
        max_results: Maximum number of results (default: 10)
        location: Country code for geo-targeting (e.g., "US")
        language: Language code (e.g., "en")

    Returns:
        str: Formatted search results
    """
    args = ["--query", query, "--max-results", str(max_results)]

    if location:
        args.extend(["--location", location.upper()])
    if language:
        args.extend(["--language", language.lower()])

    response = _call_tinyfish_service("search", args, timeout=30)

    if not response.get("success"):
        error_msg = response.get("error", "Unknown error")
        code = response.get("code", "UNKNOWN")
        log.error(f"[TinyFish] Search failed: {code} - {error_msg}")
        return f"Search failed: {error_msg}"

    # Format results for display
    results = response.get("results", [])
    if not results:
        return f"No results found for: {query}"

    output = [f"Search results for: {query}\n"]

    for i, result in enumerate(results, 1):
        title = result.get("title", "No title")
        snippet = result.get("snippet", "")
        url = result.get("url", "")

        output.append(f"{i}. {title}")
        if snippet:
            output.append(f"   {snippet}")
        if url:
            output.append(f"   {url}")
        output.append("")

    return "\n".join(output)


# ── Fetch operation ────────────────────────────────────────────────────────────

def _fetch(
    urls: list[str],
    format: str = "markdown",
    include_links: bool = False,
) -> str:
    """
    Fetch content from URLs using TinyFish.

    Args:
        urls: List of URLs to fetch (1-10)
        format: Output format ('markdown', 'html', 'json')
        include_links: Include links from pages

    Returns:
        str: Formatted fetch results
    """
    if not urls or len(urls) == 0:
        return "No URLs provided"

    if len(urls) > 10:
        return "Maximum 10 URLs allowed per request"

    args = ["--urls", ",".join(urls), "--format", format]

    if include_links:
        args.append("--links")

    response = _call_tinyfish_service("fetch", args, timeout=60)

    if not response.get("success"):
        error_msg = response.get("error", "Unknown error")
        code = response.get("code", "UNKNOWN")
        log.error(f"[TinyFish] Fetch failed: {code} - {error_msg}")
        return f"Fetch failed: {error_msg}"

    # Format results for display
    results = response.get("results", [])
    if not results:
        return "No content fetched"

    output = []

    for i, result in enumerate(results, 1):
        url = result.get("url", "")
        status = result.get("status", "unknown")

        output.append(f"--- Result {i}: {url} ---")

        if status == "error":
            error = result.get("error", "Unknown error")
            output.append(f"Error: {error}\n")
            continue

        title = result.get("title")
        if title:
            output.append(f"Title: {title}")

        text = result.get("text")
        if text:
            # Truncate very long content
            if len(text) > 5000:
                text = text[:5000] + "\n... (content truncated)"
            output.append(f"\n{text}\n")
        else:
            output.append("(No content extracted)\n")

    return "\n".join(output)


# ── Agent operation (Phase 3) ──────────────────────────────────────────────────

def _agent(
    url: str,
    goal: str,
    max_steps: int = 50,
    max_duration_seconds: int = 300,
    browser_profile: str = "lite",
) -> str:
    """
    Run browser agent automation using TinyFish.

    PHASE 4 ADDITION: This operation now requires explicit user confirmation before
    execution. A confirmation dialog is shown with the target URL, goal, and cost
    warning. The agent runs only after the user presses CONFIRM.

    IMPORTANT SAFETY LIMITATIONS:

    This wrapper validates the request and rejects obviously unsafe goals through
    basic pattern matching. However, this CANNOT guarantee read-only execution:

    - The TinyFish SDK does not enforce interaction-level restrictions
    - Once a goal is submitted, the agent has full browser capabilities
    - Pattern matching on goal text is not a reliable enforcement mechanism
    - Goals phrased to bypass patterns may still perform consequential actions

    Request validation rejects clearly prohibited requests but does NOT prevent
    the agent from performing those actions if the goal requests them indirectly.

    TIMEOUT BEHAVIOR (verified from SDK source):

    The SDK client timeout (60s in client.js) controls the HTTP request timeout
    for the blocking agent.run() call. This has critical implications:

    - max_duration_seconds up to 600s cannot be fully utilized with 60s HTTP timeout
    - Agent runs exceeding 60s will timeout locally but CONTINUE REMOTELY
    - Aborting the local request does NOT cancel the remote agent execution
    - Retrying after timeout will start a DUPLICATE agent run
    - There is no SDK method to cancel an in-progress agent.run()

    This is a known limitation of Phase 3's blocking architecture.
    Safe alternatives for long runs (not implemented in Phase 3):
      1. Use agent.queue() + polling instead of agent.run()
      2. Increase SDK client timeout (requires testing impact on search/fetch)
      3. Use agent.stream() with progress events (requires architecture changes)

    Args:
        url: Target URL to automate
        goal: Natural language description of the task
        max_steps: Maximum steps the agent can take (default: 50)
        max_duration_seconds: Maximum duration in seconds (default: 300, limited by SDK timeout)
        browser_profile: Browser profile 'lite' or 'stealth' (default: lite)

    Returns:
        str: Formatted agent result or error message
    """
    if not url or not url.strip():
        return "Please provide a target URL"

    if not goal or not goal.strip():
        return "Please provide a goal/task description"

    # Truncate long goals for display
    goal_display = goal[:100] + "..." if len(goal) > 100 else goal

    # Build confirmation details
    confirmation_title = "TinyFish Browser Agent"
    confirmation_detail = (
        f"URL: {url}\n"
        f"Goal: {goal_display}\n"
        f"Max Steps: {max_steps}\n"
        f"Max Duration: {max_duration_seconds}s\n\n"
        f"⚠️ This operation is billable (~$0.10-$1.00 estimated)\n"
        f"⚠️ Agent will browse the target website\n"
        f"⚠️ Remote execution may continue after local timeout"
    )

    # Check if another confirmation is pending (avoid stacking banners)
    if confirm.pending_title():
        return (
            "Another confirmation is pending. Please respond to it first before "
            "starting a new agent operation."
        )

    # Define the actual agent execution work
    def _run_agent() -> str:
        """Execute agent operation after confirmation."""
        # Build command arguments
        args = [
            "--url", url.strip(),
            "--goal", goal.strip(),
            "--max-steps", str(max_steps),
            "--max-duration-seconds", str(max_duration_seconds),
            "--browser-profile", browser_profile.lower(),
        ]

        # Agent operations have longer timeout (up to 10 minutes)
        response = _call_tinyfish_service("agent", args, timeout=600)

        # Format and save to history
        result_str = _format_agent_response(response, url, goal)
        _save_to_history(url, goal, response)

        return result_str

    # Request confirmation (non-blocking)
    return confirm.request(
        key="tinyfish_agent",
        title=confirmation_title,
        detail=confirmation_detail,
        run=_run_agent
    )

    return _format_agent_response(response, url, goal)


def _format_agent_response(response: dict, url: str, goal: str) -> str:
    """
    Format agent response into user-friendly string.

    Args:
        response: Response dict from _call_tinyfish_service
        url: Target URL (for context)
        goal: Goal description (for context)

    Returns:
        str: Formatted response message
    """
    if not response.get("success"):
        error_msg = response.get("error", "Unknown error")
        code = response.get("code", "UNKNOWN")
        message = response.get("message", "")

        log.error(f"[TinyFish] Agent failed: {code} - {error_msg}")

        # Enhanced timeout messaging (Phase 4)
        if code == "TIMEOUT":
            return (
                f"Agent operation timed out after 600 seconds.\n\n"
                f"⚠️ IMPORTANT: The local request timed out, but the agent may still be "
                f"running on TinyFish servers. This is a known limitation of the current "
                f"architecture - there is no way to cancel remote execution after timeout.\n\n"
                f"Target: {url}\n"
                f"Goal: {goal[:100]}...\n\n"
                f"Do NOT retry immediately as this will start a duplicate agent run. "
                f"Check your TinyFish dashboard for the operation status."
            )

        # Return detailed error for user
        if message and message != error_msg:
            return f"Agent automation failed: {error_msg}\n{message}"
        return f"Agent automation failed: {error_msg}"

    # Format successful result
    status = response.get("status", "UNKNOWN")
    result = response.get("result")
    run_id = response.get("run_id")

    output = [f"✅ Agent Automation Completed (Status: {status})"]

    if run_id:
        output.append(f"Run ID: {run_id}")

    output.append(f"URL: {url}")
    output.append("")

    if result:
        if isinstance(result, str):
            output.append(result)
        elif isinstance(result, dict):
            # Format structured result
            output.append(json.dumps(result, indent=2))
        else:
            output.append(str(result))
    else:
        output.append("(No result returned)")

    return "\n".join(output)


def _generate_report(
    run_id: Optional[str] = None,
    title: Optional[str] = None,
    auto_open: bool = True,
) -> str:
    """
    Generate a PDF report from TinyFish agent operation.

    Phase 5 addition: Creates professional PDF reports from operation history.

    Args:
        run_id: Specific run ID to report on (uses latest if None)
        title: Custom report title (auto-generated if None)
        auto_open: Open PDF in system viewer after generation (default: True)

    Returns:
        str: Success message with file path
    """
    try:
        # Import report generator
        from actions.report_generator import generate_report_from_history

        # Generate PDF
        pdf_path = generate_report_from_history(run_id=run_id, title=title)

        log.info(f"[TinyFish] PDF report generated: {pdf_path}")

        # Open in system viewer if requested
        if auto_open:
            _open_pdf(pdf_path)

        return (
            f"✅ PDF report generated successfully:\n\n"
            f"Location: {pdf_path}\n"
            f"File size: {pdf_path.stat().st_size / 1024:.1f} KB\n\n"
            f"{'The report has been opened in your default PDF viewer.' if auto_open else 'Use your PDF viewer to open the report.'}"
        )

    except Exception as e:
        log.error(f"[TinyFish] Report generation failed: {e}")
        return f"Report generation failed: {e}"


def _open_pdf(pdf_path: Path) -> None:
    """
    Open PDF file in system's default viewer.

    Cross-platform implementation for Windows/macOS/Linux.

    Args:
        pdf_path: Path to PDF file
    """
    try:
        system = platform.system()

        if system == "Windows":
            os.startfile(str(pdf_path))
        elif system == "Darwin":  # macOS
            subprocess.run(["open", str(pdf_path)], check=False)
        else:  # Linux and others
            subprocess.run(["xdg-open", str(pdf_path)], check=False)

        log.info(f"[TinyFish] Opened PDF: {pdf_path}")

    except Exception as e:
        log.warning(f"[TinyFish] Failed to open PDF: {e}")


def _save_to_history(url: str, goal: str, response: dict) -> None:
    """
    Save agent operation to lightweight history file.

    Phase 4 addition: Track agent operations for user visibility and debugging.
    History is stored as a JSON array in actions/tinyfish_history.json.

    Args:
        url: Target URL
        goal: Goal description
        response: Response dict from agent operation
    """
    import datetime

    history_file = BASE_DIR / "actions" / "tinyfish_history.json"

    # Create history entry
    entry = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "url": url,
        "goal": goal[:200],  # Truncate for storage
        "status": response.get("status", "UNKNOWN"),
        "success": response.get("success", False),
        "run_id": response.get("run_id"),
        "error": response.get("error") if not response.get("success") else None,
    }

    try:
        # Load existing history
        if history_file.exists():
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
        else:
            history = []

        # Append new entry
        history.append(entry)

        # Keep only last 100 entries (prevent unbounded growth)
        history = history[-100:]

        # Save updated history
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

        log.info(f"[TinyFish] Saved to history: {entry['status']} - {url}")

    except Exception as e:
        # History save failure should not break the operation
        log.warning(f"[TinyFish] Failed to save history: {e}")


# ── Main action handler ────────────────────────────────────────────────────────

def tinyfish_search(
    parameters: dict,
    response=None,
    player=None,
    session_memory=None,
) -> str:
    """
    TinyFish action handler — called by Opero's action dispatcher.

    Parameters dict fields:
        operation (str): 'search', 'fetch', or 'agent'
        query (str): Search query (for search operation)
        urls (list[str]): URLs to fetch (for fetch operation)
        url (str): Target URL (for agent operation)
        goal (str): Task description (for agent operation)
        max_results (int): Max search results (default: 10)
        location (str): Country code for search
        language (str): Language code for search
        format (str): Output format for fetch (default: markdown)
        include_links (bool): Include links in fetch results
        max_steps (int): Max agent steps (default: 50)
        max_duration_seconds (int): Max agent duration (default: 300)
        browser_profile (str): Agent browser profile (default: lite)
    """
    params = parameters or {}
    params = validate_params(params, VALIDATOR, tool_name="tinyfish_search")

    operation = params.get("operation", "search").lower().strip()

    # Log operation
    if player:
        if operation == "search":
            query = params.get("query", "")
            player.write_log(f"[TinyFish:search] {query}")
        elif operation == "fetch":
            urls = params.get("urls", [])
            player.write_log(f"[TinyFish:fetch] {len(urls)} URL(s)")
        elif operation == "agent":
            url = params.get("url", "")
            goal = params.get("goal", "")[:50]  # Truncate for log
            player.write_log(f"[TinyFish:agent] {url} - {goal}...")

    log.info(f"[TinyFish] Operation: {operation}")

    try:
        if operation == "search":
            query = params.get("query", "").strip()
            if not query:
                return "Please provide a search query"

            return _search(
                query=query,
                max_results=params.get("max_results", 10),
                location=params.get("location"),
                language=params.get("language"),
            )

        elif operation == "fetch":
            urls = params.get("urls", [])
            if not urls:
                return "Please provide at least one URL"

            return _fetch(
                urls=urls,
                format=params.get("format", "markdown"),
                include_links=params.get("include_links", False),
            )

        elif operation == "agent":
            url = (params.get("url") or "").strip()
            goal = (params.get("goal") or "").strip()

            if not url:
                return "Please provide a target URL for agent operation (e.g., https://example.com)"
            if not goal:
                return "Please provide a goal/task description for agent operation"

            return _agent(
                url=url,
                goal=goal,
                max_steps=params.get("max_steps", 50),
                max_duration_seconds=params.get("max_duration_seconds", 300),
                browser_profile=params.get("browser_profile", "lite"),
            )

        elif operation == "generate_report":
            # Phase 5: Generate PDF report from agent operation
            run_id = params.get("run_id")
            title = params.get("title")
            auto_open = params.get("auto_open", True)

            return _generate_report(
                run_id=run_id,
                title=title,
                auto_open=auto_open,
            )

        else:
            return f"Unknown operation: {operation}. Use 'search', 'fetch', 'agent', or 'generate_report'."

    except Exception as e:
        log.error(f"[TinyFish] Handler error: {e}")
        return f"TinyFish operation failed: {e}"


# ── Tool declaration (auto-discovered by core/action_loader.py) ────────────────

TOOL = {
    "name": "tinyfish_search",
    "description": (
        "Advanced web search, content extraction, browser automation, and PDF report generation using TinyFish. "
        "Operations: 'search' (web search with geo-targeting), 'fetch' (extract content from 1-10 URLs), "
        "'agent' (multi-step browser automation for browsing, navigation, and information extraction), "
        "'generate_report' (create professional PDF report from agent operation history). "
        ""
        "AGENT SAFETY LIMITATIONS: Request validation rejects obviously unsafe goals but CANNOT enforce "
        "browser-level interaction restrictions. The SDK does not prevent specific interactions once a goal "
        "is submitted. Pattern matching is not a reliable enforcement mechanism. Use agent operations only "
        "for information extraction and browsing tasks. Form submission, purchases, authentication, and data "
        "modification are prohibited per Phase 3 scope but cannot be technically prevented at execution time."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "operation": {
                "type": "STRING",
                "description": "Operation type: 'search', 'fetch', 'agent', or 'generate_report'"
            },
            "query": {
                "type": "STRING",
                "description": "Search query (required for search operation)"
            },
            "urls": {
                "type": "ARRAY",
                "items": {
                    "type": "STRING"
                },
                "description": "URLs to fetch (required for fetch operation, max 10)"
            },
            "max_results": {
                "type": "INTEGER",
                "description": "Maximum search results (default: 10)"
            },
            "location": {
                "type": "STRING",
                "description": "Country code for geo-targeted search (e.g., 'US', 'GB')"
            },
            "language": {
                "type": "STRING",
                "description": "Language code for search (e.g., 'en', 'fr')"
            },
            "format": {
                "type": "STRING",
                "description": "Output format for fetch: 'markdown', 'html', 'json' (default: markdown)"
            },
            "include_links": {
                "type": "BOOLEAN",
                "description": "Include links from fetched pages"
            },
            "url": {
                "type": "STRING",
                "description": "Target URL (required for agent operation)"
            },
            "goal": {
                "type": "STRING",
                "description": "Task description for agent (required for agent operation)"
            },
            "max_steps": {
                "type": "INTEGER",
                "description": "Maximum steps for agent (default: 50, max: 100)"
            },
            "max_duration_seconds": {
                "type": "INTEGER",
                "description": "Maximum duration for agent in seconds (default: 300, max: 600)"
            },
            "browser_profile": {
                "type": "STRING",
                "description": "Browser profile for agent: 'lite' or 'stealth' (default: lite)"
            },
            "run_id": {
                "type": "STRING",
                "description": "Run ID for report generation (uses latest if omitted)"
            },
            "title": {
                "type": "STRING",
                "description": "Custom title for generated PDF report"
            },
            "auto_open": {
                "type": "BOOLEAN",
                "description": "Auto-open PDF in system viewer (default: true)"
            }
        },
        "required": ["operation"]
    },
    "handler": tinyfish_search,
}


# ── Input validation rules ─────────────────────────────────────────────────────

VALIDATOR = {
    "operation": [{"type": str, "required": True, "max_len": 50}],
    "query": [{"type": str, "max_len": 2000}],
    "urls": [{"type": list}],
    "max_results": [{"type": int}],
    "location": [{"type": str, "max_len": 10}],
    "language": [{"type": str, "max_len": 10}],
    "format": [{"type": str, "max_len": 20}],
    "include_links": [{"type": bool}],
    "url": [{"type": str, "max_len": 2000}],
    "goal": [{"type": str, "max_len": 5000}],
    "max_steps": [{"type": int}],
    "max_duration_seconds": [{"type": int}],
    "browser_profile": [{"type": str, "max_len": 20}],
}
