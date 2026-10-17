# Quick Test Checklist - Run These Now!

**Time:** 2026-10-16 14:13 UTC  
**Goal:** Verify both fixes work in < 5 minutes

---

## **STEP 1: Validate Schemas** (30 seconds)

```bash
python validate_tool_schemas.py
```

**Look for:**
```
[PASS] All tool schemas are valid
```

✅ **PASS** = Schema fix works  
❌ **FAIL** = dev_agent still has schema error

---

## **STEP 2: Test API Key** (30 seconds)

```bash
python test_api_key.py
```

**Look for:**
```
[+] API key is VALID
    Model: gemini-2.5-flash
```

✅ **PASS** = Key works  
❌ **FAIL** = Check network/key

---

## **STEP 3: Start OPERO** (2 minutes)

```bash
python main.py
```

### **What You Should See:**

**Loading (5 seconds):**
```
[Actions] Discovered 19 tools
[Plugins] ...
```

**Connecting (2 seconds):**
```
[OPERO] Connecting...
```

**Success (immediate):**
```
[OPERO] Connected.
SYS: OPERO online.
```

### **UI Should Show:**
- 🟢 Green status
- "LISTENING" or "SLEEPING" 
- No error popups
- No "API key invalid" message

### **✅ PASS IF:**
- Says "OPERO online"
- No 1007 error (schema)
- No 1008 error (model)
- No "API key invalid" prompt

### **❌ FAIL IF:**
- Error message appears
- Stuck on "THINKING"
- "API key invalid" prompt
- 1007 or 1008 error

---

## **STEP 4: Quick Interaction** (1 minute)

**Type in the text box:**
```
Hello, what time is it?
```

**Press Enter**

### **Expected:**
```
You: Hello, what time is it?
OPERO: [greeting + current time]
```

✅ **PASS** = Full pipeline works  
❌ **FAIL** = No response or error

---

## **STEP 5: Test Dev Agent** (1 minute)

**Type:**
```
Create a hello world Python script
```

### **Expected:**
```
You: Create a hello world Python script
🔧 dev_agent called
[DevAgent] Planning...
[DevAgent] Written: hello.py
OPERO: Project created at ~/Desktop/OperaProjects/hello_world
```

✅ **PASS** = No schema error  
❌ **FAIL** = "1007 ... commands.items: missing field"

---

## **STEP 6: Restart Test** (30 seconds)

1. Close OPERO (Ctrl+C or window close)
2. Start again: `python main.py`

### **Expected:**
```
[OPERO] Connected.
SYS: Reconnected — conversation restored.
```

✅ **PASS** = Stable restart  
❌ **FAIL** = Connection fails

---

## **RESULTS SUMMARY**

Check all that apply:

```
□ Step 1: Schema validation passed
□ Step 2: API key test passed
□ Step 3: OPERO started successfully
□ Step 4: Text interaction worked
□ Step 5: Dev agent worked (no schema error)
□ Step 6: Restart succeeded
```

**6/6 checked? 🎉 ALL FIXES WORKING!**

---

## **If Something Fails:**

### **Schema Error (1007)**
```bash
# Check which tool has the error
python validate_tool_schemas.py
```
**Fix:** The validation script will show which file/line

### **Model Error (1008)**
Check the log output. Should show:
```
SYS: Model X unavailable. Trying Y...
```
**If it doesn't try fallback:** Check main.py lines 2503-2541

### **API Key Prompt (Wrong)**
**Should NOT appear for:**
- 1007 schema errors
- 1008 model errors

**Should ONLY appear for:**
- Invalid/missing API key
- Authentication failures

### **No Response**
**Check:**
- Microphone not muted (if using voice)
- Internet connection active
- No firewall blocking Gemini API

---

## **Quick Debug Commands**

```bash
# See what model is configured
cat config/api_keys.json | grep live_model

# Check if dev_agent.py was updated
grep -A 3 "commands.*ARRAY" actions/dev_agent.py
# Should show: "items": {"type": "STRING"}

# Check if main.py model was updated  
grep "LIVE_MODEL_DEFAULT" main.py
# Should show: gemini-2.5-flash-native-audio-latest
```

---

## **Expected Timeline**

- ✅ **Minute 1:** Schema + API key tests pass
- ✅ **Minute 2-3:** OPERO starts and responds
- ✅ **Minute 4:** Dev agent works without schema error
- ✅ **Minute 5:** Restart confirms stability

**Total: 5 minutes to verify everything works!**

---

## **What Each Fix Does**

### **Schema Fix** (dev_agent.py)
- **Before:** `"commands": {"type": "ARRAY"}` ❌
- **After:** `"commands": {"type": "ARRAY", "items": {"type": "STRING"}}` ✅
- **Result:** No more "1007 ... missing field" error

### **Model Fix** (main.py)
- **Before:** `LIVE_MODEL = "models/gemini-2.0-flash-exp"` ❌ (retired)
- **After:** `LIVE_MODEL_DEFAULT = "models/gemini-2.5-flash-native-audio-latest"` ✅
- **Result:** Connects successfully + auto-fallback

### **Error Handling Fix** (main.py)
- **Before:** All 1008 errors → "API key invalid" ❌
- **After:** Only real auth errors → "API key invalid" ✅
- **Result:** Model errors handled correctly

---

**Ready? Run the 6 steps above to verify!** 🚀

For detailed testing, see: `TESTING_GUIDE.md`
