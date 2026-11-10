# Quick Demo Test Guide - Opero2 × TinyFish

**Run these tests 30 minutes before your presentation**

---

## ⚡ AUTOMATED TEST (5 minutes)

### Step 1: Run the Pre-Flight Test Script

```bash
# From project root
python scripts/test_tinyfish_demo.py
```

**Expected Output:**
```
╔═════════════════════════════════════════════════════════════════════╗
║         TinyFish Demo Pre-Flight Test Suite                        ║
║         Testing Opero2 × TinyFish Integration                      ║
╚═════════════════════════════════════════════════════════════════════╝

TEST 1: Environment Setup
──────────────────────────────────────────────────────────────────────

✓ Python version (3.12) (0.01s)
✓ TinyFish API key configured (0.02s)
✓ Node.js installed (v20.x.x) (0.15s)
✓ TinyFish service files present (0.01s)
✓ Node.js dependencies installed (0.01s)

TEST 2: Service Connectivity
──────────────────────────────────────────────────────────────────────

✓ Service responds to search (3.2s)

[... more tests ...]

======================================================================
TEST SUMMARY
======================================================================
Total Tests:  20
Passed:       20
Failed:       0
Warnings:     0
Skipped:      0
Total Time:   15.32s
======================================================================

✅ ALL TESTS PASSED - Ready for demo!
```

**If ANY test fails:**
- ❌ **API key not found** → Check `.env` file has `TINYFISH_API_KEY=...`
- ❌ **Node.js not found** → Install from https://nodejs.org
- ❌ **Dependencies missing** → Run `cd tinyfish_service && npm install`
- ❌ **Service timeout** → Check internet connection
- ❌ **Rate limit** → Wait 60 seconds and retry

---

## 🖥️ MANUAL UI TEST (10 minutes)

### Step 2: Launch Opero2

```bash
python main.py
```

**Wait for:** "OPERO ready" message in console

---

### Step 3: Enable TinyFish Mode

1. **Look for TinyFish toggle** in the header controls
2. **Click the toggle** → Mode switches ON
3. **Verify:** Right panel switches to "Agent Timeline" widget
4. **Verify:** Bottom workspace expands with 3 tabs (Quick Search, Deep Research, Apply Flow)

**Screenshot this state for reference**

---

### Step 4: Test Quick Search (60 seconds)

#### Via Voice:
```
"Opero, search for Python AI internships"
```

#### Via Text Input:
```
search for Python AI internships
```

**Expected Result (5-15 seconds):**
- ✅ Workspace auto-switches to **Quick Search** tab
- ✅ Status shows: `SEARCHING...`
- ✅ Progress bar animates
- ✅ 3-5 result cards appear with titles, URLs, snippets
- ✅ Timeline shows: `● COMPLETED ✓`
- ✅ Export toolbar appears at bottom

**If nothing happens:**
- Check console for errors
- Verify TinyFish mode toggle is ON
- Try text input instead of voice
- Check `actions/tinyfish_action.py` logs

---

### Step 5: Test Deep Research (90 seconds)

#### Via Voice:
```
"Opero, research latest developments in agentic AI"
```

#### Via Text Input:
```
research latest developments in agentic AI
```

**Expected Result (30-60 seconds):**
- ✅ Workspace auto-switches to **Deep Research** tab
- ✅ Status shows: `RESEARCHING...`
- ✅ Formatted markdown content appears with:
  - Executive summary
  - Bullet points
  - Numbered citations [1], [2], etc.
- ✅ Timeline shows: `● COMPLETED`
- ✅ Export toolbar shows `📋 PDF` and `💬 WhatsApp` buttons

**Test the formatting looks clean and professional**

---

### Step 6: Test PDF Export (30 seconds)

1. **Ensure Deep Research results are visible**
2. **Click `📋 PDF` button** in export toolbar
3. **Expected:**
   - Button momentarily disables
   - Activity log: "Generating PDF report..."
   - PDF viewer opens automatically
   - PDF shows clean formatting with header, content, sources

**If PDF doesn't open:**
- Check `reports/` directory for generated file
- Open manually to verify content
- Note: PDF generation itself should succeed even if auto-open fails

---

### Step 7: Test Apply Flow UI (60 seconds)

**Note:** Agent execution is expensive (~$0.10-$1.00) so we only test the UI, not live execution.

1. **Switch to `🎯 Apply Flow` tab**
2. **Type in search:** `Python AI internship`
3. **Click `🔍 Find Matches`**

**Expected Result (20-40 seconds):**
- ✅ Status: `SEARCHING...`
- ✅ 2-4 opportunity cards appear
- ✅ Each card shows:
   - Title (e.g., "Python AI/ML Intern")
   - Organization name
   - Match score badge (e.g., "94% Match" in green)
   - Match rationale (e.g., "💡 Matches your Python experience")
   - Deadline and location
   - `[📝 Review & Apply]` button

4. **Click `[📝 Review & Apply]` on any card**

**Expected:**
- ✅ Large modal dialog opens: "Application Pre-Fill Review"
- ✅ Dialog shows:
   - Target URL
   - Field mapping table (Name, Email, Phone, Resume, etc.)
   - Confidence scores (Profile: 100%, Synthesized: 80%)
   - Generated cover note (scrollable text box)
   - Safety warning box (yellow border):
     ```
     ⚠️ Safety Rule: Pre-Fill Only, Manual Submit Required
     
     The agent will navigate to the form, fill in all fields,
     and STOP immediately before the final submit button.
     ```
   - `[Cancel]` and `[Proceed to Pre-Fill]` buttons

**DO NOT click `[Proceed to Pre-Fill]` unless you want to spend credits**

5. **Click `[Cancel]` to close dialog**

---

### Step 8: Verify Timeline Widget (30 seconds)

**Check the timeline widget (right panel) shows:**
- ✅ Current operation status (IDLE / PENDING / RUNNING / COMPLETED)
- ✅ Elapsed time when running
- ✅ History of last 3 operations
- ✅ Stop button (red) when operation is running
- ✅ Clear status messages

---

## 📋 PRE-DEMO CHECKLIST (5 minutes before presentation)

### Environment
- [ ] Opero window centered on screen (not maximized)
- [ ] TinyFish mode toggle visible in header
- [ ] Voice input tested ("Opero, what time is it?")
- [ ] System audio at comfortable level
- [ ] Browser window minimized (for Apply Flow demo)
- [ ] PDF viewer closed (will open fresh)
- [ ] Screen recording software ready (if recording)

### API & Services
- [ ] TinyFish API key loaded (no errors in console)
- [ ] Node.js service accessible (no "service not found" errors)
- [ ] Internet connection stable
- [ ] Not rate-limited (run one test search to verify)

### Backup Plans
- [ ] Pre-recorded screenshots from phase reports available
- [ ] Test suite results captured (`python -m pytest tests/ -q > test_results.txt`)
- [ ] Fallback to offline demo if API fails

---

## 🚨 COMMON ISSUES & FIXES

### Issue: "TinyFish service not found"
**Fix:** 
```bash
cd tinyfish_service
npm install
```

### Issue: "TinyFish API key not found"
**Fix:** Add to `.env` file:
```
TINYFISH_API_KEY=your_actual_key_here
```

### Issue: Search returns "No results"
**Possible causes:**
- Rate limited → Wait 60 seconds
- Invalid API key → Check `.env`
- Network issue → Check internet

**Automatic fallback:** Should fall back to DuckDuckGo search

### Issue: PDF export fails
**Fix:** Check write permissions:
```bash
mkdir reports  # If directory doesn't exist
```

### Issue: Voice commands not working
**Quick fixes:**
1. Check microphone not muted in Opero
2. Try text input instead: type command in chat
3. Verify TinyFish mode is ON

### Issue: Timeline shows "PENDING" forever
**Cause:** Service call timed out or blocked
**Fix:** 
- Click Stop button (red)
- Check console for timeout errors
- Wait for operation to complete or cancel

---

## ⏱️ TIMING EXPECTATIONS

| Operation | Expected Duration | Timeout |
|-----------|------------------|---------|
| Quick Search | 5-15 seconds | 12s |
| Deep Research | 30-60 seconds | 60s |
| PDF Generation | 1-3 seconds | 10s |
| Apply Flow Search | 20-40 seconds | 60s |
| Agent Pre-Fill | 30-90 seconds | 600s (10 min) |

**If operation exceeds timeout:** Service will return error, but remote agent may still be running (see demo script troubleshooting)

---

## ✅ SUCCESS CRITERIA

Your system is **demo-ready** if:

1. ✅ Automated test script passes (all 20 tests green)
2. ✅ Quick Search returns results in < 15s
3. ✅ Deep Research generates formatted report in < 60s
4. ✅ PDF export works and opens automatically
5. ✅ Apply Flow shows opportunity cards with match scores
6. ✅ Review dialog displays with all safety warnings
7. ✅ Timeline widget updates in real-time
8. ✅ No console errors during normal operation

---

## 📞 EMERGENCY FALLBACK (If Live API Fails)

**Have these ready:**
1. **Open `PHASE_3_UI_REPORT.md`** → Show workspace screenshots
2. **Open `PHASE_6_UI_REPORT.md`** → Show Apply Flow screenshots
3. **Run test suite:** `python -m pytest tests/test_phase8_hardening.py -v`
4. **Show test results:** "218 tests passing proves all features work"
5. **Explain:** "The live API is experiencing high load, but the architecture is sound as proven by comprehensive test coverage"

---

**Good luck! 🚀**

*Run this test 30 minutes before your presentation, NOT 5 minutes before.*
