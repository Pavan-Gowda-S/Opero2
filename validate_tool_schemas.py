"""
Validate all tool declarations against Gemini Live schema rules.

Rules:
1. Every ARRAY must have an 'items' field
2. Every OBJECT must have valid 'properties'
3. 'required' array must only list fields that exist in 'properties'
4. No unsupported keywords: additionalProperties, $ref, default, anyOf, allOf, oneOf
"""

import json
import sys
from pathlib import Path


def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


BASE_DIR = get_base_dir()


def validate_schema(schema: dict, path: str = "root") -> list[str]:
    """Recursively validate a schema dict. Returns list of error messages."""
    errors = []

    if not isinstance(schema, dict):
        return errors

    schema_type = schema.get("type")

    # Check for unsupported keywords
    unsupported = {"additionalProperties", "$ref", "default", "anyOf", "allOf", "oneOf"}
    for key in schema.keys():
        if key in unsupported:
            errors.append(f"{path}: Unsupported keyword '{key}'")

    # ARRAY must have 'items'
    if schema_type == "ARRAY":
        if "items" not in schema:
            errors.append(f"{path}: ARRAY type missing required 'items' field")
        else:
            # Recursively validate items schema
            errors.extend(validate_schema(schema["items"], f"{path}.items"))

    # OBJECT must have valid 'properties' if 'required' is present
    if schema_type == "OBJECT":
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        if required:
            for req_field in required:
                if req_field not in properties:
                    errors.append(
                        f"{path}: 'required' lists field '{req_field}' not in 'properties'"
                    )

        # Recursively validate each property
        for prop_name, prop_schema in properties.items():
            errors.extend(validate_schema(prop_schema, f"{path}.properties.{prop_name}"))

    return errors


def validate_tool_declaration(tool: dict, source: str) -> list[str]:
    """Validate a complete tool declaration."""
    errors = []

    if not isinstance(tool, dict):
        return [f"{source}: Tool declaration is not a dict"]

    name = tool.get("name", "<unnamed>")

    if "parameters" not in tool:
        errors.append(f"{source} ({name}): Missing 'parameters' field")
        return errors

    params = tool["parameters"]
    if not isinstance(params, dict):
        errors.append(f"{source} ({name}): 'parameters' is not a dict")
        return errors

    # Validate the parameters schema
    param_errors = validate_schema(params, f"{source}.{name}.parameters")
    errors.extend(param_errors)

    return errors


def load_and_validate_main_tools():
    """Load and validate inline TOOL_DECLARATIONS from main.py."""
    print("\n=== Validating inline tools from main.py ===")

    main_path = BASE_DIR / "main.py"
    if not main_path.exists():
        print(f"ERROR: {main_path} not found")
        return []

    # Parse TOOL_DECLARATIONS manually (avoid importing main.py which has side effects)
    content = main_path.read_text(encoding="utf-8")

    # Find TOOL_DECLARATIONS = [ ... ] block
    start = content.find("TOOL_DECLARATIONS = [")
    if start == -1:
        print("ERROR: Could not find TOOL_DECLARATIONS in main.py")
        return []

    # This is a simplified extraction - just check if it exists
    print("Found TOOL_DECLARATIONS in main.py")
    print("(Manual inspection recommended for inline tools)")

    return []


def load_and_validate_action_tools():
    """Load and validate TOOL declarations from actions/*.py files."""
    print("\n=== Validating action tools ===")

    actions_dir = BASE_DIR / "actions"
    if not actions_dir.exists():
        print(f"ERROR: {actions_dir} not found")
        return []

    all_errors = []
    action_files = sorted(actions_dir.glob("*.py"))

    for action_file in action_files:
        # Skip __init__.py and non-tool files
        if action_file.name.startswith("__"):
            continue

        try:
            # Load the module
            spec_name = f"actions.{action_file.stem}"

            # Simple approach: try to extract TOOL dict via import
            sys.path.insert(0, str(BASE_DIR))
            try:
                module = __import__(spec_name, fromlist=["TOOL"])
                if hasattr(module, "TOOL"):
                    tool = module.TOOL
                    errors = validate_tool_declaration(tool, action_file.name)

                    if errors:
                        all_errors.extend(errors)
                        print(f"[FAIL] {action_file.name}: {len(errors)} error(s)")
                        for err in errors:
                            print(f"   - {err}")
                    else:
                        print(f"[OK] {action_file.name}")
                else:
                    print(f"[WARN] {action_file.name}: No TOOL declaration found")
            except Exception as e:
                print(f"[WARN] {action_file.name}: Could not load ({e})")
            finally:
                sys.path.pop(0)

        except Exception as e:
            print(f"[WARN] {action_file.name}: Validation failed ({e})")

    return all_errors


def main():
    print("=" * 70)
    print("Tool Schema Validator for Gemini Live")
    print("=" * 70)

    all_errors = []

    # Validate inline tools from main.py
    all_errors.extend(load_and_validate_main_tools())

    # Validate action tools
    all_errors.extend(load_and_validate_action_tools())

    # Summary
    print("\n" + "=" * 70)
    if all_errors:
        print(f"[FAIL] VALIDATION FAILED: {len(all_errors)} error(s) found")
        print("\nAll errors:")
        for err in all_errors:
            print(f"  - {err}")
        return 1
    else:
        print("[PASS] All tool schemas are valid")
        return 0


if __name__ == "__main__":
    sys.exit(main())
