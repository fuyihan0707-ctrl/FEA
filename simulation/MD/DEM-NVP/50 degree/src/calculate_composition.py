#!/usr/bin/env python3
"""Calculate neutral DEM–NVP/water composition from the canonical JSON config.

Purpose: report the integer TIP3P water count matching the configured polymer
mass fraction. Inputs: JSON configuration; outputs: JSON to stdout or an
explicit new file. Units: g mol^-1 and dimensionless mass fraction. This
utility never builds coordinates or changes a simulation state.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ATOMIC_MASS_G_MOL = {"H": 1.008, "C": 12.011, "N": 14.007, "O": 15.999}
DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "config" / "pilot_323K.json"


def formula_mass_g_mol(formula: dict[str, int]) -> float:
    """Return formula mass and reject unsupported elements/counts."""
    if not formula:
        raise ValueError("Formula cannot be empty.")
    total = 0.0
    for element, count in formula.items():
        if element not in ATOMIC_MASS_G_MOL or not isinstance(count, int) or count < 0:
            raise ValueError(f"Invalid formula entry: {element}={count!r}")
        total += ATOMIC_MASS_G_MOL[element] * count
    return total


def calculate(config: dict) -> dict:
    """Calculate composition from a strict alternating, neutral pilot model."""
    polymer = config["polymer"]
    solvent = config["solvent"]
    pairs = polymer["repeat_pairs_per_chain"]
    chains = polymer["chain_count"]
    if not isinstance(pairs, int) or pairs < 1 or not isinstance(chains, int) or chains < 1:
        raise ValueError("repeat_pairs_per_chain and chain_count must be positive integers.")
    sequence = polymer["sequence"]
    if sequence != ["DEM", "NVP"]:
        raise ValueError("This reduced model requires the strict alternating sequence [DEM, NVP].")
    monomer_mass = sum(formula_mass_g_mol(polymer["monomer_formulae"][unit]) for unit in sequence)
    chain_mass = pairs * monomer_mass + float(polymer["terminal_mass_g_mol_per_chain"])
    total_polymer_mass = chains * chain_mass
    mass_fraction = float(solvent["polymer_mass_fraction"])
    if not 0.0 < mass_fraction < 1.0:
        raise ValueError("polymer_mass_fraction must be between zero and one.")
    water_mass = formula_mass_g_mol(solvent["water_formula"])
    target_water_mass = total_polymer_mass * (1.0 - mass_fraction) / mass_fraction
    water_count = round(target_water_mass / water_mass)
    achieved_fraction = total_polymer_mass / (total_polymer_mass + water_count * water_mass)
    return {
        "case_id": config["case_id"],
        "assumption": "Hydrogen-capped chain mass is provisional; replace after topology validation.",
        "monomer_pair_mass_g_mol": round(monomer_mass, 6),
        "chain_mass_g_mol": round(chain_mass, 6),
        "total_polymer_mass_g_mol": round(total_polymer_mass, 6),
        "water_mass_g_mol": round(water_mass, 6),
        "target_polymer_mass_fraction": mass_fraction,
        "tip3p_water_count": water_count,
        "achieved_polymer_mass_fraction": round(achieved_fraction, 8),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, help="Write JSON only to a new path; existing files are refused.")
    args = parser.parse_args()
    result = calculate(json.loads(args.config.read_text(encoding="utf-8")))
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        if args.output.exists():
            raise FileExistsError(f"Refusing to overwrite {args.output}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()

