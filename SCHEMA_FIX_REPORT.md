# Gemini Live Schema Error Fix Report

**Date:** 2026-10-16  
**Issue:** Websocket close with code 1007 + "missing field" error  
**Root Cause:** Tool schema validation failure (not API key issue)

---

## Problem Summary

The app was failing to connect to Gemini Live with this error:
```
1007 ... BidiGenerateContentRequest.setup.tools[0].function_declarations[13].parameters.properties[commands].items: missing field.
```

The error handler incorrectly showed "API key invalid" for this 1007 error, but:
- **1007** = WebSocket protocol violation (schema error)
- **1008/401/403** = Authentication errors (actual API key issues)

---

## Root Cause Analysis

### 1. Schema Error (Primary Issue)

**File:** `actions/dev_agent.py:791-794`

**Before (broken):**
```python
"commands": {
    "type": "ARRAY",
    "description": "List of shell commands to execute..."
}
```

**Problem:** The `commands` parameter declared type `ARRAY` but did not provide the required `items` field. Gemini Live schema validation requires every ARRAY to specify what type its elements are.

**After (fixed):**
```python
"commands": {
    "type": "ARRAY",
    "description": "List of shell commands to execute...",
    "items": {
        "type": "STRING"
    }
}
```

### 2. Error Handling Issue (Secondary Issue)

**File:** `main.py:2480-2489`

**Before (broken):**
```python
if ("API key not valid" in err_str or "1007" in err_str
        or "No API key was provided" in err_str):
    self.ui.write_log("ERR: API key invalid — please re-enter your key.")
```

**Problem:** Treated 1007 websocket close codes as API key errors, causing the app to:
1. Show wrong error message ("API key invalid")
2. Prompt for new API key (wasting user's time)
3. Discard the saved valid key
4. Never surface the real schema error

**After (fixed):**
```python
# Schema error (1007 = protocol violation)
if "1007" in err_str:
    log.error(f"[OPERO] Tool schema error: {err_str}")
    self.ui.write_log(
        f"ERR: Tool schema validation failed. "
        f"Check tool declarations for missing 'items' on arrays..."
    )
    # Don't prompt for API key on schema errors
    await asyncio.sleep(30)
    continue

# Invalid API key — real auth errors only
if ("API key not valid" in err_str
        or "API_KEY_INVALID" in err_str
        or "UNAUTHENTICATED" in err_str
        or "1008" in err_str):
    self.ui.write_log("ERR: API key invalid — please re-enter your key.")
    ...
```

---

## Changes Made

### 1. Fixed dev_agent.py Schema
- **File:** `actions/dev_agent.py`
- **Line:** 791-796
- **Change:** Added `"items": {"type": "STRING"}` to the `commands` parameter

### 2. Fixed Error Handling
- **File:** `main.py`
- **Lines:** 2479-2503
- **Changes:**
  - Separated 1007 schema errors from API key errors
  - Show real error message for schema issues
  - Only prompt for new API key on actual auth errors (400/401/403/1008)

### 3. Created Validation Scripts

**validate_tool_schemas.py:**
- Validates all tool declarations against Gemini Live rules
- Checks for missing `items` on arrays
- Checks for invalid `required` fields
- Detects unsupported keywords

**test_tool_schemas_deep.py:**
- Loads tools exactly as main.py does (via action_loader)
- Deep recursive validation
- Tests 19 action tools + inline tools

---

## Verification Results

### Schema Validation
```
[PASS] All tool schemas are valid - Gemini Live connection should work

Tools validated:
✓ 19 action tools (all PASS)
✓ 7 inline tools (manually verified)
✓ dev_agent.commands specifically tested (PASS)
```

### Gemini Live Schema Rules

All tools now comply with these rules:
1. ✅ Every ARRAY has an `items` field
2. ✅ Every OBJECT has valid `properties`
3. ✅ `required` arrays only list existing properties
4. ✅ No unsupported keywords (additionalProperties, $ref, default, anyOf)

---

## Testing Instructions

### 1. Run Validation (before starting app):
```bash
python validate_tool_schemas.py
```
Expected output: `[PASS] All tool schemas are valid`

### 2. Start the App:
```bash
python main.py
```

### Expected Behavior:
- ✅ Gemini Live connects successfully (no 1007 error)
- ✅ No "API key invalid" prompt
- ✅ "SYS: OPERO online" message appears
- ✅ Can use all tools including dev_agent

### If Schema Error Occurs:
The error message will now show:
```
ERR: Tool schema validation failed. Check tool declarations for missing 'items' on arrays, invalid 'properties', etc.
```
Instead of the misleading "API key invalid" message.

---

## Summary

**Root Cause:** `dev_agent.py` had `commands` parameter with type ARRAY but no `items` field

**Files Changed:**
1. `actions/dev_agent.py` - Fixed schema (line 791-796)
2. `main.py` - Fixed error handling (line 2479-2503)

**Files Created:**
1. `validate_tool_schemas.py` - Schema validation utility
2. `test_tool_schemas_deep.py` - Deep validation test

**Result:** 
- All 26 tool declarations (19 actions + 7 inline) are now schema-valid
- Error handling correctly distinguishes schema errors from API key errors
- App should connect to Gemini Live successfully

---

## Next Steps

1. ✅ Run `python validate_tool_schemas.py` to verify all schemas
2. ✅ Run `python test_tool_schemas_deep.py` for deep validation
3. 🔄 Start `python main.py` and confirm successful connection
4. 🔄 Test dev_agent with commands parameter
5. 🔄 Verify on restart that connection still works

---

**Fix completed:** 2026-10-16 12:51 UTC
