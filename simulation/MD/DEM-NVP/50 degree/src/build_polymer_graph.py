#!/usr/bin/env python3
"""Build an explicit-atom graph and analysis mapping for one [DEM-NVP]n chain.

Input: canonical JSON configuration. Output: JSON to stdout or a new explicit
path. It creates neither 3D coordinates nor force-field parameters.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "config" / "pilot_323K.json"
VALENCE = {"H": 1, "C": 4, "N": 3, "O": 2}


def build_graph(config: dict[str, Any]) -> dict[str, Any]:
    polymer = config["polymer"]
    if polymer["sequence"] != ["DEM", "NVP"]:
        raise ValueError("Only strict [DEM, NVP] is supported.")
    pairs = int(polymer["repeat_pairs_per_chain"])
    if pairs < 1:
        raise ValueError("repeat_pairs_per_chain must be positive.")

    atoms: list[dict[str, Any]] = []
    bonds: list[dict[str, Any]] = []
    groups: dict[str, list[str]] = defaultdict(list)
    by_name: dict[str, dict[str, Any]] = {}

    def add_atom(name: str, element: str, role: str, repeat: int, unit: str) -> str:
        if name in by_name:
            raise ValueError(f"Duplicate atom name: {name}")
        record = {
            "index": len(atoms) + 1,
            "name": name,
            "element": element,
            "formal_charge_e": 0,
            "role": role,
            "repeat_pair": repeat,
            "unit": unit,
        }
        atoms.append(record)
        by_name[name] = record
        groups["polymer_all"].append(name)
        return name

    def add_bond(atom_1: str, atom_2: str, order: int = 1) -> None:
        bonds.append({"atom_1": atom_1, "atom_2": atom_2, "order": order})

    def ester_side(prefix: str, repeat: int, side: str) -> str:
        carbonyl_c = add_atom(f"{prefix}_C{side}", "C", "DEM ester carbonyl carbon", repeat, "DEM")
        carbonyl_o = add_atom(f"{prefix}_O{side}C", "O", "DEM ester carbonyl oxygen", repeat, "DEM")
        ester_o = add_atom(f"{prefix}_O{side}E", "O", "DEM ester alkoxy oxygen", repeat, "DEM")
        ethyl_alpha = add_atom(f"{prefix}_E{side}A", "C", "DEM ethyl alpha carbon", repeat, "DEM")
        ethyl_beta = add_atom(f"{prefix}_E{side}B", "C", "DEM ethyl beta carbon", repeat, "DEM")
        for suffix in ("1", "2"):
            add_bond(ethyl_alpha, add_atom(f"{prefix}_H{side}A{suffix}", "H", "DEM ethyl alpha hydrogen", repeat, "DEM"))
        for suffix in ("1", "2", "3"):
            add_bond(ethyl_beta, add_atom(f"{prefix}_H{side}B{suffix}", "H", "DEM ethyl beta hydrogen", repeat, "DEM"))
        add_bond(carbonyl_c, carbonyl_o, 2)
        add_bond(carbonyl_c, ester_o)
        add_bond(ester_o, ethyl_alpha)
        add_bond(ethyl_alpha, ethyl_beta)
        groups["dem_ester_carbonyl_oxygens"].append(carbonyl_o)
        groups["dem_ester_alkoxy_oxygens"].append(ester_o)
        groups["dem_ethyl_carbons"].extend([ethyl_alpha, ethyl_beta])
        return carbonyl_c

    previous_v2 = None
    first_b1 = None
    final_v2 = None
    for repeat in range(1, pairs + 1):
        dem = f"D{repeat:02d}"
        b1 = add_atom(f"{dem}_B1", "C", "DEM backbone carbon 1", repeat, "DEM")
        hb1 = add_atom(f"{dem}_HB1", "H", "DEM backbone hydrogen", repeat, "DEM")
        b2 = add_atom(f"{dem}_B2", "C", "DEM backbone carbon 2", repeat, "DEM")
        hb2 = add_atom(f"{dem}_HB2", "H", "DEM backbone hydrogen", repeat, "DEM")
        left_c = ester_side(dem, repeat, "L")
        right_c = ester_side(dem, repeat, "R")
        add_bond(b1, b2)
        add_bond(b1, hb1)
        add_bond(b2, hb2)
        add_bond(b1, left_c)
        add_bond(b2, right_c)
        if previous_v2:
            add_bond(previous_v2, b1)
        else:
            first_b1 = b1

        nvp = f"N{repeat:02d}"
        v1 = add_atom(f"{nvp}_V1", "C", "NVP backbone carbon 1", repeat, "NVP")
        v2 = add_atom(f"{nvp}_V2", "C", "NVP backbone carbon 2", repeat, "NVP")
        ring_n = add_atom(f"{nvp}_N", "N", "NVP lactam nitrogen", repeat, "NVP")
        carbonyl_c = add_atom(f"{nvp}_C0", "C", "NVP lactam carbonyl carbon", repeat, "NVP")
        carbonyl_o = add_atom(f"{nvp}_O0", "O", "NVP lactam carbonyl oxygen", repeat, "NVP")
        c3 = add_atom(f"{nvp}_C3", "C", "NVP ring methylene carbon", repeat, "NVP")
        c4 = add_atom(f"{nvp}_C4", "C", "NVP ring methylene carbon", repeat, "NVP")
        c5 = add_atom(f"{nvp}_C5", "C", "NVP ring methylene carbon", repeat, "NVP")
        for suffix in ("1", "2"):
            add_bond(v1, add_atom(f"{nvp}_HV1{suffix}", "H", "NVP backbone methylene hydrogen", repeat, "NVP"))
        add_bond(v2, add_atom(f"{nvp}_HV2", "H", "NVP backbone methine hydrogen", repeat, "NVP"))
        for carbon, label in ((c3, "3"), (c4, "4"), (c5, "5")):
            for suffix in ("1", "2"):
                add_bond(carbon, add_atom(f"{nvp}_H{label}{suffix}", "H", "NVP ring methylene hydrogen", repeat, "NVP"))
        add_bond(b2, v1)
        add_bond(v1, v2)
        add_bond(v2, ring_n)
        add_bond(ring_n, carbonyl_c)
        add_bond(carbonyl_c, carbonyl_o, 2)
        add_bond(carbonyl_c, c3)
        add_bond(c3, c4)
        add_bond(c4, c5)
        add_bond(c5, ring_n)
        groups["nvp_lactam_carbonyl_oxygens"].append(carbonyl_o)
        groups["nvp_ring_atoms"].extend([ring_n, carbonyl_c, carbonyl_o, c3, c4, c5])
        previous_v2, final_v2 = v2, v2

    start_h = add_atom("TERM_START_H", "H", "hydrogen cap at DEM chain start", 0, "TERMINUS")
    end_h = add_atom("TERM_END_H", "H", "hydrogen cap at NVP chain end", pairs + 1, "TERMINUS")
    add_bond(start_h, first_b1)
    add_bond(end_h, final_v2)
    groups["terminal_hydrogens"].extend([start_h, end_h])
    validate_graph(atoms, bonds, config)

    return {
        "schema_version": 1,
        "status": "chemical_connectivity_specification_not_force_field",
        "case_id": config["case_id"],
        "molecule_name": f"DEMNVP{pairs}",
        "chain_termini": "hydrogen_capped",
        "sequence": ["DEM", "NVP"] * pairs,
        "backbone_description": "DEM B1-B2 then NVP V1-V2; each NVP V2 bonds to next DEM B1.",
        "monomer_reference_smiles": {
            "DEM": "CCOC(=O)/C=C\\C(=O)OCC",
            "NVP": "C=CN1CCCC1=O",
        },
        "atom_count": len(atoms),
        "bond_count": len(bonds),
        "atoms": atoms,
        "bonds": bonds,
        "analysis_groups": {
            group: [{"name": name, "index": by_name[name]["index"]} for name in names]
            for group, names in sorted(groups.items())
        },
        "parameterization_gate": {
            "required_method": "GAFF2 atom types and whole-chain AM1-BCC charges",
            "required_checks": [
                "net chain charge equals zero",
                "final topology atom order agrees with this map",
                "all missing parmchk2 terms are reviewed",
                "GROMACS grompp accepts final topology without maxwarn",
            ],
            "forbidden_shortcut": "Do not concatenate independent unsaturated DEM and NVP monomer topologies.",
        },
    }


def validate_graph(atoms: list[dict[str, Any]], bonds: list[dict[str, Any]], config: dict[str, Any]) -> None:
    by_name = {record["name"]: record for record in atoms}
    valence: Counter[str] = Counter()
    for bond in bonds:
        for name in (bond["atom_1"], bond["atom_2"]):
            valence[name] += bond["order"]
    errors = [
        f"{name} has valence {valence[name]}, expected {VALENCE[record['element']]}"
        for name, record in by_name.items()
        if valence[name] != VALENCE[record["element"]]
    ]
    if errors:
        raise ValueError("; ".join(errors))
    expected = Counter()
    for formula in config["polymer"]["monomer_formulae"].values():
        expected.update(formula)
    repeat_pairs = config["polymer"]["repeat_pairs_per_chain"]
    for element in tuple(expected):
        expected[element] *= repeat_pairs
    expected["H"] += 2
    observed = Counter(record["element"] for record in atoms)
    if observed != expected:
        raise ValueError(f"Formula mismatch: observed={dict(observed)}, expected={dict(expected)}")
    if sum(record["formal_charge_e"] for record in atoms) != 0:
        raise ValueError("Chain must be neutral.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--write", type=Path, help="Write JSON only to a new path; existing files are refused.")
    args = parser.parse_args()
    graph = build_graph(json.loads(args.config.read_text(encoding="utf-8")))
    rendered = json.dumps(graph, indent=2, ensure_ascii=False) + "\n"
    if args.write:
        if args.write.exists():
            raise FileExistsError(f"Refusing to overwrite {args.write}")
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
