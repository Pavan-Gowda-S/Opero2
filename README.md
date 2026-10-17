<div align="center">

# ◈ OPERO

### _A native voice-first desktop operator_

`VOICE` · `VISION` · `AUTOMATION` · `LOCAL CONTROL`

![Python](https://img.shields.io/badge/Python-3.11%2B-55c8ff?style=for-the-badge&logo=python&logoColor=white)
![Desktop](https://img.shields.io/badge/Desktop-PyQt6-20d67a?style=for-the-badge)
![Voice](https://img.shields.io/badge/Voice-Gemini%20Live-e0ad36?style=for-the-badge)
![Tests](https://img.shields.io/badge/Tests-218%20passed-4CAF50?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-9d7bff?style=for-the-badge)

<sub>OPERO listens, reasons, acts, and reports the verified result.</sub>

[**GET STARTED**](#-quick-start) · [**CAPABILITIES**](#-capabilities) · [**ARCHITECTURE**](#-system-architecture) · [**DEVELOPMENT**](#-development) · [**WHATSAPP**](#-whatsapp-call-assistant)

</div>

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│  OPERO // DESKTOP OPERATOR                                      STATUS: READY │
│  INPUT  voice · text · file · camera       OUTPUT  speech · UI · local action │
│  CORE   Gemini Live · AssemblyAI · Playwright · PyQt6 · local tool registry   │
└─────────────────────────────────────────────────────────────────────────────┘
```

> [!IMPORTANT]
> OPERO is designed to act, not merely describe how to act. It keeps consequential work visible and stops for review before final submissions or irreversible external actions.

---

## ◈ // WHY OPERO

Most assistants stop at advice. OPERO is designed to turn a spoken or typed request into an observable desktop result: opening an app, researching current information, processing a file, controlling a browser, preparing an application, or routing a voice interaction through a visual HUD.

OPERO is a **local desktop application**. Its interface, audio devices, files, browser automation, and WhatsApp Desktop controls remain on the machine. Cloud services are used only for capabilities you configure, such as Gemini or AssemblyAI.

---

## ◈ // QUICK START

### Prerequisites

| Requirement | Needed for | Notes |
| --- | --- | --- |
| Python 3.11–3.13 | Core application | Python 3.12 is recommended |
| Gemini API key | Default live voice experience | Enter on first launch or in OPERO settings |
| Node.js 18+ | WhatsApp bridge | Required only for WhatsApp pairing/call detection |
| Chrome or Edge | WhatsApp bridge runtime | The bridge discovers installed browsers; use `WA_CHROME_PATH` to override |

### Install

```powershell
git clone <your-repository-url>
cd "The Opero"
python setup.py
```

### Start

```powershell
python main.py
```

On first launch, OPERO guides you through API key configuration. All secrets stay local — `config/api_keys.json` is gitignored by default.

### Run Tests

```powershell
pip install -e ".[dev]"
python -m pytest tests/ -v
```

---

## ◈ // CAPABILITIES

| Capability | Typical request | Outcome |
| --- | --- | --- |
| Live web research | "Find internships matching my Python and AI experience." | Current links, ranked options, concise comparison |
| Application preparation | "Use my resume to fill this internship form." | Extracts details and fills fields; pauses before submission |
| Desktop control | "Set this image as my wallpaper." | Applies a local image or downloads a URL-based wallpaper |
| File processing | "Summarize this PDF" / "Convert this spreadsheet." | Reads, analyzes, transforms, or exports supported files |
| Vision | "What is on my screen?" | On-demand screen or camera analysis |
| Browser operation | "Open the docs and find the API section." | Browser navigation and page interaction |
| Call assistance | "Answer WhatsApp calls and say I'm busy." | QR pairing, bridge detection, and Desktop-call handling |
| Mini mode | Press F10 or click ◱ | Small draggable avatar widget (cat, face, emoji, Spider-Man) |
| Voice engines | Switch between Gemini Live and AssemblyAI | Real-time voice with multiple STT/TTS backends |
| Plugin system | Drop a Python file in `plugins/` | Auto-discovered, hot-loadable, with enable/disable |

> [!NOTE]
> **Operator rule:** OPERO reports verified tool results — it never claims an action occurred when it did not.

---

## ◈ // SYSTEM ARCHITECTURE

```mermaid
flowchart LR
    U[User: voice, text, file, camera] --> UI[PyQt6 HUD / OPERO UI]
    UI --> R[OperaLive runtime]
    R <--> GL[Gemini Live]
    R --> AR[Action registry]
    R --> PR[Plugin registry]
    R <--> MEM[Local memory & config]
    AR --> DESK[Desktop controls]
    AR --> WEB[Browser automation]
    AR --> FILES[File processor]
    AR --> SEARCH[Live web research]
    AR --> WA[WhatsApp call manager]
    WA <--> BRIDGE[WhatsApp Web bridge]
    R <--> DASH[Optional phone dashboard]
```

### Voice and action lifecycle

```mermaid
sequenceDiagram
    participant User
    participant HUD as OPERO HUD
    participant Runtime as OperaLive
    participant Model as Voice / LLM
    participant Tool as Action or Plugin
    User->>HUD: Speak, type, or drop a file
    HUD->>Runtime: Normalized input
    Runtime->>Model: Context + tool declarations
    Model-->>Runtime: Reply or tool call
    alt Tool required
        Runtime->>Tool: Execute local action
        Tool-->>Runtime: Verified result
        Runtime->>Model: Result context
    end
    Runtime-->>HUD: Speech, state, log, visual feedback
    HUD-->>User: Result
```

---

## ◈ // REPOSITORY MAP

```text
opero/
├── main.py                 # Entry point, OperaLive session, audio pipeline
├── ui.py                   # PyQt6 HUD, overlays, Automation Studio
├── whatsapp_call.py        # Bridge coordination and Desktop call detection
├── whatsapp_bridge/        # Node.js WhatsApp Web bridge and QR endpoint
│
├── core/                   # Voice, audio, vision, infrastructure
│   ├── gemini.py           # Gemini Live API client with model fallback
│   ├── llm_client.py       # Local LLM support (Ollama, OpenAI-compatible)
│   ├── action_loader.py    # Tool discovery, validation, and dispatch
│   ├── validator.py        # Input validation for tool parameters
│   ├── echo.py             # Content-based echo cancellation
│   ├── viseme.py           # Lip-sync viseme generation
│   ├── tts.py              # Multi-engine TTS (EdgeTTS, Kokoro, ElevenLabs)
│   ├── stt.py              # Multi-engine STT (Whisper, Vosk)
│   ├── wake_word.py        # Local "Hey opero" wake word detection
│   ├── confirm.py          # Human confirmation gate (forge-resistant token)
│   ├── logger.py           # Centralized logging configuration
│   ├── installer.py        # Auto-dependency installer
│   ├── avatar.py           # Avatar rendering (holographic orb)
│   └── prompt.txt          # AI behavior specification
│
├── actions/                # Self-registering tool modules (21+)
│   ├── browser_control.py  # Search, navigate, screenshot, form fill
│   ├── send_message.py     # WhatsApp, email, messaging
│   ├── file_ops.py         # Read, write, move, copy, delete
│   ├── computer_control.py # System commands, app control
│   ├── code_helper.py      # Code analysis and generation
│   ├── dev_agent.py        # Development task automation
│   └── ...                 # weather, reminders, flight finder, etc.
│
├── memory/
│   ├── config_manager.py   # Settings persistence (JSON + AES encryption)
│   └── memory_manager.py   # Long-term memory with search
│
├── dashboard/              # Local HTTP dashboard (FastAPI + WebSocket)
├── plugins/                # Drop-in extensions with hot-load
├── config/                 # Runtime config (gitignored)
├── tests/                  # Test suite (84 tests, pytest)
├── pyproject.toml          # Modern Python packaging
└── CONTRIBUTING.md         # Development guide
```

---

## ◈ // SYSTEM MAP

| Area | What OPERO provides | Primary component |
| --- | --- | --- |
| Voice | Gemini Live conversation, interruption, push-to-talk, wake word | `main.py`, `core/session.py` |
| Alternative voice | AssemblyAI streaming STT with TTS output | `core/assemblyai_voice.py` |
| Desktop | App launch, wallpaper, file tasks, system controls | `actions/` |
| Browser | Search, navigation, page reading, screenshots | `actions/browser_control.py` |
| Files | Documents, PDFs, images, spreadsheets, audio, video | `actions/file_processor.py` |
| WhatsApp | QR pairing, bridge events, call detection | `whatsapp_call.py`, `whatsapp_bridge/` |
| Automation | Visual trigger → logic → action maps | `ui.py` Automation Studio |
| Remote access | Optional phone dashboard with encrypted pairing | `dashboard/` |
| Mini mode | Draggable avatar widget (4 styles) | `ui.py` MiniModeWidget |
| Extensibility | Auto-discovered actions and plugins | `core/action_loader.py`, `plugins/` |

---

<a id="development"></a>
## ◈ // DEVELOPMENT

### Setup

```powershell
git clone <repo-url> && cd "The Opero"
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -e ".[dev]"
```

### Code Quality

```powershell
# Run all tests
python -m pytest tests/ -v

# Lint
ruff check .

# Type check
mypy .
```

### Adding a New Action

1. Create `actions/my_action.py`
2. Define a `TOOL` dict (name, description, JSON Schema parameters)
3. Optionally add a `VALIDATOR` dict for input validation
4. Implement `execute(params: dict) -> str`
5. The action is auto-discovered on next startup

```python
# actions/example.py
from core.logger import get_logger
from core.validator import validate_params

log = get_logger(__name__)

TOOL = {
    "name": "example_action",
    "description": "Does something useful",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "What to search for"},
        },
        "required": ["query"],
    },
}

VALIDATOR = {
    "query": [{"type": str, "required": True, "max_len": 500}],
}

def execute(params: dict) -> str:
    params = validate_params(params, VALIDATOR, "example_action")
    log.info("Running example_action with query=%s", params["query"])
    return f"Result for: {params['query']}"
```

### Adding a Plugin

Drop a Python file in `plugins/` following the template in `plugins/_template.py`. Plugins are hot-loaded — enable/disable without restart.

---

<a id="whatsapp-call-assistant"></a>
## ◈ // WHATSAPP CALL ASSISTANT

### Pairing flow

```mermaid
flowchart TD
    A[Start OPERO] --> B[Launch local WhatsApp bridge]
    B --> C{Already paired?}
    C -- No --> D[OPERO shows LINK WHATSAPP QR]
    D --> E[Phone: WhatsApp → Linked devices]
    E --> F[Scan QR]
    F --> G[Bridge reports connected]
    C -- Yes --> G
    G --> H[Monitor bridge + WhatsApp Desktop]
```

1. Start OPERO
2. Click **💬 LINK WHATSAPP** in the controls drawer (or wait for auto-prompt)
3. On your phone: **WhatsApp → Settings → Linked devices → Link a device**
4. Scan the QR code shown inside OPERO
5. Keep WhatsApp Desktop open for automated call controls

### Incoming call flow

```mermaid
flowchart LR
    I([Incoming call]) --> B{Bridge event?}
    B -- Yes --> D[Create call event]
    B -- No --> V[Inspect WhatsApp Desktop UI]
    D --> A{Auto-answer enabled?}
    A -- No --> P[Show Answer / Decline]
    A -- Yes --> Q[Click answer + speak message]
```

> [!WARNING]
> WhatsApp does not provide a public API for personal calls. OPERO uses a linked local session and Desktop UI automation, which must be tested on your machine.

---

## ◈ // VOICE ENGINES

| Engine | Use case | Setup |
| --- | --- | --- |
| Gemini Live | Low-latency bidirectional voice + native tool use | Configure Gemini key, choose a voice |
| AssemblyAI | Real-time transcription with alternate pipeline | Add `assemblyai_api_key`, switch engine in UI |

If AssemblyAI fails, OPERO falls back to the default engine automatically.

---

## ◈ // LOCAL CONFIGURATION

Configuration is stored at `config/api_keys.json` (gitignored):

```json
{
  "gemini_api_key": "",
  "assemblyai_api_key": "",
  "voice_engine": "opero",
  "whatsapp_auto_answer": false,
  "whatsapp_busy_message": "I am busy right now.",
  "moss_user_id": "123456"
}
```

---

## ◈ // TROUBLESHOOTING

| Symptom | Fix |
| --- | --- |
| Browser actions fail | Run `python -m playwright install chromium firefox` |
| AssemblyAI falls back | Re-enter API key and check microphone selection |
| QR panel never appears | Run `npm install` in `whatsapp_bridge/`, check Node.js |
| Caller hears nothing | Configure virtual audio device as WhatsApp's microphone |
| MOSS rejects submission | Use the numeric ID from Stanford MOSS registration |

---

## ◈ // SECURITY & RESPONSIBLE USE

- API keys, OAuth tokens, and WhatsApp sessions stay on your machine (`config/` is gitignored)
- Review recipients, form fields, and submissions before they leave your machine
- Dashboard is localhost-only with CORS, rate limiting, and security headers
- All tool parameters are validated before execution
- Human confirmation gate prevents irreversible actions

---

## ◈ // TINYFISH MODE

### What is TinyFish Mode?

TinyFish Mode extends Opero with advanced web research and browser automation capabilities through [TinyFish](https://tinyfish.ai), enabling intelligent opportunity discovery, automated form pre-filling, and comprehensive research with source citations—all with multi-layer safety gates.

**Key capabilities:**
- **Quick Search** - Fast web queries with ranked result cards
- **Deep Research** - Multi-source synthesis with citations and markdown formatting
- **Apply Flow** - Opportunity discovery, match scoring, and automated form pre-fill with halt-before-submit guarantee
- **Live Agent Timeline** - Real-time status tracking for all operations
- **PDF Export** - One-click professional reports with WhatsApp integration

### Setup

#### Prerequisites
- Node.js 18+ (required for TinyFish service)
- TinyFish API key ([get one at tinyfish.ai](https://tinyfish.ai))

#### Installation

1. **Install Node.js dependencies:**
```powershell
cd tinyfish_service
npm install
```

2. **Configure API key** (choose one method):

**Option A: Root `.env` file (recommended)**
```bash
# .env (in project root)
TINYFISH_API_KEY=your_api_key_here
```

**Option B: `config/api_keys.json`**
```json
{
  "gemini_api_key": "...",
  "tinyfish_api_key": "your_api_key_here"
}
```

3. **Verify service:**
```powershell
cd tinyfish_service
node --env-file=../.env index.js search --query="test" --limit=1
```

If successful, you'll see JSON output with search results.

### How to Use

#### Enabling TinyFish Mode

1. Launch Opero: `python main.py`
2. Click the **TinyFish toggle** in the header controls
3. The right panel switches to **Agent Timeline** widget
4. The bottom workspace expands with three tabs

#### Quick Search

**Voice command:**
```
"Opero, search for Python AI internships"
```

**Text command:**
```
search for Python AI internships
```

**Result:** 3-5 result cards with titles, URLs, and snippets appear in the Quick Search tab within 5-15 seconds.

#### Deep Research

**Voice command:**
```
"Opero, research latest developments in agentic AI"
```

**Text command:**
```
research latest developments in agentic AI
```

**Result:** Comprehensive markdown-formatted report with:
- Executive summary
- Key findings (bullet points)
- Numbered source citations
- Delivery time: 30-60 seconds

#### Apply Flow (Automated Form Pre-Fill)

**Step 1: Search for opportunities**
1. Switch to **🎯 Apply Flow** tab
2. Enter search: `Python AI internship` or `hackathons for students`
3. Click **🔍 Find Matches**

**Step 2: Review ranked results**
- Each opportunity card shows:
  - Match score badge (0-100%, color-coded)
  - Match rationale (why it fits your profile)
  - Deadline and location
  - **[📝 Review & Apply]** button

**Step 3: Pre-submission review**
- Click **[📝 Review & Apply]** on any opportunity
- **Pre-Fill Review Dialog** appears showing:
  - Exact field-value mappings (e.g., "Full Name: John Doe")
  - Confidence scores (Profile: 100%, Synthesized: 80%, Inferred: 50%)
  - Generated cover note (tailored to the opportunity)
  - **Safety warning:** Agent will halt before submit button

**Step 4: Confirm and pre-fill**
- Review all field mappings
- Click **[Proceed to Pre-Fill]**
- Agent opens browser, navigates to form, fills fields
- **Timeline shows: "● HALTED BEFORE SUBMIT: Ready for manual review"**

**Step 5: Manual submission**
- Review pre-filled form in browser window
- **You must manually click Submit** to complete application

### Workspace Features

| Feature | Tab | Purpose |
|---------|-----|---------|
| **Quick Search** | 🔍 Quick Search | Fast web queries, result cards with titles/URLs/snippets |
| **Deep Research** | 📚 Deep Research | Multi-source synthesis, markdown reports with citations |
| **Apply Flow** | 🎯 Apply Flow | Opportunity discovery, match scoring, form pre-fill |
| **Agent Timeline** | Right panel | Real-time status (IDLE → PENDING → RUNNING → COMPLETED) |
| **PDF Export** | Export toolbar | Generate professional PDF reports from any results |
| **WhatsApp Share** | Export toolbar | Share PDFs via WhatsApp Desktop |

### Safety Architecture

TinyFish Mode enforces a **4-layer safety system** to prevent unauthorized submissions and payment processing:

#### Layer 1: Pre-Execution Review (UI Gate)
- **Field Mapping Table** - Every field and value shown before execution
- **Confidence Scores** - Profile (100%), Synthesized (60-90%), Inferred (<60%)
- **Safety Warnings** - Explicit "halt before submit" guarantee
- **Explicit Confirmation** - User must click "Proceed to Pre-Fill"

#### Layer 2: Form Safety Validation
Runs before agent execution:
- **Payment Detection** - Blocks forms with: credit card, CVV, billing address fields
- **Goal Validation** - Blocks prohibited patterns:
  - Payment/purchase keywords
  - Account deletion/password changes
  - Social media posting
  - Data scraping
  - Mass operations
- **Required Field Check** - Halts if required fields are missing or unknown

#### Layer 3: Agent Runtime Constraint
- **Explicit Halt Instruction** - Agent goal includes: "DO NOT CLICK SUBMIT. STOP BEFORE THE FINAL SUBMIT BUTTON."
- **Timeline Updates** - Live status tracking shows each step
- **Stop Button** - User can cancel operation mid-execution

#### Layer 4: Post-Execution Safety Net
- **Submission Indicator Scan** - Checks for confirmation pages
- **Security Violation Logging** - Alerts if unauthorized submit detected
- **Browser State Verification** - Confirms form is still editable

**Safety Guarantees:**
- ✅ **Never auto-submit** - Agent always halts before final submit button
- ✅ **Never process payments** - Payment forms trigger immediate block
- ✅ **Never fabricate data** - Unknown fields flagged as "[UNKNOWN - User input needed]"
- ✅ **Always confirm** - Mandatory pre-execution review with exact field-value pairs

### Cost & Credit Information

| Operation | Cost | Notes |
|-----------|------|-------|
| Quick Search | **Free** | No TinyFish credits consumed |
| Deep Research | ~$0.05 - $0.20 USD | Varies by source count |
| Form Pre-Fill (Agent) | ~$0.10 - $1.00 USD | Remote browser automation |
| PDF Export | **Free** | Local generation, no API calls |

**Credit Guard:** Before billable agent operations, Opero displays:
```
⚠️ Estimated Cost: ~$0.10 - $1.00 USD (Remote Browser Agent)
This operation will use TinyFish credits from your account.
```

**Wallet Management:** Check balance and add funds at [tinyfish.ai/wallet](https://tinyfish.ai/wallet)

### Error Handling

TinyFish Mode provides **human-readable error messages** with clear next steps:

| Error | Meaning | Solution |
|-------|---------|----------|
| "TinyFish API key not found" | Missing configuration | Add `TINYFISH_API_KEY` to `.env` or `config/api_keys.json` |
| "TinyFish rate limit reached" | Too many requests | Wait 60 seconds before retrying |
| "Operation timed out" | Agent exceeded 10-minute limit | Remote agent may still be active; check TinyFish dashboard |
| "Navigation blocked: Safety filters triggered" | Prohibited goal pattern detected | Reformulate goal to avoid payment/account modification keywords |
| "CAPTCHA detected" | Site has bot protection | Complete CAPTCHA manually in browser window |
| "Payment form blocked" | Form requests credit card/billing | Apply manually—Opero never handles financial transactions |
| "Form structure changed" | Site redesign broke selectors | Apply manually at provided URL |

**No Stack Traces:** All user-facing errors are clean, actionable messages—never raw exceptions or HTTP codes.

### Troubleshooting

#### TinyFish service won't start
```powershell
cd tinyfish_service
npm install
node --env-file=../.env index.js search --query="test" --limit=1
```
If this fails, check:
- Node.js version: `node --version` (must be 18+)
- API key in `.env` file
- No firewall blocking Node.js

#### Search returns no results
- **Check API key:** Verify `TINYFISH_API_KEY` in `.env` or `config/api_keys.json`
- **Check rate limits:** Wait 60 seconds if you've made multiple requests
- **Check query:** Try a simpler, more general search term

#### Agent timeout
- **Expected behavior:** Complex forms may take 2-4 minutes
- **Remote execution:** Even if local UI times out, remote agent may still complete
- **Check status:** Use TinyFish dashboard to verify run completion

#### PDF export fails
- **Check permissions:** Ensure write access to `reports/` directory
- **Check dependencies:** Verify ReportLab installed: `pip list | grep reportlab`
- **Manual open:** PDF saved to `reports/Deep_Research_YYYYMMDD_HHMMSS.pdf`

#### WhatsApp share not working
- **Requires WhatsApp Desktop:** Install from [whatsapp.com/download](https://www.whatsapp.com/download)
- **Windows:** Uses `shell:AppsFolder\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App`
- **Mac/Linux:** Uses `open` / `xdg-open` with `whatsapp://` URI

### Responsible Use

- **Review before confirming:** Always check field mappings in Pre-Fill Review Dialog
- **Never use for payments:** Payment form blocking is enforced—apply manually for purchases
- **Verify agent-filled data:** Check browser window before manually clicking Submit
- **Keep API key secure:** Never share or commit your `TINYFISH_API_KEY`
- **Monitor credit usage:** Track consumption at [tinyfish.ai/wallet](https://tinyfish.ai/wallet)
- **Respect rate limits:** Wait between requests if you hit rate limit errors

---

## ◈ // LICENSE

See [LICENSE](LICENSE).
