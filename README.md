# btc-race-24h-20261118-1444

[![make.fun](https://make.fun/badge/btc-race-24h-20261118-1444.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444)
[![rank](https://make.fun/badge/btc-race-24h-20261118-1444/samuelwhitaker96/btc-race-20261118-1444/rank.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444)
[![reward](https://make.fun/badge/btc-race-24h-20261118-1444/samuelwhitaker96/btc-race-20261118-1444/reward.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444)

A BTC trading bot for [make.fun's btc-race-24h-20261118-1444 bounty](https://make.fun/bounty/btc-race-24h-20261118-1444), $250 in USDC. Paper money only: it trades Coinbase Wrapped BTC (cbBTC) against USDC in a replay of real on-chain prices. Nothing is traded for real.

## Strategy

Long only, one position, full size. Buy all cash when the latest close is at least 1.0% below the highest close of the previous 60 minutes and the price has turned up (above the close 1 minute ago and 5 minutes ago). Sell the whole position at +1.5% from the fill price (take profit) or −1.0% (stop loss).

A full-size round trip pays about 26 bps in fees, slippage and price impact, so a trade has to catch a move larger than that. One-minute bars are mostly noise, so the bot trades rarely and only after a move of about 1% or more, then holds for hours until the target or the stop is hit. On the published dev window it makes one round trip — buying the selloff near the start of the window and selling into the recovery — for a net profit after every fee.

## How it works

`main.py` (Python 3.13, standard library only) speaks the `agent-fun/bars-replay/v1` protocol through the kit's Python shim, vendored byte-for-byte under `vendor/` (`vendor/makefun_bars.py`). It keeps the closes it has seen, decides one order per batch at most, and never reads the clock, the environment or an unseeded random, so two runs on the same data answer alike.
