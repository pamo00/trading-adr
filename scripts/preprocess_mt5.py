"""Preprocess MT5 M5 and D1 CSV exports (historical data) for backtesting.

The script reads every CSV file from ``data/raw/``, renames MT5 columns,
normalizes timestamps, adds ``holiday`` and ``backtest_eligible_adr`` flags,
and writes the processed files to ``data/processed/`` using their source
filenames. M5 data marks 27 and 28 November 2025 as holidays; D1 data uses
``holiday=False`` and ``backtest_eligible_adr=True`` for every row.

Usage:
    python scripts/preprocess_mt5.py

"""


from pathlib import Path

import pandas as pd


COLUMN_MAP = {
    "<DATE>": "date",
    "<TIME>": "time",
    "<OPEN>": "open",
    "<HIGH>": "high",
    "<LOW>": "low",
    "<CLOSE>": "close",
    "<TICKVOL>": "tick_volume",
    "<VOL>": "real_volume",
    "<SPREAD>": "spread",
}

ADR_HOLIDAYS = pd.to_datetime(["2025-11-27", "2025-11-28"])
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data/raw"
OUTPUT_DIR = PROJECT_ROOT / "data/processed"


def preprocess(source: Path, destination: Path, apply_adr_holidays: bool = False) -> None:
    if source.resolve() == destination.resolve():
        raise ValueError("Input and output must be different files; keep raw data unchanged.")

    # MT5 exports are usually tab-separated; automatic detection also accepts commas.
    df = pd.read_csv(source, sep=None, engine="python", encoding="utf-8-sig")
    required = set(COLUMN_MAP) - {"<TIME>"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing MT5 columns: {sorted(missing)}. Found: {list(df.columns)}")

    datetime_values = df["<DATE>"].astype(str)
    if "<TIME>" in df.columns:
        datetime_values = datetime_values + " " + df["<TIME>"].astype(str)

    df.insert(
        0,
        "datetime",
        pd.to_datetime(
            datetime_values,
            format="%Y.%m.%d %H:%M:%S" if "<TIME>" in df.columns else "%Y.%m.%d",
            errors="raise",
        ),
    )
    df = df.drop(columns=[column for column in ("<DATE>", "<TIME>") if column in df]).rename(
        columns=COLUMN_MAP
    )
    if df["datetime"].duplicated().any():
        raise ValueError("Duplicate candle timestamps found; inspect source before processing.")
    if not df["datetime"].is_monotonic_increasing:
        raise ValueError("Candles are not in chronological order; inspect source before processing.")

    df["holiday"] = False
    if apply_adr_holidays:
        df["holiday"] = df["datetime"].dt.normalize().isin(ADR_HOLIDAYS)
    df["backtest_eligible_adr"] = ~df["holiday"]

    destination.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(destination, index=False, date_format="%Y-%m-%d %H:%M:%S")
    print(f"Saved {len(df):,} candles to {destination}")


if __name__ == "__main__":
    sources = sorted(RAW_DIR.glob("*.csv"))
    if not sources:
        raise ValueError(f"No raw CSV files found in {RAW_DIR}")

    for source in sources:
        preprocess(source, OUTPUT_DIR / source.name, apply_adr_holidays="M5" in source.stem.upper())
