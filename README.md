# Systematic Trading Research & Automation

> **Status: Research / prototype.** No live strategy or profitable trading edge has been validated yet. This repository is intended to research, backtest, and eventually automate systematic trading strategies—not to present historical examples as investment results.

## 1. Project objective

Develop a **Python-first, data-driven trading research and automation system** that can:

- Retrieve and store historical market data.
- Analyze intraday price behavior and volatility.
- Formulate measurable trading hypotheses and test them without lookahead bias.
- Backtest realistic entry, stop-loss, take-profit, position-sizing, and session-exit rules.
- Compare strategies across instruments and market regimes.
- Validate promising strategies with more granular data before any live execution.
- Eventually execute and manage trades automatically through a supported broker/platform connection.

**Initial research focus:** an **Average Daily Range (ADR) strategy** using the **market/session open**, not the operator's personal trading hours. The bot should be able to enter at the market open and manage the trade through the session without manual intervention.

### Intended markets

| Instrument | Notes |
| --- | --- |
| **US100** | Nasdaq-100-related CFD; initial priority for research. |
| **US500** | S&P 500-related CFD; comparison market. |
| **BTC/USD** | 24/7 market; the definition of a “daily open” must be explicit. |
| **XAU/USD** | Gold CFD; broker sessions and spreads matter. |
| **EUR/USD** | Optional additional comparison market. |

**Important:** CFD quotes and contract specifications may differ from the corresponding cash indices, futures, exchange spot markets, and TradingView symbols. Prefer data from the same trading environment intended for execution (e.g., FTMO-compatible MT5 symbols, if the account supports MT5).

## 2. Core hypothesis: daily open + ADR

A trading day often exhibits a measurable high-to-low range. The research question is whether yesterday's information (including historical ADR and trend) can help build a **profitable, executable strategy from today's market open**.

Define **ADR(N)** as the mean **high − low** of the **previous N completed trading sessions**:

$$
ADR_N(t) = \frac{1}{N} \sum_{i=1}^{N}\left(H_{t-i}-L_{t-i}\right)
$$

The calculation **must exclude the current session**. Session definitions must be consistent across the lookback and the day being traded.

Starting parameter: **N = 14 sessions**, with 20 as a comparison.

For a session opening price `O`:

| Level | Long | Short |
| --- | --- | --- |
| Entry | `O` (first realistically executable quote) | `O` (first realistically executable quote) |
| TP1 | `O + 0.50 × ADR` | `O − 0.50 × ADR` |
| TP2 | `O + 1.00 × ADR` | `O − 1.00 × ADR` |
| Example initial SL | `O − 1.20 × ADR` | `O + 1.20 × ADR` |
| Exit | Close remaining exposure at session end | Close remaining exposure at session end |

**Provisional trade management:** close 50% at TP1 and 50% at TP2; test whether moving the remaining stop to break-even after TP1 improves outcomes. The **1.20 × ADR stop is only a test parameter**, not an optimized or recommended live stop.

**Example (illustrative US100 prices, not a backtest):** session open = 30,000; ADR(14) = 400; long TP1 = 30,200; TP2 = 30,400; SL = 29,520. A full winner with equally weighted exits earns **0.75 ADR**, while a full stop loses **1.20 ADR**, before costs. If all trades had only those two outcomes, the break-even win rate would be approximately **61.5%**. Actual partial exits and session-end closures change this calculation.

### Critical limitation: ADR does not determine direction

ADR measures the **entire session high-to-low distance**. It is **not** the average move from the open to the high or low and does **not** tell us whether to buy or sell. A target being touched is not the same as a profitable, executable trade.

Evaluate directional rules separately rather than assuming that a long or short entry at the open has an edge.

### Strategy variants to compare

1. **Baseline A — always long at open:** useful benchmark for underlying upward drift.
2. **Baseline B — always short at open:** corresponding short-side benchmark.
3. **Candidate C — previous-session trend filter:** e.g., previous close above the *previously known* 20-session moving average → long; below → short. Treat this as a hypothesis, not a validated signal.
4. **Candidate D — opening-range breakout + ADR targets:** wait for a confirmed breakout of a predefined early-session range. This is a different entry strategy, included as an optional comparison.
5. **Other controls:** random-direction benchmark, no-trade benchmark, and alternative stop/exit rules.

No parameter combination should be described as optimal without out-of-sample evidence.

## 3. Market-open and close definitions

The strategy targets the **instrument's relevant market session**, not the operator's usual evening analysis window.

- **US100 / US500:** initial reference session = **09:30–16:00 America/New_York**, approximating US cash equity hours. This is a **research choice**; the actual CFD quote and execution hours may differ. Account for daylight-saving transitions and holidays.
- **BTC/USD:** operates 24/7; select and document a consistent daily cutoff (e.g., **00:00 UTC**) and test whether changing that boundary materially affects results.
- **XAU/USD / EUR/USD:** specify broker-defined session breaks, rollovers, and calendar conventions instead of assuming a universally valid daily open.
- **Daily ADR:** calculate from high/low prices belonging to the same defined session; do not mix broker midnight candles with US regular-session targets unintentionally.

Use **timezone-aware UTC timestamps internally**, convert to exchange/session time when assigning session labels, and preserve the broker's original timestamp rules.

## 4. Research questions before backtesting trades

For each instrument and session definition, measure:

- Distribution of `high − low` and of `high − open` versus `open − low`.
- How often price reaches **±25%, ±50%, ±75%, and ±100% of prior ADR** from the open.
- Which of the upside/downside thresholds occurs **first**, not merely whether both occur during a session.
- Frequency of both directions being touched and the time needed to reach each threshold.
- **Maximum favorable excursion (MFE)** and **maximum adverse excursion (MAE)** after entry.
- Variation by weekday, volatility regime, trend regime, and market opening conditions.
- Sensitivity to 14 vs. 20-session ADR and to different market-session boundaries.

**First deliverable:** an instrument-by-instrument statistical report, **not** a trading-profit claim.

## 5. Data sources and quality requirements

### First approach — MT5 manual CSV export on macOS (Apple Silicon M1)

**Current default: MT5 → CSV → pandas → Parquet → offline research/backtesting.** The initial priority is historical data, not up-to-the-minute candles or automated trading. This is the fastest low-complexity approach on a Mac M1: **no Docker, Wine-based Python bridge, Windows virtual machine, or third-party MT5 Python package required**. MT5 itself must be installed and able to access historical data from the intended broker.

1. In the macOS MetaTrader 5 terminal, go to **View → Symbols → Bars** (interface wording can vary by terminal build).
2. Choose the broker's exact symbol (begin with **US100**), select **M5**, choose a historical date range, click **Request** if available, then **Export** to CSV. Aim for **2–3 years** if your broker provides it; otherwise start with available history. Later, retrieve **M1** or historical ticks to resolve ambiguous intrabar fills.
3. Save the untouched export in `data/raw/`, e.g. `data/raw/US100_M5.csv`. Record the broker, symbol, export date, timeframe, and **the time-zone convention actually used by the terminal**; do not assume exported timestamps are UTC.
4. Use a **native ARM64 Python environment** on your M1, import the CSV, validate the bars, then store a processed Parquet copy in `data/processed/`.
5. Run ADR research and early backtests locally. Refresh manually only when newer history becomes necessary.

Install minimal Python dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install pandas pyarrow
```

Example loader for a typical **tab-separated MT5 Bars export** with `<DATE>`, `<TIME>`, `<OPEN>`, `<HIGH>`, `<LOW>`, `<CLOSE>`, and volume/spread columns (inspect your own file first; some exports use other delimiters):

```python
from pathlib import Path
import pandas as pd

raw = Path("data/raw/US100_M5.csv")
out = Path("data/processed/US100_M5.parquet")
out.parent.mkdir(parents=True, exist_ok=True)

# sep=None lets pandas infer tab/comma/semicolon delimiters for this small import.
df = pd.read_csv(raw, sep=None, engine="python")
df.columns = df.columns.str.strip().str.strip("<>").str.lower()

required = {"date", "time", "open", "high", "low", "close"}
missing = required - set(df.columns)
if missing:
    raise ValueError(f"Missing MT5 columns: {sorted(missing)}; found {list(df.columns)}")

df["datetime"] = pd.to_datetime(
    df["date"].astype(str) + " " + df["time"].astype(str),
    format="%Y.%m.%d %H:%M:%S",
    errors="raise",
)
df = df.set_index("datetime").sort_index()
if df.index.has_duplicates:
    raise ValueError("Duplicate candle timestamps; inspect the original export")
if df[["open", "high", "low", "close"]].isna().any().any():
    raise ValueError("Missing OHLC values")

# Index timestamps remain naive pending explicit broker/terminal timezone validation.
# Localize/convert only after confirming their original timezone.
df.to_parquet(out)
print(f"Saved {len(df):,} bars to {out}")
```

**Limits:** M5 bars do not reveal which of SL/TP was hit first when both fall inside a candle; exported bars may not include executable bid/ask or complete historical spreads. Validate strategy sensitivity to costs and ambiguous fills before drawing profitability conclusions.

### Later upgrade — automated MT5 data retrieval

If repeated data updates or automated execution become necessary, evaluate **official `MetaTrader5` Python integration with an MT5 terminal on Windows** (VM/VPS) to retrieve M5/M1 candles and available bid/ask ticks. The official integration does not run natively on macOS; Wine/Docker/third-party bridges on M1 add substantial compatibility and security complexity. Do **not** make these dependencies part of the initial research milestone.

### Alternatives

- **TradingView CSV export:** convenient for a first experiment, but manual and potentially limited in history.
- **Coinbase exchange API:** useful for BTC/USD research; exchange prices differ from CFD execution prices.
- **Yahoo Finance / `yfinance`:** exploratory benchmarks and certain daily series, **not** a substitute for realistic CFD intraday fills.
- **Databento / futures data:** higher-quality exchange data for NQ, ES, and gold futures; still different instruments from CFDs.
- **Other data APIs (e.g., Twelve Data):** evaluate history, coverage, timestamp conventions, and cost before use.

### Data validation

Check duplicate/missing bars, timestamp shifts, holiday calendars, session boundaries, price precision, changes in contract specifications, and gaps. Preserve original raw data; use local **Parquet** storage with metadata indicating source, symbol, timezone, timeframe, and download date.

## 6. Backtesting design and realism

### Fast research phase

Recommended Python stack:

- `pandas`, `numpy` — data cleaning and statistical analysis.
- Manual MT5 CSV → Parquet import — **first approach on Mac M1**; `MetaTrader5` is a later Windows-based automation option.
- `jupyterlab` — exploratory notebooks.
- `backtesting` (**Backtesting.py**) — initial trade simulation and analytics.
- `matplotlib` or `plotly` — equity curves, distributions, and trade plots.
- `pyarrow` — Parquet storage.

Optional later: `vectorbt` for many parameter scenarios, `optuna` for carefully controlled optimization, and `quantstats` for reporting.

### Realism and execution checks

A backtest must model or explicitly report its assumptions for:

1. **No lookahead:** compute ADR and signal inputs exclusively from completed prior sessions.
2. **Entry timing:** the session-open reference price is not always executable; enter at the first available tradable bid/ask quote and account for any opening spread/gap.
3. **Bid/ask spread, commission, financing, and slippage:** use broker-relevant information where available.
4. **Stop/target sequencing:** M5 OHLC alone cannot always determine whether SL or TP was hit first inside a candle. Use conservative assumptions or replay M1/ticks; never award an optimistic fill silently.
5. **Order management:** partial TP1/TP2 fills, remaining stop, break-even rules, and session-end flattening.
6. **Sizing:** correct CFD contract size, price-per-point, quote currency conversion, lot step, minimum volume, and margin.
7. **Market conditions:** trading halts, holidays, sessions, spread spikes, rollover, and data outages.
8. **Risk controls:** daily/session loss limits, open positions and exposure, correlated index positions, and broker/program-specific restrictions.

**Final verification option:** validate a promising system with **MT5 Strategy Tester** using real ticks where available. MT5's native tester runs **MQL5 Expert Advisors**, so this step may require porting the rules from Python to MQL5. A Python-only alternative is a tick/event-driven simulator such as **NautilusTrader**, provided comparable bid/ask data exists.

### Performance evaluation

Report at least: trade count, win rate, average R, expectancy **net of costs**, profit factor, maximum drawdown, equity curve, return variability, longest losing streak, average holding time, MFE/MAE, exposure, and results by month/year/market regime.

Use **chronological train/validation/test splits**, out-of-sample and walk-forward testing. Avoid choosing parameters on the final holdout sample. Compare with the baseline strategies, stress-test execution costs, and inspect sensitivity rather than only reporting the best parameter set. If many strategies are tried, account for selection/overfitting risk.

## 7. Risk management and automated execution

### Initial user-defined research risk profile

These are **configurable example account limits**, not current broker or FTMO contractual limits:

| Setting | Example |
| --- | ---: |
| Normal setup risk | **$25 per trade** |
| A+ setup risk | **$35 per trade** |
| Maximum trade attempts per session | **2** |
| Absolute session risk ceiling | **$97** |
| Trade management | TP1/TP2 partial exits; optional SL-to-BE test |

Size positions from the stop distance and the symbol's verified monetary point value, e.g. `volume = risk_budget / (stop_distance × money_per_price_unit_per_lot)` before rounding to valid lot increments and checking costs and margin. **Do not assume “points” or lot values are consistent across assets.** Reject trades that violate the risk or execution constraints.

A production bot should:

- Run on a dependable environment at the configured market opening (or on a continuously running service).
- Load only completed prior-session data and calculate the signal and ADR.
- Confirm session status, tradable quotes, acceptable spread, and remaining account risk.
- Submit appropriately sized orders with protective exits, using broker-supported order types.
- Prevent duplicate entries on restart, persist position/order state, and reconcile with broker positions.
- Manage TP1/TP2, residual stops, and session-close liquidation.
- Stop safely on connectivity errors, rejected orders, stale data, or rule breaches.
- Log signals, orders, fills, transaction costs, errors, and resulting P&L.
- Alert on failures and require periodic oversight; “automated” does not mean risk-free or maintenance-free.

**FTMO compatibility must be checked against the applicable account type and current rules before deployment**, including any algorithmic trading, daily loss, maximum loss, and prohibited-practice requirements. Start with **backtests → paper/demo forward tests → tightly controlled live deployment only if justified**. Do not use the verification account as the initial experiment.

## 8. Proposed repository structure

```text
trading-research/
├── README.md
├── requirements.txt
├── config/
│   └── research.yaml            # markets, sessions, parameters, costs, risk
├── data/
│   ├── raw/                     # original downloaded data (prefer Git-ignored)
│   └── processed/               # validated/session-labeled Parquet files
├── src/
│   ├── data_loader.py           # download/import market data
│   ├── sessions.py              # market calendars and time zones
│   ├── indicators.py            # ADR and other indicators
│   ├── adr_analysis.py          # descriptive statistical research
│   ├── signals.py               # long/short/flat rules
│   ├── strategies.py            # backtest-ready strategy definitions
│   ├── backtest.py              # simulation and realistic cost assumptions
│   ├── risk.py                  # position sizing and risk checks
│   ├── performance.py           # expectancy, drawdown, robustness
│   └── execution/              # future broker bot; not initially live
├── notebooks/                   # research notebooks
├── tests/                       # no-lookahead, sizing, session and fill tests
└── results/                     # reports, metrics, plots (large outputs Git-ignored)
```

The structure is **planned**; directories/modules should only be marked as implemented when actual code exists. Keep broker credentials, secrets, and private account data out of Git.

## 9. Development roadmap

- [ ] **Phase 1 — Data (Mac M1, manual first):** export US100 M5 candles from MT5 as CSV, import with pandas, validate the terminal timezone, and store Parquet. Target at least 2–3 years if available; ensure the same 09:30–16:00 New York sessions are used throughout. Add automated retrieval only if needed.
- [ ] **Phase 2 — Descriptive ADR research:** quantify historical target-touch rates, first-touch sequencing, intraday excursions, and regime sensitivity.
- [ ] **Phase 3 — Simple backtest:** implement long-only, short-only, and basic trend-filter variants with TP1/TP2, configurable stop, end-of-day exit, and realistic estimated costs.
- [ ] **Phase 4 — Robustness:** evaluate walk-forward/out-of-sample performance, sensitivity to costs/parameters, baselines, and failure regimes.
- [ ] **Phase 5 — Better execution realism:** replay lower-timeframe/tick data, verify broker specifications and compare with MT5 Strategy Tester or another execution simulator.
- [ ] **Phase 6 — Other instruments:** test US500, BTC/USD, XAU/USD, and optionally EUR/USD with asset-specific session rules.
- [ ] **Phase 7 — Demo automation:** paper trade, log every signal/fill/error, add alerts and a kill switch; only consider live deployment after validation.

**Initial milestone:** determine whether an ADR-based market-open strategy on **US100** achieves robust **positive net expectancy**, not merely a high target-touch rate or visually attractive historical trades.

## 10. Interpretation and limitations

- No backtest of the **exact rules** above has been completed in this project.
- Literature and online examples concerning ADR, average true range (ATR), and opening-range breakouts are **related but not equivalent**; their results do not prove this strategy's profitability.
- A **high win rate does not guarantee profitability**, especially when stops are wider than average realized profits.
- **Positive backtests do not guarantee live results**. Strategy selection, slippage, spreads, and regime changes can erase apparent advantages.
- The system is for research and engineering purposes; users remain responsible for risk management and compliance with their trading platform's rules.

## 11. Useful documentation

- [MetaTrader 5 — Python integration](https://www.mql5.com/en/docs/python_metatrader5)
- [MetaTrader 5 — Strategy Tester](https://www.metatrader5.com/en/automated-trading/strategy-tester)
- [Backtesting.py](https://kernc.github.io/backtesting.py/)
- [VectorBT](https://vectorbt.dev/)
- [NautilusTrader](https://nautilustrader.io/)
