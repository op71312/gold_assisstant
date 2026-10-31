"""Recalculate simulator data from thai_gold_features_v1.csv.

Run from the simulator project directory:
    python scripts/recalculate_from_features.py

The script writes to the configured output directory and never edits the
feature source file. It refuses to overwrite a populated output directory
unless ``--confirm-overwrite`` is supplied.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from gold_portfolio_simulator.config import DataConfig, SimulationConfig  # noqa: E402
from gold_portfolio_simulator.data.audit import (  # noqa: E402
    audit_dataset,
    build_daily_prices,
    coverage_by_year,
    load_raw,
    write_audit_outputs,
)
from gold_portfolio_simulator.data.feature_adapter import (  # noqa: E402
    feature_prices_to_simulator_input,
)
from gold_portfolio_simulator.cli import render_audit_md  # noqa: E402
from gold_portfolio_simulator.validation.figures import (  # noqa: E402
    make_all_figures,
)
from gold_portfolio_simulator.simulation.run import (  # noqa: E402
    checksum,
    run_simulation,
)

DEFAULT_FEATURES = (
    PROJECT_ROOT.parent.parent
    / "dataset"
    / "datset a gold price"
    / "data"
    / "processed"
    / "thai_gold_features_v1.csv"
)
REPOSITORY_ROOT = PROJECT_ROOT.parent.parent
GROUND_TRUTH_QUERY_PATHS = [
    REPOSITORY_ROOT / "multi_agent" / "gt" / "ground_truth_fed_v1.jsonl",
    REPOSITORY_ROOT / "multi_agent" / "gt" / "ground_truth_fed_ready_v1.jsonl",
    REPOSITORY_ROOT / "multi_agent" / "GAIB-1" / "ground_truth_all_v1.jsonl",
    REPOSITORY_ROOT / "embedding" / "embedding" / "ground_truth_queries_v2.jsonl",
]
GROUND_TRUTH_SOURCE_DATA_PATH = (
    REPOSITORY_ROOT / "dataset" / "ground_truth_source_data_4_datasets.jsonl"
)


def build_data_config(input_path: Path, outputs_dir: Path) -> DataConfig:
    return DataConfig(
        input_path=input_path,
        date_column="timestamp",
        columns={
            "timestamp": "timestamp",
            "announce_seq": "announce_seq",
            "ornament_buy": "ornament_buy_thb",
            "bar_buy": "bar_buy_thb",
            "bar_sell": "bar_sell_thb",
            "ornament_sell": "ornament_sell_thb",
            "ornament_tax_base": "ornament_tax_base_thb",
            "gold_spot_usd": "gold_spot_usd",
            "usd_thb": "usd_thb",
            "change": "change_thb",
            "source_url": "source_url",
        },
        selection="last_valid_of_day",
        alt_selection="first_valid_of_day",
        require_valid_pair=True,
        min_positive_price=1000.0,
        outputs_dir=outputs_dir,
    )


def write_manifest(output_dir: Path, source_path: Path, input_path: Path,
                   source_rows: int, daily_rows: int, diagnostics: dict,
                   price_comparison: dict, ground_truth_audit: dict) -> Path:
    files = sorted(
        path for path in output_dir.iterdir()
        if path.is_file() and path.name != "feature_recalculation_manifest.json"
    )
    manifest = {
        "run_id": "R_FEATURE_V1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input_file": str(source_path),
        "input_sha256": checksum(source_path),
        "source_dataset": str(source_path),
        "source_sha256": checksum(source_path),
        "adapted_input": str(input_path),
        "adapted_input_sha256": checksum(input_path),
        "source_rows": source_rows,
        "daily_quote_rows": daily_rows,
        "counts": {
            "portfolios": diagnostics["total_portfolios"],
            "transaction_events": diagnostics["total_transaction_events"],
            "portfolio_year_records": diagnostics["portfolio_year_records"],
            "monthly_valuations": diagnostics["monthly_valuation_records"],
        },
        "validation": {
            "accounting_reconciliation_failures":
                diagnostics["accounting_reconciliation_failures"],
            "attribution_residual_failures":
                diagnostics["attribution_residual_failures"],
            "failures": diagnostics["validation_failures"],
        },
        "quote_selection_policy": "last_valid_of_day",
        "feature_valid_price_pair_semantics": (
            "A price-change computability flag requiring a prior same-day row; "
            "not used to filter quotes."
        ),
        "comparison_with_pre_recalculation_prices": price_comparison,
        "ground_truth_query_audit": ground_truth_audit,
        "unavailable_fields": {
            "ornament_tax_base_thb": (
                "Not present in the feature dataset; preserved as null and unused "
                "by the portfolio replay."
            ),
        },
        "ornament_buyback_price_policy": (
            "Use observed ornament_buy_thb when present; A04 fallback applies only "
            "to inputs without an observed buy quote."
        ),
        "ground_truth_scope": (
            "News/Fed query ground truth is unchanged: inspected benchmark query sets "
            "contain no gold-price or simulator-output questions. This avoids deriving "
            "evaluation labels from the system outputs being evaluated."
        ),
        "simulation": diagnostics,
        "output_sha256": {path.name: checksum(path) for path in files},
    }
    manifest_path = output_dir / "feature_recalculation_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    if output_dir == (PROJECT_ROOT / "outputs").resolve():
        artifact_dir = PROJECT_ROOT / "artifacts"
        artifact_dir.mkdir(parents=True, exist_ok=True)
        (artifact_dir / "run_manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
        checksum_files = sorted(
            path for path in output_dir.iterdir()
            if path.is_file() and path.name != "checksums.txt"
        )
        (artifact_dir / "checksums.txt").write_text(
            "".join(f"{checksum(path)}  {path.name}\n" for path in checksum_files),
            encoding="utf-8",
        )
    return manifest_path


def compare_to_existing_prices(old_path: Path, new_daily: pd.DataFrame) -> dict:
    if not old_path.is_file():
        return {"status": "no_previous_daily_prices"}
    old = pd.read_parquet(old_path)
    if "date" not in old.columns:
        raise ValueError(f"Previous price table has no date column: {old_path}")
    price_columns = [
        "bar_buy_thb", "bar_sell_thb", "ornament_sell_thb",
        "gold_spot_usd", "usd_thb",
    ]
    missing = [column for column in price_columns
               if column not in old.columns or column not in new_daily.columns]
    if missing:
        raise ValueError(f"Cannot compare price tables; missing columns: {missing}")
    old["date"] = pd.to_datetime(old["date"]).dt.normalize()
    current = new_daily.copy()
    current["date"] = pd.to_datetime(current["date"]).dt.normalize()
    joined = old[["date", *price_columns]].merge(
        current[["date", *price_columns]],
        on="date",
        how="outer",
        suffixes=("_previous", "_feature"),
        indicator=True,
    )
    overlap = joined[joined["_merge"] == "both"]
    changed = pd.Series(False, index=overlap.index)
    max_abs_diff = {}
    for column in price_columns:
        left = pd.to_numeric(overlap[f"{column}_previous"], errors="coerce")
        right = pd.to_numeric(overlap[f"{column}_feature"], errors="coerce")
        changed |= ~left.eq(right).fillna(False)
        max_abs_diff[column] = (
            float((left - right).abs().max())
            if left.notna().any() and right.notna().any()
            else None
        )
    return {
        "status": "compared",
        "comparison_source": str(old_path),
        "shared_price_columns": price_columns,
        "added_price_columns": [
            "ornament_buy_thb"
        ] if "ornament_buy_thb" in new_daily.columns
        and "ornament_buy_thb" not in old.columns else [],
        "previous_dates": int(len(old)),
        "feature_dates": int(len(current)),
        "overlapping_dates": int(len(overlap)),
        "identical_price_rows_on_overlap": int((~changed).sum()),
        "changed_price_rows_on_overlap": int(changed.sum()),
        "only_in_previous": int((joined["_merge"] == "left_only").sum()),
        "only_in_feature_source": int((joined["_merge"] == "right_only").sum()),
        "max_absolute_difference_by_column": max_abs_diff,
    }


def extract_question_dates(query: str) -> list[str]:
    dates = set(re.findall(r"20\d{2}-\d{2}-\d{2}", query))
    thai_october = re.compile(
        r"(?P<first>\d{1,2})(?:\s*(?:and|&|,|และ)\s*(?P<second>\d{1,2}))?"
        r"\s*(?:ตุลาคม|ต\.ค\.?)\s*(?P<year>20\d{2}|25\d{2})"
    )
    for match in thai_october.finditer(query):
        year = int(match.group("year"))
        if year >= 2400:
            year -= 543
        for day in (match.group("first"), match.group("second")):
            if day:
                dates.add(f"{year:04d}-10-{int(day):02d}")
    return sorted(dates)


def audit_ground_truth_queries(price_coverage_end: str) -> dict:
    news_terms = ["gold", "ทอง"]
    simulator_terms = ["portfolio", "valuation", "p&l", "pnl", "simulator", "พอร์ต"]
    results = []
    price_rows = []
    for path in GROUND_TRUTH_QUERY_PATHS:
        if not path.is_file():
            results.append({"path": str(path), "status": "not_found"})
            continue
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()]
        news_queries = []
        simulator_queries = []
        for row in rows:
            query = str(row.get("query", ""))
            query_lower = query.lower()
            if any(term in query_lower for term in news_terms):
                news_queries.append(row)
            if any(term in query_lower for term in simulator_terms):
                simulator_queries.append(row)
            answer = row.get("expected_answer", {})
            facts = answer.get("facts", []) if isinstance(answer, dict) else []
            gold_facts = [
                fact for fact in facts
                if str(fact.get("name", "")).startswith("gold_")
            ]
            if gold_facts:
                question_dates = extract_question_dates(query)
                price_rows.append({
                    "ground_truth_file": str(path),
                    "query_id": row.get("query_id"),
                    "question_dates": ";".join(question_dates),
                    "expected_answer_source": "news_ground_truth",
                    "expected_facts": "; ".join(
                        f"{fact.get('name')}={fact.get('raw_value')}"
                        for fact in gold_facts
                    ),
                    "feature_price_coverage_end": price_coverage_end,
                    "coverage_status": (
                        "OUT_OF_FEATURE_PRICE_COVERAGE"
                        if any(question_date > price_coverage_end
                               for question_date in question_dates)
                        else "IN_FEATURE_PRICE_RANGE_REQUIRES_DATE_MATCH"
                        if question_dates
                        else "DATE_NOT_IN_QUERY"
                    ),
                    "ground_truth_modified": False,
                })
        results.append({
            "path": str(path),
            "query_count": len(rows),
            "news_gold_query_count": len(news_queries),
            "simulator_output_query_count": len(simulator_queries),
        })
    source_inventory = {"path": str(GROUND_TRUTH_SOURCE_DATA_PATH), "status": "not_found"}
    if GROUND_TRUTH_SOURCE_DATA_PATH.is_file():
        source_rows = [
            json.loads(line)
            for line in GROUND_TRUTH_SOURCE_DATA_PATH.read_text(
                encoding="utf-8"
            ).splitlines()
            if line.strip()
        ]
        source_inventory = {
            "path": str(GROUND_TRUTH_SOURCE_DATA_PATH),
            "record_count": len(source_rows),
            "datasets": sorted({
                str(row.get("dataset"))
                for row in source_rows
                if row.get("dataset") is not None
            }),
            "modified": False,
        }
    audit = {
        "status": (
            "review_simulator_ground_truth"
            if any(item.get("simulator_output_query_count", 0) for item in results)
            else "news_ground_truth_preserved"
        ),
        "feature_price_coverage_end": price_coverage_end,
        "files": results,
        "gold_price_fact_queries": price_rows,
        "source_evidence_inventory": source_inventory,
        "ground_truth_files_modified": False,
    }
    return audit


def write_ground_truth_coverage_audit(output_dir: Path, ground_truth_audit: dict) -> Path:
    path = output_dir / "ground_truth_price_coverage_audit.csv"
    pd.DataFrame(ground_truth_audit["gold_price_fact_queries"]).to_csv(path, index=False)
    return path


def write_recalculation_report(report_path: Path, source_path: Path,
                               source_rows: int, daily: pd.DataFrame,
                               diagnostics: dict, price_comparison: dict,
                               ground_truth_audit: dict) -> None:
    lines = [
        "# Feature-based simulator recalculation",
        "",
        f"- Source: `{source_path}`",
        f"- Input records: {source_rows:,}",
        f"- Daily quotes used: {len(daily):,} "
        f"({pd.to_datetime(daily['date']).min().date()} to "
        f"{pd.to_datetime(daily['date']).max().date()})",
        "- `valid_price_pair` is a price-change computability flag, not a quote "
        "quality filter; every row with positive ordered quote prices is retained.",
        "- Ornament tax-base values are unavailable in this source and remain null; "
        "the replay does not use this field.",
        f"- Observed ornament buy-back quotes: "
        f"{int(pd.to_numeric(daily['ornament_buy_thb'], errors='coerce').gt(0).sum()):,} "
        f"of {len(daily):,} daily rows; A04 fallback used for "
        f"{int(pd.to_numeric(daily['ornament_buy_thb'], errors='coerce').isna().sum()):,} rows. "
        "Other "
        "simulation parameters remain unchanged.",
        "",
        "## Recalculated outputs",
        f"- Portfolios: {diagnostics['total_portfolios']:,}",
        f"- Transaction events: {diagnostics['total_transaction_events']:,} "
        f"({diagnostics['accepted_transactions']:,} accepted; "
        f"{diagnostics['rejected_transactions']:,} rejected)",
        f"- Monthly valuations: {diagnostics['monthly_valuation_records']:,}",
        f"- Portfolio-year and attribution records: "
        f"{diagnostics['portfolio_year_records']:,}",
        f"- Accounting reconciliation failures: "
        f"{diagnostics['accounting_reconciliation_failures']}",
        f"- Attribution residual failures: {diagnostics['attribution_residual_failures']}",
        "",
        "## Comparison to prior daily prices",
        f"- Status: {price_comparison['status']}",
    ]
    if price_comparison["status"] == "compared":
        lines += [
            f"- Overlapping dates: {price_comparison['overlapping_dates']:,}",
            f"- Same price rows on overlap: "
            f"{price_comparison['identical_price_rows_on_overlap']:,}",
            f"- Changed price rows on overlap: "
            f"{price_comparison['changed_price_rows_on_overlap']:,}",
            f"- Added observed price fields: "
            f"{', '.join(price_comparison.get('added_price_columns', [])) or 'none'}",
            f"- Dates only in previous source: {price_comparison['only_in_previous']:,}",
            f"- Dates only in feature source: "
            f"{price_comparison['only_in_feature_source']:,}",
        ]
    lines += [
        "",
        "## Ground Truth impact",
        "- Article-specific Thai PBS/news facts remain unchanged: their evidence "
        "is the cited news, not the simulator's numeric outputs. Replacing those "
        "answers with feature prices would change the question being evaluated.",
        f"- Audit status: {ground_truth_audit['status']}",
        f"- Source-evidence inventory: "
        f"{ground_truth_audit['source_evidence_inventory'].get('record_count', 'not found')} "
        "records; source evidence was not modified.",
        f"- Gold price fact queries: "
        f"{len(ground_truth_audit['gold_price_fact_queries'])}; "
        f"{sum(row['coverage_status'] == 'OUT_OF_FEATURE_PRICE_COVERAGE' for row in ground_truth_audit['gold_price_fact_queries'])} "
        "refer to dates after the feature dataset ends. See "
        "`ground_truth_price_coverage_audit.csv` in the output directory.",
    ]
    for item in ground_truth_audit["files"]:
        if "query_count" in item:
            lines.append(
                f"- `{item['path']}`: {item['query_count']} queries; "
                f"{item.get('news_gold_query_count', 0)} news-gold and "
                f"{item.get('simulator_output_query_count', 0)} simulator-output queries."
            )
        else:
            lines.append(f"- `{item['path']}`: {item['status']}.")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def recalculate_sensitivity(simulation_config: SimulationConfig,
                            data_config: DataConfig) -> pd.DataFrame:
    rows = []
    variants = simulation_config.sensitivity.get(
        "variants", [{"name": "base", "overrides": {}}])
    for variant in variants:
        cfg = copy.deepcopy(simulation_config)
        cfg.cohort_years = [2013, 2016, 2019, 2022, 2024]
        cfg.portfolios_per_cohort = 40
        overrides = variant.get("overrides", {})
        for key, value in overrides.items():
            if key == "population":
                for subkey, subvalue in value.items():
                    getattr(cfg.population, subkey).update(subvalue)
            elif key == "behavior":
                for subkey, subvalue in value.items():
                    if subkey == "weights":
                        cfg.behavior.weights = subvalue
                    else:
                        cfg.behavior.params.update(subvalue)
            elif key == "pricing":
                cfg.pricing.update(value)

        print(f"recalculating sensitivity variant: {variant['name']}")
        result = run_simulation(
            cfg,
            data_config,
            write_outputs=False,
            label=f"feature-sensitivity-{variant['name']}",
        )
        yearly = result["yearly"]
        transactions = result["transactions"]
        accepted = transactions[
            transactions["execution_status"] == "ACCEPTED"
        ] if len(transactions) else transactions
        lifetime = yearly.sort_values(
            ["portfolio_id", "calendar_year"]
        ).groupby("portfolio_id").tail(1)
        rows.append({
            "variant": variant["name"],
            "n_portfolios": result["diagnostics"]["total_portfolios"],
            "mean_annual_return": float(yearly["annual_return"].astype(float).mean()),
            "loss_year_share": float((yearly["net_pnl_thb"] < 0).mean()),
            "loss_lifetime_share": float((lifetime["net_pnl_thb"] < 0).mean()),
            "median_lifetime_pnl_thb": float(lifetime["net_pnl_thb"].median()),
            "mean_costs_frac_gross": float(
                accepted["transaction_cost_thb"].sum()
                / max(
                    1e-9,
                    accepted[accepted["side"] == "BUY"]["gross_amount_thb"].sum(),
                )
            ) if len(accepted) else 0.0,
            "tx_per_portfolio": float(
                len(accepted) / max(1, result["diagnostics"]["total_portfolios"])
            ),
        })
    sensitivity = pd.DataFrame(rows)
    sensitivity.to_csv(data_config.outputs_dir / "sensitivity_analysis.csv", index=False)
    return sensitivity


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--features", type=Path, default=DEFAULT_FEATURES)
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs")
    parser.add_argument(
        "--adapted-input", type=Path,
        default=PROJECT_ROOT / "dataset" / "thai_gold_features_v1_simulator_input.csv",
    )
    parser.add_argument("--confirm-overwrite", action="store_true")
    parser.add_argument(
        "--simulation-config", type=Path,
        default=PROJECT_ROOT / "configs" / "simulation.yaml",
    )
    args = parser.parse_args()
    source_path = args.features.resolve()
    output_dir = args.output_dir.resolve()
    adapted_path = args.adapted_input.resolve()
    if not source_path.is_file():
        raise FileNotFoundError(f"Feature source not found: {source_path}")
    if output_dir.exists() and any(output_dir.iterdir()) and not args.confirm_overwrite:
        raise FileExistsError(
            f"Output directory is not empty: {output_dir}. "
            "Back it up and pass --confirm-overwrite to replace active results.")

    features = pd.read_csv(source_path)
    adapted = feature_prices_to_simulator_input(features)
    adapted_path.parent.mkdir(parents=True, exist_ok=True)
    adapted.to_csv(adapted_path, index=False)

    data_config = build_data_config(adapted_path, output_dir)
    simulation_config = SimulationConfig.from_yaml(args.simulation_config.resolve())
    simulation_config.run_id = "R_FEATURE_V1"
    baseline_prices_path = (
        PROJECT_ROOT / "baseline_raw_R001" / "outputs" / "daily_market_prices.parquet"
    )
    previous_prices_path = (
        baseline_prices_path if baseline_prices_path.is_file()
        else output_dir / "daily_market_prices.parquet"
    )
    raw = load_raw(data_config)
    daily, daily_meta = build_daily_prices(raw, data_config)
    price_comparison = compare_to_existing_prices(previous_prices_path, daily)
    coverage = coverage_by_year(daily)
    audit = audit_dataset(raw, data_config, daily)
    write_audit_outputs(daily, coverage, audit, data_config)
    report_path = (
        PROJECT_ROOT / "reports" / "data_audit.md"
        if output_dir == (PROJECT_ROOT / "outputs").resolve()
        else output_dir / "data_audit.md"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_audit_md(audit, {
        "policy": data_config.selection,
        "n_valid_pair_rows": daily_meta["n_valid_pair_rows"],
        "n_daily_rows": len(daily),
    }, coverage, data_config) + (
        "\n\n## Feature dataset provenance\n"
        f"- Source: `{source_path}` (SHA-256 recorded in the run manifest).\n"
        "- `valid_price_pair` is not used to filter rows; it describes "
        "price-change computability against a prior same-day observation.\n"
        "- `ornament_buy` is used as the observed customer sell quote for ornaments.\n"
        "- Ornament tax-base values are unavailable in the feature source and "
        "remain null; portfolio replay does not use this field.\n"
    ), encoding="utf-8")

    result = run_simulation(
        simulation_config,
        data_config,
        write_outputs=True,
        label="feature-dataset-recalculation",
    )
    if result["diagnostics"]["validation_failures"]:
        raise RuntimeError(
            "Simulation validation failed: "
            + "; ".join(result["diagnostics"]["validation_failures"])
        )
    recalculate_sensitivity(simulation_config, data_config)
    make_all_figures(data_config)
    coverage_end = pd.to_datetime(daily["date"]).max().date().isoformat()
    ground_truth_audit = audit_ground_truth_queries(coverage_end)
    write_ground_truth_coverage_audit(output_dir, ground_truth_audit)
    recalculation_report = (
        PROJECT_ROOT / "reports" / "feature_v1_recalculation.md"
        if output_dir == (PROJECT_ROOT / "outputs").resolve()
        else output_dir / "feature_v1_recalculation.md"
    )
    write_recalculation_report(
        recalculation_report,
        source_path,
        len(features),
        daily,
        result["diagnostics"],
        price_comparison,
        ground_truth_audit,
    )
    manifest_path = write_manifest(
        output_dir,
        source_path,
        adapted_path,
        len(features),
        len(daily),
        result["diagnostics"],
        price_comparison,
        ground_truth_audit,
    )
    print(json.dumps({
        "source": str(source_path),
        "source_rows": len(features),
        "daily_quote_rows": len(daily),
        "date_range": [
            str(pd.to_datetime(daily["date"]).min().date()),
            str(pd.to_datetime(daily["date"]).max().date()),
        ],
        "portfolio_count": result["diagnostics"]["total_portfolios"],
        "transaction_count": result["diagnostics"]["total_transaction_events"],
        "accounting_reconciliation_failures":
            result["diagnostics"]["accounting_reconciliation_failures"],
        "attribution_residual_failures":
            result["diagnostics"]["attribution_residual_failures"],
        "manifest": str(manifest_path),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
