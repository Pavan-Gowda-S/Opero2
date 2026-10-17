# Phase 4 Repository Audit

**Date:** 2026-10-17  
**Audit Type:** Pre-implementation architecture analysis  
**Status:** ✅ COMPLETE

---

## 1. Existing Architecture

### 1.1 Application Type

**Opero2** is a **native desktop voice-first operator** built with Python 3.11+ and PyQt6.

**Core Characteristics:**
- Local desktop application with GUI (not CLI-only)
- Voice-first interface using Gemini Live API
- Modular action system with auto-discovery
- Real-time audio processing and visual feedback
- Plugin architecture for extensibility

**Entry Point:** `main.py` (not a CLI script)

**UI Framework:** PyQt6 with custom HUD interface (`ui/` package)

### 1.2 Action System Architecture

Opero2 uses a **declarative action system** with automatic discovery:

**Discovery Mechanism:** (`core/action_loader.py`)
```python
def discover_actions():
    """Auto-discover all actions from actions/*.py files"""
    # Scans actions/ directory
    # Loads modules that define TOOL dict
    # Returns list of tool declarations
```

**Action Declaration Pattern:**
Every action file in `actions/` follows this pattern:
```python
# Define handler function
def my_action(parameters, response=None, player=None, session_memory=None):
    """Action implementation"""
    return result_string

# Declare tool metadata for Gemini function calling
TOOL = {
    "name": "action_name",
    "description": "What this action does",
    "parameters": {
        "type": "OBJECT",
        "properties": { ... },
        "required": [...]
    },
    "handler": my_action,  # Function reference
}
```

**Integration Point:**
- `main.py` calls `discover_actions()` at startup
- Actions are registered with Gemini Live as function tools
- User speaks/types request → Gemini decides which tool to call
- Gemini returns function call → `core.tool_dispatch` invokes handler
- Handler returns string result → displayed to user

**Existing Actions:** 24 action files discovered, including:
- `web_search.py` - Web search using multiple providers
- `browser_control.py` - Playwright browser automation  
- `file_processor.py` - File operations
- `computer_control.py` - System control
- **`tinyfish_action.py` - TinyFish integration (NEW, Phase 3)**

### 1.3 TinyFish Integration Status

**Current State:**
- ✅ `actions/tinyfish_action.py` exists (Phase 3 implementation)
- ✅ Declares `TOOL` dict with handler `tinyfish_search`
- ✅ Supports 3 operations: search, fetch, agent
- ✅ Uses subprocess to call Node.js service
- ✅ Node.js service (`tinyfish_service/`) fully implemented
- ✅ Validation, error handling, timeout handling present

**TOOL Declaration:**
```python
TOOL = {
    "name": "tinyfish_search",
    "description": "Advanced web search, content extraction, and browser automation...",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "operation": {"type": "STRING"},  # search, fetch, agent
            "query": {"type": "STRING"},
            "urls": {"type": "ARRAY"},
            "url": {"type": "STRING"},        # For agent
            "goal": {"type": "STRING"},       # For agent
            # ... more parameters
        },
        "required": ["operation"]
    },
    "handler": tinyfish_search,
}
```

**Handler Function:**
```python
def tinyfish_search(parameters, response=None, player=None, session_memory=None) -> str:
    """Main handler - routes to _search(), _fetch(), or _agent()"""
    operation = parameters.get("operation", "search")
    if operation == "agent":
        return _agent(url, goal, max_steps, max_duration_seconds, browser_profile)
    # ... etc
```

**Key Finding:** **TinyFish is ALREADY integrated into Opero's action system.** Phase 3 completed the subprocess integration. The action is auto-discoverable and callable by Gemini.

### 1.4 User Interaction Flow

**Current Flow:**
1. User speaks/types request to Opero
2. Gemini Live receives audio/text
3. Gemini reasons about request
4. Gemini decides to call `tinyfish_search` function
5. Gemini provides parameters: `{"operation": "agent", "url": "...", "goal": "..."}`
6. Opero's tool dispatcher calls `tinyfish_search(parameters)`
7. Handler validates, calls Node.js subprocess
8. Result returned as string
9. Gemini incorporates result into response
10. User sees/hears final answer

**UI Components:**
- `ui/window.py` - Main window (MainWindow class)
- `ui/widgets.py` - HUD canvas, log widget, metrics
- `ui/overlays.py` - Setup, settings, API key management
- Voice input/output handled by Gemini Live session

**No Explicit Confirmation System Observed:** Actions are executed when Gemini calls them. No pre-execution confirmation dialogs present in existing action files.

### 1.5 Git Working Tree

**Untracked Files (Phase 3 additions):**
```
?? actions/tinyfish_action.py
?? tinyfish_service/
?? package.json
?? node_modules/
?? .env.example
?? PHASE_3_REPORT.md
?? PHASE_3.1_HARDENING_REPORT.md
?? PHASE_3_2_REPORT.md
?? TINYFISH_INTEGRATION_REPORT.md
```

**Modified Files:**
```
M .gitignore          (added .env, node_modules, TinyFish patterns)
M package-lock.json   (new file from npm install)
```

**Protected Files:**
```
.env                  (exists, gitignored, contains TINYFISH_API_KEY)
```

**Status:** No conflicts. Phase 3 files are uncommitted but functional. User has not committed Phase 3 yet, waiting for Phase 4 completion.

---

## 2. Phase 4 Integration Point

### 2.1 What Already Works

**TinyFish agent is already callable:**
```python
# Gemini can call this right now:
{
  "name": "tinyfish_search",
  "args": {
    "operation": "agent",
    "url": "https://example.com",
    "goal": "Extract page title"
  }
}
```

The handler will:
1. Validate inputs
2. Call Node.js subprocess
3. Wait for result (blocking, up to 600s timeout)
4. Return formatted string or error

**What's Missing for Phase 4:**

1. **No User Confirmation** - Agent executes immediately when Gemini calls it
2. **No Execution Status Visibility** - User doesn't see "running" state
3. **No Cost Warning** - No indication that operation is billable
4. **No Operation History** - No record of past agent runs
5. **No Timeout Explanation** - Timeout just returns error, no context
6. **No Safety Guardrails** - Gemini could call with any goal

### 2.2 Required Integration Strategy

**Minimal Approach (follows Opero's existing patterns):**

Phase 4 must add confirmation and visibility **without rewriting the action system**.

**Two viable paths:**

#### Path A: Confirmation Gate (Recommended)
Use Opero's existing `core.confirm` module to gate agent operations:

```python
from core import confirm as confirm_gate

def _agent(url, goal, ...):
    # Show confirmation dialog
    confirmed = confirm_gate.request_confirmation(
        action="TinyFish Agent Automation",
        details={
            "url": url,
            "goal": goal,
            "cost": "~$0.10-$1.00 estimated",
            "safety": "Agent will browse the target site"
        }
    )
    
    if not confirmed:
        return "Agent operation cancelled by user."
    
    # Proceed with execution
    response = _call_tinyfish_service("agent", args, timeout=600)
    # ...
```

#### Path B: Validation-Level Rejection
Modify validation to require explicit opt-in flag:

```python
# Reject agent operations unless user has opted in
if operation == "agent" and not parameters.get("confirmed", False):
    return (
        "TinyFish agent automation requires explicit confirmation. "
        "This operation will access the target website and may incur charges. "
        "Please confirm you want to proceed."
    )
```

**Recommendation:** Path A (confirmation gate) is more user-friendly and follows Opero's existing confirmation pattern.

### 2.3 Files Requiring Modification

**Minimum Changes:**

1. **`actions/tinyfish_action.py`** (modify)
   - Add confirmation gate before agent execution
   - Add execution status logging
   - Improve timeout error messages
   - Add operation history tracking (if lightweight option available)

2. **`core/confirm.py`** (inspect, possibly extend)
   - Check if existing confirmation system supports agent use case
   - May need minor extension for cost warnings

3. **NEW: `actions/tinyfish_history.py` or similar** (create if needed)
   - Lightweight execution history
   - JSON file storage (no new database)
   - Track: timestamp, url, goal summary, status, run_id, duration

**Optional Enhancements:**

4. **`ui/overlays.py`** (extend if UI needed)
   - Add TinyFish status overlay showing running operations
   - Only if confirmation gate is insufficient

5. **`ui/widgets.py`** (extend if UI needed)
   - Add agent status indicator to HUD
   - Only if real-time progress is required

### 2.4 New Files Required

**Minimum:**
- None (if using existing confirmation system)

**Recommended:**
- `tests/test_tinyfish_action.py` - Unit tests for agent execution
- `actions/tinyfish_history.json` - Operation history (data file, not code)

**Documentation:**
- `PHASE_4_IMPLEMENTATION_REPORT.md` - This phase's report

---

## 3. Risks and Limitations

### 3.1 Technical Risks

**1. Confirmation Timing**
- **Risk:** Confirmation dialog interrupts voice conversation flow
- **Mitigation:** Keep confirmation UI minimal, non-blocking where possible

**2. Timeout Ambiguity**
- **Risk:** Local timeout ≠ remote cancellation (documented in Phase 3.1)
- **Mitigation:** Clear messaging that remote operation may continue

**3. No Streaming Progress**
- **Risk:** Agent runs for 60s with no feedback
- **Impact:** User experience issue, not a blocker
- **Mitigation:** Document limitation, defer streaming to Phase 5

**4. Confirmation Bypass**
- **Risk:** Gemini might retry without user knowledge if first attempt fails
- **Mitigation:** Track confirmation state, require re-confirmation

### 3.2 Integration Risks

**1. Breaking Existing Actions**
- **Risk:** Changes to confirmation system affect other actions
- **Mitigation:** Test all existing actions after modification

**2. Git Conflicts**
- **Risk:** User has uncommitted Phase 3 work
- **Status:** No conflicts observed, clean working tree except new files

**3. Python Environment**
- **Risk:** Missing dependencies for new features
- **Status:** All required packages present (PyQt6, pathlib, json)

### 3.3 Known Limitations (From Phase 3)

**Cannot be fixed in Phase 4:**

1. **60s HTTP Timeout** - Agent operations exceeding 60s timeout locally but continue remotely
2. **No Remote Cancellation** - Cannot stop agent after submission
3. **Pattern Matching Not Reliable** - Cannot guarantee read-only execution
4. **Beta Program Required** - Custom agent_config needs TinyFish beta access
5. **No Cost Verification** - Actual charges not available in response

**Must be documented, not "fixed".**

---

## 4. Phase 4 Scope Definition

### 4.1 In Scope

**Required (Completion Criteria):**
- ✅ Add user confirmation before agent execution
- ✅ Display target URL, goal, and cost warning
- ✅ Track execution status (READY, RUNNING, COMPLETED, FAILED, TIMED_OUT)
- ✅ Return structured results with clear success/failure indication
- ✅ Handle timeouts with honest messaging
- ✅ Preserve existing search/fetch functionality
- ✅ Add lightweight operation history
- ✅ Write comprehensive tests
- ✅ Document implementation

**Optional (If Time Permits):**
- Visual execution status indicator in UI
- Cost estimation based on past runs
- Goal safety review in confirmation dialog

### 4.2 Out of Scope (Phase 5 or Beyond)

**Explicitly Deferred:**
- ❌ Streaming progress (`agent.stream()` requires architecture change)
- ❌ Live browser preview URL (requires UI redesign)
- ❌ Queueing + polling for long operations (requires async architecture)
- ❌ Wallet balance display (requires additional API call approval)
- ❌ Custom agent_config support (requires TinyFish beta program)
- ❌ Multi-user support (Opero is single-user desktop app)
- ❌ Database-backed history (overkill for desktop app)

### 4.3 Testing Strategy

**Unit Tests:**
- Input validation (URL, goal, parameters)
- Confirmation gate behavior
- Error handling (auth, network, timeout)
- History tracking

**Integration Tests:**
- Action discoverable by `discover_actions()`
- Handler callable with valid parameters
- Subprocess execution (mocked)
- Result formatting

**Regression Tests:**
- Existing search operation unchanged
- Existing fetch operation unchanged
- Other actions not affected

**Live Test:**
- One controlled live agent run (with approval only)
- Safe public page (example.com)
- Strictly read-only goal

---

## 5. Audit Conclusion

### 5.1 Key Findings

1. **TinyFish is already integrated** at the action system level (Phase 3)
2. **No confirmation system exists** for agent operations
3. **Opero has a confirmation module** (`core.confirm`) that can be extended
4. **Action system is mature and stable** - minimal changes needed
5. **No architectural blockers** to Phase 4 implementation

### 5.2 Recommended Approach

**Use existing Opero patterns:**
- Extend `core.confirm` for agent confirmation
- Add lightweight history to `actions/` directory
- Keep UI changes minimal (confirmation dialog only)
- Preserve subprocess architecture (no HTTP service)
- Follow existing action file patterns

**Implementation Order:**
1. Inspect `core/confirm.py` and extend if needed
2. Modify `actions/tinyfish_action.py` to add confirmation gate
3. Add execution history tracking
4. Improve error messages and timeout handling
5. Write comprehensive test suite
6. Test existing actions for regression
7. Document everything

### 5.3 Completion Criteria Met?

**Can Phase 4 be implemented safely?** ✅ YES

**Requirements:**
- ✅ Existing architecture understood
- ✅ Integration point identified (action handler)
- ✅ Required files identified (1 modification, 1-2 new)
- ✅ Risks assessed and mitigated
- ✅ No architectural blockers
- ✅ Git conflicts avoided
- ✅ Testing strategy defined

**Ready to proceed with implementation.**

---

## 6. Files Summary

### 6.1 Existing Files to Modify

| File | Purpose | Changes Needed |
|------|---------|----------------|
| `actions/tinyfish_action.py` | TinyFish integration | Add confirmation, history, improved errors |
| `core/confirm.py` | Confirmation gate | Inspect, possibly extend for cost warnings |

### 6.2 New Files to Create

| File | Purpose | Size Estimate |
|------|---------|---------------|
| `tests/test_tinyfish_action.py` | Unit tests | ~300 lines |
| `PHASE_4_IMPLEMENTATION_REPORT.md` | Documentation | ~500 lines |

### 6.3 Data Files (Optional)

| File | Purpose | Format |
|------|---------|--------|
| `actions/tinyfish_history.json` | Operation history | JSON array |

---

## 7. Next Steps

1. **Read `core/confirm.py`** - Understand existing confirmation system
2. **Implement confirmation gate** - Add to `_agent()` function
3. **Add execution tracking** - Status lifecycle implementation
4. **Improve error messages** - Timeout, cost, safety warnings
5. **Add lightweight history** - JSON file with operation records
6. **Write test suite** - Unit + integration + regression
7. **Test live** - One controlled agent run (with approval)
8. **Document** - Create Phase 4 report

**No blockers identified. Ready to proceed.**

---

**Audit completed:** 2026-10-17T07:46:24Z  
**Status:** ✅ READY FOR PHASE 4 IMPLEMENTATION
