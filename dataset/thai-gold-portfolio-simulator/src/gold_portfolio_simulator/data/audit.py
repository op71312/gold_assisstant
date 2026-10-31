"""Stage B — Data audit and daily price construction.

Audits the raw GTA price-announcement dataset and produces:
  - outputs/daily_market_prices.parquet (+ .csv)
  - outputs/market_coverage_by_year.csv
  - outputs/data_quality_summary.csv
  - reports/data_audit.md (written by the CLI from the returned report dict)

The original input file is never modified (spec 5.3).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import DataConfig

REQUIRED_CANONICAL = ["bar_buy", "bar_sell", "ornament_sell"]


def load_raw(cfg: DataConfig) -> pd.DataFrame:
    df = pd.read_csv(cfg.input_path)
    df["timestamp"] = pd.to_datetime(df[cfg.columns["timestamp"]])
    df = df.sort_values(["timestamp", cfg.columns["announce_seq"]]).reset_index(drop=True)
    return df


def _valid_pair(df: pd.DataFrame, cfg: DataConfig) -> pd.Series:
    bb = pd.to_numeric(df[cfg.columns["bar_buy"]], errors="coerce")
    bs = pd.to_numeric(df[cfg.columns["bar_sell"]], errors="coerce")
    ok = (bb > 0) & (bs > 0) & bb.notna() & bs.notna()
    if cfg.require_valid_pair:
        return ok
    return (bb > 0) | (bs > 0)


def build_daily_prices(raw: pd.DataFrame, cfg: DataConfig) -> tuple[pd.DataFrame, dict]:
    """Apply the configured selection policy -> one row per calendar date.

    Policy (documented in reports/data_audit.md): a date is usable if at least
    one announcement on that date has a valid bar quote pair. Among the valid
    announcements of the day the configured selection picks the quote:
      - last_valid_of_day  (default; the day's standing quote)
      - first_valid_of_day (alternative policy, kept for sensitivity testing)
    No imputation across days is performed (missing days stay missing and are
    flagged), per spec 5.3.
    """
    raw = raw.copy()
    colmap = cfg.columns
    raw["date"] = raw["timestamp"].dt.normalize()
    raw["valid_price_pair"] = _valid_pair(raw, cfg)
    raw["data_quality_flag"] = np.where(
        raw["valid_price_pair"], "OK", "INVALID_BAR_PAIR"
    )
    cand = raw[raw["valid_price_pair"]].copy()
    cand = cand.sort_values(["date", "timestamp", cfg.columns["announce_seq"]])
    if cfg.selection == "last_valid_of_day":
        sel = cand.groupby("date").tail(1)
    elif cfg.selection == "first_valid_of_day":
        sel = cand.groupby("date").head(1)
    else:  # pragma: no cover
        raise ValueError(f"unknown selection policy {cfg.selection}")

    daily = pd.DataFrame({
        "date": sel["date"].values,
        "price_quote_timestamp": sel["timestamp"].values,
        "bar_buy_thb": sel[cfg.columns["bar_buy"]].values,
        "bar_sell_thb": sel[cfg.columns["bar_sell"]].values,
        "ornament_buy_thb": (
            pd.to_numeric(sel[colmap["ornament_buy"]], errors="coerce").values
            if colmap.get("ornament_buy") in sel.columns
            else np.full(len(sel), np.nan)
        ),
        "ornament_sell_thb": sel[cfg.columns["ornament_sell"]].values,
        "ornament_tax_base_thb": (
            sel[colmap["ornament_tax_base"]].values
            if colmap.get("ornament_tax_base") in sel.columns
            else np.full(len(sel), np.nan)
        ),
        "gold_spot_usd": sel[cfg.columns["gold_spot_usd"]].values,
        "usd_thb": sel[cfg.columns["usd_thb"]].values,
        "change_thb": sel[cfg.columns["change"]].values,
        "announce_seq": sel[cfg.columns["announce_seq"]].values,
        "selection_policy": cfg.selection,
        "quality_flag": "OK",
    }).reset_index(drop=True)

    meta = {
        "n_raw_rows": int(len(raw)),
        "n_valid_pair_rows": int(raw["valid_price_pair"].sum()),
        "n_daily_rows": int(len(daily)),
        "policy": cfg.selection,
    }
    return daily, meta


def audit_dataset(raw: pd.DataFrame, cfg: DataConfig, daily: pd.DataFrame) -> dict:
    """Full audit per spec 5.1. Returns a report dict; caller renders it."""
    colmap = cfg.columns
    rep: dict = {}
    rep["row_count"] = int(len(raw))
    rep["columns"] = {c: str(raw[c].dtype) for c in raw.columns}
    rep["min_timestamp"] = str(raw["timestamp"].min())
    rep["max_timestamp"] = str(raw["timestamp"].max())

    # Missingness by column and year
    by_year = raw.assign(year=raw["timestamp"].dt.year)
    miss = {}
    for canon, col in colmap.items():
        if canon in ("timestamp", "source_url", "announce_seq"):
            continue
        s = pd.to_numeric(by_year[col], errors="coerce") if col in by_year else None
        if s is None:
            continue
        miss[canon] = {int(y): int(n) for y, n in s.isna().groupby(by_year["year"]).sum().items()
                       if n > 0}
    rep["missing_by_column_year"] = miss

    # Invalid / nonpositive prices
    for canon in ("bar_buy", "bar_sell", "ornament_sell"):
        s = pd.to_numeric(raw[colmap[canon]], errors="coerce")
        rep[f"{canon}_invalid_count"] = int((~((s > 0) | s.isna())).sum())
        rep[f"{canon}_missing_count"] = int(s.isna().sum())
    ornament_buy_col = colmap.get("ornament_buy")
    if ornament_buy_col and ornament_buy_col in raw:
        ornament_buy = pd.to_numeric(raw[ornament_buy_col], errors="coerce")
        ornament_sell = pd.to_numeric(raw[colmap["ornament_sell"]], errors="coerce")
        rep["ornament_buy_invalid_count"] = int(
            ((ornament_buy <= 0) & ornament_buy.notna()).sum()
        )
        rep["ornament_buy_missing_count"] = int(ornament_buy.isna().sum())
        rep["ornament_buy_above_ornament_sell_count"] = int(
            (ornament_buy > ornament_sell).sum()
        )
    else:
        rep["ornament_buy_available"] = False

    # Duplicate timestamps (kept: same timestamp with different seq is a legitimate
    # same-minute correction; exact duplicates counted, not auto-removed)
    dup_exact = raw.duplicated(subset=[colmap["timestamp"], colmap["announce_seq"]])
    rep["exact_duplicate_rows"] = int(dup_exact.sum())
    dup_ts = raw.duplicated(subset=[colmap["timestamp"]], keep=False)
    rep["rows_sharing_timestamp"] = int(dup_ts.sum())

    # Price changes / unchanged quote observations (bar mid)
    mid = (pd.to_numeric(raw[colmap["bar_buy"]], errors="coerce")
           + pd.to_numeric(raw[colmap["bar_sell"]], errors="coerce")) / 2
    changed = pd.to_numeric(raw[colmap["change"]], errors="coerce").dropna()
    rep["share_change_nonzero"] = (
        float((changed != 0).mean()) if len(changed) else float("nan")
    )
    rep["bar_mid_intraday_moves_per_day_mean"] = float(
        raw.assign(date=raw["timestamp"].dt.date).groupby("date").size().mean()
    )

    # Intraday observations per date
    per_day = raw.assign(date=raw["timestamp"].dt.date).groupby("date").size()
    rep["intraday_obs_per_date"] = {
        "mean": float(per_day.mean()), "median": float(per_day.median()),
        "max": int(per_day.max()), "min": int(per_day.min()),
    }

    # Days with missing or insufficient valid quotes
    all_days = pd.date_range(raw["timestamp"].min().normalize(),
                             raw["timestamp"].max().normalize(), freq="D")
    have = set(daily["date"])
    missing_days = [d for d in all_days if d not in have]
    rep["calendar_days_total"] = int(len(all_days))
    rep["calendar_days_with_valid_quote"] = int(len(have))
    rep["calendar_days_missing"] = int(len(missing_days))
    # GTA publishes on business days only; weekend gaps are expected. Count long gaps.
    if missing_days:
        md = pd.Series(pd.to_datetime(missing_days))
        wd = md[md.dt.dayofweek < 5]  # weekdays
        rep["missing_weekdays"] = int(len(wd))
        # longest consecutive weekday gap
        rep["missing_weekday_blocks"] = [
            {"start": str(g.min().date()), "end": str(g.max().date()), "n": int(len(g))}
            for _, g in wd.groupby((wd.diff().dt.days > 10).cumsum())
            if len(g) >= 5
        ][:20]

    # Bar vs ornament differences
    bb = pd.to_numeric(raw[colmap["bar_buy"]], errors="coerce")
    bs = pd.to_numeric(raw[colmap["bar_sell"]], errors="coerce")
    os_ = pd.to_numeric(raw[colmap["ornament_sell"]], errors="coerce")
    spread = bs - bb
    wage = os_ - bs
    rep["bar_spread_stats"] = {
        "mean": float(spread.mean()), "p5": float(spread.quantile(0.05)),
        "p95": float(spread.quantile(0.95)), "min": float(spread.min()),
        "max": float(spread.max()),
    }
    rep["ornament_wage_stats"] = {
        "mean": float(wage.mean()), "min": float(wage.min()), "max": float(wage.max()),
    }
    rep["bar_spread_negative_announcements"] = int((spread < 0).sum())
    rep["ornament_below_bar_announcements"] = int((os_ < bs).sum())

    # Derived daily-return sanity: effect of selection policy
    d2, _ = build_daily_prices(
        raw, type(cfg)(**{**cfg.__dict__,
                          "selection": cfg.alt_selection if cfg.selection != "first_valid_of_day"
                          else "last_valid_of_day"}))
    r1 = daily["bar_sell_thb"].pct_change().dropna()
    r2 = d2["bar_sell_thb"].pct_change().dropna()
    rep["policy_return_sensitivity"] = {
        "alt_policy": cfg.alt_selection if cfg.selection != "first_valid_of_day" else "last_valid_of_day",
        "corr": float(np.corrcoef(r1.align(r2, join="inner"))[0][1]) if len(r1) > 2 else None,
        "mean_abs_return_diff": float((r1 - r2.reindex(r1.index)).abs().mean())
        if len(r1) == len(r2) else float((r1 - r2.reindex(r1.index)).abs().mean()),
        "annualized_vol_primary": float(r1.std() * np.sqrt(252)),
        "annualized_vol_alt": float(r2.std() * np.sqrt(252)),
    }
    return rep


def coverage_by_year(daily: pd.DataFrame) -> pd.DataFrame:
    g = daily.assign(year=daily["date"].dt.year).groupby("year")
    cov = pd.DataFrame({
        "valid_quote_days": g.size(),
        "first_quote_date": g["date"].min(),
        "last_quote_date": g["date"].max(),
        "bar_sell_min": g["bar_sell_thb"].min(),
        "bar_sell_max": g["bar_sell_thb"].max(),
        "bar_sell_year_end": g["bar_sell_thb"].last(),
        "bar_spread_mean": (g["bar_sell_thb"].mean() - g["bar_buy_thb"].mean()),
    })
    cov["is_partial_year"] = [
        not (d.min().month == 1 and d.max().month == 12) for _, d in g["date"]
    ]
    cov.index.name = "year"
    return cov.reset_index()


def write_audit_outputs(daily: pd.DataFrame, cov: pd.DataFrame, rep: dict,
                        cfg: DataConfig) -> None:
    out = cfg.outputs_dir
    out.mkdir(parents=True, exist_ok=True)
    daily.to_parquet(out / "daily_market_prices.parquet", index=False)
    daily.to_csv(out / "daily_market_prices.csv", index=False)
    cov.to_csv(out / "market_coverage_by_year.csv", index=False)
    # quality summary: compact per-year quality table
    qs = cov.copy()
    qs["days_missing_in_year"] = [
        int((pd.date_range(f"{y}-01-01", f"{y}-12-31", freq="D").shape[0] - r.valid_quote_days)
            if not r.is_partial_year else 0)
        for y, r in qs.set_index("year").iterrows()] if False else [
        int(max(0, 365 - r.valid_quote_days)) if not r.is_partial_year else -1
        for _, r in qs.iterrows()
    ]
    qs.to_csv(out / "data_quality_summary.csv", index=False)
    with open(out / "data_audit_report.json", "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=2, ensure_ascii=False, default=str)
