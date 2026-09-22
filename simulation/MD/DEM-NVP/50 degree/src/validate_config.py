#!/usr/bin/env python3
"""Read-only validation of the DEM–NVP 50 °C pilot configuration.

Purpose: reject invalid physical/count settings before topology or packing work.
Input: canonical JSON configuration. Output: JSON report on stdout. No solver,
coordinate, or file-state changes are performed.
"""
from __future__ import annotations

import json

from calculate_composition import DEFAULT_CONFIG, calculate


def validate(config: dict) -> list[str]:
    """Return every configuration violation without modifying any files."""
    errors: list[str] = []
    if config.get("temperature_K") != 323.15:
        errors.append("This directory is reserved for the 323.15 K pilot.")
    if config.get("polymer", {}).get("sequence") != ["DEM", "NVP"]:
        errors.append("Sequence must be the strict DEM/NVP alternation.")
    if config.get("solvent", {}).get("polymer_mass_fraction") != 0.60:
        errors.append("The user-confirmed pilot composition is 0.60 polymer mass fraction.")
    if config.get("packing", {}).get("initial_box_length_nm", 0.0) <= 0.0:
        errors.append("Initial box length must be positive in nm.")
    if config.get("solvent", {}).get("ions") != "none":
        errors.append("The first neutral screening model includes no ions.")
    try:
        calculate(config)
    except (KeyError, TypeError, ValueError) as exc:
        errors.append(str(exc))
    return errors


def main() -> None:
    config = json.loads(DEFAULT_CONFIG.read_text(encoding="utf-8"))
    errors = validate(config)
    report = {
        "config": str(DEFAULT_CONFIG),
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "composition": calculate(config) if not errors else None,
        "next_gate": "Validate the polymerized-chain topology and its atom mapping before generating coordinates.",
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

