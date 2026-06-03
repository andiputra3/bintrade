# BIN TRADING ENGINE

Version: 1.1
Status: DESIGN PHASE
Source Of Truth: TRUE

---

# PROJECT VISION

Membangun Trading Engine berbasis BIN yang terinspirasi dari Meteora DLMM untuk:

- Binance Spot
- Binance Futures
- OKX Spot
- OKX Futures

BIN adalah unit utama keputusan.

Harga -> BIN -> EVENT -> ACTION

Contoh:

ENTER_BIN
→ BUY
→ TAKE_PROFIT
→ BUYBACK
→ COMPOUND GROWTH

---

# DEVELOPMENT ORDER

## PHASE 0
Simulator Only

Target:
- ATR Engine
- Dynamic Bin
- Event Engine
- Single Side Bid
- BOT23
- Hybrid Trailing
- Replay Simulator
- Dashboard

DO NOT IMPLEMENT YET:
- Live Trading
- Telegram
- Discord
- AI Agent
- Darwin
- Funding/OI/Liquidation

## PHASE 1
Exchange Integration
- Binance Spot/Futures
- OKX Spot/Futures

## PHASE 2
Market Intelligence
- Funding
- Open Interest
- Liquidation

## PHASE 3
AI Layer
- Probability Engine
- Darwin Learning
- Regime Detection

---

# SYSTEM ARCHITECTURE

Data Layer
- CSV Loader
- Kline Parser
- Replay Engine

Core Layer
- ATR Engine
- Bin Builder
- Event Engine
- Inventory Engine
- Risk Engine

Strategy Layer
- Single Side Bid
- BOT23
- Trailing Engine

Analytics Layer
- Metrics
- Equity Curve
- Drawdown

Dashboard Layer
- Control Center
- Bin Visualizer
- Replay
- Portfolio
- Strategy Lab

---

# BIN ENGINE

Dynamic ATR Bin:

bin_size = ATR(14) × atr_multiplier

Default:
atr_multiplier = 2

BIN 0 = current price
BIN +1 = above price
BIN -1 = below price

---

# BIN STATE

Each bin stores:
- bin_id
- lower_price
- upper_price
- allocation
- inventory
- hit_count
- realized_pnl
- unrealized_pnl
- last_event

---

# EVENT ENGINE

Allowed Events:
- ENTER_BIN
- EXIT_BIN
- BUY
- SELL
- BUYBACK
- TAKE_PROFIT
- STOP_LOSS
- TRAILING_STOP
- TRAILING_TP
- TRAILING_ARMED
- PEAK_UPDATE
- BIN_RECENTER

No strategy may bypass Event Engine.

---

# STRATEGY 1 - SINGLE SIDE BID

Purpose:
Accumulate inventory as price moves lower.

Example Distribution:

BIN -1 = 10
BIN -2 = 15
BIN -3 = 20
BIN -4 = 30
BIN -5 = 40
BIN -6 = 55
BIN -7 = 75
BIN -8 = 100
BIN -9 = 140
BIN -10 = 200

Distribution Modes:
- Linear
- Exponential
- Meteora (Default)

---

# STRATEGY 2 - BOT23

Default Variant

TP +2 BIN
BUYBACK -3 BIN
SELL = 20%

Variants:
- BOT11
- BOT22
- BOT23
- BOT35

---

# INVENTORY MODEL

Track:
- cash
- inventory_qty
- inventory_value
- average_entry
- realized_pnl
- unrealized_pnl
- equity

---

# POSITION MODEL

Track:
- position_id
- entry_price
- entry_bin
- qty
- remaining_qty
- realized_pnl
- status

---

# RISK ENGINE

Track:
- max_position_pct
- max_capital_per_bin
- max_daily_loss_pct
- max_drawdown_pct
- max_leverage

Violation:
REJECT_ORDER

---

# TRAILING ENGINE

Default Mode:
HYBRID

Percent Trailing:
trail_peak_pct = 1.5%

Bin Trailing:
trail_peak_bin = 2

Hybrid:
Exit when either rule triggers.

Partial Trailing:
25% → 25% → 50%

Priority:
1. Emergency Stop Loss
2. Trailing Stop
3. Trailing Take Profit
4. BOT23
5. Buyback

---

# DATA SOURCE

BTCUSDT
Timeframe: 1 Minute
Source: Binance Klines

Replay from CSV only in Phase 0.

CSV Format:
- timestamp
- open
- high
- low
- close

---

# REPLAY ENGINE

For every candle:
1. Update ATR
2. Update BIN
3. Generate Events
4. Execute Strategy
5. Update Inventory
6. Update PnL
7. Update Dashboard

No future candle access allowed.

---

# RESULT CSV

Columns:
- timestamp
- price
- bin
- event
- action
- qty
- cash
- inventory
- equity
- realized_pnl
- unrealized_pnl

---

# DASHBOARD

Framework: Streamlit
Target: 2 CPU / 2GB RAM

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

---

# PHASE 0 SUCCESS CRITERIA

[ ] Load BTCUSDT 1m CSV
[ ] Calculate ATR
[ ] Build Dynamic Bin
[ ] Generate ENTER_BIN events
[ ] Execute Single Side Bid
[ ] Execute BOT23
[ ] Execute Trailing Engine
[ ] Generate Trade Log
[ ] Generate PnL
[ ] Dashboard Replay Works
[ ] Dashboard Strategy Lab Works

---

# SOURCE OF TRUTH

If code conflicts with this document:
Follow MASTER_SPEC.md.
