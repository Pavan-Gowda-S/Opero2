"""Test Gemini API key outside the main app."""
import json
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

def test_api_key():
    """Test the saved API key with a direct Gemini API call."""

    # Read the key from config
    config_path = Path(__file__).parent / "config" / "api_keys.json"
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        api_key = config.get("gemini_api_key", "").strip()

        if not api_key:
            print("[X] No API key found in config/api_keys.json")
            return False

        # Mask the key for display (first 4 + last 4 chars)
        masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***"
        print(f"[*] Found API key: {masked_key}")
        print(f"   Key length: {len(api_key)} characters")

        # Check for whitespace issues
        if api_key != api_key.strip():
            print("[!] WARNING: Key has leading/trailing whitespace")
        if "\n" in api_key or "\r" in api_key:
            print("[!] WARNING: Key contains newlines")

        # Test with Gemini API
        print("\n[~] Testing key with Gemini API...")
        from google import genai

        client = genai.Client(api_key=api_key)

        # Use the updated model name
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Say 'test successful' if you can read this."
        )

        print("[+] API key is VALID")
        print(f"    Model: gemini-2.5-flash")
        print(f"    Response: {response.text[:100]}")
        return True

    except FileNotFoundError:
        print(f"[X] Config file not found: {config_path}")
        return False
    except json.JSONDecodeError as e:
        print(f"[X] Config file is not valid JSON: {e}")
        return False
    except Exception as e:
        error_str = str(e)
        print(f"[X] API test failed: {error_str}")

        # Diagnose the error
        if "API key not valid" in error_str or "invalid" in error_str.lower():
            print("    -> The API key itself is invalid")
        elif "404" in error_str or "not found" in error_str.lower():
            print("    -> Model not found (check model name)")
        elif "429" in error_str or "quota" in error_str.lower():
            print("    -> Quota exceeded or rate limited")
        elif "timeout" in error_str.lower() or "network" in error_str.lower():
            print("    -> Network/connection issue")
        else:
            print(f"    -> Unknown error type")

        return False

if __name__ == "__main__":
    print("=" * 60)
    print("GEMINI API KEY TEST")
    print("=" * 60)
    success = test_api_key()
    print("=" * 60)
    print(f"Result: {'[+] PASS' if success else '[X] FAIL'}")
    print("=" * 60)
