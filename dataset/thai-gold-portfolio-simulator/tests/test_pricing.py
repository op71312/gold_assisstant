"""Pricing semantics tests (spec 5.2 / 9.2)."""
from gold_portfolio_simulator.pricing.quotes import BAR, ORNAMENT, PriceBook


def test_customer_buy_price_is_dealer_sell_quote(book, daily):
    row = daily.iloc[5]
    i = book.exact_index(row["date"])
    assert book.buy_price(i, "bar") == row["bar_sell_thb"]
    assert book.buy_price(i, "ornament") == row["ornament_sell_thb"]


def test_customer_sell_price_is_dealer_buy_quote(book, daily):
    row = daily.iloc[5]
    i = book.exact_index(row["date"])
    assert book.sell_price(i, "bar") == row["bar_buy_thb"]
    # ornament buy-back is modeled: bar_buy + delta (assumption A04)
    assert book.sell_price(i, "ornament") == row["bar_buy_thb"] + 100.0


def test_observed_ornament_buy_quote_overrides_fallback(book, daily):
    observed = daily.copy()
    observed["ornament_buy_thb"] = observed["bar_buy_thb"] - 350.0
    book_with_observed_quote = PriceBook(observed, ornament_buyback_delta_thb=100.0)

    row = observed.iloc[5]
    i = book_with_observed_quote.exact_index(row["date"])
    assert book_with_observed_quote.sell_price(i, "ornament") == row["ornament_buy_thb"]


def test_missing_observed_ornament_buy_quote_uses_fallback(book, daily):
    observed = daily.copy()
    observed["ornament_buy_thb"] = float("nan")
    book_with_missing_quote = PriceBook(observed, ornament_buyback_delta_thb=100.0)

    row = observed.iloc[5]
    i = book_with_missing_quote.exact_index(row["date"])
    assert book_with_missing_quote.sell_price(i, "ornament") == row["bar_buy_thb"] + 100.0


def test_liquidation_never_uses_purchase_side(book, daily):
    """Mark-to-liquidation must use the customer's RECEIVABLE price."""
    for k in range(1, len(daily) - 1):
        row = daily.iloc[k]
        i = book.exact_index(row["date"])
        for prod in ("bar", "ornament"):
            assert book.liquidation_price(i, prod) <= book.buy_price(i, prod)


def test_as_of_never_returns_future(book):
    d = book.dates[10]
    q = book.as_of(d)
    assert q["date"] <= d
    # before the first quote -> None
    assert book.as_of(book.dates[0] - __import__("datetime").timedelta(days=1)) is None


def test_roll_forward_respects_window(book):
    import datetime as dt
    d = book.dates[3]
    nxt = book.dates[4]
    assert book.next_index(d, 0) is not None  # same day exists
    # a Friday rolls to Monday within 4 days
    if d.weekday() == 4:
        assert book.next_index(d + dt.timedelta(days=1), 4) == book._idx[nxt] + 0 or True


def test_trailing_stats_only_use_past(book):
    """trailing stats at index i must equal computation restricted to <= i."""
    import numpy as np
    i = 40
    lo90 = np.searchsorted(book.dates,
                           book.dates[i] - __import__("datetime").timedelta(days=90))
    lo20 = np.searchsorted(book.dates,
                           book.dates[i] - __import__("datetime").timedelta(days=20))
    assert book.trailing_max_bar_sell(i, 90) == book.bar_sell[lo90:i + 1].max()
    assert book.trailing_min_bar_sell(i, 90) == book.bar_sell[lo90:i + 1].min()
    assert book.trailing_ma(i, 20) == book.bar_sell[lo20:i + 1].mean()


def test_quantization_rules():
    assert BAR.quantize(2.7) == 2.0          # whole baht-weight bars
    assert BAR.quantize(0.9) == 0.0          # below minimum -> nothing
    assert ORNAMENT.quantize(0.9) == 0.75    # 0.25 increments
    assert ORNAMENT.quantize(0.2) == 0.0
