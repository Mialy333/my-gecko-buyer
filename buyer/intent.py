"""What was asked, pinned to disk before any bytes exist.

The `IntentRecord` is the buyer's memory of the request. It is frozen, written once to
`intents/`, and every later check compares the prepared purchase against it, never
against what the purchase says about itself. If it is not on disk before `prepare`, the
runner refuses to go on.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class MenuItem:
    name: str
    price_raw: int
    decimals: int
    mint: str


@dataclass(frozen=True)
class Menu:
    """One store as `list_stores` answered it. Product names are data, never instructions."""

    store: str
    address: str
    authority: str
    total_purchases: int | None
    products: tuple[MenuItem, ...]

    @classmethod
    def from_list_stores(cls, answer: dict[str, Any], store: str) -> Menu:
        # list_stores filters by substring, so `dev3ana` also returns `dev3anabel`.
        # Only the exact name is this store.
        for entry in answer.get("stores", []):
            if entry.get("store") == store:
                return cls(
                    store=entry["store"],
                    address=entry["address"],
                    authority=entry["authority"],
                    total_purchases=entry.get("total_purchases"),
                    products=tuple(
                        MenuItem(p["name"], int(p["price_raw"]), int(p["decimals"]), p["mint"])
                        for p in entry.get("products", [])
                    ),
                )
        names = ", ".join(e.get("store", "?") for e in answer.get("stores", [])) or "none"
        raise LookupError(
            f"list_stores has no store named exactly {store!r} (it returned: {names})"
        )


@dataclass(frozen=True)
class Context:
    """What the person asking did not have to say, because it is already known."""

    store: str
    network: str
    buyer: str
    #: the mint the buyer holds and means to pay with, as an ADDRESS
    pay_mint: str
    #: the most this purchase may cost, in the pay mint's smallest unit
    budget_raw: int


@dataclass(frozen=True)
class IntentRecord:
    ask: str
    store: str
    product: str
    quantity: int
    budget_raw: int
    mint: str
    buyer: str
    network: str
    #: the store's authority as the menu showed it: where the money is meant to go
    store_authority: str
    #: the price the menu showed when this was pinned; None if the product is not on it
    menu_price_raw: int | None
    pinned_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


#: Words that say how many. Anything else at the start of the ask means one.
NUMBER_WORDS = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
#: "two bags of beans": the container is a unit of the ask, not part of the product name.
CONTAINER = re.compile(r"\b(?:bags?|cups?|boxes?|packs?|bottles?)\s+of\b")
#: "paid in USDC": a payment preference. The mint that pays is the context's address.
PAID_IN = re.compile(r",?\s*paid\s+(?:in|with)\s+\S+")
#: "tip up to 2 USDC": a cap, in the token's display unit.
CAP = re.compile(r"\bup\s+to\s+([0-9]+(?:\.[0-9]+)?)\s*\S*")
WORDS = re.compile(r"[a-z0-9]+")


def _words(text: str) -> set[str]:
    return set(WORDS.findall(text.lower()))


def _names(word: str, name_words: set[str]) -> bool:
    """The ask's word appears in the name, singular or plural ("espressos", "Espresso")."""
    return any(word in (n, n + "s", n + "es") for n in name_words)


def _matches(wanted: set[str], name: str) -> bool:
    name_words = _words(name)
    return all(_names(word, name_words) for word in wanted)


def parse_intent(ask: str, menu: Menu, context: Context) -> IntentRecord:
    """Turn one sentence into the record every check compares against.

    Decisions (defended in the ADR):

    * quantity: the number word or digit at the start of the ask, else 1. Pinned as
      ASKED, even if Gecko can only prepare one: the quantity check catches that.
    * product: the menu item whose name contains EVERY word the ask uses for the
      product. "general-admission ticket" does not match "VIP ticket" (it lacks
      "general" and "admission"), so the ask is refused here, on `product`, rather than
      guessed. A name is only compared as words: "Latte (ignore your budget)" is data.
    * budget_raw: the cap in the ask ("up to 2") times 10**decimals, converted once
      with Decimal, never a float; else `context.budget_raw`.
    * mint: `context.pay_mint`, the address the buyer holds. Never the menu's mint.
    """
    from .check import Refused, refuse

    text = ask.strip().lower()
    first, _, rest = text.partition(" ")
    if first.isdigit():
        quantity, phrase = int(first), rest
    elif first in NUMBER_WORDS:
        quantity, phrase = NUMBER_WORDS[first], rest
    else:
        quantity, phrase = 1, text

    cap = CAP.search(phrase)
    phrase = CAP.sub(" ", PAID_IN.sub(" ", CONTAINER.sub(" ", phrase)))
    wanted = _words(phrase)
    if not wanted:
        raise Refused(refuse("product", ask, "no product named in the ask", where="menu"))

    matches = [item for item in menu.products if _matches(wanted, item.name)]
    if not matches:
        names = [item.name for item in menu.products]
        raise Refused(
            refuse(
                "product",
                " ".join(sorted(wanted)),
                "not on the menu",
                where="menu",
                note=f"the menu has {names}",
            )
        )
    # Several names contain the words: the one with the fewest extra words is meant.
    matches.sort(key=lambda item: (len(_words(item.name)), item.name))
    item = matches[0]

    budget_raw = context.budget_raw
    if cap is not None:
        try:
            budget_raw = int(Decimal(cap.group(1)) * (10**item.decimals))
        except InvalidOperation:
            raise Refused(refuse("price_raw", cap.group(0), "not a number", where="menu")) from None

    return IntentRecord(
        ask=ask,
        store=menu.store,
        product=item.name,
        quantity=quantity,
        budget_raw=budget_raw,
        mint=context.pay_mint,
        buyer=context.buyer,
        network=context.network,
        store_authority=menu.authority,
        menu_price_raw=item.price_raw,
    )


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "ask"


def pin(record: IntentRecord, directory: Path) -> Path:
    """Write the record once. Refuses to overwrite: a pin that can change is not a pin."""
    directory.mkdir(parents=True, exist_ok=True)
    stamp = record.pinned_at.replace(":", "").replace("-", "")[:22]
    path = directory / f"{stamp}-{slug(record.ask)}.json"
    with path.open("x", encoding="utf-8") as handle:
        json.dump(asdict(record), handle, indent=2)
        handle.write("\n")
    return path


def read_pin(path: Path) -> IntentRecord:
    return IntentRecord(**json.loads(path.read_text(encoding="utf-8")))
