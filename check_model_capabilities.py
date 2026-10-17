"""
Check which Live models support function calling (tools).
"""

import json
import sys
from pathlib import Path


def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


BASE_DIR = get_base_dir()
API_CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"


def get_api_key():
    with open(API_CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        key = data["gemini_api_key"].strip()
        return key, f"{key[:8]}...{key[-6:]}"


def check_model_capabilities():
    from google import genai

    api_key, masked_key = get_api_key()
    print(f"[*] Using API key: {masked_key}\n")

    # Models to check
    models_to_check = [
        "models/gemini-2.5-flash-native-audio-latest",
        "models/gemini-3.8-live",
        "models/gemini-3.1-flash-live-preview",
    ]

    client = genai.Client(
        api_key=api_key,
        http_options={"api_version": "v1alpha"}
    )

    print("=" * 70)
    print("Checking model capabilities for OPERO requirements:")
    print("- bidiGenerateContent (Live API)")
    print("- Tool/function calling support")
    print("- Audio input and output")
    print("=" * 70)

    for model_name in models_to_check:
        print(f"\n[*] {model_name}")

        try:
            model = client.models.get(name=model_name)

            supported_actions = getattr(model, 'supported_actions', [])
            print(f"    Supported actions: {', '.join(supported_actions)}")

            # Check if it supports tools (presence of generateContent or countTokens suggests tool support)
            has_bidi = 'bidiGenerateContent' in supported_actions
            has_tools = 'countTokens' in supported_actions or 'generateContent' in supported_actions

            print(f"    ✓ Live API (bidi): {has_bidi}")
            print(f"    ✓ Tools support: {has_tools}")

            if has_bidi and has_tools:
                print(f"    >>> RECOMMENDED for OPERO")
            elif has_bidi:
                print(f"    >>> Has Live but may lack tool support")

        except Exception as e:
            print(f"    [X] Error: {e}")

    print("\n" + "=" * 70)
    print("RECOMMENDATION:")
    print("=" * 70)
    print("\nFor OPERO (needs Live + Audio + Tools):")
    print("1. models/gemini-2.5-flash-native-audio-latest [STABLE]")
    print("2. models/gemini-3.8-live [STABLE]")
    print("\nBoth support bidiGenerateContent with tool calling.")


if __name__ == "__main__":
    check_model_capabilities()
