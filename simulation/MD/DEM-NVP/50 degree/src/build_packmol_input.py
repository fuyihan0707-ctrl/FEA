#!/usr/bin/env python3
"""Render Packmol input for the 60 wt% DEM–NVP 50 °C pilot.

Purpose: create a reproducible packing instruction after validated single-chain
and water PDB files exist. Inputs: canonical JSON and two PDB paths. Output:
Packmol text to stdout or an explicit new file. Coordinates are not generated
by this script, and existing files are never overwritten.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from calculate_composition import DEFAULT_CONFIG, calculate


def render(config: dict, polymer_pdb: Path, water_pdb: Path) -> str:
    """Render a Packmol input deck using the computed integer water count."""
    composition = calculate(config)
    packing = config["packing"]
    polymer = config["polymer"]
    upper_angstrom = float(packing["initial_box_length_nm"]) * 10.0
    return f"""# Generated from {config['case_id']}; inspect topology mass before use.
tolerance {packing['packmol_tolerance_angstrom']:.3f}
filetype pdb
output packed_system.pdb
seed {packing['seed']}

structure {polymer_pdb}
  number {polymer['chain_count']}
  inside box 0. 0. 0. {upper_angstrom:.3f} {upper_angstrom:.3f} {upper_angstrom:.3f}
end structure

structure {water_pdb}
  number {composition['tip3p_water_count']}
  inside box 0. 0. 0. {upper_angstrom:.3f} {upper_angstrom:.3f} {upper_angstrom:.3f}
end structure
"""


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--polymer-pdb", type=Path, default=root / "parameters/coordinates/dem_nvp_alt10.pdb")
    parser.add_argument("--water-pdb", type=Path, default=root / "parameters/coordinates/tip3p_water.pdb")
    parser.add_argument("--write", type=Path, help="Write Packmol input to a new file; otherwise print only.")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    rendered = render(config, args.polymer_pdb, args.water_pdb)
    if args.write:
        if args.write.exists():
            raise FileExistsError(f"Refusing to overwrite {args.write}")
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()

