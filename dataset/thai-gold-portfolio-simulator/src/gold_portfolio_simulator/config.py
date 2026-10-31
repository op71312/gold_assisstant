"""Configuration loading for the Thai gold portfolio simulator."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_yaml(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@dataclass
class DataConfig:
    input_path: Path
    date_column: str
    columns: dict
    selection: str
    alt_selection: str
    require_valid_pair: bool
    min_positive_price: float
    outputs_dir: Path

    @classmethod
    def from_yaml(cls, path: Path) -> "DataConfig":
        raw = load_yaml(path)
        input_path = Path(os.environ.get("GOLD_DATA_PATH", "") or raw["input_path"])
        if not input_path.is_absolute():
            input_path = (PROJECT_ROOT / input_path).resolve()
        return cls(
            input_path=input_path,
            date_column=raw["date_column"],
            columns=raw["columns"],
            selection=raw["daily_price_policy"]["selection"],
            alt_selection=raw["daily_price_policy"]["alt_selection"],
            require_valid_pair=bool(raw["daily_price_policy"]["require_valid_pair"]),
            min_positive_price=float(raw["min_positive_price"]),
            outputs_dir=(PROJECT_ROOT / raw.get("outputs_dir", "outputs")).resolve(),
        )


@dataclass
class PopulationConfig:
    initial_capital: dict
    gold_allocation: dict
    product_mix: dict
    bar_increment_bw: float
    ornament_increment_bw: float
    initialization: str


@dataclass
class BehaviorConfig:
    decision_frequency: str
    decision_roll_forward_days: int
    weights: dict
    params: dict


@dataclass
class SimulationConfig:
    run_id: str
    global_seed: int
    cohort_years: list
    portfolios_per_cohort: int
    pricing: dict
    inventory_costing: str
    valuation_frequency: str
    population: PopulationConfig
    behavior: BehaviorConfig
    missing_price_policy: str
    output_formats: list
    validation_thresholds: dict
    sensitivity: dict = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: Path) -> "SimulationConfig":
        raw = load_yaml(path)
        pop = PopulationConfig(**raw["population"])
        beh = BehaviorConfig(**raw["behavior"])
        return cls(
            run_id=raw["run_id"],
            global_seed=int(raw["global_seed"]),
            cohort_years=[int(y) for y in raw["cohort_years"]],
            portfolios_per_cohort=int(raw["portfolios_per_cohort"]),
            pricing=raw["pricing"],
            inventory_costing=raw["inventory_costing"],
            valuation_frequency=raw["valuation_frequency"],
            population=pop,
            behavior=beh,
            missing_price_policy=raw["missing_price_policy"],
            output_formats=raw["output_formats"],
            validation_thresholds=raw["validation_thresholds"],
            sensitivity=raw.get("sensitivity", {}),
        )
