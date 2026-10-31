"""CLI entry point (spec 15).

Examples (see README.md for full instructions):
  python -m gold_portfolio_simulator.cli audit
  python -m gold_portfolio_simulator.cli research-validate
  python -m gold_portfolio_simulator.cli smoke
  python -m gold_portfolio_simulator.cli full
  python -m gold_portfolio_simulator.cli validate-outputs
  python -m gold_portfolio_simulator.cli verify-reproducibility
  python -m gold_portfolio_simulator.cli sensitivity
  python -m gold_portfolio_simulator.cli figures
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

from .config import DataConfig, SimulationConfig, PROJECT_ROOT
from .data.audit import (audit_dataset, build_daily_prices, coverage_by_year,
                         load_raw, write_audit_outputs)
from .simulation.run import checksum, load_price_book, run_simulation


def _configs(args):
    dcfg = DataConfig.from_yaml(Path(args.data_config))
    scfg = SimulationConfig.from_yaml(Path(args.sim_config))
    if args.input:
        dcfg.input_path = Path(args.input).resolve()
    return dcfg, scfg


def _require_input(dcfg: DataConfig) -> None:
    if not dcfg.input_path.exists():
        sys.exit(f"FAIL: input dataset not found: {dcfg.input_path}\n"
                 "Set GOLD_DATA_PATH or --input to the gold price CSV "
                 "(see configs/data.yaml). Refusing to fabricate data.")


def cmd_audit(args):
    dcfg, _ = _configs(args)
    _require_input(dcfg)
    raw = load_raw(dcfg)
    daily, meta = build_daily_prices(raw, dcfg)
    cov = coverage_by_year(daily)
    rep = audit_dataset(raw, dcfg, daily)
    write_audit_outputs(daily, cov, rep, dcfg)
    md = render_audit_md(rep, meta, cov, dcfg)
    reports = PROJECT_ROOT / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "data_audit.md").write_text(md, encoding="utf-8")
    print(json.dumps({k: rep[k] for k in
                      ["row_count", "min_timestamp", "max_timestamp",
                       "calendar_days_with_valid_quote", "calendar_days_missing"]},
                     indent=2, default=str))
    print(f"audit outputs -> {dcfg.outputs_dir}\nreport -> reports/data_audit.md")


def render_audit_md(rep, meta, cov, dcfg) -> str:
    lines = ["# Data Audit Report", "",
             f"Input file: `{dcfg.input_path}` (sha256 `{checksum(dcfg.input_path)[:16]}...`) "
             "- original preserved unmodified.", ""]
    lines += [
        f"- Input rows: **{rep['row_count']:,}** (valid two-sided bar quote rows: "
        f"{meta['n_valid_pair_rows']:,})",
        f"- Period: **{rep['min_timestamp']} .. {rep['max_timestamp']}**",
        f"- Daily rows after selection policy `{meta['policy']}`: **{meta['n_daily_rows']:,}**",
        f"- Calendar days with a valid quote: {rep['calendar_days_with_valid_quote']:,} "
        f"of {rep['calendar_days_total']:,} (missing {rep['calendar_days_missing']:,} days; "
        f"weekends and GTA non-publication days are expected)",
    ]
    if rep.get("missing_weekday_blocks"):
        lines.append("- Missing weekday blocks (incl. source gaps):")
        for b in rep["missing_weekday_blocks"]:
            lines.append(f"  - {b['start']} .. {b['end']} ({b['n']} weekdays)")
    lines += [
        "",
        "## Price semantics",
        "Columns follow the published GTA convention: `รับซื้อ` (bar_buy) = dealer buys = "
        "customer SELL price; `ขายออก` (bar_sell / ornament_sell) = dealer sells = customer "
        "BUY price. `ornament_buy`, when present, is the observed ornament customer SELL "
        "price; otherwise A04 is used as fallback. Liquidation valuation uses the customer SELL side. Units: THB per "
        "baht-weight (15.244 g, 96.5% purity). The historical ornament buy-back quote is not "
        "present in the raw archive and is modeled only for sources without an observed quote.",
        "",
        "## Quality checks",
        f"- Invalid/nonpositive bar buy: {rep['bar_buy_invalid_count']}, bar sell: "
        f"{rep['bar_sell_invalid_count']}, ornament sell: {rep['ornament_sell_invalid_count']}",
        *(
            [f"- Invalid/missing ornament buy quotes: "
              f"{rep['ornament_buy_invalid_count']}/"
              f"{rep['ornament_buy_missing_count']}; above ornament sell: "
              f"{rep['ornament_buy_above_ornament_sell_count']}"]
            if "ornament_buy_invalid_count" in rep else []
        ),
        f"- Exact duplicate (timestamp,seq) rows: {rep['exact_duplicate_rows']} (none removed; "
        f"daily selection policy picks the authoritative quote per day)",
        f"- Input rows sharing a timestamp: {rep['rows_sharing_timestamp']}",
        f"- Input rows per date: mean {rep['intraday_obs_per_date']['mean']:.2f}, "
        f"max {rep['intraday_obs_per_date']['max']}",
        f"- Share of input rows with nonzero change: {rep['share_change_nonzero']:.1%}",
        f"- Bar buy-sell spread (THB/baht-weight): mean {rep['bar_spread_stats']['mean']:.0f}, "
        f"p5 {rep['bar_spread_stats']['p5']:.0f}, p95 {rep['bar_spread_stats']['p95']:.0f}",
        f"- Ornament sell minus bar sell (wage proxy): mean "
        f"{rep['ornament_wage_stats']['mean']:.0f} THB/baht-weight",
        f"- Negative bar spreads: {rep['bar_spread_negative_announcements']} (flagged, not removed)",
        "",
        "## Selection-policy sensitivity",
        f"- Alternative policy `{rep['policy_return_sensitivity']['alt_policy']}`: "
        f"correlation of daily bar returns "
        f"{rep['policy_return_sensitivity']['corr']:.4f}; annualized vol "
        f"{rep['policy_return_sensitivity']['annualized_vol_primary']:.1%} (primary) vs "
        f"{rep['policy_return_sensitivity']['annualized_vol_alt']:.1%} (alt).",
        "",
        "## Coverage by year",
        cov.to_markdown(index=False),
        "",
        "## Anomalies and limitations",
        "- No imputation is performed; trading and valuation skip unavailable quote dates "
        "(policy `skip_and_log`).",
        f"- Input coverage ends at **{rep['max_timestamp']}**; the final calendar year "
        "is partial when the input ends before December.",
        "- Quotes are market-wide GTA prices, not individual shop transactions.",
    ]
    return "\n".join(lines)


def cmd_research_validate(args):
    import csv
    ok = True
    problems = []
    sr = PROJECT_ROOT / "outputs/source_registry.csv"
    pe = PROJECT_ROOT / "outputs/parameter_evidence.csv"
    ar = PROJECT_ROOT / "outputs/assumptions_register.csv"
    rp = PROJECT_ROOT / "configs/research_parameters.yaml"
    for f in (sr, pe, ar, rp):
        if not f.exists():
            ok = False
            problems.append(f"missing {f.name}")
    if sr.exists():
        rows = list(csv.DictReader(open(sr, encoding="utf-8")))
        need = {"source_id", "organization", "url", "metric", "access_date"}
        miss = need - set(rows[0].keys()) if rows else need
        if miss:
            ok = False
            problems.append(f"source_registry missing columns {miss}")
        ids = {r["source_id"] for r in rows}
        if pe.exists():
            prows = list(csv.DictReader(open(pe, encoding="utf-8")))
            for r in prows:
                for sid in (r.get("source_id") or "").split(";"):
                    sid = sid.strip()
                    if sid and sid != "NONE" and sid not in ids:
                        ok = False
                        problems.append(f"parameter_evidence cites unknown source {sid}")
            gaps = [r for r in prows if r.get("evidence_type") == "gap"]
            print(f"sources: {len(rows)}, parameters: {len(prows)} "
                  f"(explicit gaps: {len(gaps)})")
    if ar.exists():
        arows = list(csv.DictReader(open(ar, encoding="utf-8")))
        bad = [r["assumption_id"] for r in arows
               if r.get("status") not in ("SCENARIO_ASSUMPTION", "LABELED_ASSUMPTION",
                                          "LABELLED_INITIALIZATION", "METHOD_CHOICE",
                                          "MARKET_CONVENTION_ASSUMPTION")]
        if bad:
            ok = False
            problems.append(f"assumptions without explicit status: {bad}")
    print("RESEARCH INTEGRITY:", "PASS" if ok else "FAIL")
    for p in problems:
        print("  -", p)
    sys.exit(0 if ok else 1)


def cmd_run(args, label: str, scale: dict | None = None):
    dcfg, scfg = _configs(args)
    _require_input(dcfg)
    if scale:
        scfg.cohort_years = scale.get("cohort_years", scfg.cohort_years)
        scfg.portfolios_per_cohort = scale.get("portfolios_per_cohort",
                                               scfg.portfolios_per_cohort)
    # gate: research integrity must pass before full runs
    if label == "full":
        r = subprocess.run([sys.executable, "-m", "gold_portfolio_simulator.cli",
                            "research-validate"], capture_output=True, text=True,
                           env={"PYTHONPATH": str(PROJECT_ROOT / "src")})
        if r.returncode != 0:
            sys.exit("GATE BLOCKED: research integrity check failed.\n" + r.stdout)
    t0 = pd.Timestamp.now()
    print(f"[{label}] run_id={scfg.run_id} seed={scfg.global_seed} "
          f"cohorts={len(scfg.cohort_years)} portfolios/cohort={scfg.portfolios_per_cohort}")
    res = run_simulation(scfg, dcfg, write_outputs=True, label=label)
    d = res["diagnostics"]
    print(f"portfolios={d['total_portfolios']} tx={d['total_transaction_events']} "
          f"accepted={d['accepted_transactions']} rejected={d['rejected_transactions']}")
    print(f"portfolio-years={d['portfolio_year_records']} "
          f"monthly-valuations={d['monthly_valuation_records']}")
    print(f"accounting reconciliation failures: "
          f"{d['accounting_reconciliation_failures']} "
          f"(max err {d['accounting_reconciliation_max_error_thb']:.6f} THB)")
    print(f"attribution residual failures: {d['attribution_residual_failures']} "
          f"(max residual {d['attribution_max_residual_thb']:.6f} THB)")
    print(f"elapsed {(pd.Timestamp.now() - t0).total_seconds():.1f}s")
    if d["validation_failures"]:
        print("VALIDATION FAILURES:")
        for w in d["validation_failures"]:
            print("  -", w)
    return res


def cmd_smoke(args):
    scale = {"cohort_years": [2015, 2020], "portfolios_per_cohort": 8}
    res = cmd_run(args, "smoke", scale)
    d = res["diagnostics"]
    ok = (d["accounting_reconciliation_failures"] == 0
          and d["attribution_residual_failures"] == 0)
    print("SMOKE TEST:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


def cmd_full(args):
    res = cmd_run(args, "full")
    d = res["diagnostics"]
    if d["validation_failures"]:
        print("FULL RUN COMPLETED WITH VALIDATION FAILURES - see simulation_diagnostics.json")
        sys.exit(1)
    print("FULL RUN: PASS")
    write_run_manifest(args, res)


def cmd_validate_outputs(args):
    dcfg, scfg = _configs(args)
    out = dcfg.outputs_dir
    required = ["daily_market_prices.parquet", "portfolio_master.parquet",
                "transaction_ledger.parquet", "cashflow_ledger.parquet",
                "portfolio_valuation_monthly.parquet", "portfolio_yearly.parquet",
                "pnl_attribution_yearly.parquet", "simulation_diagnostics.json"]
    ok = True
    problems = []
    for f in required:
        if not (out / f).exists():
            ok = False
            problems.append(f"missing {f}")
    if ok:
        diag = json.load(open(out / "simulation_diagnostics.json", encoding="utf-8"))
        if diag["accounting_reconciliation_failures"] > 0:
            ok = False
            problems.append("diagnostics report accounting reconciliation failures")
        if diag["attribution_residual_failures"] > 0:
            ok = False
            problems.append("diagnostics report attribution residual failures")
        if diag["validation_failures"]:
            ok = False
            problems += diag["validation_failures"]
        # record counts must match actual files
        counts = {"portfolio_master": len(pd.read_parquet(out / "portfolio_master.parquet")),
                  "transaction_ledger": len(pd.read_parquet(out / "transaction_ledger.parquet")),
                  "portfolio_valuation_monthly": len(pd.read_parquet(out / "portfolio_valuation_monthly.parquet")),
                  "portfolio_yearly": len(pd.read_parquet(out / "portfolio_yearly.parquet")),
                  "pnl_attribution_yearly": len(pd.read_parquet(out / "pnl_attribution_yearly.parquet"))}
        expected = {"portfolio_master": diag["total_portfolios"],
                    "transaction_ledger": diag["total_transaction_events"],
                    "portfolio_valuation_monthly": diag["monthly_valuation_records"],
                    "portfolio_yearly": diag["portfolio_year_records"],
                    "pnl_attribution_yearly": diag["attribution_records"]}
        for k, v in expected.items():
            if counts[k] != v:
                ok = False
                problems.append(f"{k}: file has {counts[k]} rows, diagnostics claims {v}")
    print("OUTPUT VALIDATION:", "PASS" if ok else "FAIL")
    for p in problems:
        print("  -", p)
    sys.exit(0 if ok else 1)


def cmd_verify_reproducibility(args):
    dcfg, scfg = _configs(args)
    _require_input(dcfg)
    scfg.cohort_years = [2019, 2020]
    scfg.portfolios_per_cohort = 5
    import tempfile
    import io
    from contextlib import redirect_stdout

    def run_once():
        buf = io.StringIO()
        with redirect_stdout(buf):
            res = run_simulation(scfg, dcfg, write_outputs=False, label="repro")
        tx = res["transactions"].drop(columns=[], errors="ignore")
        yr = res["yearly"]
        h1 = hashlib.sha256(pd.util.hash_pandas_object(tx, index=True).values.tobytes()).hexdigest()
        h2 = hashlib.sha256(pd.util.hash_pandas_object(yr, index=True).values.tobytes()).hexdigest()
        return h1, h2

    h1 = run_once()
    h2 = run_once()
    ok = h1 == h2
    print("REPRODUCIBILITY:", "PASS" if ok else "FAIL")
    print("  run1:", h1[:16], " run2:", h2[:16])
    sys.exit(0 if ok else 1)


def cmd_sensitivity(args):
    dcfg, scfg = _configs(args)
    _require_input(dcfg)
    import copy
    base_cfg = scfg
    rows = []
    for variant in base_cfg.sensitivity.get("variants", [{"name": "base", "overrides": {}}]):
        cfg = copy.deepcopy(base_cfg)
        cfg.cohort_years = [2013, 2016, 2019, 2022, 2024]
        cfg.portfolios_per_cohort = 40
        _apply_overrides(cfg, variant.get("overrides", {}))
        print(f"variant: {variant['name']}")
        res = run_simulation(cfg, dcfg, write_outputs=False,
                             label=f"sensitivity-{variant['name']}")
        yr = res["yearly"]
        tx = res["transactions"]
        acc = tx[tx["execution_status"] == "ACCEPTED"] if len(tx) else tx
        lifetime = yr.sort_values(["portfolio_id", "calendar_year"]).groupby(
            "portfolio_id").tail(1)
        rows.append({
            "variant": variant["name"],
            "n_portfolios": res["diagnostics"]["total_portfolios"],
            "mean_annual_return": float(yr["annual_return"].astype(float).mean()),
            "loss_year_share": float((yr["net_pnl_thb"] < 0).mean()),
            "loss_lifetime_share": float((lifetime["net_pnl_thb"] < 0).mean()),
            "median_lifetime_pnl_thb": float(lifetime["net_pnl_thb"].median()),
            "mean_costs_frac_gross": float(
                (acc["transaction_cost_thb"].sum()
                 / max(1e-9, acc[acc["side"] == "BUY"]["gross_amount_thb"].sum()))
                if len(acc) else 0.0),
            "tx_per_portfolio": float(len(acc)
                                      / max(1, res["diagnostics"]["total_portfolios"])),
        })
    df = pd.DataFrame(rows)
    out = dcfg.outputs_dir
    df.to_csv(out / "sensitivity_analysis.csv", index=False)
    print(df.to_string(index=False))
    print(f"saved -> {out / 'sensitivity_analysis.csv'}")


def _apply_overrides(cfg, overrides: dict):
    for key, val in overrides.items():
        if key == "population":
            for k2, v2 in val.items():
                getattr(cfg.population, k2).update(v2)
        elif key == "behavior":
            for k2, v2 in val.items():
                if k2 == "weights":
                    cfg.behavior.weights = v2
                else:
                    cfg.behavior.params.update(v2)
        elif key == "pricing":
            cfg.pricing.update(val)


def cmd_figures(args):
    from .validation.figures import make_all_figures
    dcfg, _ = _configs(args)
    make_all_figures(dcfg)
    print(f"figures -> {dcfg.outputs_dir / 'figures'}")


def write_run_manifest(args, res):
    dcfg, scfg = _configs(args)
    out = dcfg.outputs_dir
    art = PROJECT_ROOT / "artifacts"
    art.mkdir(exist_ok=True)
    manifest = {
        "run_id": scfg.run_id,
        "executed_at": pd.Timestamp.now(tz="Asia/Bangkok").isoformat(),
        "input_file": str(dcfg.input_path),
        "input_sha256": checksum(dcfg.input_path),
        "config_sha256": {f: checksum(PROJECT_ROOT / "configs" / f)
                          for f in ["data.yaml", "simulation.yaml",
                                    "research_parameters.yaml"]
                          if (PROJECT_ROOT / "configs" / f).exists()},
        "random_seed": scfg.global_seed,
        "simulation_parameters": {
            "cohort_years": scfg.cohort_years,
            "portfolios_per_cohort": scfg.portfolios_per_cohort,
            "inventory_costing": scfg.inventory_costing,
            "valuation_frequency": scfg.valuation_frequency,
            "ornament_buyback_delta_thb": scfg.pricing.get("ornament_buyback_delta_thb"),
            "explicit_fee_thb": scfg.pricing.get("explicit_fee_thb"),
        },
        "counts": {
            "portfolios": res["diagnostics"]["total_portfolios"],
            "transaction_events": res["diagnostics"]["total_transaction_events"],
            "portfolio_year_records": res["diagnostics"]["portfolio_year_records"],
            "monthly_valuations": res["diagnostics"]["monthly_valuation_records"],
        },
        "validation": {
            "accounting_reconciliation_failures":
                res["diagnostics"]["accounting_reconciliation_failures"],
            "attribution_residual_failures":
                res["diagnostics"]["attribution_residual_failures"],
            "failures": res["diagnostics"]["validation_failures"],
        },
        "known_limitations": [
            "Synthetic behaviour parameters are scenario assumptions, not calibrated to Thai investor data",
            "Ornament buy-back quote modeled (assumption A04)",
            "Source mirror gaps: Mar 2013, Aug-Nov 2016, Aug-Nov 2017, Oct 1-14 2026",
        ],
    }
    with open(art / "run_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    # checksums of major outputs
    lines = []
    for f in sorted(out.glob("*.parquet")) + sorted(out.glob("*.csv")) + \
             sorted(out.glob("*.json")):
        lines.append(f"{checksum(f)}  {f.name}")
    (art / "checksums.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"manifest -> {art / 'run_manifest.json'}")


def main():
    ap = argparse.ArgumentParser(prog="gold_portfolio_simulator",
                                 description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-config", default="configs/data.yaml")
    ap.add_argument("--sim-config", default="configs/simulation.yaml")
    ap.add_argument("--input", default=None,
                    help="override input dataset path (or env GOLD_DATA_PATH)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ["audit", "research-validate", "smoke", "full",
                 "validate-outputs", "verify-reproducibility", "sensitivity",
                 "figures"]:
        p = sub.add_parser(name)
        p.set_defaults(func={"audit": cmd_audit, "research-validate": cmd_research_validate,
                             "smoke": cmd_smoke, "full": cmd_full,
                             "validate-outputs": cmd_validate_outputs,
                             "verify-reproducibility": cmd_verify_reproducibility,
                             "sensitivity": cmd_sensitivity,
                             "figures": cmd_figures}[name])
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
