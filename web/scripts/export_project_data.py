#!/usr/bin/env python
"""Export the checked-in project Parquet tables as immutable web data bundles."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
FEATURES = Path("dataset/datset a gold price/data/processed/thai_gold_features_v1.parquet")
SIMULATOR_OUTPUTS = Path("dataset/thai-gold-portfolio-simulator/outputs")

MASTER_COLUMNS = [
    "portfolio_id",
    "cohort_start_year",
    "start_timestamp",
    "end_timestamp",
    "portfolio_segment",
    "gold_product_type",
    "initial_capital_thb",
    "initial_cash_thb",
    "initial_gold_quantity",
    "initial_gold_value_thb",
    "behavior_scenario",
    "parameter_set_id",
    "random_seed_id",
    "simulation_run_id",
    "is_synthetic",
    "calibration_status",
]


def json_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return json.loads(frame.to_json(orient="records", date_format="iso", double_precision=12))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
    temporary.write_bytes(gzip.compress(serialized, compresslevel=9, mtime=0) if path.suffix == ".gz" else serialized)
    os.replace(temporary, path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def export(project_root: Path) -> dict[str, Any]:
    features_path = project_root / FEATURES
    outputs = project_root / SIMULATOR_OUTPUTS
    market = pd.read_parquet(features_path).sort_values(["date", "timestamp_parsed"], kind="stable")
    master = pd.read_parquet(outputs / "portfolio_master.parquet").sort_values("portfolio_id", kind="stable")
    valuations = pd.read_parquet(outputs / "portfolio_valuation_monthly.parquet")
    transactions = pd.read_parquet(outputs / "transaction_ledger.parquet")

    required_features = {"date", "timestamp_parsed", "bar_buy", "bar_sell", "gold_spot_clean", "thb_usd_clean"}
    if not required_features.issubset(market.columns):
        raise ValueError(f"Market table is missing required columns: {sorted(required_features - set(market.columns))}")
    for label, frame, required in (
        ("Portfolio master", master, set(MASTER_COLUMNS)),
        ("Portfolio valuation", valuations, {"portfolio_id", "valuation_date", "simulation_run_id", "is_synthetic"}),
        ("Transaction ledger", transactions, {"portfolio_id", "transaction_id", "event_timestamp", "simulation_run_id", "is_synthetic"}),
    ):
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(f"{label} table is missing required columns: {sorted(missing)}")
        if not frame["is_synthetic"].fillna(False).all():
            raise ValueError(f"Portfolio export refused: {label} contains non-synthetic records")
    if master["portfolio_id"].isna().any() or master["portfolio_id"].duplicated().any():
        raise ValueError("Portfolio master must contain unique, non-null portfolio IDs")

    portfolio_ids = set(master["portfolio_id"].astype(str))
    for label, frame in (("Portfolio valuation", valuations), ("Transaction ledger", transactions)):
        if not set(frame["portfolio_id"].astype(str)).issubset(portfolio_ids):
            raise ValueError(f"{label} contains portfolio IDs missing from portfolio master")

    run_ids = {
        str(value)
        for frame in (master, valuations, transactions)
        for value in frame["simulation_run_id"].dropna().unique()
    }
    if len(run_ids) != 1:
        raise ValueError(f"Expected one simulation run across portfolio tables, found: {sorted(run_ids)}")
    portfolio_run_id = run_ids.pop()

    market_records = json_records(market)
    market_start = str(market["date"].min())[:10]
    market_end = str(market["date"].max())[:10]

    valuation_groups = {
        str(portfolio_id): group.sort_values("valuation_date", kind="stable")
        for portfolio_id, group in valuations.groupby("portfolio_id", sort=False)
    }
    transaction_groups = {
        str(portfolio_id): group.sort_values("event_timestamp", kind="stable")
        for portfolio_id, group in transactions.groupby("portfolio_id", sort=False)
    }

    catalog: list[dict[str, Any]] = []
    output_root = project_root / "web" / "data"
    portfolio_dir = output_root / "portfolio-years"
    portfolio_dir.mkdir(parents=True, exist_ok=True)
    stale_outputs = [
        output_root / "market-history.json",
        output_root / "portfolio-catalog.json",
        *(portfolio_dir / f"{year}.json" for year in range(2006, 2027)),
    ]
    for stale_path in stale_outputs:
        stale_path.unlink(missing_ok=True)
    year_groups: dict[int, list[dict[str, Any]]] = {}

    for row in json_records(master[MASTER_COLUMNS]):
        portfolio_id = row["portfolio_id"]
        history_frame = valuation_groups.get(portfolio_id, pd.DataFrame())
        transactions_frame = transaction_groups.get(portfolio_id, pd.DataFrame())
        history = json_records(history_frame) if not history_frame.empty else []
        ledger = json_records(transactions_frame) if not transactions_frame.empty else []
        latest = history[-1] if history else None
        year = int(row["cohort_start_year"])

        catalog.append({
            **row,
            "valuation_count": len(history),
            "transaction_count": len(ledger),
            "latest_valuation": latest,
        })
        year_groups.setdefault(year, []).append({
            "portfolio": row,
            "valuation": history,
            "transactions": ledger,
        })

    for year, records in year_groups.items():
        write_json(portfolio_dir / f"{year}.json.gz", {"cohort_year": year, "portfolios": records})

    manifest = {
        "schema_version": 1,
        "portfolio_run_id": portfolio_run_id,
        "market": {
            "source": "dataset/datset a gold price/data/processed/thai_gold_features_v1.parquet",
            "start_date": market_start,
            "end_date": market_end,
            "rows": len(market_records),
            "missing_spot_rows": int(market["gold_spot_clean"].isna().sum()),
            "missing_fx_rows": int(market["thb_usd_clean"].isna().sum()),
            "imputed_values": 0,
            "sha256": sha256(features_path),
        },
        "portfolios": {
            "source_tables": [
                "dataset/thai-gold-portfolio-simulator/outputs/portfolio_master.parquet",
                "dataset/thai-gold-portfolio-simulator/outputs/portfolio_valuation_monthly.parquet",
                "dataset/thai-gold-portfolio-simulator/outputs/transaction_ledger.parquet",
            ],
            "count": len(catalog),
            "valuation_rows": len(valuations),
            "transaction_rows": len(transactions),
            "all_synthetic": True,
            "sha256": {
                name: sha256(outputs / f"{name}.parquet")
                for name in ("portfolio_master", "portfolio_valuation_monthly", "transaction_ledger")
            },
        },
    }

    write_json(output_root / "market-history.json.gz", {"manifest": manifest["market"], "rows": market_records})
    write_json(output_root / "portfolio-catalog.json.gz", {"manifest": manifest["portfolios"], "rows": catalog})
    write_json(output_root / "manifest.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    args = parser.parse_args()
    manifest = export(args.project_root.resolve())
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
