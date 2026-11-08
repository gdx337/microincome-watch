#!/usr/bin/env python3
"""Inspect a single public AgentExchange brief without revealing operator data."""
import json
import os
import sys
from agentexchange_readonly import rpc

BRIEF_ID = "654e4ecc-a0ca-4e7b-a023-de7419f8504f"

def decoded(result):
    for item in result.get("content", []):
        if isinstance(item, dict) and isinstance(item.get("text"), str):
            try:
                return json.loads(item["text"])
            except json.JSONDecodeError:
                pass
    return {}

def structure(value):
    if isinstance(value, dict):
        return {key: type(val).__name__ for key, val in value.items()}
    if isinstance(value, list):
        return {"list_length": len(value)}
    return {"type": type(value).__name__}

def main():
    key = os.environ.get("AGENTEXCHANGE_API_KEY", "")
    if not key.startswith("axk_"):
        print("FAIL: Valid AgentExchange secret was not provided.")
        return 2
    for name, args, rid in [
        ("get_marketplace_guide", {}, 1),
        ("whoami", {}, 2),
        ("get_opportunity", {"opportunityId": BRIEF_ID}, 3),
        ("list_my_applications", {}, 4),
    ]:
        try:
            result = decoded(rpc(key, "tools/call", {"name": name, "arguments": args}, rid))
            print("PASS:", name)
            if name == "get_marketplace_guide":
                guide = result if isinstance(result, str) else json.dumps(result)
                for line in guide.splitlines():
                    if any(term in line.lower() for term in
                           ("apply_to_opportunity", "negotiate_opportunity", "post_message", "publish_agent", "proposal")):
                        print("GUIDE:", line[:180])
            elif name == "whoami":
                print("Identity response structure only:", json.dumps(structure(result)))
            elif name == "get_opportunity":
                print("Opportunity response structure:", json.dumps(structure(result)))
                obj = result.get("opportunity", result) if isinstance(result, dict) else {}
                if isinstance(obj, dict):
                    for attr in ("status", "budgetMin", "budgetMax", "applicantCount",
                                 "trust", "fundingStatus", "currency"):
                        if attr in obj:
                            value = obj[attr]
                            if isinstance(value, (str, int, float, bool, type(None))):
                                print("BRIEF", attr, "=", str(value)[:80])
            elif name == "list_my_applications":
                print("Application response structure only:", json.dumps(structure(result)))
        except RuntimeError as exc:
            print("FAIL:", name, str(exc))
    print("Read-only inspection complete; no applications submitted.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
