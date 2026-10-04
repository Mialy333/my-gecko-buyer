# Issues

Real incidents from the week, newest first.

## 2026-10-04: the setup script could not get devnet SOL from the faucet

- **What I saw:** `uv run python scripts/devnet_setup.py` printed
  `faucet refused (requestAirdrop: {'code': -32603, 'message': 'Internal error'})`, then
  `Not funded yet: the owner holds 0.000000 SOL and needs 0.035000 SOL.`
- **What was actually wrong:** the public devnet faucet refuses programmatic airdrops most
  of the time; nothing was wrong with the keys or the script.
- **How I found it:** the script's own message, then the instructor's note to use
  https://faucet.solana.com/.
- **What I changed:** funded the owner address (`4WVGu…noe6`) with 0.5 SOL from the web
  faucet, on devnet, then ran the script again: `ready`, own token created, 100 tokens to
  the buyer. No code change.
- **What it cost:** a few minutes, and no devnet SOL.
- **Would the checks have caught it?** No: this is setup, before any purchase. The script
  refused to go on without funds instead of failing halfway, which is the behaviour I want.

## 2026-10-03: "two espressos" was refused on `product` instead of `quantity`

- **What I saw:** `uv run buyer --cards --recorded` gave `3/4 cards`, and pytest failed
  `tests/test_your_work.py::test_each_recorded_case_ends_as_expected[cards/quantity]`. The
  card printed `REFUSED on product: asked 'espressos', menu 'not on the menu'`.
- **What was actually wrong:** `parse_intent` matched the ask's words to menu names
  exactly, so the plural "espressos" did not find "Espresso". The buyer refused for the
  wrong reason: still safe, but it named the wrong field.
- **How I found it:** the recorded card and its test, before any devnet run.
- **What I changed:** a word now matches a name word, singular or plural (`n`, `n+"s"`,
  `n+"es"`). The quantity card test is green; on devnet, "two espressos" is refused on
  `quantity: asked 2, prepared 1`.
- **What it cost:** nothing on chain; found offline.
- **Would the checks have caught it?** It was a refusal either way, so nothing could be
  signed. But a refusal that names the wrong field is a wrong explanation, and the card
  test is what showed it.
