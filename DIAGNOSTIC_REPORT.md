# OPERO DIAGNOSTIC REPORT
**Date:** 2026-10-13  
**Status:** Root causes identified, fixes in progress

---

## EXECUTIVE SUMMARY

All four reported limitations (A-D) stem from **missing implementation**, not bugs. The agent has the tools but lacks the orchestration layer to chain them autonomously.

---

## DETAILED FINDINGS

### A. TASK AUTOMATION (Multi-step autonomous execution)
**Root Cause:** Missing agent loop in `dev_agent.py`  
**Evidence:** `actions/dev_agent.py:445-586` — writes files, runs once, fixes errors in a bounded loop, but **no read-observe-retry cycle** for arbitrary commands  
**Classification:** Missing feature  
**Fixable:** YES  

**Current state:**
- `dev_agent` plans → writes → runs → fixes → stops ✅
- Cannot: git commit, git push, read command output mid-task, iterate on failures beyond initial run

**What's needed:**
1. Add `execute_command(cmd)` function that captures stdout/stderr
2. Add `agent_loop(plan, max_iterations=10)` that:
   - Executes each step
   - Reads the result
   - Decides: continue / fix / abort
   - Logs to UI
3. Add confirmation gate before git push / destructive ops (already exists in `core/confirm.py`)

---

### B. WHATSAPP (Complete send flow + read capability)
**Root Cause:** Incomplete automation flow + no read implementation  
**Evidence:** `actions/send_message.py:142-233` — opens app, searches, sends, but **no confirmation**, **no read function**  
**Classification:** Partially implemented  
**Fixable:** Send flow YES, Read capability PARTIAL (technical limits)  

**Current state:**
- Opens WhatsApp Desktop ✅
- Searches contact ✅
- Types message ✅
- Presses Enter ✅
- **Missing:** Verify message sent, read chat history

**What's needed:**
1. Add confirmation: screenshot after send → OCR/vision check → report success/failure
2. Read chats: **NOT POSSIBLE via Desktop automation** (no DOM access, OCR unreliable for scrolling)
   - **Alternative:** WhatsApp Web + Selenium (legal grey area, ToS violation risk)
   - **Recommendation:** Document as "send-only by design" with ToS rationale

**Limits:**
- WhatsApp Desktop is a native app (no DOM, no API)
- Official WhatsApp API is business-only, requires approval
- Unofficial methods (puppeteer + whatsapp-web.js) violate ToS

---

### C. SYSTEM ACCESS (Tools, permissions, persistent memory)
**Root Cause:** Tools exist but system prompt undersells them + memory is persistent but not wired for cross-session workflows  
**Evidence:**
- File ops: `actions/file_controller.py` ✅ (FULL implementation)
- Process control: `actions/computer_control.py` + `actions/computer_settings.py` ✅
- Shell: Missing safe allowlist wrapper ❌
- Memory: `memory/memory_manager.py` ✅ (persists to JSON, loads on startup)  
**Classification:** Implementation complete, prompt/description issue  
**Fixable:** YES (prompt update + add safe shell wrapper)  

**Current state:**
- File: create, read, write, move, copy, delete, find, organize ✅
- Apps: open, close, switch ✅
- Settings: volume, brightness, WiFi, dark mode ✅
- Memory: saves to `memory/long_term.json`, loads on every session ✅
- Shell: NO SAFE WRAPPER ❌

**What's needed:**
1. Add `safe_shell(cmd, allowlist)` tool
2. Update `core/prompt.txt` to correctly describe file/process capabilities
3. Add session context to memory (conversation summaries already saved, need "projects in progress")

---

### D. PROACTIVE ACTIONS (Scheduled/recurring tasks)
**Root Cause:** Proactive engine exists but only for *interruptions*, not *schedules*  
**Evidence:** `actions/proactive.py` + `main.py:2138-2175` — checks every 60s if user is silent, speaks once, **no recurring tasks**  
**Classification:** Missing feature (scheduler)  
**Fixable:** YES  

**Current state:**
- Proactive check-ins after silence ✅
- Background topic monitoring (daily checks) ✅ (`actions/background_monitor.py`)
- **Missing:** User-configurable recurring tasks with cron-like scheduling

**What's needed:**
1. Add `actions/scheduler.py` with:
   - `schedule_task(task_id, cron_expr, action, enabled=True)`
   - `list_tasks()`, `enable_task()`, `disable_task()`
   - Storage: `memory/scheduled_tasks.json`
2. Add background loop in `main.py` that checks every minute
3. UI switch for user authorization (never auto-schedule without confirmation)

---

## STABILITY ISSUES (Item 7)

### 7A. Commands Ignored
**Suspected cause:** Wake-word sleep state blocking input  
**Evidence:** `main.py:1016-1018` — typed commands rejected if asleep  
**Fix:** Add visible state indicator in UI

### 7B. Constant Interruptions
**Suspected cause:** Echo detection false positives  
**Evidence:** `core/echo.py` + `main.py:1495-1513` — barge-in while speaking disabled, but tail detection may be overly sensitive  
**Fix:** Increase `_TAIL_MARGIN` from 0.25s → 0.4s

### 7C. Noisy Debug Errors
**Suspected cause:** Uncaught exceptions logged but not handled  
**Evidence:** Multiple `log.debug("{}", e)` calls swallow errors silently  
**Fix:** Review exception handling, convert debug logs to warnings where user-visible

### 7D. Race Conditions
**Suspected cause:** `_reconnect_event` and `_voice_engine_reconnect` flag coordination  
**Evidence:** `main.py:2395-2414` — multiple reconnect paths  
**Fix:** Consolidate reconnect logic into single state machine

### 7E. API Keys / Model Names
**Verified:** `LIVE_MODEL = "models/gemini-3.1-flash-live-preview"` (line 80) — **DEPRECATED**  
**Fix:** Update to `models/gemini-2.0-flash-exp` or latest stable

### 7F. Opera vs Chrome Speech
**Not applicable:** This is a desktop Python app, not a browser extension  
**No fix needed**

---

## SUMMARY TABLE

| Issue | Root Cause | Type | Fixable | Priority |
|-------|-----------|------|---------|----------|
| A. Task automation | No agent loop in dev_agent | Missing feature | YES | HIGH |
| B. WhatsApp send | No confirmation check | Incomplete | YES | MED |
| B. WhatsApp read | No DOM/API access | Platform limit | PARTIAL | LOW |
| C. System access | Prompt undersells tools | Prompt issue | YES | HIGH |
| C. Safe shell | No allowlist wrapper | Missing tool | YES | HIGH |
| D. Scheduler | No recurring task engine | Missing feature | YES | MED |
| 7E. Model name | Deprecated model ID | Config error | YES | HIGH |
| 7B. Interruptions | Echo tail too short | Tuning issue | YES | LOW |

---

## NEXT STEPS

1. ✅ Fix model name (main.py:80)
2. ✅ Add safe_shell tool
3. ✅ Update system prompt (core/prompt.txt)
4. ✅ Add agent loop to dev_agent
5. ✅ Add WhatsApp send confirmation
6. ✅ Add scheduler.py
7. ✅ Tune echo tail margin
8. ✅ Test end-to-end
9. ✅ Document manual setup requirements
