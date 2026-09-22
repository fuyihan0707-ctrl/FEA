"""Prepare traceable sample1 material tables without changing raw source records.

1. Purpose and intended result:
   Extract the raw tensile and compression tables, apply the user-approved first-point
   origin correction, and optionally export documented derived tables for material review.
2. Inputs and outputs:
   Inputs are `sample1-compress.rtf` and `sample1-strain.rtf` (MPa, mm/mm). With
   `--write`, outputs are CSV/JSON files below `derived/sample1_material/`; raw files
   are never changed.
3. Prerequisites and assumptions:
   Python 3 standard library only. The RTF files contain two numeric columns of
   user-confirmed engineering stress and engineering strain.
4. Software requirements and run instructions:
   Run from any directory with `python3 FEA/scripts/prepare_sample1_material.py` for a
   read-only preview, or add `--write` to create derived files.
5. Key parameters:
   The project-relative JSON configuration controls source paths and sign conventions.
   Stress is MPa and strain is mm/mm.
6. Data-processing rules:
   Subtract both coordinates of the first point from each curve; do not smooth, clip,
   interpolate, or remove post-peak data. Compression is exported as negative stress
   and negative strain in the combined curve.
7. Result interpretation:
   The output is derived experimental data, not a fitted material law or a solver-ready
   material card. The combined curve requires review before any OpenRadioss use.
8. Author and dates:
   Author: Codex. Created: 2026-09-18. Last modified: 2026-09-18.
9. Related files:
   `config/sample1_dryrun.json`, `README.md`, `PROJECT_RULES.md`, and
   `KNOWLEDGE_BASE.md` in the FEA project root.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "sample1_dryrun.json"
NUMBER = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?"
PAIR_LINE = re.compile(rf"(?m)^\s*({NUMBER})\s+({NUMBER})\s*$")


@dataclass(frozen=True)
class Curve:
    """A source curve whose values preserve input row order."""

    name: str
    source: Path
    rows: list[tuple[float, float]]


def read_config(path: Path) -> dict:
    """Read the approved case configuration without modifying it."""
    return json.loads(path.read_text(encoding="utf-8"))


def extract_rtf_pairs(path: Path) -> list[tuple[float, float]]:
    """Extract exactly two numeric columns from the project's simple RTF data table."""
    rows = [(float(first), float(second)) for first, second in PAIR_LINE.findall(
        path.read_text(encoding="utf-8")
    )]
    if len(rows) < 2:
        raise ValueError(f"No usable two-column data table found in {path}")
    return rows


def zero_first_point(rows: Iterable[tuple[float, float]]) -> tuple[list[tuple[float, float]], tuple[float, float]]:
    """Apply the user-approved constant origin correction to a single curve."""
    values = list(rows)
    offset_strain, offset_stress = values[0]
    corrected = [
        (strain - offset_strain, stress - offset_stress)
        for strain, stress in values
    ]
    return corrected, (offset_strain, offset_stress)


def source_sha256(path: Path) -> str:
    """Provide a stable source-data identifier for the derived-data report."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def curve_report(curve: Curve, corrected: list[tuple[float, float]], offset: tuple[float, float]) -> dict:
    """Summarize the transformation without changing, smoothing, or fitting data."""
    peak_index = max(range(len(corrected)), key=lambda index: corrected[index][1])
    return {
        "name": curve.name,
        "source_path": str(curve.source.relative_to(PROJECT_ROOT)),
        "source_sha256": source_sha256(curve.source),
        "row_count": len(curve.rows),
        "units": {"strain": "mm/mm", "stress": "MPa"},
        "processing": "subtract first recorded strain and stress",
        "subtracted_offset": {
            "strain_mm_per_mm": offset[0],
            "stress_mpa": offset[1],
        },
        "first_corrected_point": corrected[0],
        "maximum_corrected_stress_mpa": corrected[peak_index][1],
        "strain_at_maximum_corrected_stress_mm_per_mm": corrected[peak_index][0],
        "post_peak_data_preserved": True,
        "smoothing": "none",
        "solver_ready": False,
    }


def write_curve_csv(path: Path, rows: Iterable[tuple[float, float]]) -> None:
    """Write a new derived CSV with unit-bearing column names."""
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["engineering_strain_mm_per_mm", "engineering_stress_mpa"])
        writer.writerows(rows)


def run(config_path: Path, write_outputs: bool) -> dict:
    """Produce a read-only preview or explicitly requested derived-material artifacts."""
    config = read_config(config_path)
    source = config["source_data"]
    compression_path = PROJECT_ROOT / source["compression_rtf"]
    tension_path = PROJECT_ROOT / source["tension_rtf"]

    compression = Curve("compression", compression_path, extract_rtf_pairs(compression_path))
    tension = Curve("tension", tension_path, extract_rtf_pairs(tension_path))
    compression_zeroed, compression_offset = zero_first_point(compression.rows)
    tension_zeroed, tension_offset = zero_first_point(tension.rows)

    # Adopt one sign convention only in the new combined review curve: tension positive.
    compression_signed = [(-strain, -stress) for strain, stress in compression_zeroed]
    compression_signed.reverse()
    combined = compression_signed + tension_zeroed[1:]
    report = {
        "case_id": config["case_id"],
        "status": "derived_material_preview" if not write_outputs else "derived_material_files_written",
        "write_requested": write_outputs,
        "config_path": str(config_path.relative_to(PROJECT_ROOT)),
        "curves": [
            curve_report(compression, compression_zeroed, compression_offset),
            curve_report(tension, tension_zeroed, tension_offset),
        ],
        "source_measure": {
            "stress": source["stress_measure"],
            "strain": source["strain_measure"],
        },
        "combined_curve": {
            "convention": "tension positive; compression negative",
            "row_count": len(combined),
            "smoothing": "none",
            "fit_status": "review required before constitutive fitting",
        },
        "limitations": [
            "Compression and tension use different nominal crosshead speeds.",
            "The combined curve is not evidence of rate-independent material behaviour.",
            "The post-peak tensile region is preserved for traceability but is not approved as a hyperelastic-fit input.",
        ],
    }

    if write_outputs:
        output_directory = PROJECT_ROOT / "derived" / "sample1_material"
        output_directory.mkdir(parents=True, exist_ok=True)
        write_curve_csv(output_directory / "sample1_compression_zeroed.csv", compression_zeroed)
        write_curve_csv(output_directory / "sample1_tension_zeroed.csv", tension_zeroed)
        write_curve_csv(output_directory / "sample1_combined_signed_review.csv", combined)
        (output_directory / "sample1_material_processing_report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Preview or explicitly write sample1 derived material tables.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="Path to the case configuration JSON.")
    parser.add_argument("--write", action="store_true", help="Create derived CSV and JSON files; omit for read-only preview.")
    arguments = parser.parse_args()
    print(json.dumps(run(arguments.config.resolve(), arguments.write), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
