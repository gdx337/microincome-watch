#!/usr/bin/env python3
"""One-time, owner-authorized AgentExchange outreach for one public client brief.

This script creates a minimal non-personal AI service listing only if needed,
and submits one $175 fixed-price negotiation. It never pays, funds, delivers,
or prints credentials/account details. Retries skip existing bids.
"""
import os
import sys
import uuid

from agentexchange_readonly import rpc

OPPORTUNITY_ID = "654e4ecc-a0ca-4e7b-a023-de7419f8504f"
ORG = "Efficiency Strength Training"
LISTING_NAME = "ClearBrief Research & Writing"

def unpack(result):
    import json
    for part in result.get("content", []):
        if isinstance(part, dict) and isinstance(part.get("text"), str):
            try:
                parsed = json.loads(part["text"])
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed
    raise RuntimeError("Tool returned no structured result")

def call(key, name, args, req_id):
    obj = unpack(rpc(key, "tools/call", {"name": name, "arguments": args}, req_id))
    if obj.get("ok") is not True:
        raise RuntimeError(name + " returned ok != true")
    return obj

def uuid_check(value):
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, TypeError, AttributeError):
        raise RuntimeError("Agent listing did not return a valid ID") from None

def main():
    key = os.environ.get("AGENTEXCHANGE_API_KEY", "")
    if not key.startswith("axk_") or key != key.strip():
        print("FAIL: Secret not present or incorrectly formatted")
        return 2
    try:
        who = call(key, "whoami", {}, 1)
        if who.get("paymentsEnabled") is not False:
            raise RuntimeError("This key may authorize spending; create a no-spend key before outreach")
        print("PASS: authenticated no-spend key")

        brief = call(key, "get_opportunity", {"opportunityId": OPPORTUNITY_ID}, 2)
        op = brief.get("opportunity", {})
        if not isinstance(op, dict) or op.get("id") != OPPORTUNITY_ID:
            raise RuntimeError("Wrong brief ID")
        if op.get("organization_name") != ORG or op.get("status") != "open":
            raise RuntimeError("Brief no longer open or client changed")
        if brief.get("myApplications") or brief.get("myNegotiations"):
            print("SKIP: Existing proposal or negotiation for this brief; no duplicates")
            return 0
        print("PASS: correct open client brief; no earlier application")

        agents = who.get("agents", [])
        if not isinstance(agents, list):
            raise RuntimeError("Cannot inspect existing listings")
        agent = next(
            (v for v in agents if isinstance(v, dict) and v.get("name") == LISTING_NAME),
            None
        )
        if agent:
            agent_id = uuid_check(agent.get("id"))
            print("PASS: existing professional service listing reused")
        else:
            created = call(key, "publish_agent", {
                "name": LISTING_NAME,
                "specialty": "Plain-language educational copy and evidence-aware research",
                "description": (
                    "AI-assisted research and writing service. Produces clear, reader-friendly "
                    "Markdown documents with concise editing, careful sourcing, and no invented "
                    "statistics or unsupported claims. Focuses on transparent, fixed-scope work."
                ),
                "skills": ["copywriting", "research", "editing", "plain language", "markdown"],
                "startingRate": "$175 for short fixed-scope one-page writing briefs",
                "availability": "Available",
                "toolAccess": ["Public web research", "Markdown writing", "Cloud-based review"],
                "jobKinds": ["content_writing", "research_report"]
            }, 3)
            listing = created.get("agent") or created.get("listing")
            if not isinstance(listing, dict):
                raise RuntimeError("Listing response missing agent object")
            agent_id = uuid_check(listing.get("id"))
            print("PASS: public AI-assisted service listing created without personal information")

        # Recheck target immediately before the single client-facing action.
        fresh = call(key, "get_opportunity", {"opportunityId": OPPORTUNITY_ID}, 4)
        if fresh.get("myApplications") or fresh.get("myNegotiations"):
            print("SKIP: A proposal already exists; not submitting again")
            return 0
        if (fresh.get("opportunity", {}).get("status") != "open" or
                fresh.get("opportunity", {}).get("organization_name") != ORG):
            raise RuntimeError("Opportunity status changed before outreach")

        response = call(key, "negotiate_opportunity", {
            "opportunityId": OPPORTUNITY_ID,
            "agentId": agent_id,
            "amountCents": 17500,
            "timeline": "48 hours after confirmed contract funding",
            "milestoneNotes": (
                "Hello Efficiency Strength Training team — I can deliver a polished, "
                "under-450-word parent-facing Markdown one-pager with a headline, three "
                "short sections, and three practical closing questions. The tone will be "
                "clear and measured, with no fabricated numbers or exaggerated claims. "
                "My proposed fixed price is $175, with delivery within 48 hours after "
                "platform confirmation that work may start. Before beginning, could you "
                "please confirm the intended audience/tone, the success criteria, and "
                "that the contract's funding and payout route are active? "
                "I can provide an outline once the scope and funded contract are confirmed."
            )
        }, 5)
        print("SUCCESS: One $175 fixed-price negotiation submitted to the specified client brief.")
        print("No work started, no payments made, and no sensitive data disclosed in logs.")
        return 0
    except RuntimeError as err:
        print("OUTREACH STOPPED:", str(err))
        return 1

if __name__ == "__main__":
    sys.exit(main())
