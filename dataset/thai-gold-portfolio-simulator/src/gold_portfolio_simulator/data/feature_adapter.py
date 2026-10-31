"""Adapters for the processed Thai gold feature dataset."""
from __future__ import annotations

import numpy as np
import pandas as pd


FEATURE_COLUMNS = {
    "timestamp": "timestamp_parsed",
    "ornament_buy": "ornament_buy",
    "bar_buy": "bar_buy",
    "bar_sell": "bar_sell",
    "ornament_sell": "ornament_sell",
    "gold_spot": "gold_spot_clean",
    "usd_thb": "thb_usd_clean",
    "change": "change",
}


def feature_prices_to_simulator_input(features: pd.DataFrame) -> pd.DataFrame:
    """Map processed features to the simulator's canonical quote schema.

    ``valid_price_pair`` in the feature dataset means that a prior same-day
    observation exists for calculating a price change; it is not a quote
    validity flag. Therefore all rows are retained when their actual quote
    prices are valid.
    """
    missing = [column for column in FEATURE_COLUMNS.values()
               if column not in features.columns]
    if missing:
        raise ValueError(f"Feature dataset is missing required columns: {missing}")

    out = pd.DataFrame({
        "timestamp": pd.to_datetime(features["timestamp_parsed"], errors="coerce"),
        "ornament_buy_thb": pd.to_numeric(features["ornament_buy"], errors="coerce"),
        "bar_buy_thb": pd.to_numeric(features["bar_buy"], errors="coerce"),
        "bar_sell_thb": pd.to_numeric(features["bar_sell"], errors="coerce"),
        "ornament_sell_thb": pd.to_numeric(features["ornament_sell"], errors="coerce"),
        "ornament_tax_base_thb": np.nan,
        "gold_spot_usd": pd.to_numeric(features["gold_spot_clean"], errors="coerce"),
        "usd_thb": pd.to_numeric(features["thb_usd_clean"], errors="coerce"),
        "change_thb": pd.to_numeric(features["change"], errors="coerce"),
        "announce_seq": np.arange(len(features), dtype=np.int64),
        "source_url": pd.NA,
        "source_feature_row": np.arange(2, len(features) + 2, dtype=np.int64),
    })

    quote_columns = [
        "ornament_buy_thb", "bar_buy_thb", "bar_sell_thb", "ornament_sell_thb",
    ]
    invalid_timestamp = out["timestamp"].isna()
    invalid_prices = (
        out[quote_columns].isna().any(axis=1)
        | (out[quote_columns] <= 0).any(axis=1)
        | (out["bar_buy_thb"] > out["bar_sell_thb"])
        | (out["ornament_buy_thb"] > out["ornament_sell_thb"])
    )
    if invalid_timestamp.any():
        raise ValueError(
            f"Feature dataset has {int(invalid_timestamp.sum())} invalid timestamps")
    if invalid_prices.any():
        raise ValueError(
            f"Feature dataset has {int(invalid_prices.sum())} invalid quote rows")
    if out["timestamp"].dt.date.duplicated().any():
        raise ValueError("Feature dataset has multiple rows per date; resolve quote selection first")

    return out.sort_values(["timestamp", "announce_seq"], kind="stable").reset_index(drop=True)
