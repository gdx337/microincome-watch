#!/usr/bin/env python3
"""Read-only microtask / small USDC opportunity watch. Python stdlib only.

This never signs transactions, submits work, claims rewards, or handles secrets.
"""
import argparse
import datetime as dt
import json
import urllib.request
import urllib.error

HEADERS = {"Accept": "application/json", "User-Agent": "MicroIncomeWatch/1.0 (read-only)"}


def get_json(url):
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.load(response)


def print_apex(wallet):
    info = get_json("https://apexfaucet.xyz/api/arc/faucet")
    print("\nAPEX / Arc mainnet — charity faucet, NOT earned income")
    print("  Chain:", info.get("chainId"), "| Payout per claim:", info.get("claimUsdc"), "USDC")
    print("  Claims available now:", info.get("claimsLeftNow"), "| Next window:", info.get("nextReleaseAt"))
    if wallet:
        state = get_json("https://apexfaucet.xyz/api/arc/faucet/next/" + wallet)
        print("  Wallet eligible now:", state.get("canClaimNow"))
    print("  Information only. Claim eligibility and quota can change at any moment.")


def print_swarmmemo():
    doc = get_json("https://swarmmemo.com/api/works?kind=rewarded&limit=30")
    works = doc.get("data", {}).get("works", [])
    print("\nSwarmMemo / available per-result work (payout is conditional)")
    seen = 0
    for work in works:
        if not work.get("claimable"):
            continue
        standing = work.get("standing") or {}
        tiers = standing.get("tiers") or []
        usdc = next((t.get("usdc") for t in tiers if t.get("usdc")), None)
        if not usdc or int(standing.get("open", 0)) <= 0:
            continue
        print("  - {} | {} USDC per accepted result | {} seats | https://swarmmemo.com/work/{}".format(
            work.get("title", "(untitled)"), usdc, standing.get("open"), work.get("id")))
        seen += 1
    if not seen:
        print("  No currently claimable USDC work returned by the public feed.")
    print("  No money is paid merely for viewing, registering or making an unaccepted submission.")


def print_frantic():
    doc = get_json("https://gofrantic.com/v1/board")
    bounties = doc.get("board", {}).get("open_bounties", [])
    print("\nFrantic / funded public slots (individually judged)")
    seen = 0
    for item in bounties:
        if not item.get("funded") or item.get("visibility") != "public":
            continue
        slots = item.get("claim_slots") or {}
        if int(slots.get("available") or 0) <= 0:
            continue
        print("  - #{} {} | ${} per accepted delivery | {} slots | https://gofrantic.com/bounties/{}".format(
            item.get("number"), item.get("title"), item.get("price_usd"), slots.get("available"), item.get("number")))
        seen += 1
    if not seen:
        print("  No funded public slots returned.")
    print("  Identity checks and review may apply. Listing is not an offer of instant cash.")


def main():
    parser = argparse.ArgumentParser(description="Read-only microincome opportunity checker (no wallet keys)")
    parser.add_argument("--wallet", help="Optional public 0x EVM address to check APEX eligibility")
    args = parser.parse_args()
    if args.wallet and (len(args.wallet) != 42 or not args.wallet.startswith("0x") or
                        any(c not in "0123456789abcdefABCDEF" for c in args.wallet[2:])):
        parser.error("--wallet must be a 0x-prefixed 20-byte public EVM address")
    print("MicroIncome Watch — public information at", dt.datetime.now(dt.timezone.utc).isoformat())
    for fn, value in ((print_apex, args.wallet), (print_swarmmemo, None), (print_frantic, None)):
        try:
            fn(value) if fn is print_apex else fn()
        except (urllib.error.URLError, TimeoutError, ValueError, TypeError, KeyError) as exc:
            print("\n{}: source unavailable ({})".format(fn.__name__, type(exc).__name__))
    print("\nCheck visa/local work rules, platform conditions and fees. Zero income is possible.")


if __name__ == "__main__":
    main()
