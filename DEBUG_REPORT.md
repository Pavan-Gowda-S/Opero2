# OPERO Debug Report
**Date:** 2026-10-11  
**Status:** Issues Identified and Fixed

## Issues Found & Fixed

### 1. **Missing API Keys Configuration File**
**Location:** `config/api_keys.json`  
**Root Cause:** The application expects `config/api_keys.json` but only `api_keys.example.json` exists.  
**Impact:** App cannot start without valid configuration.  
**Fix:** Create `config/api_keys.json` from the example template with placeholder keys.

### 2. **Echo Guard State Leak in Barge-In Logic**
**Location:** `main.py:1519-1528` (echo tail handling)  
**Root Cause:** The echo guard's history (`_echo._hist`) is cleared immediately when the tail expires, but if a user speaks during the tail window, their voice is correctly identified and `_tail_until` is set to 0.0. However, the history is then cleared on the NEXT callback (line 1527-1528), meaning subsequent frames have no echo reference and may incorrectly pass through as "user speech" even when they're still our own echo.  
**Impact:** False positives in voice detection → assistant responds to its own voice → constant interruptions.  
**Fix:** Only clear echo history when the tail has FULLY expired AND no echo is currently playing.

### 3. **Vision Cooldown Race Condition**
**Location:** `main.py:1332-1342` (_execute_tool screen_process)  
**Root Cause:** `_vision_busy` is set before the async capture, but if two rapid `screen_process` calls arrive (e.g., user says "what's on screen" twice), the second call checks `_vision_busy` BEFORE the first has completed its capture, sees it's False, and both proceed. The cooldown check (`_vision_last_time`) uses `monotonic()` but doesn't update it until AFTER the capture completes, creating a race window.  
**Impact:** Duplicate vision captures, wasted API calls, confused responses.  
**Fix:** Set `_vision_last_time` BEFORE starting the async capture, not after.

### 4. **AssemblyAI Duplicate Final Transcript Delivery**
**Location:** `core/assemblyai_voice.py:114-127` (_accept_final)  
**Root Cause:** The duplicate detection window is 1 second, but AssemblyAI's WebSocket can redeliver finals across multiple seconds during reconnections or network jitter. The `_recent_finals` dict is pruned to keep only the last second, but a redelivery arriving 1.1 seconds later will be accepted as new.  
**Impact:** Commands execute twice (e.g., "open browser" opens two browser windows).  
**Fix:** Extend the deduplication window to 5 seconds and increase buffer size to 20 entries.

### 5. **Audio Queue Full - No Backpressure**
**Location:** `main.py:1540-1543` (mic callback), `main.py:1669-1673` (receive audio)  
**Root Cause:** When `out_queue` is full (maxsize=200), the mic callback silently drops audio via `put_nowait()` + `except QueueFull`. Similarly, the receive loop drops incoming audio chunks when `audio_in_queue` is full. There's no backpressure mechanism to slow down the sender.  
**Impact:** Audio dropout → transcripts are incomplete → commands are misunderstood or ignored.  
**Fix:** 
- Increase `out_queue` maxsize from 200 to 500 (buys ~2.5 seconds at 16kHz)
- Increase `audio_in_queue` default size (currently unbounded, but should be bounded for memory safety)
- Log queue-full events so they're visible in diagnostics

### 6. **Interrupted Flag Cleared Too Early**
**Location:** `main.py:1707-1711` (turn_complete handling)  
**Root Cause:** When a turn completes after an interruption, `_interrupted` is cleared and buffers are reset. But if the user interrupts DURING a tool call (not just during speech), the tool response still arrives and triggers a turn_complete, clearing the flag before the model has finished draining queued audio from the interrupted turn.  
**Impact:** Partial responses leak through after interruption.  
**Fix:** Only clear `_interrupted` when `audio_in_queue` is actually empty, confirming all queued audio from the interrupted turn has been discarded.

### 7. **Wake Word Detector Queue Overflow**
**Location:** `core/wake_word.py:169-181` (feed method)  
**Root Cause:** The wake detector's queue (maxsize=50) drops frames when full, but at 16kHz with 1024-sample chunks (~64ms each), 50 frames = 3.2 seconds. If the inference thread is slow or blocked, the queue fills and detection becomes unreliable.  
**Impact:** "Hey Opero" fails to wake the assistant intermittently.  
**Fix:** Increase queue size to 100 frames (~6.4s buffer) and add a warning log when >80% full.

### 8. **Gemini Live Connection Backoff Not Persistent**
**Location:** `main.py:2467-2476` (connection retry logic)  
**Root Cause:** `_conn_backoff` is stored as an instance variable but isn't initialized in `__init__`, so on the first connection failure it defaults to `getattr(self, "_conn_backoff", 3)` = 3s. However, after a successful connection and subsequent failure, `_conn_backoff` may have been set to a high value (e.g., 60s), and a quick voice-engine switch resets it via `_on_voice_engine_change` but doesn't reset the backoff.  
**Impact:** After one network failure, all subsequent reconnects wait 60 seconds even if the network is back.  
**Fix:** Initialize `_conn_backoff = 3` in `__init__` and reset it to 3 on successful connection.

### 9. **Phone Audio Relay Deadlock Risk**
**Location:** `main.py:2169-2186` (_relay_phone_audio)  
**Root Cause:** The phone relay waits on `_dashboard._phone_audio_queue.get()` with a 1-second timeout. If the dashboard is None or the queue doesn't exist (optional dependency), this raises AttributeError on every iteration.  
**Impact:** Crashes the relay task, silently breaking phone input.  
**Fix:** Check `_dashboard` and queue existence before entering the relay loop, exit cleanly if unavailable.

### 10. **Session Log Unbounded Growth**
**Location:** `main.py:606-608` (_session_log list)  
**Root Cause:** `_session_log` accumulates every turn of the conversation for end-of-session summarization, but it's never capped. A long conversation (100+ turns) grows the list indefinitely in memory.  
**Impact:** Memory leak over long sessions.  
**Fix:** Cap `_session_log` at 100 most recent turns (keep only the tail during append).

## Verification Steps (To Be Run After Fixes)

1. **Environment Check:**
   ```bash
   python --version  # Should be 3.11-3.13
   pip list | grep -E "PyQt6|sounddevice|google-genai|assemblyai"
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API Keys:**
   - Edit `config/api_keys.json`
   - Add valid Gemini API key
   - (Optional) Add AssemblyAI key for alternate voice engine

4. **Run Startup Test:**
   ```bash
   python main.py
   ```
   - Should open UI without errors
   - Check console for "OPERO online" message
   - Verify no repeated error messages in log

5. **Voice Command Test Sequence:**
   - "What time is it?" (basic command)
   - "What's on my screen?" (vision tool)
   - Wait for response, then interrupt mid-sentence with "Stop" (barge-in)
   - "Open calculator" (system action)
   - (If AssemblyAI configured) Switch voice engine in settings, test same commands

6. **Expected Behavior:**
   - Commands should execute once, not twice
   - Interruptions should stop speech cleanly within 200ms
   - No self-responses (assistant answering itself)
   - Console shows clean command logs, no queue-full warnings under normal use

## Files Modified
- `main.py` (8 fixes)
- `core/assemblyai_voice.py` (1 fix)
- `core/wake_word.py` (1 fix)
- `config/api_keys.json` (created)

## Next Steps
- Run full test suite: `pytest tests/ -v`
- Monitor real-world usage for recurring issues
- Check browser automation: `python -m playwright install chromium`
