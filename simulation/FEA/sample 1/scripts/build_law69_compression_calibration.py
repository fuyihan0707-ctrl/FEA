"""Create a documented compression-priority candidate curve for OpenRadioss LAW69.

1. Purpose and intended result:
   Create a monotonic, uniformly sampled candidate calibration table from sample1 compression data.
2. Inputs and outputs:
   Input: derived/sample1_material/sample1_compression_zeroed.csv in MPa and mm/mm.
   Output with --write: a candidate CSV and provenance JSON in the same directory.
3. Prerequisites and assumptions:
   Python 3 standard library. The selected range is measured engineering compression from 0 to 0.40.
4. Software requirements and run instructions:
   Run python3 FEA/scripts/build_law69_compression_calibration.py for preview; add --write to create files.
5. Key parameters:
   Maximum compression is 0.40 mm/mm and output spacing is 0.005 mm/mm.
6. Data-processing rules:
   Isotonic regression removes only local stress reversals; linear interpolation resamples without extrapolation.
7. Result interpretation:
   The result is a candidate curve, not a validated material card; Starter fit and smoke tests remain required.
8. Author and dates:
   Author: Codex. Created: 2026-09-18. Last modified: 2026-09-18.
9. Related files:
   config/sample1_dryrun.json, scripts/prepare_sample1_material.py, README.md,
   PROJECT_RULES.md, and KNOWLEDGE_BASE.md in the FEA project root.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DERIVED_DIRECTORY = PROJECT_ROOT / "derived" / "sample1_material"
SOURCE_CSV = DERIVED_DIRECTORY / "sample1_compression_zeroed.csv"
OUTPUT_CSV = DERIVED_DIRECTORY / "sample1_law69_compression_calibration.csv"
REPORT_JSON = DERIVED_DIRECTORY / "sample1_law69_compression_calibration_report.json"
MAX_COMPRESSION = 0.40
STRAIN_INCREMENT = 0.005


def read_curve(path: Path) -> list[tuple[float, float]]:
    """Read the approved derived curve and retain only the measured calibration range."""
    with path.open(encoding="utf-8", newline="") as stream:
        rows = [
            (float(row["engineering_strain_mm_per_mm"]), float(row["engineering_stress_mpa"]))
            for row in csv.DictReader(stream)
        ]
    if not rows or rows[0] != (0.0, 0.0):
        raise ValueError("Compression source must begin at the documented zeroed origin.")
    if any(next_strain <= strain for (strain, _), (next_strain, _) in zip(rows, rows[1:])):
        raise ValueError("Compression source strain must be strictly increasing.")
    selected: list[tuple[float, float]] = []
    for row in rows:
        selected.append(row)
        if row[0] >= MAX_COMPRESSION:
            break
    if selected[-1][0] < MAX_COMPRESSION:
        raise ValueError("Measured compression data do not reach the requested 0.40 limit.")
    return selected


def isotonic_increasing(values: list[float]) -> list[float]:
    """Apply pooled-adjacent-violators regression to enforce nondecreasing stress only."""
    blocks: list[list[float]] = []  # Each block stores [stress_sum, point_count].
    for value in values:
        blocks.append([value, 1.0])
        while len(blocks) >= 2 and blocks[-2][0] / blocks[-2][1] > blocks[-1][0] / blocks[-1][1]:
            right = blocks.pop()
            blocks[-1][0] += right[0]
            blocks[-1][1] += right[1]
    corrected: list[float] = []
    for total, count in blocks:
        corrected.extend([total / count] * int(count))
    return corrected


def interpolate(rows: list[tuple[float, float]], strain: float) -> float:
    """Interpolate inside the measured range and reject all extrapolation."""
    if not rows[0][0] <= strain <= rows[-1][0]:
        raise ValueError(f"Requested strain {strain} lies outside the measured calibration range.")
    for (left_strain, left_stress), (right_strain, right_stress) in zip(rows, rows[1:]):
        if left_strain <= strain <= right_strain:
            fraction = (strain - left_strain) / (right_strain - left_strain)
            return left_stress + fraction * (right_stress - left_stress)
    return rows[-1][1]


def build_candidate() -> tuple[list[tuple[float, float]], dict]:
    """Convert measured positive compression to a signed, increasing-strain LAW69 candidate."""
    raw = read_curve(SOURCE_CSV)
    raw_stresses = [stress for _, stress in raw]
    corrected_stresses = isotonic_increasing(raw_stresses)
    monotonic = [(strain, stress) for (strain, _), stress in zip(raw, corrected_stresses)]
    output_count = round(MAX_COMPRESSION / STRAIN_INCREMENT) + 1
    uniform_positive = [
        (round(index * STRAIN_INCREMENT, 12), interpolate(monotonic, index * STRAIN_INCREMENT))
        for index in range(output_count)
    ]

    # LAW69 uses negative strain and stress for compression; its abscissa must increase.
    law69_curve = [(-strain, -stress) for strain, stress in uniform_positive]
    law69_curve.reverse()
    corrections = [abs(corrected - original) for original, corrected in zip(raw_stresses, corrected_stresses)]
    report = {
        "status": "candidate_curve_preview_not_starter_verified",
        "source_csv": str(SOURCE_CSV.relative_to(PROJECT_ROOT)),
        "source_rows_within_0_to_0p40_compression": len(raw),
        "selected_measured_range": {
            "compression_strain_mm_per_mm": [0.0, MAX_COMPRESSION],
            "stress_mpa": [raw[0][1], interpolate(monotonic, MAX_COMPRESSION)]
        },
        "transformations": [
            "Rows beyond 0.40 compression are outside this candidate calibration scope, except for the first measured point above 0.40 used only to interpolate the 0.40 endpoint; no source file was changed.",
            "Pooled-adjacent-violators isotonic regression made stress nondecreasing with compression strain.",
            "Linear interpolation resampled the monotonic curve at 0.005 engineering-strain intervals.",
            "Compression strain and stress were negated and reversed for LAW69 sign convention."
        ],
        "isotonic_correction": {
            "source_rows_changed": sum(value > 1e-15 for value in corrections),
            "maximum_absolute_stress_change_mpa": max(corrections),
            "mean_absolute_stress_change_mpa": sum(corrections) / len(corrections)
        },
        "output": {
            "path": str(OUTPUT_CSV.relative_to(PROJECT_ROOT)),
            "row_count": len(law69_curve),
            "columns": ["engineering_strain_mm_per_mm", "engineering_stress_mpa"],
            "sign_convention": "negative values are compression; strain increases from -0.40 to 0.00"
        },
        "limitations": [
            "This curve is compression-priority and does not validate tensile response.",
            "It contains no unloading, hysteresis, failure, or strain-rate calibration.",
            "OpenRadioss Starter fit error and one-element reproduction remain required checks."
        ]
    }
    return law69_curve, report


def write_candidate(rows: list[tuple[float, float]], report: dict) -> None:
    """Write the new candidate artifacts only after explicit --write invocation."""
    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["engineering_strain_mm_per_mm", "engineering_stress_mpa"])
        writer.writerows(rows)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Preview or write the compression-priority LAW69 candidate curve.")
    parser.add_argument("--write", action="store_true", help="Create the candidate CSV and provenance report.")
    arguments = parser.parse_args()
    rows, report = build_candidate()
    if arguments.write:
        report["status"] = "candidate_curve_written_not_starter_verified"
        write_candidate(rows, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
