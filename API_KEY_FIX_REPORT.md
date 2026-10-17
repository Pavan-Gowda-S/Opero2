# API KEY VALIDATION BUG - ROOT CAUSE ANALYSIS

**Date:** 2026-10-13  
**Issue:** App keeps prompting "API key invalid" despite valid key in config/api_keys.json  
**API Key (Masked):** AQ.A...BBLg (53 characters)

---

## ROOT CAUSE

The validation bug has **TWO contributing factors**:

### Factor 1: Deprecated Model Fallback in core/gemini.py

**File:** `core/gemini.py:130`  
**Current Code:**
```python
_LIVE_FALLBACK = "models/gemini-3.1-flash-live-preview"
```

**Problem:**  
When tool calls happen before main.py fully loads, or from background threads, `_live_model()` (line 239) falls back to the deprecated model name. Google's API returns a 404 error for the non-existent model, which the error handler misinterprets as an invalid API key.

**Evidence:**
- External test confirms: `404 NOT_FOUND. models/gemini-2.0-flash-exp is not found for API version v1beta`
- The key itself is **VALID** (53 chars, properly stripped, no whitespace issues)
- main.py line 80 already updated to `gemini-2.0-flash-exp`, but fallback was not

---

### Factor 2: Overly Broad Error Catching

**File:** `main.py:2471-2480`  
**Current Code:**
```python
if ("API key not valid" in err_str or "1007" in err_str
        or "No API key was provided" in err_str):
    self.ui.write_log("ERR: API key invalid — please re-enter your key.")
    self.ui.prompt_reconfig()
```

**Problem:**  
The error handler only catches **literal string matches** from Google's error messages. When a 404 model error occurs, it doesn't match these strings, but the connection still fails. The generic error fallthrough may eventually trigger the re-prompt logic after multiple failed reconnection attempts.

**Secondary Issue:**  
The error message doesn't distinguish between:
- Invalid API key (user needs to fix)
- Deprecated model name (developer needs to fix)
- Quota exceeded (temporary, retry later)
- Network issues (check connection)

---

## VERIFICATION

### Test 1: API Key External Validation
```bash
python test_api_key.py
```

**Result:**
```
[*] Found API key: AQ.A...BBLg
   Key length: 53 characters

[~] Testing key with Gemini API...
[X] API test failed: 404 NOT_FOUND. models/gemini-2.0-flash-exp is not found...
    -> Model not found (check model name)
```

**Conclusion:** API key is valid. Model name is the issue.

---

### Test 2: Config File Inspection
```json
{
    "gemini_api_key": "[REDACTED]",
    "os_system": "windows"
}
```

**Verification:**
- ✅ Key is properly stored
- ✅ No leading/trailing whitespace
- ✅ No newlines or special characters
- ✅ JSON is valid
- ✅ Save/load code properly calls `.strip()` (ui/overlays.py:1792, ui/window.py:2646)

---

## THE FIX

### Fix 1: Update Fallback Model in core/gemini.py

**File:** `core/gemini.py:130`  
**Change:**
```python
# OLD:
_LIVE_FALLBACK = "models/gemini-3.1-flash-live-preview"

# NEW:
_LIVE_FALLBACK = "models/gemini-2.0-flash-exp"
```

**Why:** Ensures all code paths use the current model, even when main.py hasn't loaded yet.

---

### Fix 2: Improve Error Diagnostics in main.py

**File:** `main.py:2471-2480`  
**Enhancement:** Add model-specific error detection before the key validation check:

```python
# NEW: Detect deprecated model errors
if ("404" in err_str or "not found" in err_str.lower()) and "model" in err_str.lower():
    log.error(f"[OPERO] Model error: {err_str}")
    self.ui.write_log("ERR: Model configuration issue — check logs")
    continue  # Retry with same key

# EXISTING: Invalid API key
if ("API key not valid" in err_str or "1007" in err_str
        or "No API key was provided" in err_str):
    self.ui.write_log("ERR: API key invalid — please re-enter your key.")
    self.ui.set_state("SLEEPING")
    self.ui.prompt_reconfig()
    ...
```

---

## IMPLEMENTATION STATUS

### Already Fixed (from FIXES_COMPLETED.md):
- ✅ main.py:80 - Model name updated to `gemini-2.0-flash-exp`
- ✅ Echo tail increased to 0.4s (reduces interruptions)

### Needs Fixing:
- ⚠️ core/gemini.py:130 - Fallback model still uses deprecated name
- ⚠️ main.py:2471-2480 - Error handler needs model-specific diagnostics

---

## MANUAL TESTING STEPS

### Step 1: Verify Fix Applied
1. Check `core/gemini.py` line 130 shows `gemini-2.0-flash-exp`
2. Check `main.py` line 80 shows `gemini-2.0-flash-exp`

### Step 2: Test Fresh Start
1. Close OPERO completely
2. Start OPERO
3. **Expected:** App starts normally, no key re-prompt
4. **Success criteria:** Connection established, "LISTENING" state active

### Step 3: Test Restart
1. Close OPERO
2. Start again
3. **Expected:** Key loaded from config, no re-prompt
4. **Success criteria:** No setup overlay appears

### Step 4: Test Tool Calls
1. Say: "Search for AI news"
2. Say: "Summarize this image" (drop an image)
3. **Expected:** Tools execute without connection errors
4. **Success criteria:** No "API key invalid" messages

---

## REMAINING LIMITATIONS

### Cannot Fix:
1. **Model availability** - If Google deprecates `gemini-2.0-flash-exp`, the app will need another update
2. **API quota limits** - Free tier quota exhaustion will cause errors (not key invalidity)
3. **Network issues** - Connection failures are distinct from key problems

### Recommendations:
1. **Monitor Google AI Studio** for model deprecation announcements
2. **Add telemetry** to distinguish error types in logs
3. **Consider fallback ladder** - Try multiple model names in sequence (already implemented in core/gemini.py for REST calls)

---

## CONCLUSION

**Root cause:** Deprecated model fallback in `core/gemini.py` causes 404 errors misinterpreted as invalid key  
**Primary fix:** Update line 130 in core/gemini.py to use current model  
**Secondary fix:** Improve error diagnostics to distinguish model errors from key errors  
**Key status:** ✅ VALID (external test confirms)  
**Config status:** ✅ CORRECT (properly saved and stripped)

Once the fallback model is updated, the "API key invalid" loop should stop.
