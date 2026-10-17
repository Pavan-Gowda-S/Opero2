# TinyFish Service for Opero2

Node.js subprocess service that wraps the TinyFish SDK for Python integration.

## Architecture

This service runs as a subprocess called from Python's `actions/tinyfish_action.py`. It communicates via JSON on stdout/stderr.

## Operations

### Phase 2 (Completed)
- **Search**: Web search using TinyFish
- **Fetch**: Parallel content extraction from URLs

### Phase 3 (Current)
- **Agent**: Multi-step browser automation for browsing, navigation, and information extraction

**Phase 3 Safety Boundaries:**
- ✅ Permitted: Browsing pages, following links, clicking navigation buttons, extracting information
- ❌ Prohibited: Form submission, purchases, authentication, account changes, data modification

## Setup

### 1. Install Dependencies

From the repository root:

```bash
cd tinyfish_service
npm install
```

This installs `@tiny-fish/sdk@0.8.0` locally in this directory.

### 2. Configure API Key

The API key is already configured in the root `.env` file:

```bash
# Repository root: .env
TINYFISH_API_KEY=your_key_here
```

The Node.js service will automatically load this when called with `--env-file` by Python.

## Usage

### Command Line Interface

#### Agent Operation (Phase 3)
```bash
node index.js agent --url "https://example.com" --goal "Find the main headings and summarize" [--max-steps 50] [--max-duration-seconds 300] [--browser-profile lite]
```

**Options:**
- `--url` (required): Target URL to automate
- `--goal` (required): Natural language task description (max 5000 characters)
- `--max-steps` (optional): Maximum steps the agent can take (default: 50, max: 100)
- `--max-duration-seconds` (optional): Maximum duration in seconds (default: 300, max: 600)
- `--browser-profile` (optional): Browser profile - `lite` or `stealth` (default: lite)

**Example:**
```bash
node --env-file=../.env index.js agent --url "https://news.ycombinator.com" --goal "Extract the top 5 story titles"
```

**Safety Note:** The agent wrapper enforces Phase 3 restrictions. Goals requesting form submission, purchases, authentication, or data modification will be rejected.

#### Search Operation
```bash
node index.js search --query "artificial intelligence" [--location US] [--language en] [--max-results 10]
```

**Options:**
- `--query` (required): Search query string
- `--location` (optional): Country code for geo-targeting (e.g., "US", "GB")
- `--language` (optional): Language code (e.g., "en", "fr")
- `--max-results` (optional): Maximum results to return (default: 10)

**Example:**
```bash
node --env-file=../.env index.js search --query "Node.js tutorials"
```

#### Fetch Operation
```bash
node index.js fetch --urls "url1,url2,url3" [--format markdown] [--links] [--image-links] [--timeout 45000]
```

**Options:**
- `--urls` (required): Comma-separated list of URLs (1-10 URLs)
- `--format` (optional): Output format - `markdown`, `html`, or `json` (default: markdown)
- `--links` (optional): Include outbound links from pages
- `--image-links` (optional): Include image URLs from pages
- `--timeout` (optional): Per-URL timeout in milliseconds (default: 45000)

**Example:**
```bash
node --env-file=../.env index.js fetch --urls "https://example.com" --format markdown
```

#### Dry Run Mode

Test the CLI without making API calls:

```bash
node index.js search --query "test" --dry-run
node index.js fetch --urls "https://example.com" --dry-run
node index.js agent --url "https://example.com" --goal "test" --dry-run
```

**Important:** Agent operations are billable. Always test with `--dry-run` first.

### Output Format

All operations return JSON to stdout:

**Success:**
```json
{
  "success": true,
  "results": [...],
  ...
}
```

**Error:**
```json
{
  "success": false,
  "error": "Error message",
  "code": "ERROR_CODE"
}
```

## Python Integration

The Python action handler (`actions/tinyfish_action.py`) calls this service via subprocess:

```python
import subprocess
import json

# Agent operation example
result = subprocess.run(
    [
        "node", "--env-file=.env", "tinyfish_service/index.js", 
        "agent",
        "--url", "https://example.com",
        "--goal", "Extract the page title and main headings"
    ],
    capture_output=True,
    text=True,
    timeout=600  # Agent operations have longer timeout
)

response = json.loads(result.stdout)
```

## Security

- ✅ API key loaded from environment variable only
- ✅ Never logged or printed
- ✅ Not exposed in subprocess output
- ✅ Input validation on all parameters
- ✅ Safe error messages (no credential leakage)

## Error Handling

The service handles common errors gracefully:

- `AUTH_ERROR`: Invalid or missing API key
- `RATE_LIMIT`: Too many requests
- `SDK_ERROR`: TinyFish API error
- `UNKNOWN`: Unexpected error

## File Structure

```
tinyfish_service/
├── index.js              # CLI entry point
├── package.json          # Node.js dependencies
├── lib/
│   ├── client.js         # TinyFish SDK wrapper
│   ├── search.js         # Search operations
│   ├── fetch.js          # Fetch operations
│   ├── agent.js          # Agent operations (Phase 3)
│   └── validation.js     # Input validation
└── README.md             # This file
```

## Testing

Test without making API calls:

```bash
# Test agent (dry run)
node index.js agent --url "https://example.com" --goal "test task" --dry-run

# Test search (dry run)
node index.js search --query "test query" --dry-run

# Test fetch (dry run)
node index.js fetch --urls "https://example.com" --dry-run
```

**Live testing (uses TinyFish credits):**

⚠️ **Agent operations are billable and require explicit approval before testing.**

```bash
# Search (typically $0.001)
node --env-file=../.env index.js search --query "Node.js"

# Fetch (free tier)
node --env-file=../.env index.js fetch --urls "https://example.com"

# Agent (pricing varies by complexity, typically $0.10-$1.00 per run)
# DO NOT RUN without explicit user approval
# node --env-file=../.env index.js agent --url "..." --goal "..."
```

## Requirements

- Node.js ≥18 (verified: v24.21.0)
- `@tiny-fish/sdk@0.8.0` (installed via npm)
- Valid TinyFish API key in `.env`

## Limitations

- Maximum 10 URLs per fetch operation (TinyFish API limit)
- Search queries limited to 2000 characters
- Agent goals limited to 5000 characters
- Agent operations timeout after SDK client timeout (60s) or agent-specific max duration
- **Phase 3 agent restrictions**: No form submission, purchases, authentication, or data modification
- Agent prohibition detection is basic pattern matching; complex goals may bypass detection
- The TinyFish SDK cannot enforce all interaction restrictions programmatically
