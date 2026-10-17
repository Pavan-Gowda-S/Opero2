"""Persistent task scheduler for recurring user-authorized actions."""
import json
import time
from datetime import datetime
from pathlib import Path
from threading import Lock
import sys

from core.logger import get_logger
log = get_logger(__name__)


def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


SCHEDULER_PATH = _base_dir() / "memory" / "scheduled_tasks.json"
_lock = Lock()


def _load_tasks() -> dict:
    """Load scheduled tasks from JSON."""
    if not SCHEDULER_PATH.exists():
        return {"tasks": []}
    with _lock:
        try:
            data = json.loads(SCHEDULER_PATH.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) and "tasks" in data else {"tasks": []}
        except Exception as e:
            log.warning(f"[Scheduler] Load error: {e}")
            return {"tasks": []}


def _save_tasks(data: dict) -> None:
    """Save scheduled tasks to JSON."""
    SCHEDULER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        SCHEDULER_PATH.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )


def schedule_task(
    task_id: str,
    description: str,
    action: str,
    interval_minutes: int,
    enabled: bool = True,
) -> str:
    """Schedule a recurring task. Requires user authorization before execution."""
    if interval_minutes < 1:
        return "Interval must be at least 1 minute."
    if interval_minutes > 10080:  # 1 week
        return "Interval cannot exceed 1 week (10080 minutes)."

    data = _load_tasks()
    tasks = data.get("tasks", [])

    # Check if task_id already exists
    existing = next((t for t in tasks if t["id"] == task_id), None)
    if existing:
        return f"Task '{task_id}' already exists. Use enable/disable to control it."

    task = {
        "id": task_id,
        "description": description,
        "action": action,
        "interval_minutes": interval_minutes,
        "enabled": enabled,
        "created": datetime.now().isoformat(),
        "last_run": None,
        "next_run": None,
    }

    tasks.append(task)
    data["tasks"] = tasks
    _save_tasks(data)

    log.info(f"[Scheduler] Created task: {task_id} (every {interval_minutes}m)")
    return (
        f"Task '{task_id}' scheduled: {description}\n"
        f"Runs every {interval_minutes} minutes.\n"
        f"Status: {'enabled' if enabled else 'disabled'}"
    )


def list_tasks() -> str:
    """List all scheduled tasks."""
    data = _load_tasks()
    tasks = data.get("tasks", [])

    if not tasks:
        return "No scheduled tasks."

    lines = ["Scheduled tasks:"]
    for task in tasks:
        status = "✓ enabled" if task.get("enabled") else "✗ disabled"
        interval = task.get("interval_minutes", 0)
        last = task.get("last_run")
        last_str = f", last: {last[:16]}" if last else ""
        lines.append(
            f"  • {task['id']}: {task['description']} "
            f"(every {interval}m, {status}{last_str})"
        )

    return "\n".join(lines)


def enable_task(task_id: str) -> str:
    """Enable a scheduled task."""
    data = _load_tasks()
    tasks = data.get("tasks", [])

    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        return f"Task '{task_id}' not found."

    task["enabled"] = True
    _save_tasks(data)
    log.info(f"[Scheduler] Enabled: {task_id}")
    return f"Task '{task_id}' enabled."


def disable_task(task_id: str) -> str:
    """Disable a scheduled task."""
    data = _load_tasks()
    tasks = data.get("tasks", [])

    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        return f"Task '{task_id}' not found."

    task["enabled"] = False
    _save_tasks(data)
    log.info(f"[Scheduler] Disabled: {task_id}")
    return f"Task '{task_id}' disabled."


def delete_task(task_id: str) -> str:
    """Delete a scheduled task."""
    data = _load_tasks()
    tasks = data.get("tasks", [])

    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        return f"Task '{task_id}' not found."

    tasks = [t for t in tasks if t["id"] != task_id]
    data["tasks"] = tasks
    _save_tasks(data)
    log.info(f"[Scheduler] Deleted: {task_id}")
    return f"Task '{task_id}' deleted."


def check_due_tasks() -> list[dict]:
    """Return list of enabled tasks that are due to run. Background loop calls this."""
    data = _load_tasks()
    tasks = data.get("tasks", [])
    now = time.time()
    due = []

    for task in tasks:
        if not task.get("enabled"):
            continue

        last_run = task.get("last_run")
        interval_sec = task.get("interval_minutes", 0) * 60

        # First run or interval elapsed
        if last_run is None:
            due.append(task)
        else:
            try:
                last_time = datetime.fromisoformat(last_run).timestamp()
                if now - last_time >= interval_sec:
                    due.append(task)
            except Exception as e:
                log.debug("{}", e)

    return due


def mark_task_run(task_id: str) -> None:
    """Mark a task as having just run."""
    data = _load_tasks()
    tasks = data.get("tasks", [])

    task = next((t for t in tasks if t["id"] == task_id), None)
    if task:
        task["last_run"] = datetime.now().isoformat()
        _save_tasks(data)


def scheduler(
    parameters: dict,
    response=None,
    player=None,
    session_memory=None,
) -> str:
    """
    Manage recurring scheduled tasks.

    Actions:
    - schedule: Create a new recurring task
    - list: Show all scheduled tasks
    - enable: Enable a task
    - disable: Disable a task
    - delete: Remove a task
    """
    params = parameters or {}
    action = params.get("action", "").lower().strip()

    if not action:
        return "No action specified. Use: schedule, list, enable, disable, delete."

    if player:
        player.write_log(f"[Scheduler] {action}")

    try:
        if action == "schedule":
            task_id = params.get("task_id", "").strip()
            description = params.get("description", "").strip()
            task_action = params.get("task_action", "").strip()
            interval = int(params.get("interval_minutes", 60))

            if not task_id:
                return "task_id is required."
            if not description:
                return "description is required."
            if not task_action:
                return "task_action is required."

            return schedule_task(task_id, description, task_action, interval)

        elif action == "list":
            return list_tasks()

        elif action == "enable":
            task_id = params.get("task_id", "").strip()
            if not task_id:
                return "task_id is required."
            return enable_task(task_id)

        elif action == "disable":
            task_id = params.get("task_id", "").strip()
            if not task_id:
                return "task_id is required."
            return disable_task(task_id)

        elif action == "delete":
            task_id = params.get("task_id", "").strip()
            if not task_id:
                return "task_id is required."
            return delete_task(task_id)

        else:
            return f"Unknown action: {action}"

    except Exception as e:
        log.error(f"[Scheduler] Error: {e}")
        return f"Scheduler error: {e}"


# ── Tool declaration ──────────────────────────────────────────────────────────
TOOL = {
    "name": "scheduler",
    "description": (
        "Manage recurring scheduled tasks. Create tasks that run automatically "
        "at specified intervals (e.g., check email every 30 minutes, run backups daily). "
        "All tasks require user authorization before creation. "
        "Use for: reminders, automated checks, periodic reports."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "schedule | list | enable | disable | delete",
            },
            "task_id": {
                "type": "STRING",
                "description": "Unique task identifier (e.g., 'daily_backup')",
            },
            "description": {
                "type": "STRING",
                "description": "Human-readable task description",
            },
            "task_action": {
                "type": "STRING",
                "description": "Action to perform (plain English instruction)",
            },
            "interval_minutes": {
                "type": "INTEGER",
                "description": "How often to run (in minutes, min 1, max 10080)",
            },
        },
        "required": ["action"],
    },
    "handler": scheduler,
}
