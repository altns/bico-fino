"""PreToolUse hook: always ask the user before a command that starts a print.

Matches `flashforge_lan.py upload ... --print` (and the other way around). Anything else passes untouched.
"""
import json
import re
import sys


def main():
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return
    cmd = payload.get("tool_input", {}).get("command", "")
    if re.search(r"flashforge_lan\.py", cmd) and re.search(r"(^|\s)--print(\s|$)", cmd):
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": "This command starts a print on the printer. Confirm only if you asked for it.",
        }}))


if __name__ == "__main__":
    main()
