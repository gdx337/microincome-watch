#!/usr/bin/env python3
"""Read-only AgentExchange MCP probe. No applications, payments or deliveries."""
import json
import os
import sys
import urllib.error
import urllib.request

ENDPOINT = "https://www.agentsexchange.ai/api/mcp"
MAX_RESPONSE_BYTES = 256 * 1024


def rpc(token, method, params, request_id):
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": params,
    }).encode("utf-8")
    request = urllib.request.Request(
        ENDPOINT,
        data=payload,
        method="POST",
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
            "User-Agent": "microincome-watch/1.0 (read-only MCP client)",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            media = response.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        # Classify server response without echoing a response body or secrets.
        media = (exc.headers.get("Content-Type") or "").lower()
        edge = (exc.headers.get("Server") or "").lower()
        if "json" in media:
            detail = "JSON response"
        elif "html" in media:
            detail = "HTML block/error page"
        else:
            detail = "unclassified response"
        edge_hint = "; Cloudflare edge" if "cloudflare" in edge else ""
        raise RuntimeError("MCP returned HTTP " + str(exc.code) + " (" + detail + edge_hint + ")") from None
    except urllib.error.URLError:
        raise RuntimeError("MCP connection failed") from None

    if len(raw) > MAX_RESPONSE_BYTES:
        raise RuntimeError("MCP response too large")
    text = raw.decode("utf-8")
    if "text/event-stream" in media:
        messages = [
            line[5:].strip()
            for line in text.splitlines()
            if line.startswith("data:") and line[5:].strip() not in ("", "[DONE]")
        ]
        if not messages:
            raise RuntimeError("MCP did not return a JSON-RPC result")
        text = messages[-1]
    try:
        message = json.loads(text)
    except json.JSONDecodeError:
        raise RuntimeError("MCP returned invalid JSON") from None
    if not isinstance(message, dict):
        raise RuntimeError("Unexpected MCP response")
    if message.get("error"):
        error = message["error"]
        code = error.get("code") if isinstance(error, dict) else "unknown"
        raise RuntimeError("MCP JSON-RPC error " + str(code))
    result = message.get("result")
    if not isinstance(result, dict) or result.get("isError") is True:
        raise RuntimeError("MCP tool returned an error")
    return result


def tools_from_result(result):
    return {
        tool.get("name")
        for tool in result.get("tools", [])
        if isinstance(tool, dict) and isinstance(tool.get("name"), str)
    }


def approximate_count(result):
    """Count search result arrays without exposing their content in public logs."""
    candidates = [result]
    for content in result.get("content", []):
        if isinstance(content, dict) and isinstance(content.get("text"), str):
            try:
                parsed = json.loads(content["text"])
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                candidates.append(parsed)
            elif isinstance(parsed, list):
                return len(parsed)
    for candidate in candidates:
        for key in ("opportunities", "items", "briefs", "results", "jobs"):
            if isinstance(candidate.get(key), list):
                return len(candidate[key])
            nested = candidate.get("data")
            if isinstance(nested, dict) and isinstance(nested.get(key), list):
                return len(nested[key])
    return None


def main():
    token = os.environ.get("AGENTEXCHANGE_API_KEY", "")
    if not token:
        print("FAIL: AGENTEXCHANGE_API_KEY secret missing or empty.")
        return 2
    if token != token.strip() or not token.startswith("axk_"):
        print("FAIL: API secret formatting does not match expected axk_ key (check for spaces or copied label).")
        return 2
    print("PASS: AgentExchange key format valid (secret contents hidden).")

    required = {"get_marketplace_guide", "whoami", "search_opportunities"}
    try:
        # Direct tools/call follows the vendor's documented raw JSON-RPC sample.
        rpc(token, "tools/call", {
            "name": "get_marketplace_guide", "arguments": {}
        }, 1)
        print("PASS: Marketplace guide readable.")

        rpc(token, "tools/call", {
            "name": "whoami", "arguments": {}
        }, 2)
        print("PASS: API key authenticated (identity withheld from public logs).")

        for i, query in enumerate(("writing", "research"), start=4):
            result = rpc(token, "tools/call", {
                "name": "search_opportunities", "arguments": {"query": query}
            }, i)
            count = approximate_count(result)
            suffix = "count not provided" if count is None else str(count) + " returned"
            print("PASS: read-only " + query + " search (" + suffix + ").")

        print("PASS: Read-only probe complete. No applications or payments made.")
        return 0
    except RuntimeError as exc:
        # Intentionally never print the API key, response payload, user identity,
        # opportunity descriptions, or request headers in public workflow logs.
        print("FAIL: " + str(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())
