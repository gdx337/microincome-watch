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
                guide = result.get("guide", "") if isinstance(result, dict) else str(result)
                for line in guide.splitlines():
                    if any(term in line.lower() for term in
                           ("apply_to_opportunity", "negotiate_opportunity", "post_message", "publish_agent", "proposal", "agent listing", "application")):
                        print("GUIDE:", line[:240])
            elif name == "whoami":
                print("Identity response structure only:", json.dumps(structure(result)))
                agents = result.get("agents", [])
                print("Existing agent listing count:", len(agents) if isinstance(agents, list) else "unknown")
                if isinstance(agents, list):
                    for item in agents[:3]:
                        if isinstance(item, dict):
                            print("Agent listing field names:", sorted(item.keys()))
                profile = result.get("profile")
                print("Operator profile exists:", isinstance(profile, dict) and bool(profile))
            elif name == "get_opportunity":
                print("Opportunity response structure:", json.dumps(structure(result)))
                obj = result.get("opportunity", result) if isinstance(result, dict) else {}
                if isinstance(obj, dict):
                    print("Opportunity field names:", sorted(obj.keys()))
                    for attr in ("status", "budgetMin", "budgetMax", "applicantCount",
                                 "trust", "fundingStatus", "currency", "jobKind"):
                        if attr in obj:
                            value = obj[attr]
                            if isinstance(value, (str, int, float, bool, type(None))):
                                print("BRIEF", attr, "=", str(value)[:80])
                for field in ("myApplications", "myNegotiations"):
                    value = result.get(field)
                    if isinstance(value, list):
                        print("Existing targeted", field, "count:", len(value))
                        if field == "myNegotiations" and value:
                            print("VERIFIED: Client brief has a saved negotiation on this account.")
                            for item in value[:1]:
                                if isinstance(item, dict):
                                    for key_name in ("amountCents", "amount_cents", "status"):
                                        if key_name in item and isinstance(item[key_name], (str, int, float)):
                                            print("Negotiation", key_name, "=", item[key_name])
            elif name == "list_my_applications":
                print("Application response structure only:", json.dumps(structure(result)))
                for field in ("applications", "negotiations"):
                    value = result.get(field)
                    if isinstance(value, list):
                        print("My total", field, "count:", len(value))
        except RuntimeError as exc:
            print("FAIL:", name, str(exc))
    try:
        tools_result = rpc(key, "tools/list", {}, 5)
        for tool in tools_result.get("tools", []):
            if isinstance(tool, dict) and tool.get("name") in (
                    "publish_agent", "apply_to_opportunity", "negotiate_opportunity", "post_message"):
                print("TOOL_SCHEMA:", json.dumps({
                    "name": tool.get("name"), "description": tool.get("description", "")[:600],
                    "inputSchema": tool.get("inputSchema")
                })[:2800])
    except RuntimeError as exc:
        print("TOOL_SCHEMAS unavailable:", str(exc))
    print("Read-only inspection complete; no applications submitted.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
