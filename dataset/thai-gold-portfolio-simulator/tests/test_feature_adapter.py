"""Feature-dataset adapter tests."""
import pandas as pd
import pytest

from gold_portfolio_simulator.data.feature_adapter import (
    feature_prices_to_simulator_input,
)


def feature_frame():
    return pd.DataFrame({
        "timestamp_parsed": ["2020-01-01 09:30:00", "2020-01-02 09:30:00"],
        "ornament_buy": [24500.0, 24600.0],
        "bar_buy": [25000.0, 25100.0],
        "bar_sell": [25100.0, 25200.0],
        "ornament_sell": [25500.0, 25600.0],
        "gold_spot_clean": [1500.0, 1501.0],
        "thb_usd_clean": [31.0, 31.1],
        "change": [None, 100.0],
        "valid_price_pair": [False, True],
        "is_first_session": [True, False],
    })


def test_adapter_keeps_first_session_with_valid_quotes():
    adapted = feature_prices_to_simulator_input(feature_frame())

    assert len(adapted) == 2
    assert adapted["bar_buy_thb"].tolist() == [25000.0, 25100.0]
    assert adapted["announce_seq"].tolist() == [0, 1]


def test_adapter_leaves_unavailable_tax_base_missing():
    adapted = feature_prices_to_simulator_input(feature_frame())

    assert adapted["ornament_tax_base_thb"].isna().all()
    assert adapted["ornament_buy_thb"].tolist() == [24500.0, 24600.0]


def test_adapter_rejects_invalid_actual_quote_prices():
    features = feature_frame()
    features.loc[1, "bar_buy"] = 0

    with pytest.raises(ValueError, match="invalid quote rows"):
        feature_prices_to_simulator_input(features)


def test_adapter_rejects_duplicate_dates():
    features = feature_frame()
    features.loc[1, "timestamp_parsed"] = "2020-01-01 15:00:00"

    with pytest.raises(ValueError, match="multiple rows per date"):
        feature_prices_to_simulator_input(features)
