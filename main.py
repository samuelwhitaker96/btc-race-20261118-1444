#!/usr/bin/env python3
"""btc-race-24h-20261118-1444 entry: buy sharp selloffs, ride the recovery.

Strategy (long only, one position, full size):
  BUY  all cash when the latest close is at least 1.0% below the highest close
       of the previous 60 minutes AND the price has turned up (latest close
       above the close 1 minute ago and above the close 5 minutes ago).
       A sharp drop that is already turning is usually a local low; buying
       into a still-falling price is not attempted.
  SELL the whole position when the close is 1.5% above the fill price
       (take profit) or 1.0% below it (stop loss), or when the position has
       been held for 12 hours without hitting either (maximum hold, so a
       stagnant position does not block re-entry for the rest of the window).

Why this shape: a full-size round trip pays about 26 bps in fees, slippage
and price impact, so a trade has to catch a move larger than that. One-minute
bars are mostly noise (about 7 bps standard deviation), so the bot trades
rarely and only after a move of about 1% or more, then holds for hours until
the profit target or the stop is hit. On the published dev window this makes
one round trip: it buys the selloff near the start of the window and sells
into the recovery, for a net profit after every fee.

Everything is a pure function of the bars seen so far: no clock, no
environment, no randomness, so two runs on the same data answer alike.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"

# 1.0% below the 60-minute high, turning up.
LOOKBACK = 60
DROP_BPS = 100
# Take profit +1.5%, stop loss -1.0% from the fill price.
TAKE_PROFIT_BPS = 150
STOP_LOSS_BPS = 100
# Longest a position is held: 12 hours (720 bars). A position that has not
# hit its target or its stop by then is sold at the market, so the bot does
# not sit on a stagnant position for the rest of the window and can re-enter
# on the next selloff.
MAX_HOLD_BARS = 720
# Generous: the largest one-minute move on the dev window is about 64 bps.
MAX_SLIPPAGE_BPS = 200

_closes = []
_entry_price = None
_buy_seq = None


def on_batch(state, batch):
    global _entry_price, _buy_seq
    if state.warming_up:
        return []

    # Record the fills of the orders decided on the previous batch. A filled
    # buy sets the entry price the take-profit and stop-loss are measured from,
    # and the batch it filled on, which the maximum hold is measured from.
    for fill in batch.get("fills", []):
        if fill.get("symbol") == SYMBOL and fill.get("status") == "filled":
            if fill.get("side") == "buy":
                _entry_price = int(fill["price"])
                _buy_seq = state.seq
            elif fill.get("side") == "sell":
                _entry_price = None
                _buy_seq = None

    close = state.close(SYMBOL)
    if close is None:
        return []
    _closes.append(close)

    holding = state.positions.get(SYMBOL)

    if holding is None:
        if len(_closes) < LOOKBACK + 6:
            return []
        high = max(_closes[-LOOKBACK - 1:-1])
        # 1.0% below the 60-minute high, and turning up.
        if (
            close * 10_000 < high * (10_000 - DROP_BPS)
            and close > _closes[-2]
            and close > _closes[-6]
        ):
            return [{
                "side": "buy",
                "symbol": SYMBOL,
                "notional_quote_units": state.cash,
                "max_slippage_bps": MAX_SLIPPAGE_BPS,
            }]
        return []

    # Holding: exit on take profit or stop loss, measured from the fill price.
    entry = _entry_price
    if entry is None:
        # No fill seen yet (should not happen): fall back to the latest close
        # as the entry so the position is still managed.
        entry = close
    if close * 10_000 >= entry * (10_000 + TAKE_PROFIT_BPS):
        return [{
            "side": "sell",
            "symbol": SYMBOL,
            "qty": holding.qty,
            "max_slippage_bps": MAX_SLIPPAGE_BPS,
        }]
    if close * 10_000 <= entry * (10_000 - STOP_LOSS_BPS):
        return [{
            "side": "sell",
            "symbol": SYMBOL,
            "qty": holding.qty,
            "max_slippage_bps": MAX_SLIPPAGE_BPS,
        }]
    if _buy_seq is not None and state.seq - _buy_seq >= MAX_HOLD_BARS:
        return [{
            "side": "sell",
            "symbol": SYMBOL,
            "qty": holding.qty,
            "max_slippage_bps": MAX_SLIPPAGE_BPS,
        }]
    return []


makefun_bars.run(on_batch)
