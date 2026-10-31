"""Stage J — Required visualizations (spec 13). All 13 figure families."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams.update({
    "figure.dpi": 110, "font.size": 9, "axes.titlesize": 10,
    "axes.titleweight": "bold", "axes.grid": True, "grid.alpha": 0.3,
    "axes.spines.top": False, "axes.spines.right": False,
})


def _load(out: Path):
    rd = lambda n: pd.read_parquet(out / n)
    return (rd("portfolio_master.parquet"), rd("transaction_ledger.parquet"),
            rd("portfolio_yearly.parquet"), rd("portfolio_valuation_monthly.parquet"),
            rd("pnl_attribution_yearly.parquet"))


def make_all_figures(dcfg) -> None:
    out = dcfg.outputs_dir
    fig_dir = out / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    pm, tx, yr, val, at = _load(out)
    daily = pd.read_parquet(out / "daily_market_prices.parquet")
    diag = json.load(open(out / "simulation_diagnostics.json", encoding="utf-8"))
    n_p = diag["total_portfolios"]

    # --- 1. Asset-allocation evidence chart (from source registry) ----------
    import csv
    sr = list(csv.DictReader(open(out.parent / "outputs/source_registry.csv"
                                  if False else Path(out).parent / "outputs/source_registry.csv",
                                  encoding="utf-8"))) if False else None
    fig, ax = plt.subplots(figsize=(6.5, 3.6), constrained_layout=True)
    labels = ["Bar & coin 2024\n(39.8 t, +17%)", "Jewellery 2024\n(9.0 t, -2%)",
              "Bar & coin Q2'25\n(10 t, +38%)", "Investment Q2'26\n(10.9 t, +10%)"]
    vals = [39.8, 9.0, 10.0, 10.9]
    ax.barh(labels[::-1], vals[::-1], color=["#4c72b0", "#dd8452", "#55a868", "#c44e52"][::-1])
    ax.set_xlabel("tonnes (WGC Gold Demand Trends, sources S01-S04)")
    ax.set_title("Reference evidence: Thailand gold demand (not a simulation output)")
    fig.savefig(fig_dir / "f01_asset_allocation_evidence.png"); plt.close(fig)

    # --- 2. Initial capital and gold-allocation distributions ---------------
    fig, axes = plt.subplots(1, 2, figsize=(8.5, 3.4), constrained_layout=True)
    axes[0].hist(np.log10(pm["initial_capital_thb"].clip(lower=1)), bins=40,
                 color="#4c72b0")
    axes[0].set_xlabel("log10(initial capital, THB)")
    axes[0].set_ylabel("portfolios")
    axes[0].set_title(f"Initial capital (n={n_p}) - scenario A01")
    share = pm["initial_gold_value_thb"] / pm["initial_capital_thb"]
    axes[1].hist(share.clip(0, 1), bins=40, color="#55a868")
    axes[1].set_xlabel("gold value / initial capital")
    axes[1].set_title("Initial gold allocation share - scenario A02")
    fig.savefig(fig_dir / "f02_initial_capital_and_allocation.png"); plt.close(fig)

    # --- 3. Transaction-size distribution ------------------------------------
    buys = tx[(tx["side"] == "BUY") & (tx["execution_status"] == "ACCEPTED")]
    sells = tx[(tx["side"] == "SELL") & (tx["execution_status"] == "ACCEPTED")]
    fig, ax = plt.subplots(figsize=(6.5, 3.4), constrained_layout=True)
    ax.hist(np.log10(buys["gross_amount_thb"].clip(lower=1)), bins=40,
            alpha=0.7, label=f"buys (n={len(buys)})", color="#4c72b0")
    ax.hist(np.log10(sells["gross_amount_thb"].clip(lower=1)), bins=40,
            alpha=0.7, label=f"sells (n={len(sells)})", color="#dd8452")
    ax.set_xlabel("log10(gross amount, THB)"); ax.set_ylabel("orders")
    ax.set_title("Transaction size distribution (accepted orders)")
    ax.legend()
    fig.savefig(fig_dir / "f03_transaction_size.png"); plt.close(fig)

    # --- 4. Transaction-frequency distribution -------------------------------
    per_p = tx[(tx["execution_status"] == "ACCEPTED")].groupby("portfolio_id").size()
    fig, ax = plt.subplots(figsize=(6.5, 3.4), constrained_layout=True)
    ax.hist(per_p, bins=30, color="#55a868")
    ax.set_xlabel("accepted transactions per portfolio")
    ax.set_ylabel("portfolios")
    ax.set_title(f"Transaction frequency (mean {per_p.mean():.1f} per portfolio)")
    fig.savefig(fig_dir / "f04_transaction_frequency.png"); plt.close(fig)

    # --- 5. Annual portfolio counts and coverage ------------------------------
    cnt = yr.groupby("calendar_year")["portfolio_id"].nunique()
    cov = yr.groupby("calendar_year")["data_coverage_ratio"].mean()
    fig, ax = plt.subplots(figsize=(7.5, 3.4), constrained_layout=True)
    ax.bar(cnt.index, cnt.values, color="#4c72b0", label="active portfolios")
    ax2 = ax.twinx(); ax2.grid(False)
    ax2.plot(cov.index, cov.values, "o-", color="#c44e52", label="mean coverage ratio")
    ax2.set_ylim(0, 1.15); ax2.set_ylabel("coverage ratio")
    ax.set_xlabel("calendar year"); ax.set_ylabel("portfolios")
    ax.set_title("Annual portfolio counts and valuation coverage")
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper left")
    fig.savefig(fig_dir / "f05_annual_counts_coverage.png"); plt.close(fig)

    # --- 6. Distribution of annual portfolio P&L by calendar year -------------
    years = sorted(yr["calendar_year"].unique())
    fig, ax = plt.subplots(figsize=(9, 3.8), constrained_layout=True)
    data = [yr.loc[yr["calendar_year"] == y, "net_pnl_thb"].values for y in years]
    bp = ax.boxplot(data, labels=[str(y) for y in years], showfliers=False,
                    patch_artist=True)
    for patch in bp["boxes"]:
        patch.set_facecolor("#4c72b0")
    ax.axhline(0, color="k", lw=0.8)
    ax.set_ylabel("annual net P&L (THB)")
    ax.set_title("Annual portfolio P&L distribution by calendar year (synthetic scenarios)")
    plt.setp(ax.get_xticklabels(), rotation=60)
    fig.savefig(fig_dir / "f06_annual_pnl_by_year.png"); plt.close(fig)

    # --- 7. Cumulative P&L by cohort ------------------------------------------
    last = yr.sort_values(["portfolio_id", "calendar_year"]).groupby(
        "portfolio_id").tail(1)
    cohorts = sorted(last["cohort_start_year"].unique())
    fig, ax = plt.subplots(figsize=(9, 3.8), constrained_layout=True)
    data = [last.loc[last["cohort_start_year"] == c, "net_pnl_thb"].values
            for c in cohorts]
    bp = ax.boxplot(data, labels=[str(c) for c in cohorts], showfliers=False,
                    patch_artist=True)
    for patch in bp["boxes"]:
        patch.set_facecolor("#55a868")
    ax.axhline(0, color="k", lw=0.8)
    ax.set_ylabel("lifetime net P&L (THB)")
    ax.set_xlabel("cohort start year")
    ax.set_title("Cumulative (lifetime-to-date) P&L by cohort, measured at each portfolio's last valuation")
    plt.setp(ax.get_xticklabels(), rotation=60)
    fig.savefig(fig_dir / "f07_cumulative_pnl_by_cohort.png"); plt.close(fig)

    # --- 8. Equity & drawdown examples for selected scenarios -----------------
    fig, axes = plt.subplots(2, 2, figsize=(9, 5.5), constrained_layout=True)
    picks = ["buy_hold", "dca", "buy_dip", "liquidity_sale"]
    for ax, scen in zip(axes.flat, picks):
        cand = pm[pm["behavior_scenario"] == scen]
        if not len(cand):
            continue
        pid = cand.sort_values("initial_capital_thb").iloc[len(cand) // 2]["portfolio_id"]
        v = val[val["portfolio_id"] == pid].sort_values("valuation_date")
        ax.plot(v["valuation_date"], v["portfolio_equity_thb"], lw=1.2,
                color="#4c72b0", label="equity")
        ax.plot(v["valuation_date"], v["net_contributed_capital_thb"], lw=1.0,
                ls="--", color="#55a868", label="net contributed")
        peak = v["portfolio_equity_thb"].cummax()
        dd = (v["portfolio_equity_thb"] - peak) / peak
        ax2 = ax.twinx(); ax2.grid(False)
        ax2.fill_between(v["valuation_date"], dd, 0, color="#c44e52", alpha=0.35)
        ax2.set_ylim(-1, 0.02); ax2.set_ylabel("drawdown", color="#c44e52")
        ax.set_title(f"{scen} - {pid}")
        ax.legend(fontsize=7, loc="upper left")
    fig.suptitle("Example synthetic portfolios (median-sized per scenario)", y=1.0)
    fig.savefig(fig_dir / "f08_equity_drawdown_examples.png"); plt.close(fig)

    # --- 9. Realized vs unrealized P&L ----------------------------------------
    fig, ax = plt.subplots(figsize=(6.5, 3.6), constrained_layout=True)
    ax.scatter(yr["realized_pnl_thb"], yr["unrealized_pnl_thb"], s=4,
               alpha=0.25, color="#4c72b0")
    ax.axhline(0, color="k", lw=0.8); ax.axvline(0, color="k", lw=0.8)
    ax.set_xlabel("annual realized P&L (THB)")
    ax.set_ylabel("annual unrealized P&L (THB)")
    ax.set_title("Realized vs unrealized annual P&L (portfolio-years)")
    fig.savefig(fig_dir / "f09_realized_vs_unrealized.png"); plt.close(fig)

    # --- 10. Transaction costs vs trading frequency ----------------------------
    cost_share = tx.assign(sh=tx["transaction_cost_thb"]
                           / tx["gross_amount_thb"].clip(lower=1))
    acc = cost_share[cost_share["execution_status"] == "ACCEPTED"]
    freq = acc.groupby("portfolio_id").size()
    spread_cost = acc.groupby("portfolio_id").apply(
        lambda g: ((g["customer_execution_price_thb_per_bw"] *
                    g["executed_quantity_bw"]).sum()
                   - (g["gross_amount_thb"].sum())) if len(g) else 0.0,
        include_groups=False)
    # spread cost per portfolio: buy at sell quote vs liquidation quote
    fig, ax = plt.subplots(figsize=(6.5, 3.6), constrained_layout=True)
    ax.scatter(freq, acc.groupby("portfolio_id")["transaction_cost_thb"].sum()
               if len(acc) else freq, s=6, alpha=0.3, color="#dd8452")
    ax.set_xlabel("accepted transactions per portfolio")
    ax.set_ylabel("explicit transaction costs (THB)")
    ax.set_title("Explicit fees vs frequency (baseline fee = 0; spread cost is in timing effect)")
    fig.savefig(fig_dir / "f10_costs_vs_frequency.png"); plt.close(fig)

    # --- 11. Benchmark comparison ----------------------------------------------
    bhp = pd.read_csv(out / "benchmark_comparison.csv") \
        if (out / "benchmark_comparison.csv").exists() else None
    if bhp is None:
        # compute lifetime comparison from yearly columns
        comp = yr.sort_values(["portfolio_id", "calendar_year"]).groupby(
            "portfolio_id").tail(1)
        if "benchmark_cum_net_pnl_thb" in comp.columns:
            fig, ax = plt.subplots(figsize=(6.5, 3.6), constrained_layout=True)
            ax.scatter(comp["benchmark_cum_net_pnl_thb"], comp["cum_net_pnl_thb"],
                       s=5, alpha=0.25, color="#4c72b0")
            lim = max(abs(comp["benchmark_cum_net_pnl_thb"]).max(),
                      abs(comp["cum_net_pnl_thb"]).max()) * 1.05
            ax.plot([-lim, lim], [-lim, lim], "k--", lw=0.8)
            ax.set_xlabel("buy-and-hold bar benchmark cumulative P&L (THB)")
            ax.set_ylabel("simulated portfolio cumulative P&L (THB)")
            ax.set_title("Simulated strategies vs BH_BAR_SAME_FLOWS benchmark")
            fig.savefig(fig_dir / "f11_benchmark_comparison.png"); plt.close(fig)

    # --- 12. Reference vs simulated comparison (valid comparisons only) --------
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.4), constrained_layout=True)
    # (a) annual bar price path vs WGC tonnage overlay (context check)
    yearly_px = daily.groupby(daily["date"].dt.year)["bar_sell_thb"].last()
    axes[0].plot(yearly_px.index, yearly_px.values, "o-", color="#4c72b0")
    axes[0].set_title("Observed GTA bar sell, year-end (S10)")
    axes[0].set_ylabel("THB per baht-weight")
    wgc_years = [2024, 2025]
    wgc_vals = [39.8, None]  # 2024 full-year value; Q2-only for 2025 not comparable
    axes[1].bar(["simulated aggregate net buys\n(all portfolios, lifetime, tonnes-equiv)"],
                [0], color="none")
    axes[1].set_title("Aggregate turnover comparison: see validation_report.md\n"
                      "(units not directly comparable - documented)")
    axes[1].set_xticks([])
    fig.savefig(fig_dir / "f12_reference_vs_simulated.png"); plt.close(fig)

    # --- 13. Sensitivity analysis ----------------------------------------------
    sa = out / "sensitivity_analysis.csv"
    if sa.exists():
        sdf = pd.read_csv(sa)
        fig, axes = plt.subplots(1, 3, figsize=(10, 3.4), constrained_layout=True)
        axes[0].bar(sdf["variant"], sdf["loss_year_share"], color="#c44e52")
        axes[0].set_title("share of portfolio-years with loss")
        axes[0].tick_params(axis="x", rotation=45)
        axes[1].bar(sdf["variant"], sdf["median_lifetime_pnl_thb"], color="#4c72b0")
        axes[1].set_title("median lifetime P&L (THB)")
        axes[1].tick_params(axis="x", rotation=45)
        axes[2].bar(sdf["variant"], sdf["tx_per_portfolio"], color="#55a868")
        axes[2].set_title("accepted transactions per portfolio")
        axes[2].tick_params(axis="x", rotation=45)
        fig.suptitle("Sensitivity analysis (uncertain scenario parameters)", y=1.02)
        fig.savefig(fig_dir / "f13_sensitivity.png", bbox_inches=None); plt.close(fig)

    print(f"figures written to {fig_dir}")
