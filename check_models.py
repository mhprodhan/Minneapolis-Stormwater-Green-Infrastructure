#!/usr/bin/env python3
"""Check scenario isolation, LID deployments and rainfall data (stdlib only).

This is an input-file QA check, not a substitute for a SWMM engine run.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FILES = (
    ROOT / "Minneapolis_Stormwater_Baseline.inp",
    ROOT / "Minneapolis_Stormwater_Green_S1.inp",
    ROOT / "Minneapolis_Stormwater_Green_All.inp",
)
METRICS = json.loads((ROOT / "results/scenario_metrics.json").read_text())
DATA = ROOT / "Data/Minneapolis_NOAA14_10yr24h_Q1_50pct_15min.dat"


def sections(path: Path) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    current = None
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.rstrip()
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1].upper()
            result[current] = []
        elif current is not None:
            result[current].append(line)
    return result


def entries(lines: list[str]) -> list[list[str]]:
    return [line.split() for line in lines
            if line.strip() and not line.lstrip().startswith(";")]


def assert_same_except_lid(models: list[dict[str, list[str]]]) -> None:
    def without_lid(model):
        return {k: v for k, v in model.items()
                if k not in ("LID_CONTROLS", "LID_USAGE")}
    baseline = without_lid(models[0])
    for i, model in enumerate(models[1:], 1):
        if without_lid(model) != baseline:
            raise AssertionError(f"Scenario {FILES[i].name} changed non-LID inputs")


def validate() -> None:
    models = [sections(p) for p in FILES]
    assert_same_except_lid(models)
    expected_subcats = (set(), {"S1"}, {"S1", "S2", "S3", "S4", "S5", "S6"})
    unit_area = METRICS["lid_definition"]["unit_area_square_feet"]

    for file, model, expected in zip(FILES, models, expected_subcats):
        deployed = entries(model.get("LID_USAGE", []))
        names = {row[0] for row in deployed}
        if names != expected:
            raise AssertionError(f"{file.name}: found {names}, expected {expected}")
        for row in deployed:
            subcat, control = row[0], row[1]
            units, area, width, initial, from_imp, to_perv = map(float, row[2:8])
            if (control != "RG_01" or units != 10 or
                abs(area - unit_area[subcat]) > 0.01 or width != 0 or
                initial != 0 or from_imp != 50 or to_perv != 0):
                raise AssertionError(f"Unexpected LID usage: {row}")

    subcatch_rows = entries(models[0]["SUBCATCHMENTS"])
    areas = {row[0]: float(row[3]) for row in subcatch_rows}
    if abs(sum(areas.values()) - 82.607) > 1e-3:
        raise AssertionError("Unexpected total catchment area")
    for name, area in areas.items():
        footprint = 10 * unit_area[name]
        share = footprint / (area * 43560)
        if not (0.0499 < share < 0.0501):
            raise AssertionError(f"{name} footprint {share:.3%} is not about 5%")

    rain_entries = entries(DATA.read_text().splitlines())
    depths = [float(row[1]) for row in rain_entries]
    if len(depths) != 96 or abs(sum(depths) - 4.2) > 0.0001:
        raise AssertionError("Rainfall file does not contain 96 bins totaling 4.2 in")
    for model in models:
        ref = entries(model["TIMESERIES"])[0]
        if ref[0] != "TS_10Y24H" or ref[1] != "FILE":
            raise AssertionError("Unexpected rain time series configuration")

    print("PASS: non-LID inputs identical across the three scenarios.")
    print("PASS: baseline / S1 / all-six LID assignments and 5% footprints.")
    print("PASS: 96 rainfall increments total 4.20 inches.")
    print("NOTE: run all scenarios in EPA SWMM to check simulation results.")


if __name__ == "__main__":
    validate()
