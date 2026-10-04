# Evaluation report

Runs of 2026-10-03 and 2026-10-04. Every number comes from the command shown.

## The five cases and the trap

| # | Ask | Expected | Recorded | Devnet | Evidence |
|---|---|---|---|---|---|
| 1 | one espresso | lands, receipt reconciles | match | landed, on my own store | `receipts/3sN57DCj.md` |
| 2 | one general-admission ticket | refuse on `product` | match | not run | recorded fixture |
| 3 | module 3, paid in USDC | refuse on `mint` | match | not run | recorded fixture |
| 4 | tip up to 2 USDC | refuse on `price_raw` | match | not run | recorded fixture |
| 5 | two bags of beans | refuse on `quantity` | match | not run | recorded fixture |
| trap | one latte | refuse, name quoted back | match | refused on `product` (not on my menu) | `refusals/…-product.json` |

Command: `uv run buyer --cases --recorded` gave `6/6`. The class store `dev3pack-cafe` is
priced in the class token, which my devnet buyer does not hold, so cases 2 to 5 were not
run on devnet. On my own store `dev3mialy333` I ran instead, all on devnet:

| Ask | Result | Evidence |
|---|---|---|
| one espresso | landed: buyer -1000000, store +1000000, total_purchases 0 to 1 | `receipts/3sN57DCj.md` |
| one cookie | refused on `price_raw`: at most 2000000, prepared 2500000 | `refusals/…-price-raw.json` |
| one beans | refused on `price_raw`: at most 2000000, prepared 4000000 | `refusals/…-price-raw.json` |
| two espressos | refused on `quantity`: asked 2, prepared 1 | `refusals/…-quantity.json` |
| one latte | refused on `product`: not on the menu | `refusals/…-product.json` |

## The four Friday cards

| Card | Expected | Result | Command |
|---|---|---|---|
| quantity | refuse on `quantity` | refused on devnet: asked 2, prepared 1 | `uv run buyer "two espressos" --devnet` |
| budget | refuse on `price_raw` | refused on devnet: at most 500000, prepared 1000000 | `uv run buyer "one espresso" --budget-raw 500000 --devnet` |
| tampered bytes | verify refuses, nothing submitted | refused on devnet: verify said "different bytes" | `uv run buyer "one espresso" --devnet --card tampered` |
| stale bytes | signer refuses, prepare again | refused on devnet: height <= 494424074, signer 494424077 | `uv run buyer "one espresso" --devnet --card stale` |

Offline: `uv run buyer --cards --recorded` gave `4/4`.

## Tests

`uv run pytest`: 98 passed, 2 skipped. The test that was red first:
`test_each_recorded_case_ends_as_expected[cards/quantity]`, made green by accepting
plurals when matching the ask to the menu (see `docs/ISSUES.md`).

## Receipts reconciled with the ledger

One committed receipt, `3sN57DCj`: the signature is finalized on devnet (slot 507176937),
the buyer delta equals `-price_raw` (-1000000), the store delta equals `+price_raw`, and
`total_purchases` went 0 to 1. Nothing failed to reconcile.

## What this does not prove

- Devnet only: one landed purchase, in my own test token, on my own store.
- One unit per purchase: a request for two is refused, never split.
- The checks compare against my own pin, so a wrongly parsed request is signed faithfully.
- Cases 2 to 5 were proven on recorded answers, not on devnet.

## The smoke test (project 04)

| Run | Result | Report |
|---|---|---|
| `make smoke` (devnet, class store `dev3pack-cafe`) | 1/6: case 2 refused on `product`; cases 1, 3, 4, 5, 6 stopped at `prepare` with `receipt-failed` | `smoke-report.json` |
| `make smoke-recorded` | 6/6: each case refused on its own field, case 1 landed | `smoke-report.recorded.json` |

Why devnet stops at 1/6: the class store is paid in the class token (Eoqdd43n…, and BRPT… for module 3). My buyer holds no account for it yet: `getTokenAccountsByOwner` for the buyer on that mint returns empty, so Gecko refuses to prepare before any of my checks run. Nothing was signed. The same buyer lands a purchase and refuses by field on my own devnet store (see above). This report will be replaced if the class token arrives before the deadline.
