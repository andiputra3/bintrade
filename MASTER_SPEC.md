# MASTER_SPEC.md

# BIN TRADING ENGINE

Version: 1.1

Status: DESIGN PHASE

Source Of Truth: TRUE

---

# PROJECT VISION

Tujuan proyek adalah membangun Trading Engine berbasis Bin yang terinspirasi dari Meteora DLMM tetapi diterapkan pada:

* Binance Spot
* Binance Futures
* OKX Spot
* OKX Futures

Sistem tidak menggunakan Grid Trading klasik.

Unit utama keputusan adalah BIN.

Semua strategi bekerja berdasarkan perpindahan antar BIN.

---

# CORE PHILOSOPHY

Harga bergerak.

Harga masuk dan keluar BIN.

Perpindahan BIN menghasilkan EVENT.

EVENT memicu aksi.

Contoh:

ENTER_BIN

↓

BUY

↓

TAKE_PROFIT

↓

BUYBACK

↓

COMPOUND GROWTH

---

# DEVELOPMENT ORDER

## PHASE 0

Simulator Only

Belum ada:

* Binance Trading
* OKX Trading
* AI
* Telegram
* Discord

Target:

* ATR Engine
* Dynamic Bin
* Event Engine
* Single Side Bid
* BOT23
* Trailing Engine
* Replay Simulator
* Dashboard

---

## PHASE 1

Exchange Integration

* Binance Spot
* Binance Futures
* OKX Spot
* OKX Futures

---

## PHASE 2

Market Intelligence

* Funding Rate
* Open Interest
* Liquidation Data

---

## PHASE 3

AI Layer

* Probability Engine
* Darwin Learning
* Regime Detection

---

# BIN ENGINE

## DYNAMIC ATR BIN

Bin tidak menggunakan ukuran tetap.

Formula:

bin_size = ATR(14) × atr_multiplier

Default:

atr_multiplier = 2

Contoh:

ATR = 50

bin_size = 100

---

## BIN NUMBERING

BIN 0

adalah harga saat ini.

BIN +1

di atas harga.

BIN -1

di bawah harga.

Contoh:

Price = 105000

Bin Size = 100

BIN +1 = 105100

BIN +2 = 105200

BIN -1 = 104900

BIN -2 = 104800

---

# BIN STATE

Setiap BIN wajib menyimpan:

bin_id

lower_price

upper_price

allocation

inventory

status

last_event

hit_count

realized_pnl

unrealized_pnl

---

# EVENT ENGINE

Event yang diizinkan:

ENTER_BIN

EXIT_BIN

BUY

SELL

BUYBACK

TAKE_PROFIT

STOP_LOSS

TRAILING_STOP

TRAILING_TP

TRAILING_ARMED

PEAK_UPDATE

BIN_RECENTER

Tidak boleh ada strategi yang bypass Event Engine.

---

# STRATEGY 1

SINGLE SIDE BID

Tujuan:

Akumulasi inventory saat harga turun.

Semakin harga turun semakin besar posisi.

Contoh distribusi:

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

Semakin jauh dari harga saat ini:

Semakin besar ukuran posisi.

---

# DISTRIBUTION MODES

## LINEAR

10

20

30

40

50

---

## EXPONENTIAL

10

20

40

80

160

---

## METEORA

10

12

15

20

28

40

55

75

100

145

Default:

METEORA

---

# STRATEGY 2

BOT23

Definisi resmi.

TP +2 BIN

BUYBACK -3 BIN

Default Sell:

20%

---

Contoh:

Entry BIN -4

Naik ke BIN -2

SELL 20%

Naik ke BIN 0

SELL 20%

Naik ke BIN +2

SELL 20%

Jika harga turun 3 BIN dari TP terakhir:

BUYBACK

---

# BOT VARIANTS

BOT11

TP +1

BUYBACK -1

---

BOT22

TP +2

BUYBACK -2

---

BOT23

TP +2

BUYBACK -3

---

BOT35

TP +3

BUYBACK -5

---

Default:

BOT23

---

# INVENTORY MODEL

Track:

cash

inventory_qty

inventory_value

average_entry

realized_pnl

unrealized_pnl

equity

---

# RISK ENGINE

Mandatory.

Track:

max_position_pct

max_capital_per_bin

max_daily_loss_pct

max_drawdown_pct

max_leverage

Jika melanggar:

REJECT_ORDER

---

# TRAILING ENGINE

Tujuan:

Mengunci profit saat market berbalik arah.

Mode:

Percent

Bin

Hybrid

Default:

Hybrid

---

## PERCENT TRAILING

Trailing berdasarkan harga tertinggi sejak posisi dibuka.

Parameter:

trail_peak_pct

Default:

1.5%

Contoh:

Entry = 100

Peak = 120

Trailing Exit:

120 × (1 - 0.015)

=

118.2

Jika harga <= 118.2

SELL ALL

---

## BIN TRAILING

Trailing berdasarkan BIN.

Parameter:

trail_peak_bin

Default:

2

Contoh:

Peak BIN = +10

Trailing = 2 BIN

Jika harga turun ke:

BIN +8

SELL ALL

---

## HYBRID TRAILING

Percent dan Bin berjalan bersamaan.

Parameter:

trail_peak_pct = 1.5%

trail_peak_bin = 2

Exit jika salah satu terpenuhi.

---

## PARTIAL TRAILING

Mode:

sell_partial

Trigger 1:

SELL 25%

Trigger 2:

SELL 25%

Trigger 3:

SELL 50%

---

## TRAILING STATE

Track:

highest_price

highest_bin

trailing_price

trailing_bin

active

armed

---

# EXECUTION PRIORITY

Urutan prioritas:

1. Emergency Stop Loss
2. Trailing Stop
3. Trailing Take Profit
4. BOT Strategy
5. Buyback

---

# DATA SOURCE

PHASE 0

Binance Klines

BTCUSDT

1 Minute

Contoh:

https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=1000

Data disimpan ke CSV.

Format:

timestamp

open

high

low

close

---

# REPLAY ENGINE

Simulator membaca candle satu per satu.

Tidak boleh melihat candle masa depan.

Replay harus realistis.

Setiap candle:

Update ATR

Update BIN

Generate Event

Execute Strategy

Update Inventory

Update PnL

Update Dashboard

---

# BACKTEST METRICS

cash

inventory

realized_pnl

unrealized_pnl

total_pnl

equity

max_drawdown

profit_factor

win_rate

trade_count

buy_count

sell_count

buyback_count

tp_count

trailing_exit_count

---

# DASHBOARD

Framework:

Streamlit

Target:

2 CPU

2GB RAM

---

# PAGE 1

CONTROL CENTER

Fungsi:

Start Simulation

Pause Simulation

Stop Simulation

Reset Simulation

Load CSV

Download Results

Konfigurasi:

Capital

ATR Multiplier

Distribution Mode

BOT Variant

Risk Settings

Trailing Settings

---

# PAGE 2

BIN VISUALIZER

Visualisasi:

BIN +20

...

BIN +1

BIN 0

BIN -1

...

BIN -20

Tampilkan:

Allocation

Inventory

Hit Count

Current Price

Current Bin

Highlight BIN aktif

---

# PAGE 3

PRICE REPLAY

Candlestick Replay

Play

Pause

Speed x1

Speed x10

Speed x100

Jump To Timestamp

Overlay:

BUY

SELL

BUYBACK

TP

TRAILING

---

# PAGE 4

TRADE LOG

Time

Price

Bin

Action

Size

PnL

Filter:

BUY

SELL

BUYBACK

TP

TRAILING

STOP

---

# PAGE 5

PORTFOLIO

Cash

Inventory

Average Entry

Equity

Realized PnL

Unrealized PnL

Total PnL

---

# PAGE 6

ANALYTICS

Equity Curve

Drawdown Curve

Trade Distribution

Bin Usage

Event Frequency

Profit Per Bin

---

# PAGE 7

STRATEGY LAB

Tujuan:

Menguji strategi tanpa coding.

Input:

TP Bin

Buyback Bin

Sell Percent

Distribution

ATR Multiplier

Output:

PnL

Drawdown

Win Rate

Trade Count

---

# PAGE 8

TRAILING LAB

Visualisasi:

Current Price

Peak Price

Trailing Price

Peak Bin

Trailing Bin

Exit Projection

Konfigurasi:

trail_peak_pct

trail_peak_bin

mode

---

# PAGE 9

BIN ANALYZER

Tampilkan:

Most Active Bin

Least Active Bin

Profit Per Bin

Inventory Per Bin

Hit Count Per Bin

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

# DO NOT IMPLEMENT YET

* Live Binance Trading
* Live OKX Trading
* Futures Live Orders
* Telegram
* Discord
* AI Agent
* Darwin
* Funding Analysis
* Open Interest Analysis
* Liquidation Analysis

Focus only on Simulator.

---

# SOURCE OF TRUTH

File ini adalah sumber kebenaran proyek.

Jika ada konflik antara kode dan dokumen:

Ikuti MASTER_SPEC.md

Jangan mengubah definisi strategi tanpa persetujuan pengguna.
