# BIN TRADING ENGINE

Version: 1.1

Source Of Truth

## PROJECT VISION
Build a Bin-based Trading Engine inspired by Meteora DLMM for Binance and OKX.

Core concepts:
- Dynamic ATR Bin
- Single Side Bid
- BOT23
- Hybrid Trailing
- Replay Simulator

## PHASE 0
Simulator only.

Components:
- ATR Engine
- Dynamic Bin
- Event Engine
- Single Side Bid
- BOT23
- Trailing Engine
- Dashboard

## BIN ENGINE
bin_size = ATR(14) * atr_multiplier
Default atr_multiplier = 2

## STRATEGY
Single Side Bid:
Accumulate more inventory as price moves lower.

BOT23:
TP +2 BIN
BUYBACK -3 BIN

## TRAILING
Modes:
- Percent
- Bin
- Hybrid

Default:
Hybrid

trail_peak_pct = 1.5%
trail_peak_bin = 2

Priority:
1. Emergency Stop
2. Trailing Stop
3. BOT23
4. Buyback

## DATA SOURCE
BTCUSDT 1m CSV replay.

## DASHBOARD
Pages:
1. Control Center
2. Bin Visualizer
3. Price Replay
4. Trade Log
5. Portfolio
6. Analytics
7. Strategy Lab
8. Trailing Lab
9. Bin Analyzer
