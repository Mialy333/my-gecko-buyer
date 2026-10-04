# Evaluation report

Runs of 2026-10-03 and 2026-10-04. Every number comes from the command shown.

## The five cases and the trap

| # | Ask | Expected | Recorded | Devnet | Evidence |
|---|---|---|---|---|---|
| 1 | one espresso | lands, receipt reconciles | match | landed (total_purchases 8 to 9) | `receipts/5UzEduTx.md` |
| 2 | one general-admission ticket | refuse on `product` | match | refused on `product` | `smoke-report.json` |
| 3 | module 3, paid in USDC | refuse on `mint` | match | refused on `mint` (Eoqd… asked, BRPT… prepared) | `smoke-report.json` |
| 4 | tip up to 2 USDC | refuse on `price_raw` | match | refused on `price_raw` (3000000 > 2000000) | `smoke-report.json` |
| 5 | two bags of beans | refuse on `quantity` | match | refused on `quantity` (2 asked, 1 prepared) | `smoke-report.json` |
| trap | one latte | refuse, name quoted back | match | refused on `price_raw` (5000000), name quoted, not obeyed | `smoke-report.json` |

Commands: `make smoke` (devnet, class store `dev3pack-cafe`) gave `6/6`, and
`uv run buyer --cases --recorded` gave `6/6`. On my own store `dev3mialy333` I also ran, all on devnet:

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
`total_purchases` went 0 to 1. A second receipt, `5UzEduTx` (class store `dev3pack-cafe`, slot 507425423): buyer -1000000, store +1000000, total_purchases 8 to 9. Nothing failed to reconcile.

## What this does not prove

- Devnet only: two landed purchases, one on my own store in my own token, one on the class store.
- One unit per purchase: a request for two is refused, never split.
- The checks compare against my own pin, so a wrongly parsed request is signed faithfully.

## The smoke test (project 04)

| Run | Result | Report |
|---|---|---|
| `make smoke` (devnet, class store `dev3pack-cafe`) | 6/6: case 1 landed, cases 2 to 6 refused on their own field, nothing signed for a refusal | `smoke-report.json` |
| `make smoke-recorded` | 6/6 on the recorded answers | `smoke-report.recorded.json` |

History: the first two `make smoke` runs on devnet gave 1/6, because my buyer held no
class token yet (Gecko refused to prepare with `receipt-failed`, nothing signed; those
refusals are kept in `refusals/`). After the instructor funded the buyer (20 class
tokens), the same command gave 6/6. Landed purchase on the class store:
https://explorer.solana.com/tx/5UzEduTxhxf13WLGK5cEjauFMRevu4JRo3QgThuJH1pxZ8pYxH6tT5uN7J8B4YpXk63U4deHDjrLYkPcqRGBw64u?cluster=devnet
