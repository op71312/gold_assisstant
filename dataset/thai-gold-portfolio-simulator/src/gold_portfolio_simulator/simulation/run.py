"""Run orchestration: audit -> population -> replay -> outputs (spec 12).

All write operations target the configured outputs directory. The original
input dataset is never modified.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import DataConfig, SimulationConfig
from ..data.audit import (audit_dataset, build_daily_prices, coverage_by_year,
                          load_raw, write_audit_outputs)
from ..population.generator import generate_population, population_frame
from ..pricing.quotes import PriceBook
from .engine import ReplayEngine


def checksum(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_price_book(dcfg: DataConfig) -> tuple[PriceBook, pd.DataFrame, dict, pd.DataFrame]:
    raw = load_raw(dcfg)
    daily, meta = build_daily_prices(raw, dcfg)
    cov = coverage_by_year(daily)
    report = audit_dataset(raw, dcfg, daily)
    book = PriceBook(daily, ornament_buyback_delta_thb=0.0)  # neutral for audit
    return book, daily, report, cov


def run_simulation(cfg: SimulationConfig, dcfg: DataConfig,
                   write_outputs: bool = True, label: str = "full") -> dict:
    out = dcfg.outputs_dir
    raw = load_raw(dcfg)
    daily, _ = build_daily_prices(raw, dcfg)
    book = PriceBook(daily, ornament_buyback_delta_thb=
                     float(cfg.pricing["ornament_buyback_delta_thb"]))

    plans = generate_population(cfg, book)
    tx_rows, cf_rows, val_rows, year_rows, attr_rows = [], [], [], [], []
    diag: dict = {"warnings": [], "validation_failures": []}

    engine = ReplayEngine(cfg, book)
    for k, plan in enumerate(plans):
        engine.run_portfolio(plan, tx_rows, cf_rows, val_rows, year_rows,
                             attr_rows, diag)
        if (k + 1) % 200 == 0:
            print(f"  simulated {k + 1}/{len(plans)} portfolios")

    tx = pd.DataFrame(tx_rows)
    cf = pd.DataFrame(cf_rows)
    val = pd.DataFrame(val_rows)
    yr = pd.DataFrame(year_rows)
    at = pd.DataFrame(attr_rows)
    pm = population_frame(plans)
    # portfolio master: end timestamps from actual exit events
    if len(tx) and "portfolio_id" in tx.columns:
        last_active = val.groupby("portfolio_id")["valuation_date"].max()
        pm["end_timestamp"] = pm["portfolio_id"].map(last_active)
    pm["calibration_status"] = "SCENARIO_ASSUMPTION"

    # ---- accounting reconciliation across the whole population ----
    tol = float(cfg.validation_thresholds["accounting_identity_tol_thb"])
    identity_failures = 0
    recon = []
    if len(val):
        v = val.sort_values(["portfolio_id", "valuation_date"])
        v["inv_gain"] = v["cumulative_realized_pnl_thb"] + v["unrealized_pnl_thb"] \
            - v["cumulative_transaction_cost_thb"]
        v["lhs"] = v["portfolio_equity_thb"] - v["net_contributed_capital_thb"]
        v["recon_err"] = (v["lhs"] - v["inv_gain"]).abs()
        identity_failures = int((v["recon_err"] > max(tol, 0.01)).sum())
        recon = v[["portfolio_id", "valuation_date", "recon_err"]] \
            .nlargest(10, "recon_err").to_dict("records")
    diag["accounting_reconciliation_failures"] = identity_failures
    diag["accounting_reconciliation_max_error_thb"] = \
        float(v["recon_err"].max()) if len(val) else 0.0
    if identity_failures > 0:
        diag["validation_failures"].append(
            f"{identity_failures} valuation rows exceed identity tolerance")
    # attribution residual check
    if len(at):
        bad = at[at["attribution_quality_flag"] != "RECONCILED"]
        diag["attribution_residual_failures"] = int(len(bad))
        diag["attribution_max_residual_thb"] = float(
            at["unattributed_residual_thb"].abs().max())
        if len(bad):
            diag["validation_failures"].append(
                f"{len(bad)} attribution rows failed reconciliation")

    diagnostics = {
        "simulation_run_id": cfg.run_id,
        "label": label,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_portfolios": int(len(pm)),
        "total_cohorts": int(pm["cohort_start_year"].nunique()) if len(pm) else 0,
        "cohorts": sorted(int(x) for x in pm["cohort_start_year"].unique()) if len(pm) else [],
        "total_transaction_events": int(len(tx)),
        "accepted_transactions": int((tx["execution_status"] == "ACCEPTED").sum())
            if len(tx) else 0,
        "rejected_transactions": int((tx["execution_status"] == "REJECTED").sum())
            if len(tx) else 0,
        "rejection_reasons": tx["rejection_reason"].value_counts().to_dict()
            if len(tx) else {},
        "portfolio_year_records": int(len(yr)),
        "monthly_valuation_records": int(len(val)),
        "cashflow_records": int(len(cf)),
        "attribution_records": int(len(at)),
        "missing_invalid_price_events": int((tx["rejection_reason"]
                                             == "NO_VALID_PRICE").sum())
            if len(tx) else 0,
        "accounting_reconciliation_failures": diag["accounting_reconciliation_failures"],
        "accounting_reconciliation_max_error_thb":
            diag["accounting_reconciliation_max_error_thb"],
        "attribution_residual_failures": diag.get("attribution_residual_failures", 0),
        "attribution_max_residual_thb": diag.get("attribution_max_residual_thb", 0.0),
        "reproducibility": {
            "global_seed": cfg.global_seed,
            "seed_mechanism": "numpy SeedSequence spawn: cohort <- global, portfolio <- cohort",
            "parameter_set_id": f"PS_{cfg.run_id}",
        },
        "calibration_gaps": [
            "transaction_frequency", "transaction_size", "initial_capital",
            "holding_period", "ornament_buyback_quote", "behavior_weights"
        ],
        "warnings": diag["warnings"],
        "validation_failures": diag["validation_failures"],
    }

    if write_outputs:
        out.mkdir(parents=True, exist_ok=True)
        pm.to_parquet(out / "portfolio_master.parquet", index=False)
        tx.to_parquet(out / "transaction_ledger.parquet", index=False)
        cf.to_parquet(out / "cashflow_ledger.parquet", index=False)
        val.to_parquet(out / "portfolio_valuation_monthly.parquet", index=False)
        yr.to_parquet(out / "portfolio_yearly.parquet", index=False)
        at.to_parquet(out / "pnl_attribution_yearly.parquet", index=False)
        if "csv" in cfg.output_formats:
            pm.to_csv(out / "portfolio_master.csv", index=False)
            tx.to_csv(out / "transaction_ledger.csv", index=False)
            cf.to_csv(out / "cashflow_ledger.csv", index=False)
            val.to_csv(out / "portfolio_valuation_monthly.csv", index=False)
            yr.to_csv(out / "portfolio_yearly.csv", index=False)
            at.to_csv(out / "pnl_attribution_yearly.csv", index=False)
        with open(out / "simulation_diagnostics.json", "w", encoding="utf-8") as f:
            json.dump(diagnostics, f, indent=2, ensure_ascii=False, default=str)
        print(f"  outputs written to {out}")
    return {"diagnostics": diagnostics, "portfolio_master": pm, "transactions": tx,
            "cashflows": cf, "valuations": val, "yearly": yr, "attribution": at,
            "daily_prices": daily}
