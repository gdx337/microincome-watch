# MicroIncome Watch — read-only live microtask checker

A small **free, AI-assisted Python 3 script** that reads public data from APEX's Arc-mainnet USDC faucet, SwarmMemo's per-result work board, and Frantic's funded public bounty slots. It never claims tasks, sends cryptocurrency, registers an account, signs a message, reads a private key, or pays fees.

Run:

```bash
python3 microincome_watch.py
# Optional: use your own public EVM address to see faucet eligibility:
python3 microincome_watch.py --wallet 0xYOUR_PUBLIC_EVM_ADDRESS
```

Requires Python 3.8+ and network access. Uses only the Python standard library. A listed task is **not** a guaranteed payout; most task providers require identity checks, accepted results and/or review. Check your work/visa conditions and read fees before taking paid tasks. Faucet gifts are not earned task income.

## Voluntary micro-tip

If this public resource saves you time, you can send a completely optional **0.01 USDC tip on Base mainnet** (not Arc and not a test network) to:

`0xa66B7534cdcfb0833652D7052A48BaCe8F627c42`

This is a transparent tip request, not a fee. **Nothing is promised in exchange**, and nobody is under any obligation to pay. Please verify the network and token yourself and never send keys or seed phrases. The script and information remain free.

## The voluntary one-cent kindness experiment

This free project also asks a simple question: **will anyone voluntarily gift 0.01 USDC to a published, honest, zero-paywall tool?** No payment is required, expected, or linked to any work or promised return. The public address above is solely a voluntary-gift endpoint. Any reported success must be independently checked on the actual blockchain, not inferred from page views or pledges.
