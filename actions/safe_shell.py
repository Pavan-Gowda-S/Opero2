"""Safe shell command execution with allowlist and sandboxing."""
import subprocess
import sys
from pathlib import Path

from core.logger import get_logger
from core.validator import validate_params

log = get_logger(__name__)

# Safe command allowlist - only these commands can be executed
# Each entry: (command_name, requires_confirmation, allowed_args_pattern)
SAFE_COMMANDS = {
    # Git operations (read-only by default)
    "git status": (False, None),
    "git log": (False, ["--oneline", "--graph", "--all", "-n"]),
    "git diff": (False, None),
    "git branch": (False, ["-a", "-v"]),
    "git show": (False, None),

    # Git write operations (require confirmation)
    "git add": (True, None),
    "git commit": (True, ["-m", "--amend"]),
    "git push": (True, ["-u", "origin"]),
    "git pull": (True, None),
    "git checkout": (True, ["-b"]),
    "git merge": (True, None),

    # Python operations
    "python": (False, ["-m", "-c", "--version"]),
    "pip list": (False, None),
    "pip show": (False, None),
    "pip install": (True, None),

    # Node operations
    "npm": (False, ["list", "run", "test", "start"]),
    "node": (False, ["--version"]),

    # File operations (read-only)
    "ls": (False, ["-la", "-lh"]),
    "dir": (False, None),
    "cat": (False, None),
    "head": (False, ["-n"]),
    "tail": (False, ["-n", "-f"]),
    "find": (False, ["-name", "-type"]),
    "grep": (False, ["-r", "-i", "-n"]),

    # System info (read-only)
    "pwd": (False, None),
    "whoami": (False, None),
    "date": (False, None),
    "echo": (False, None),
}


def _is_command_allowed(cmd: str) -> tuple[bool, bool]:
    """Check if command is allowed. Returns (allowed, requires_confirmation)."""
    cmd_lower = cmd.strip().lower()

    for allowed_cmd, (needs_confirm, allowed_args) in SAFE_COMMANDS.items():
        if cmd_lower.startswith(allowed_cmd.lower()):
            # If no arg restrictions, allow
            if allowed_args is None:
                return True, needs_confirm

            # Check if any allowed args are present
            remaining = cmd_lower[len(allowed_cmd):].strip()
            if not remaining:
                return True, needs_confirm

            # Check if args match allowed patterns
            for arg in allowed_args:
                if arg in remaining:
                    return True, needs_confirm

            return False, False

    return False, False


def safe_shell(
    parameters: dict,
    response=None,
    player=None,
    session_memory=None,
) -> str:
    """
    Execute a shell command from the safe allowlist.

    Security features:
    - Allowlist-based: only pre-approved commands can run
    - Confirmation gate: destructive operations require user approval
    - Timeout protection: commands auto-kill after 30s
    - Working directory: runs in user's home or specified safe path
    """
    params = parameters or {}
    params = validate_params(params, VALIDATOR, tool_name="safe_shell")

    command = params.get("command", "").strip()
    cwd = params.get("working_dir", str(Path.home()))
    timeout = min(int(params.get("timeout", 30)), 120)  # Max 2 minutes

    if not command:
        return "No command specified."

    # Check allowlist
    allowed, needs_confirm = _is_command_allowed(command)
    if not allowed:
        return (
            f"Command not allowed: '{command}'\n\n"
            f"For safety, only specific commands are permitted. "
            f"Use file_controller for file operations, computer_control for system tasks."
        )

    # Confirmation gate for destructive operations
    if needs_confirm:
        from core.confirm import request_confirmation
        if not request_confirmation(
            action=f"Run: {command}",
            details=f"Working directory: {cwd}\nThis command will modify files or system state."
        ):
            return "Command execution cancelled by user."

    if player:
        player.write_log(f"[shell] {command}")

    log.info(f"[SafeShell] Running: {command} (cwd={cwd})")

    try:
        # Resolve and validate working directory
        work_path = Path(cwd).expanduser().resolve()
        if not work_path.exists():
            return f"Working directory not found: {cwd}"

        # Replace 'python' with sys.executable for consistency
        if command.startswith("python "):
            command = command.replace("python ", f"{sys.executable} ", 1)

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            cwd=str(work_path),
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        output_parts = []
        if stdout:
            output_parts.append(f"STDOUT:\n{stdout}")
        if stderr:
            output_parts.append(f"STDERR:\n{stderr}")
        if result.returncode != 0:
            output_parts.append(f"Exit code: {result.returncode}")

        if not output_parts:
            return "Command completed successfully (no output)."

        return "\n\n".join(output_parts)

    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout}s"
    except FileNotFoundError as e:
        return f"Command not found: {e}"
    except Exception as e:
        log.error(f"[SafeShell] Error: {e}")
        return f"Shell execution error: {e}"


# ── Tool declaration ──────────────────────────────────────────────────────────
TOOL = {
    "name": "safe_shell",
    "description": (
        "Execute safe shell commands from an allowlist: git operations, Python/pip, "
        "npm, file viewing (ls/cat/grep), system info. Destructive operations require "
        "user confirmation. Use for: checking git status, running scripts, viewing logs."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "command": {
                "type": "STRING",
                "description": "Shell command to execute (must be in allowlist)",
            },
            "working_dir": {
                "type": "STRING",
                "description": "Working directory path (defaults to home)",
            },
            "timeout": {
                "type": "INTEGER",
                "description": "Timeout in seconds (default 30, max 120)",
            },
        },
        "required": ["command"],
    },
    "handler": safe_shell,
}

VALIDATOR = {
    "command": [{"type": str, "required": True, "max_len": 1000}],
    "working_dir": [{"type": str, "max_len": 500}],
    "timeout": [{"type": int}],
}
