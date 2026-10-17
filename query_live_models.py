"""
Query Gemini API for all models supporting bidiGenerateContent (Live API).
Find the current stable model with audio input/output and tool support.
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
        # Mask key in output
        return key, f"{key[:8]}...{key[-6:]}"


def query_live_models():
    """Query all models supporting bidiGenerateContent."""
    print("=" * 70)
    print("Querying Gemini API for Live models (bidiGenerateContent support)")
    print("=" * 70)

    try:
        from google import genai

        api_key, masked_key = get_api_key()
        print(f"\n[*] Using API key: {masked_key}")

        # Try both API versions
        for api_version in ["v1alpha", "v1beta"]:
            print(f"\n=== Checking API version: {api_version} ===")

            try:
                client = genai.Client(
                    api_key=api_key,
                    http_options={"api_version": api_version}
                )

                print(f"[*] Listing models...")
                models_response = client.models.list()

                # Convert to list if it's an iterator
                models = list(models_response) if models_response else []

                print(f"[*] Total models returned: {len(models)}")

                if not models:
                    print("[!] No models returned from API")
                    continue

                live_models = []

                for model in models:
                    model_name = model.name

                    # Get supported actions (correct attribute name)
                    supported_actions = getattr(model, 'supported_actions', [])

                    # Check for bidiGenerateContent support
                    if 'bidiGenerateContent' in supported_actions:
                        # Get additional info
                        display_name = getattr(model, 'display_name', model_name)
                        description = getattr(model, 'description', '')[:80]

                        live_models.append({
                            'name': model_name,
                            'bidi': True,
                            'display_name': display_name,
                            'description': description,
                            'actions': supported_actions
                        })

                if live_models:
                    print(f"\n[+] Found {len(live_models)} models with bidiGenerateContent support:")
                    print("-" * 70)

                    for i, m in enumerate(live_models, 1):
                        # Classify as stable/exp/preview
                        name = m['name']
                        if 'exp' in name.lower():
                            stability = "[EXP]"
                        elif 'preview' in name.lower():
                            stability = "[PREVIEW]"
                        else:
                            stability = "[STABLE]"

                        print(f"\n{i}. {stability} {name}")
                        print(f"   Display: {m['display_name']}")
                        print(f"   Actions: {', '.join(m['actions'][:5])}")
                        if m['description']:
                            print(f"   Desc: {m['description']}")

                    # Recommend best model
                    print("\n" + "=" * 70)
                    print("RECOMMENDATION:")
                    print("=" * 70)

                    # Prefer stable over experimental/preview
                    stable_models = [m for m in live_models if 'exp' not in m['name'].lower() and 'preview' not in m['name'].lower()]
                    exp_models = [m for m in live_models if 'exp' in m['name'].lower() or 'preview' in m['name'].lower()]

                    recommended = None
                    reason = ""

                    if stable_models:
                        recommended = stable_models[0]['name']
                        reason = "Stable release with bidiGenerateContent support"
                    elif exp_models:
                        recommended = exp_models[0]['name']
                        reason = "Experimental/preview model (no stable version available)"

                    if recommended:
                        print(f"\nBest model for LIVE_MODEL: {recommended}")
                        print(f"Reason: {reason}")
                        print(f"API version: {api_version}")
                        return recommended, api_version
                    else:
                        print("\n[!] No suitable bidiGenerateContent models found")

                else:
                    print(f"[!] No models with bidiGenerateContent support found in {api_version}")

            except Exception as e:
                print(f"[X] Error querying {api_version}: {e}")
                continue

        return None, None

    except Exception as e:
        print(f"[X] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return None, None


if __name__ == "__main__":
    recommended_model, api_version = query_live_models()

    if recommended_model:
        print("\n" + "=" * 70)
        print("UPDATE INSTRUCTIONS:")
        print("=" * 70)
        print(f'\n1. Set LIVE_MODEL = "{recommended_model}" in main.py line 80')
        print(f'2. Use API version: {api_version}')
        print('3. Add config override in config/api_keys.json:')
        print('   "live_model": "<model_name>" (optional)')
        sys.exit(0)
    else:
        print("\n[X] Could not find suitable Live model")
        sys.exit(1)
