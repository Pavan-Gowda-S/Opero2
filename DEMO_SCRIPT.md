# Opero2 × TinyFish Integration — Live Demo Script

**Date:** 2026-10-17  
**Duration:** ~8 minutes (3 scenarios)  
**Preparation Time:** 5 minutes  
**Presenter:** [Your Name]

---

## Pre-Demo Checklist (5 minutes before start)

### Environment Setup
```bash
# 1. Start Opero2
cd C:\Users\Pavan Gowda S\OneDrive\Desktop\Projects\The-Opero
python main.py

# 2. Verify TinyFish service is ready
cd tinyfish_service
npm install  # If first time
node --env-file=../.env index.js search --query="test" --limit=1

# 3. Check API keys loaded
# - Verify .env has TINYFISH_API_KEY
# - Verify config/api_keys.json has gemini_api_key
```

### Pre-Flight Checks
- [ ] Opero window opened in center of screen (not maximized - better for screen recording)
- [ ] TinyFish mode toggle visible in header
- [ ] Voice input working (say "Opero, what time is it?" to test)
- [ ] System audio output at comfortable level
- [ ] Browser window ready but minimized (for Apply Flow demo)
- [ ] PDF viewer closed (will open fresh during export demo)
- [ ] Screen recording software ready (OBS, QuickTime, etc.)

### Demo Safety Notes
- **TinyFish credits:** Each agent run costs ~$0.10-$1.00. Have 3-5 credits minimum.
- **Timeout handling:** Agent operations may take 2-4 minutes. Do NOT refresh.
- **Fallback plan:** If TinyFish API fails, show pre-recorded screenshots from `PHASE_*_REPORT.md` files.

---

## Demo Introduction (30 seconds)

**[Screen: Opero main window, TinyFish mode OFF]**

**Script:**
> "Welcome! Today I'm demonstrating Opero2 with TinyFish integration—a voice-controlled AI assistant with advanced web research and automated form-filling capabilities.
>
> I'll show three scenarios:
> 1. Intelligent web research with source citations
> 2. One-click PDF report generation
> 3. Automated job application with safety gates
>
> Let's begin by enabling TinyFish mode."

**Action:** Click TinyFish toggle in header → mode switches ON  
**Expected:** Right panel switches from activity log to Agent Timeline widget  
**Timing:** 5 seconds

---

## Scenario 1: Intelligent Web Research (3 minutes)

### Part A: Quick Search (60 seconds)

**[Screen: TinyFish workspace with Quick Search tab]**

**Script:**
> "First, a quick search. I'll ask Opero to research the latest AI breakthroughs."

**Voice Command (speak clearly):**
> "Opero, search for latest breakthroughs in agentic AI."

**Alternative Text Command (if voice fails):**
Type in chat: `search for latest breakthroughs in agentic AI`

**Expected UI Reaction (within 3-5 seconds):**
1. TinyFish workspace panel expands from bottom
2. Quick Search tab auto-selected
3. Status indicator changes: `READY` → `SEARCHING...`
4. Progress bar appears (indeterminate pulse)
5. Cancel button becomes visible
6. Agent Timeline shows: `◐ PENDING` → `◉ RUNNING`

**Expected Results (15-30 seconds):**
1. 3-5 result cards appear in Quick Search tab
2. Each card shows:
   - Title (blue, clickable-looking)
   - URL (gray, small font)
   - Snippet (white text)
3. Status returns to `READY`
4. Progress bar hides
5. Agent Timeline shows: `● COMPLETED ✓`
6. Export toolbar appears at bottom

**Narration during wait:**
> "Notice the live agent timeline on the right tracking the search operation. The agent is querying TinyFish's web index in real-time."

**On completion:**
> "We now have curated results with clean snippets. Each card links to the original source."

**Troubleshooting:**
- **If timeout (>60s):** "The search is taking longer than expected. In production, we'd show cached results. Let me move to the next demo."
- **If error:** "We're hitting a rate limit. This is expected behavior—the system shows clear error messages instead of crashing."

### Part B: Deep Research (90 seconds)

**Script:**
> "Now let's trigger a deep research query for more comprehensive analysis."

**Voice Command:**
> "Opero, deep research on Claude AI and multi-agent systems."

**Alternative Text:**
Type: `research Claude AI and multi-agent systems`

**Expected UI Reaction (immediate):**
1. Workspace auto-switches to "Deep Research" tab
2. Status: `SEARCHING...`
3. Agent Timeline updates: `PENDING` → `RUNNING`

**Expected Results (30-60 seconds):**
1. Deep Research tab populates with formatted markdown content
2. Content includes:
   - Executive summary paragraph
   - Bullet points with key findings
   - Numbered source citations
3. Export toolbar appears
4. Timeline shows: `COMPLETED`

**Narration during wait:**
> "Deep research synthesizes information from multiple sources and generates a structured report with citations."

**On completion:**
> "The system has compiled a comprehensive overview with inline citations. This is perfect for research tasks."

---

## Scenario 2: One-Click PDF Export (90 seconds)

**[Screen: Deep Research results visible from Scenario 1]**

**Script:**
> "Let's export this research as a professional PDF report."

**Action:** Click `📋 PDF` button in export toolbar

**Expected UI Reaction (within 2 seconds):**
1. Button momentarily disabled
2. Brief activity log message: "Generating PDF report..."
3. PDF viewer opens automatically (system default)

**Expected Result:**
PDF displays with:
- **Header:** "Deep Research: Claude AI and multi-agent systems"
- **Timestamp:** Current date/time
- **Executive Summary:** First paragraph of content
- **Content:** Full research text, formatted
- **Sources Section:** URLs listed if available
- **Footer:** "Generated by Opero2 × TinyFish | [timestamp]"

**Narration:**
> "The PDF includes our entire research summary with professional formatting. Notice the automatic timestamp and source citations at the bottom.
>
> This report is ready to attach to emails or share with colleagues."

**Optional Enhancement:** Click `💬 WhatsApp` button  
**Result:** WhatsApp Desktop opens (if installed), PDF is ready to attach

**Troubleshooting:**
- **If PDF doesn't open:** "The PDF was generated successfully at reports/[filename].pdf. Let me open it manually." [Open from file browser]
- **If generation fails:** "PDF generation requires write permissions. The text content is still available in the workspace."

---

## Scenario 3: Opportunity Discovery & Safety Gates (3.5 minutes)

### Part A: Opportunity Search (60 seconds)

**[Screen: Switch to Apply Flow tab]**

**Script:**
> "Now for the centerpiece demo: automated job applications with safety gates. Let's find Python AI internships."

**Action:** Click "🎯 Apply Flow" tab

**Expected UI:**
1. Apply Flow search bar appears
2. Profile indicator shows: "Profile: Loading..."
3. Empty opportunity list

**Action:** Type in Apply Flow search: `Python AI internship`  
**Action:** Click `🔍 Find Matches`

**Expected Results (20-40 seconds):**
1. Status: `SEARCHING...`
2. Timeline: `RUNNING`
3. 2-4 opportunity cards appear, each showing:
   - Title (e.g., "Python AI/ML Intern")
   - Organization (e.g., "Google AI Research")
   - Match score badge (e.g., "94% Match" in green)
   - Match rationale (e.g., "💡 Matches your Python and Gemini experience")
   - Deadline & location
   - `[📝 Review & Apply]` button

**Narration during wait:**
> "The system is searching job boards and ranking opportunities based on skills match. Each result gets a match score explaining why it fits."

**On completion:**
> "Here we have ranked opportunities. The 94% match at the top aligns perfectly with my profile skills."

### Part B: Pre-Fill Review (90 seconds)

**Script:**
> "Let's apply to this top match. Watch what happens when I click Review & Apply."

**Action:** Click `[📝 Review & Apply]` on the highest-match card

**Expected Result (immediately):**
Large modal dialog appears: "Application Pre-Fill Review: [Title]"

**Dialog Contents:**
1. **Header:** Opportunity title in blue
2. **Target URL:** Full application URL displayed
3. **Field Mapping Table:**
   ```
   Field Name          | Proposed Value       | Source/Confidence
   ────────────────────┼─────────────────────┼──────────────────
   Full Name           | John Doe            | Profile (100%)
   Email               | john@example.com    | Profile (100%)
   Phone               | +1-555-0123         | Profile (100%)
   Resume              | resume_2024.pdf     | file_processor (100%)
   LinkedIn            | linkedin.com/in/... | Profile (100%)
   Why are you inter...| I am excited about...| Generated (85%)
   ```
4. **Generated Cover Note:** Scrollable text box with tailored message
5. **Safety Warning Box (yellow border):**
   ```
   ⚠️ Safety Rule: Pre-Fill Only, Manual Submit Required
   
   The agent will navigate to the form, fill in all fields with the
   values shown above, and STOP immediately before the final submit
   button. You must review the pre-filled form in the browser window
   and click Submit yourself to complete the application.
   ```
6. **Buttons:** `[Cancel]` (gray) | `[Proceed to Pre-Fill]` (blue)

**Narration (point to each section):**
> "This is our safety gate. Before any automation happens, we see:
> 
> 1. The exact field-value pairs that will be filled
> 2. Confidence scores for each field
> 3. The generated cover note
> 4. And most importantly: this warning that the agent will STOP before clicking submit.
>
> This prevents accidental submissions. Let's proceed."

**Action:** Click `[Proceed to Pre-Fill]`

### Part C: Agent Pre-Fill Execution (60 seconds)

**Expected UI Reaction (immediately):**
1. Dialog closes
2. Agent Timeline activates: `◉ RUNNING`
3. Timeline entries appear sequentially:
   - "Navigating to application form"
   - "Filling applicant details"
   - "Attaching resume"
   - "● HALTED BEFORE SUBMIT: Ready for manual review"

**Expected Result (30-60 seconds):**
1. Browser window opens showing the application form
2. Fields are pre-filled with values from review dialog
3. Submit button is visible but NOT clicked
4. Timeline shows: `● COMPLETED` or `⊗ CANCELLED`
5. Banner appears in workspace:
   > "Form pre-filled! Please check the browser window and click Submit yourself."

**Narration during execution:**
> "The agent is now opening the application page and filling in our details. Watch the timeline for progress updates.
>
> [When browser opens]
> Perfect! The form is pre-filled. Notice the submit button is untouched—we maintain full control over the final submission."

**Safety Demonstration:**
> "This architecture enforces multiple safety layers:
> 1. Pre-execution review with explicit field mapping
> 2. Payment form detection and blocking
> 3. Agent instruction to halt before submit
> 4. Manual confirmation required for final submission
>
> The user always has the last word."

**Troubleshooting:**
- **If agent times out:** "The agent operation exceeded its timeout. This is a safety feature—long-running operations don't silently continue forever."
- **If form detection fails:** "The agent couldn't locate the form structure. In production, we'd show a manual application link."
- **If payment form detected:** "This form requests payment information, which triggers an automatic block. Opero never handles financial transactions."

---

## Demo Conclusion (30 seconds)

**[Screen: Return to main Opero window]**

**Script:**
> "That completes our demo. We've seen:
>
> 1. Intelligent web research with TinyFish's advanced search
> 2. One-click PDF export for professional reports
> 3. Automated form filling with multi-layer safety gates
>
> The key innovation is the safety-first architecture: every consequential action requires explicit user confirmation, payment forms are blocked, and agents never click 'submit' automatically.
>
> Questions?"

**Optional: Show Architecture Diagram**
Open `PHASE_6_UI_REPORT.md` and scroll to the architecture diagram if technical questions arise.

---

## Backup Demo (If Live API Unavailable)

### Fallback Plan A: Screenshot Walkthrough
1. Open `PHASE_3_UI_REPORT.md` → show workspace screenshots
2. Open `PHASE_4_UI_REPORT.md` → show timeline screenshots
3. Open `PHASE_5_UI_REPORT.md` → show export toolbar
4. Open `PHASE_6_UI_REPORT.md` → show Apply Flow cards and review dialog

### Fallback Plan B: Test Suite Demonstration
```bash
# Show comprehensive testing
python -m pytest tests/ -v --tb=short

# Highlight key test files
python -m pytest tests/test_phase6_apply_flow.py -v
```

**Narration:**
> "While the live API is unavailable, our comprehensive test suite demonstrates all functionality. We have 192 passing tests covering search, agent operations, PDF export, and safety gates."

---

## Technical Q&A Preparation

### Expected Questions & Answers

**Q: "How much do TinyFish credits cost?"**  
A: "TinyFish operates on a consumption-based model. Quick searches are free, agent operations cost approximately $0.10-$1.00 per run depending on complexity. The system includes a credit guard warning before billable operations."

**Q: "What happens if the agent encounters a CAPTCHA?"**  
A: "TinyFish's stealth browser includes CAPTCHA detection. When encountered, the agent returns a clear error: 'CAPTCHA detected. Manual intervention required.' The user can then complete the form manually."

**Q: "Can the agent submit forms automatically?"**  
A: "No. This is a core safety guarantee. The agent fills form fields but is programmed to halt before any submit button. The user must review and manually complete the submission."

**Q: "What prevents the agent from making purchases?"**  
A: "Multiple layers: (1) Goal validation blocks purchase-related keywords. (2) Payment field detection blocks forms requesting credit cards or CVV. (3) The confirmation gate shows all fields before execution. (4) Agent instructions explicitly forbid clicking purchase/checkout buttons."

**Q: "How do you handle API rate limits?"**  
A: "The system catches rate limit errors from TinyFish and displays a clear message: 'TinyFish rate limit reached. Please wait a moment before trying again.' No crash, no confusion."

**Q: "Is the code open source?"**  
A: "The Opero2 integration code is available in this repository. TinyFish itself is a commercial API service, but the integration layer is fully transparent."

**Q: "What's the test coverage?"**  
A: "192 tests covering all features, with 100% passing. Tests are offline with mocks, so they run instantly without API credits. Key test files: test_phase3_workspace.py (search), test_phase4_timeline.py (agent lifecycle), test_phase5_ui_export.py (PDF generation), test_phase6_apply_flow.py (safety gates)."

**Q: "Does this work on Mac/Linux?"**  
A: "Yes. The code is cross-platform. The Node.js service runs on any OS with Node 18+. PDF export uses platform-specific open commands (open on Mac, xdg-open on Linux, startfile on Windows)."

**Q: "How long does a typical agent run take?"**  
A: "Quick searches: 5-15 seconds. Deep research: 30-60 seconds. Form pre-fill: 30-90 seconds depending on page complexity. All operations have configurable timeouts (default: 10 minutes)."

---

## Post-Demo Actions

### If Demo Successful
1. **Provide access to repository:**
   - Repository URL: [Your GitHub/GitLab link]
   - Documentation: `README.md` for setup
   - Architecture: `PROJECT_FINAL_REPORT.md` for complete overview

2. **Offer live access (if appropriate):**
   - Share `.env.example` for API key setup
   - Guide through `npm install` in tinyfish_service/
   - Run verification: `python -m pytest tests/ -q`

3. **Share recordings/screenshots:**
   - Export demo screen recording
   - Share PDF report samples from reports/
   - Provide phase report PDFs for reference

### If Demo Failed
1. **Collect logs for debugging:**
   ```bash
   # Copy last 100 lines of activity log
   python -c "from core.logger import get_logger; log = get_logger('main'); print(log.get_recent_logs(100))"
   ```

2. **Document failure mode:**
   - Exact error message displayed
   - Screenshot of error state
   - API response if available

3. **Provide offline artifacts:**
   - All `PHASE_*_REPORT.md` files
   - Test execution proof: `pytest --tb=short > test_output.txt`
   - Architecture diagrams from reports

---

## Demo Timing Breakdown

| Segment | Duration | Buffer |
|---------|----------|--------|
| Introduction | 30s | +10s |
| Scenario 1: Web Research | 3m | +30s |
| Scenario 2: PDF Export | 90s | +20s |
| Scenario 3: Apply Flow | 3.5m | +60s |
| Conclusion | 30s | +10s |
| **Total** | **8m** | **+2m buffer** |

**Recommended:** Rehearse once with timer. If running long, shorten Scenario 1 Deep Research wait by showing results earlier.

---

## Recording Settings (if recording for submission)

### OBS Studio Settings
- **Resolution:** 1920x1080 (1080p)
- **FPS:** 30 (smooth enough for UI, small file size)
- **Encoder:** x264 or NVENC
- **Bitrate:** 2500 kbps (good quality, manageable file size)
- **Audio:** Mix system audio (Opero TTS) + microphone
- **Hotkey:** F9 to start/stop recording

### Camera Position (if showing presenter)
- Small PIP (picture-in-picture) in bottom-right corner
- 20% screen size maximum
- Ensure it doesn't cover UI elements

### Screen Layout
```
┌─────────────────────────────────────────────────┐
│  Opero Window (centered, not maximized)        │
│  ┌──────────────────────────────────────────┐  │
│  │ ┌─────────────────────┬────────────────┐ │  │
│  │ │  Chat/Workspace     │  Agent Timeline │ │  │
│  │ │                     │  (Live Status)  │ │  │
│  │ │                     │                 │ │  │
│  │ └─────────────────────┴────────────────┘ │  │
│  └──────────────────────────────────────────┘  │
│                                   [Camera PIP]  │
└─────────────────────────────────────────────────┘
```

---

**End of Demo Script**  
**Version:** 1.0  
**Last Updated:** 2026-10-17
