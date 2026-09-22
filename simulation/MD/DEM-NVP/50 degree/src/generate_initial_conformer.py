#!/usr/bin/env python3
"""Make an RDKit 3D conformer from the reviewed DEM-NVP chemical graph.

Inputs: parameters/chemical_model.json. Outputs: a new directory containing
SDF, PDB, and atom_order.json. The output is an initial construction geometry,
not an equilibrated configuration or a GAFF2 topology. RDKit is required but
is never installed by this script.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_rdkit():
    try:
        from rdkit import Chem
        from rdkit.Chem import AllChem
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "RDKit is unavailable. Install it in an authorized isolated environment, then retry. "
            "No coordinate files were written."
        ) from exc
    return Chem, AllChem


def make_molecule(spec: dict, chem):
    molecule = chem.RWMol()
    name_to_index: dict[str, int] = {}
    for source in spec["atoms"]:
        atom = chem.Atom(source["element"])
        atom.SetNoImplicit(True)
        atom.SetProp("source_name", source["name"])
        atom.SetIntProp("source_index", source["index"])
        name_to_index[source["name"]] = molecule.AddAtom(atom)
    bond_types = {1: chem.BondType.SINGLE, 2: chem.BondType.DOUBLE}
    for bond in spec["bonds"]:
        molecule.AddBond(name_to_index[bond["atom_1"]], name_to_index[bond["atom_2"]], bond_types[bond["order"]])
    result = molecule.GetMol()
    chem.SanitizeMol(result)
    return result


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=root / "parameters/chemical_model.json")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=13054)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise FileExistsError(f"Refusing to overwrite {args.output_dir}")
    chem, all_chem = load_rdkit()
    spec = json.loads(args.input.read_text(encoding="utf-8"))
    molecule = make_molecule(spec, chem)
    embedding = all_chem.ETKDGv3()
    embedding.randomSeed = args.seed
    embedding.useRandomCoords = True
    embedding.maxAttempts = 1000
    if all_chem.EmbedMolecule(molecule, embedding) != 0:
        raise RuntimeError("RDKit ETKDG embedding failed; no files were written.")
    mmff_status = all_chem.MMFFOptimizeMolecule(molecule, maxIters=2000)
    args.output_dir.mkdir(parents=True)
    chem.MolToMolFile(molecule, str(args.output_dir / "dem_nvp_alt10.sdf"))
    chem.MolToPDBFile(molecule, str(args.output_dir / "dem_nvp_alt10.pdb"))
    atom_order = {
        "input_graph": str(args.input),
        "rdkit_version": __import__("rdkit").__version__,
        "embedding": "ETKDGv3 with explicit hydrogen atoms",
        "optimization": "MMFF94s; status 0 means converged",
        "optimization_status": mmff_status,
        "atoms": [
            {
                "rdkit_index": atom.GetIdx(),
                "graph_index": atom.GetIntProp("source_index"),
                "graph_name": atom.GetProp("source_name"),
            }
            for atom in molecule.GetAtoms()
        ],
    }
    (args.output_dir / "atom_order.json").write_text(json.dumps(atom_order, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "written", "output_dir": str(args.output_dir), "atoms": molecule.GetNumAtoms()}))


if __name__ == "__main__":
    main()

