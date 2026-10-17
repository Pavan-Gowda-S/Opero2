# OPERO END-TO-END TEST PLAN
**Date:** 2026-10-13  
**Purpose:** Verify all fixes for issues A-D and stability problems

---

## PREREQUISITES

### Manual Setup Required
1. **API Keys** - Verify in `config/api_keys.json`:
   - `gemini_api_key` (required for all AI features)
   - `assemblyai_key` (optional, for AssemblyAI voice input)
   - `newsapi_key` (optional, for news briefings)

2. **OS Permissions**:
   - **Windows**: No special permissions needed
   - **macOS**: Grant Accessibility permissions for keyboard/mouse control
   - **Linux**: Install `wmctrl` or `xdotool` for window focus

3. **Python Packages** - Run: `pip install -r requirements.txt`

4. **WhatsApp Desktop** - Install from Microsoft Store (for messaging tests)

5. **Browser** - Any modern browser for web automation tests

---

## TEST SUITE

### A. TASK AUTOMATION (Multi-step workflows)

#### Test A1: Simple Command Sequence
**Objective:** Verify agent loop executes multiple commands  
**Steps:**
1. Start OPERO
2. Say: "Use dev_agent in agent mode to run these commands: 'python --version', 'pip list'"
3. Verify each command executes
4. Check output logs show both results

**Expected:** Both commands execute successfully, output displayed

---

#### Test A2: Git Workflow with Confirmation
**Objective:** Verify destructive commands require confirmation  
**Steps:**
1. Create a test git repo: `mkdir test_repo && cd test_repo && git init`
2. Add a file: `echo "test" > test.txt`
3. Say: "Use dev_agent agent mode to: git add test.txt, git commit -m 'test', git push"
4. Verify confirmation dialog appears before git push
5. Deny the push, verify it stops

**Expected:** 
- git add and commit succeed
- Confirmation dialog shown for git push
- Loop stops when denied

---

#### Test A3: Retry on Failure
**Objective:** Verify agent loop retries after auto-fixing dependency errors  
**Steps:**
1. Create Python file missing `requests`: `import requests; requests.get('http://example.com')`
2. Say: "Run this file in agent mode"
3. Verify auto-install of requests
4. Verify retry succeeds after install

**Expected:** Auto-detects missing module, installs, retries, succeeds

---

### B. WHATSAPP (Send + Read Capability)

#### Test B1: Send Message with Confirmation
**Objective:** Verify WhatsApp send flow completes  
**Steps:**
1. Open WhatsApp Desktop and sign in
2. Say: "Send a WhatsApp message to [contact name]: 'Test from OPERO'"
3. Verify OPERO confirms recipient and message
4. Approve and verify message appears in WhatsApp

**Expected:** 
- WhatsApp opens
- Contact searched
- Message typed and sent
- Confirmation message includes note about delivery verification

---

#### Test B2: Read Chat History Request
**Objective:** Verify OPERO correctly states read limitation  
**Steps:**
1. Say: "Read my last 5 WhatsApp messages from [contact]"
2. Verify OPERO explains Desktop automation cannot read chats
3. Verify suggestion to check manually

**Expected:** Clear explanation of technical limitation, no false promise

---

### C. SYSTEM ACCESS (Tools + Memory)

#### Test C1: File Operations
**Objective:** Verify file_controller works across operations  
**Steps:**
1. Say: "Create a text file on desktop called test_opero.txt with content 'Hello OPERO'"
2. Say: "Read the file test_opero.txt from desktop"
3. Say: "Move test_opero.txt to downloads folder"
4. Say: "Delete test_opero.txt from downloads"

**Expected:** All operations succeed, file appears/moves/deletes correctly

---

#### Test C2: Safe Shell Commands
**Objective:** Verify safe_shell allowlist and confirmation  
**Steps:**
1. Say: "Run git status in my home directory"
2. Verify command executes (read-only, no confirmation)
3. Say: "Run rm -rf *" 
4. Verify command rejected (not in allowlist)

**Expected:** 
- Allowed commands execute
- Dangerous commands blocked with explanation

---

#### Test C3: Persistent Memory Across Sessions
**Objective:** Verify memory survives restart  
**Steps:**
1. Say: "Remember my favorite color is blue"
2. Close OPERO completely
3. Restart OPERO
4. Say: "What's my favorite color?"

**Expected:** OPERO recalls "blue" from previous session

---

#### Test C4: Scheduler Creation
**Objective:** Verify recurring task scheduling  
**Steps:**
1. Say: "Schedule a task to remind me to stretch every 60 minutes"
2. Verify confirmation dialog
3. Say: "List my scheduled tasks"
4. Verify task appears enabled

**Expected:** 
- Task created with user confirmation
- Listed in scheduler with correct interval

---

### D. PROACTIVE ACTIONS (Background + Scheduled)

#### Test D1: Background Topic Monitoring
**Objective:** Verify existing background monitor still works  
**Steps:**
1. Say: "Monitor AI news for me"
2. Wait 5 minutes (or manually trigger background check)
3. Verify OPERO announces when check runs

**Expected:** Topic added, background loop checks daily

---

#### Test D2: Scheduled Task Execution
**Objective:** Verify scheduler actually runs tasks  
**Steps:**
1. Create a 2-minute test task: "Schedule task: log 'test' every 2 minutes"
2. Wait 2+ minutes
3. Check if task ran (check logs or UI notification)

**Expected:** Task executes at specified interval

---

### E. STABILITY FIXES

#### Test E1: Wake Word State Visibility
**Objective:** Verify user knows when OPERO is asleep  
**Steps:**
1. Enable wake word mode
2. Wait for auto-sleep (2 minutes of silence)
3. Verify UI shows "SLEEPING" state clearly
4. Type a command → verify rejection message mentions wake word

**Expected:** Clear sleep state indicator, helpful rejection message

---

#### Test E2: Echo Tail Adjustment
**Objective:** Verify reduced false interruptions  
**Steps:**
1. Ask OPERO to speak a long answer (30+ seconds)
2. Stay silent during answer
3. Verify OPERO completes without self-interrupting

**Expected:** Full answer delivered, no premature stops

---

#### Test E3: Model Name Update
**Objective:** Verify connection uses current model  
**Steps:**
1. Start OPERO
2. Check log for connection message
3. Verify shows `gemini-2.0-flash-exp` not `3.1-flash-live-preview`

**Expected:** Log shows updated model name, connection succeeds

---

## VERIFICATION CHECKLIST

- [ ] A1: Simple command sequence executed
- [ ] A2: Git workflow confirmation works
- [ ] A3: Dependency auto-fix and retry works
- [ ] B1: WhatsApp send completes with confirmation
- [ ] B2: Read limitation explained correctly
- [ ] C1: File operations (create/read/move/delete) work
- [ ] C2: Safe shell allowlist enforced
- [ ] C3: Memory persists across restarts
- [ ] C4: Scheduler creates authorized tasks
- [ ] D1: Background monitoring works
- [ ] D2: Scheduled tasks execute
- [ ] E1: Wake word state visible
- [ ] E2: Echo tail reduced interruptions
- [ ] E3: Model name updated

---

## KNOWN LIMITATIONS (NOT FIXABLE)

### WhatsApp Read Capability
**Why:** WhatsApp Desktop is a native app with no DOM access. Alternatives:
- WhatsApp Web + Selenium (violates ToS, risk of account ban)
- Official Business API (requires business account + approval)
- OCR on screenshots (unreliable for scrolling, multi-language)

**Recommendation:** Document as "send-only by design" for ToS compliance

---

### Scheduled Task Precision
**Why:** Checks run every ~60 seconds, tasks fire when interval elapsed
- 5-minute task may run at 4:58 or 5:02
- Not suitable for second-precision timing

---

### Shell Command Restrictions
**Why:** Security by design - only allowlisted commands permitted
- Cannot run arbitrary scripts without adding to allowlist
- Destructive operations always require confirmation
- Protects user from malicious/accidental damage

---

## TROUBLESHOOTING

### "API key invalid"
→ Check `config/api_keys.json` has valid `gemini_api_key`

### "PyAutoGUI not installed"
→ Run: `pip install pyautogui`

### "WhatsApp Desktop not found"
→ Install from Microsoft Store / whatsapp.com

### "Safe_shell command not allowed"
→ Command not in allowlist. Use file_controller or computer_control for most tasks

### Memory not persisting
→ Check `memory/long_term.json` exists and is writable
→ Verify OPERO has write permissions in project directory

---

## SUCCESS CRITERIA

**All fixes implemented successfully if:**
1. ✅ A: Agent loop executes multi-step workflows with retry logic
2. ✅ B: WhatsApp send completes reliably (read limitation documented)
3. ✅ C: File ops + shell + memory + scheduler all functional
4. ✅ D: Background monitor + new scheduler both work
5. ✅ E: Model updated, echo improved, state visible

**OPERO now demonstrates:**
- **Task chaining:** Run sequences like build → test → commit
- **Persistent memory:** Recalls facts across restarts  
- **Scheduled actions:** User-authorized recurring tasks
- **Safe automation:** Confirmation gates on destructive ops
- **Clear boundaries:** Honest about what it can/cannot do
